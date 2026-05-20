"""Phonology layer: validate and re-segment IPA via merkmal.

Best-of policy: trust source Segments where they are present AND all
tokens are recognized by merkmal. Otherwise, attempt re-segmentation
from the raw Form via greedy longest-match against merkmal's inventory.

If re-segmentation also fails to cover the form completely, the field is
emitted as-is and flagged not CLTS-compliant.
"""

from __future__ import annotations

import logging
import re
from functools import lru_cache

import merkmal

logger = logging.getLogger(__name__)

SYSTEM = "phoible"
SEPARATORS = ("+", "_")


@lru_cache(maxsize=1)
def _grapheme_set() -> frozenset[str]:
    return frozenset(merkmal.get_system(SYSTEM).list_graphemes())


@lru_cache(maxsize=1)
def _max_grapheme_len() -> int:
    return max((len(g) for g in _grapheme_set()), default=0)


def is_valid_grapheme(g: str) -> bool:
    if not g:
        return False
    if g in SEPARATORS:
        return True
    return merkmal.get_features(g, system=SYSTEM) is not None


def segments_are_valid(segments: str) -> bool:
    if not segments or not segments.strip():
        return False
    tokens = [t for t in segments.split() if t]
    if not tokens:
        return False
    return all(is_valid_grapheme(t) for t in tokens)


_SPACES_RE = re.compile(r"\s+")


def resegment(form: str) -> tuple[str, bool]:
    """Greedy longest-match segmentation against merkmal's inventory.

    Returns (space-joined segments, fully_covered).
    Underscores and pluses are preserved as morpheme separators.
    Whitespace in the input becomes nothing (multiple forms should be
    split upstream).
    """
    if not form:
        return "", False
    form = _SPACES_RE.sub("", form)
    if not form:
        return "", False

    inventory = _grapheme_set()
    max_len = _max_grapheme_len()
    tokens: list[str] = []
    fully_covered = True
    i = 0
    n = len(form)
    while i < n:
        ch = form[i]
        if ch in SEPARATORS:
            tokens.append(ch)
            i += 1
            continue
        matched = ""
        end = min(n, i + max_len)
        for j in range(end, i, -1):
            cand = form[i:j]
            if cand in inventory:
                matched = cand
                break
        if matched:
            tokens.append(matched)
            i += len(matched)
        else:
            tokens.append(ch)
            fully_covered = False
            i += 1
    return " ".join(tokens), fully_covered


def normalize_segments(source_segments: str, source_form: str) -> tuple[str, str]:
    """Return (segments, segments_source).

    Policy:
      1. If source segments are present and fully recognized → use them
         (segments_source = 'source').
      2. Else attempt re-segmentation from the form. If it covers the
         whole string → use it (segments_source = 'resegmented').
      3. Else leave segments as-is (or empty) and mark 'unclean'.
    """
    if source_segments and segments_are_valid(source_segments):
        return source_segments.strip(), "source"
    if source_form:
        reseg, ok = resegment(source_form)
        if ok and reseg:
            return reseg, "resegmented"
    return (source_segments or "").strip(), "unclean"
