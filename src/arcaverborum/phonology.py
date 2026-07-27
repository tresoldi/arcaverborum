"""Phonology layer: validate and re-segment IPA via merkmal.

Policy: trust source Segments where they are present AND all tokens are
recognized by merkmal ('source'). Source segments that are present but
not fully recognized are kept verbatim and flagged 'unclean' — real IPA
is never discarded in favour of re-segmenting the (often orthographic)
form, so a later normalization pass can reclaim those tokens in place.
Only when source segments are absent do we attempt re-segmentation from
the Form via merkmal's IPA tokenizer (``segment_ipa``), flagged
'resegmented'; if any token fails to validate, it is 'unclean'.

Uses merkmal's ``descriptive`` system — the merkmal-native categorical
feature engine that the downstream cognate toolchain (cognator, proteus)
also defaults to. Validity is generative: a token validates when merkmal
can derive its features compositionally (base + diacritics), not only
when the exact string is attested. Tone digits are attached to their
syllabic nucleus via ``merge_tone_digits`` before validation, so
tone-bearing segments validate.
"""

from __future__ import annotations

import logging
import re
import unicodedata

import merkmal

logger = logging.getLogger(__name__)

SYSTEM = "descriptive"
SEPARATORS = ("+", "_")
SOURCE_TOKEN_ALIASES = {
    # Arca source shorthand for pre-nasalized stops. merkmal intentionally
    # keeps bare clusters invalid and accepts the explicit modifier forms.
    "mb": "ᵐb",
    "nd": "ⁿd",
}


def is_valid_grapheme(g: str) -> bool:
    if not g:
        return False
    if g in SEPARATORS:
        return True
    return bool(merkmal.is_segment(g, system=SYSTEM))


def canonicalize_token(token: str) -> str:
    return merkmal.normalize(SOURCE_TOKEN_ALIASES.get(token, token))


def canonicalize(tokens: list[str]) -> tuple[list[str], bool]:
    """Resolve tokens to canonical BIPA, drop emptied tokens, merge tone.

    Each non-separator token is passed through ``merkmal.normalize``, which
    resolves CLTS source/BIPA slash notation (``a/b`` → ``b``), expands
    deprecated affricate ligatures (``ʤ`` → ``dʒ``), maps ASCII colon to the
    IPA length mark, strips suprasegmental stress, and returns canonical NFC
    IPA. Separators (``+``/``_``) are preserved; tokens that normalize to
    nothing (a bare stress mark) are dropped. Returns (canonical tokens,
    all_valid). Tone digits are kept as separate tokens (the CLDF
    convention) but validity is checked with them attached to their nucleus,
    so a tone-bearing form counts as valid.
    """
    out: list[str] = []
    for t in tokens:
        if not t:
            continue
        if t in SEPARATORS:
            out.append(t)
            continue
        norm = canonicalize_token(t)
        if norm:
            out.append(norm)
    ok = all(is_valid_grapheme(t) for t in merkmal.merge_tone_digits(out))
    return out, ok


def segments_are_valid(segments: str) -> bool:
    if not segments or not segments.strip():
        return False
    _, ok = canonicalize([t for t in segments.split() if t])
    return ok


_SPACES_RE = re.compile(r"\s+")


def resegment(form: str) -> tuple[str, bool]:
    """Tokenize a continuous form into canonical IPA segments via merkmal.

    Returns (space-joined segments, fully_covered). Uses
    ``merkmal.segment_ipa`` (diacritics bind to their base, tie-bars and
    affricates stay whole, no cluster over-merge), then canonicalizes each
    token (see :func:`canonicalize`). Underscores and pluses survive as
    morpheme separators. ``fully_covered`` is False if any resulting token
    fails to validate (e.g. orthography merkmal cannot read as IPA).
    """
    if not form:
        return "", False
    form = _SPACES_RE.sub("", form)
    if not form:
        return "", False
    tokens, fully_covered = canonicalize(merkmal.segment_ipa(form))
    if not tokens:
        return "", False
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
      1. Source segments present and fully recognized → canonicalize them to
         clean BIPA (resolve CLTS slash notation, expand ligatures, etc.) and
         use them (segments_source = 'source').
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
        canon, ok = canonicalize([t for t in src.split() if t])
        if ok and canon:
            return " ".join(canon), "source"
        return src, "unclean"  # keep real source IPA verbatim for later recovery
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
