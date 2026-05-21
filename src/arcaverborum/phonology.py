"""Phonology layer: validate and re-segment IPA via merkmal.

Policy: trust source Segments where they are present AND all tokens are
recognized by merkmal ('source'). Source segments that are present but
not fully recognized are kept verbatim and flagged 'unclean' — real IPA
is never discarded in favour of re-segmenting the (often orthographic)
form, so a later normalization pass can reclaim those tokens in place.
Only when source segments are absent do we attempt re-segmentation from
the Form via greedy longest-match against merkmal's inventory
('resegmented'); if that fails to cover the form, it is 'unclean'.
"""

from __future__ import annotations

import logging
import re
import unicodedata
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


# --- TEMPORARY affricate normalization (remove once merkmal handles it) ---
# merkmal's phoible system stores the postalveolar affricates with a
# retracted stop (t̠ʃ / d̠ʒ, U+0320) and rejects the plain tʃ / dʒ that
# IE-CoR and many sources write. That is BIPA/CLTS canonicalization and
# belongs in merkmal — being reworked at ~/nas-dev/new_chl/merkmal (with
# Go support). Until that lands we normalize here so the real source IPA
# validates instead of being discarded as 'unclean'. Substring replacement
# also fixes the variants (tʃʰ→t̠ʃʰ, dʒʱ→d̠ʒʱ, tʃʲ→t̠ʃʲ, …) since the
# diacritic simply inserts between stop and sibilant. REMOVE this and the
# call in normalize_segments once merkmal canonicalizes affricates. See the
# note in the merkmal rework dir.
_AFFRICATE_NORMALIZATION = {
    "tʃ": "t̠ʃ",   # tʃ → t̠ʃ
    "dʒ": "d̠ʒ",   # dʒ → d̠ʒ
}


def _normalize_affricates(segments: str) -> str:
    for plain, retracted in _AFFRICATE_NORMALIZATION.items():
        if plain in segments:
            segments = segments.replace(plain, retracted)
    return segments


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


def load_profile(path) -> dict[str, str]:
    """Load an orthographic profile: ``Grapheme`` → ``IPA`` (tab-separated).

    A grapheme is any orthographic substring (a letter, a digraph, or a
    whole word for hard-coded forms); its IPA value is the (possibly
    space-separated, possibly empty for a deletion) segment string it maps
    to. Returns ``{}`` when the file is absent or has only a header.
    """
    from pathlib import Path

    p = Path(path)
    if not p.exists():
        return {}
    profile: dict[str, str] = {}
    with p.open(encoding="utf-8") as f:
        f.readline()  # skip header: Grapheme<TAB>IPA[<TAB>notes]
        for line in f:
            if not line.strip():
                continue
            cols = line.rstrip("\n").split("\t")
            grapheme = cols[0]
            if grapheme == "" or grapheme.startswith("#"):
                continue
            ipa = cols[1] if len(cols) > 1 else ""
            profile[unicodedata.normalize("NFC", grapheme)] = ipa.strip()
    return profile


def apply_profile(form: str, profile: dict[str, str]) -> tuple[str, bool]:
    """Greedy longest-match segmentation of ``form`` against ``profile``.

    Returns (space-joined IPA segments, fully_covered). A grapheme mapping
    to an empty IPA deletes that orthographic unit. Whitespace not claimed
    by an explicit profile rule becomes a word-boundary token ``_`` (multi-
    word forms stay covered, with their boundary preserved). ``fully_covered``
    is False if any non-space character is matched by no grapheme.
    """
    if not form or not profile:
        return "", False
    form = unicodedata.normalize("NFC", form)
    max_len = max(len(g) for g in profile)
    out: list[str] = []
    covered = True
    i, n = 0, len(form)
    while i < n:
        matched = ""
        for j in range(min(n, i + max_len), i, -1):
            if form[i:j] in profile:
                matched = form[i:j]
                break
        if matched:
            ipa = profile[matched]
            if ipa:
                out.append(ipa)
            i += len(matched)
        elif form[i].isspace():
            if out and out[-1] != "_":
                out.append("_")
            i += 1
        else:
            covered = False
            i += 1
    while out and out[0] == "_":
        out.pop(0)
    while out and out[-1] == "_":
        out.pop()
    return _SPACES_RE.sub(" ", " ".join(out)).strip(), covered


def normalize_segments(
    source_segments: str, source_form: str, profile: dict[str, str] | None = None,
) -> tuple[str, str]:
    """Return (segments, segments_source).

    Policy (prefer real source IPA over a guess from the orthography):
      1. Source segments present and fully recognized → use them
         (segments_source = 'source').
      2. Source segments present but not fully recognized → keep them
         verbatim and mark 'unclean'. We do NOT discard real IPA in favour
         of deriving segments from the (often orthographic) form: a later
         normalization pass can reclaim these tokens in place.
      3. No source segments but an orthographic profile is given → the
         profile is authoritative for this variety: if it covers the whole
         form use its IPA ('profile'), otherwise 'unclean' (a profile miss
         flags an incomplete profile; we do NOT fall back to re-segmenting
         the orthography, which is exactly what the profile replaces).
      4. No source segments and no profile → attempt re-segmentation from
         the form. If it covers the whole string → 'resegmented', else
         'unclean'.
    """
    src = (source_segments or "").strip()
    if src:
        src = _normalize_affricates(src)  # TEMP: see _AFFRICATE_NORMALIZATION
        return (src, "source") if segments_are_valid(src) else (src, "unclean")
    if profile:
        if source_form:
            prof, ok = apply_profile(source_form, profile)
            if ok and prof:
                return prof, "profile"
        return "", "unclean"
    if source_form:
        reseg, ok = resegment(source_form)
        if ok and reseg:
            return reseg, "resegmented"
    return "", "unclean"
