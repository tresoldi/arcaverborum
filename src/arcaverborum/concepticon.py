"""Concepticon data loading and auto-mapping for Wiktionary parameters."""

from __future__ import annotations

import csv
import io
import urllib.request
from dataclasses import dataclass
from pathlib import Path

CONCEPTICON_URL = (
    "https://raw.githubusercontent.com/concepticon/concepticon-data/"
    "master/concepticondata/concepticon.tsv"
)
RAW_CACHE = Path("raw/concepticon/concepticon.tsv")

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


def _read_concepticon_text(source: str | Path | None = None) -> str:
    """Read the Concepticon TSV from an explicit path, the raw cache, or URL."""
    if source and Path(source).exists():
        return Path(source).read_text(encoding="utf-8")
    if RAW_CACHE.exists():
        return RAW_CACHE.read_text(encoding="utf-8")
    url = str(source) if source and str(source).startswith("http") else CONCEPTICON_URL
    return urllib.request.urlopen(url, timeout=30).read().decode("utf-8")


def _entry_from_row(row: dict) -> ConcepticonEntry:
    # csv.DictReader fills missing trailing fields with None.
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


def load_concepticon(source: str | Path | None = None) -> dict[str, ConcepticonEntry]:
    """Load Concepticon TSV into {UPPER_GLOSS: entry} dict (first gloss wins)."""
    reader = csv.DictReader(io.StringIO(_read_concepticon_text(source)), delimiter="\t")
    index: dict[str, ConcepticonEntry] = {}
    for row in reader:
        gloss = row.get("GLOSS", "").strip()
        if not gloss:
            continue
        key = gloss.upper()
        if key not in index:
            index[key] = _entry_from_row(row)
    return index


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
    concepticon: dict[str, ConcepticonEntry],
) -> tuple[str, str] | None:
    """Try to match a Wiktionary word+POS to a Concepticon concept.

    Uses exact normalized-gloss matching with POS compatibility filtering.
    Returns (concepticon_id, concepticon_gloss) or None.
    """
    key = word.strip().upper()
    if not key:
        return None

    entry = concepticon.get(key)
    if entry is None:
        return None

    allowed = POS_TO_CATEGORIES.get(pos)
    if allowed is not None and entry.ontological_category not in allowed:
        return None

    return entry.id, entry.gloss
