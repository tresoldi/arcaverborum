"""Parameter ID generation for Wiktionary senses."""

from __future__ import annotations

import hashlib
import re
import unicodedata


def slugify(word: str) -> str:
    s = unicodedata.normalize("NFKD", word)
    s = s.encode("ascii", "ignore").decode("ascii").lower()
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s or "unknown"


def make_parameter_id(word: str, pos: str, sense: str) -> str:
    slug = slugify(word)
    sense_hash = hashlib.sha256(sense.encode("utf-8")).hexdigest()[:8]
    return f"wikt_{slug}_{pos}_{sense_hash}"


def make_parameter_name(word: str, pos: str, sense: str) -> str:
    if sense:
        return f"{word} ({pos}): {sense}"
    return f"{word} ({pos})"


def parse_parameter_name(name: str) -> tuple[str, str, str]:
    """Invert make_parameter_name: 'water (noun): liquid' -> ('water', 'noun', 'liquid')."""
    paren = name.find("(")
    if paren < 0:
        return name, "", ""
    word = name[:paren].strip()
    rest = name[paren + 1 :]
    close = rest.find(")")
    if close < 0:
        return word, rest.strip(), ""
    pos = rest[:close].strip()
    sense = rest[close + 1 :].lstrip(": ").strip()
    return word, pos, sense
