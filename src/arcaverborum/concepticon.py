"""Concepticon data loading and auto-mapping for Wiktionary parameters."""

from __future__ import annotations

import csv
import io
import logging
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

from arcaverborum.concepts import normalize_gloss

logger = logging.getLogger(__name__)

CONCEPTICON_URL = (
    "https://raw.githubusercontent.com/concepticon/concepticon-data/"
    "master/concepticondata/concepticon.tsv"
)
RAW_CACHE = Path("raw/concepticon/concepticon.tsv")

DATA_DIR = Path(__file__).parent / "data"
ALIASES_CSV = DATA_DIR / "concepticon_aliases.csv"
POS_BLOCKLIST_CSV = DATA_DIR / "concepticon_pos_blocklist.csv"

POS_TO_CATEGORIES: dict[str, set[str]] = {
    "noun": {"Person/Thing", "Other"},
    "verb": {"Action/Process"},
    "adj": {"Property"},
    "adv": {"Property", "Other"},
    "num": {"Number"},
}


@dataclass(frozen=True, slots=True)
class ConcepticonEntry:
    id: str
    gloss: str
    ontological_category: str
    semantic_field: str = ""
    definition: str = ""
    replacement_id: str = ""


@dataclass(frozen=True, slots=True)
class ConcepticonIndex:
    by_gloss: dict[str, ConcepticonEntry]
    by_base: dict[str, list[ConcepticonEntry]]
    by_alias: dict[str, ConcepticonEntry]
    pos_blocklist: set[tuple[str, str]] = field(default_factory=set)


def _read_concepticon_text(source: str | Path | None = None) -> str:
    """Read the Concepticon TSV from an explicit path, the raw cache, or URL."""
    if source and Path(source).exists():
        return Path(source).read_text(encoding="utf-8")
    if RAW_CACHE.exists():
        return RAW_CACHE.read_text(encoding="utf-8")
    url = str(source) if source and str(source).startswith("http") else CONCEPTICON_URL
    return urllib.request.urlopen(url, timeout=30).read().decode("utf-8")


def _entry_from_row(row: dict) -> ConcepticonEntry:
    def g(key: str) -> str:
        return (row.get(key) or "").strip()

    return ConcepticonEntry(
        id=g("ID"),
        gloss=g("GLOSS"),
        ontological_category=g("ONTOLOGICAL_CATEGORY"),
        semantic_field=g("SEMANTICFIELD"),
        definition=g("DEFINITION"),
        replacement_id=g("REPLACEMENT_ID"),
    )


def _read_entries(source: str | Path | None = None) -> list[ConcepticonEntry]:
    reader = csv.DictReader(io.StringIO(_read_concepticon_text(source)), delimiter="\t")
    entries = []
    for row in reader:
        gloss = row.get("GLOSS", "").strip()
        if gloss:
            entries.append(_entry_from_row(row))
    return entries


def _build_gloss_index(entries: list[ConcepticonEntry]) -> dict[str, ConcepticonEntry]:
    index: dict[str, ConcepticonEntry] = {}
    for e in entries:
        key = e.gloss.upper()
        if key not in index:
            index[key] = e
    return index


def _build_base_index(
    entries: list[ConcepticonEntry],
    gloss_index: dict[str, ConcepticonEntry],
) -> dict[str, list[ConcepticonEntry]]:
    base_index: dict[str, list[ConcepticonEntry]] = {}
    for e in entries:
        label, qualifier = normalize_gloss(e.gloss)
        if not qualifier:
            continue
        base_key = label.upper()
        if base_key in gloss_index:
            continue
        base_index.setdefault(base_key, []).append(e)
    return base_index


def _load_aliases(
    by_id: dict[str, ConcepticonEntry],
    path: Path = ALIASES_CSV,
) -> dict[str, ConcepticonEntry]:
    index: dict[str, ConcepticonEntry] = {}
    if not path.exists():
        return index
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            alias = (row.get("alias") or "").strip()
            cid = (row.get("concepticon_id") or "").strip()
            if not alias or not cid:
                continue
            entry = by_id.get(cid)
            if entry is None:
                logger.warning("Alias %r → Concepticon %s not found, skipping", alias, cid)
                continue
            key = alias.upper()
            if key not in index:
                index[key] = entry
    return index


def _load_pos_blocklist(path: Path = POS_BLOCKLIST_CSV) -> set[tuple[str, str]]:
    blocklist: set[tuple[str, str]] = set()
    if not path.exists():
        return blocklist
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            word = (row.get("word") or "").strip().upper()
            pos = (row.get("pos") or "").strip()
            if word and pos:
                blocklist.add((word, pos))
    return blocklist


def load_concepticon(source: str | Path | None = None) -> ConcepticonIndex:
    """Load Concepticon and build the three-tier matching index."""
    entries = _read_entries(source)
    by_gloss = _build_gloss_index(entries)
    by_base = _build_base_index(entries, by_gloss)

    by_id: dict[str, ConcepticonEntry] = {}
    for e in entries:
        by_id.setdefault(e.id, e)

    by_alias = _load_aliases(by_id)
    pos_blocklist = _load_pos_blocklist()
    return ConcepticonIndex(
        by_gloss=by_gloss,
        by_base=by_base,
        by_alias=by_alias,
        pos_blocklist=pos_blocklist,
    )


def load_concepticon_by_id(source: str | Path | None = None) -> dict[str, ConcepticonEntry]:
    """Load Concepticon TSV into {ID: entry} dict over every concept.

    Unlike ``load_concepticon`` (gloss-keyed, lossy on duplicate glosses)
    this keeps one entry per Concepticon id — the form the concept
    catalog bootstrap needs.
    """
    reader = csv.DictReader(io.StringIO(_read_concepticon_text(source)), delimiter="\t")
    index: dict[str, ConcepticonEntry] = {}
    for row in reader:
        cid = row.get("ID", "").strip()
        if cid:
            index[cid] = _entry_from_row(row)
    return index


def match_parameter(
    word: str,
    pos: str,
    index: ConcepticonIndex,
) -> tuple[str, str] | None:
    """Match a Wiktionary word+POS to a Concepticon concept.

    Three-tier cascade: exact gloss → base form → alias.
    POS filtering is replaced by a curated blocklist for exact/alias
    matches, and used only for disambiguation on base-form matches.
    """
    key = word.strip().upper()
    if not key:
        return None

    blocked = index.pos_blocklist

    # Tier 1: exact gloss
    entry = index.by_gloss.get(key)
    if entry is not None and (key, pos) not in blocked:
        return entry.id, entry.gloss

    # Tier 2: base form (parenthetical-stripped)
    candidates = index.by_base.get(key)
    if candidates is not None:
        if len(candidates) == 1:
            e = candidates[0]
            if (key, pos) not in blocked:
                return e.id, e.gloss
        else:
            allowed = POS_TO_CATEGORIES.get(pos)
            if allowed is not None:
                compatible = [e for e in candidates if e.ontological_category in allowed]
                if len(compatible) == 1 and (key, pos) not in blocked:
                    return compatible[0].id, compatible[0].gloss

    # Tier 3: alias
    entry = index.by_alias.get(key)
    if entry is not None and (key, pos) not in blocked:
        return entry.id, entry.gloss

    return None
