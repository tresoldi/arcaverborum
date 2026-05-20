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


def load_concepticon(source: str | Path | None = None) -> dict[str, ConcepticonEntry]:
    """Load Concepticon TSV into {UPPER_GLOSS: entry} dict."""
    if source and Path(source).exists():
        data = Path(source).read_text(encoding="utf-8")
    elif RAW_CACHE.exists():
        data = RAW_CACHE.read_text(encoding="utf-8")
    else:
        url = str(source) if source and str(source).startswith("http") else CONCEPTICON_URL
        data = urllib.request.urlopen(url, timeout=30).read().decode("utf-8")

    index: dict[str, ConcepticonEntry] = {}
    reader = csv.DictReader(io.StringIO(data), delimiter="\t")
    for row in reader:
        gloss = row.get("GLOSS", "").strip()
        if not gloss:
            continue
        entry = ConcepticonEntry(
            id=row.get("ID", "").strip(),
            gloss=gloss,
            ontological_category=row.get("ONTOLOGICAL_CATEGORY", "").strip(),
        )
        key = gloss.upper()
        if key not in index:
            index[key] = entry

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
