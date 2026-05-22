"""Phonology normalization policy (merkmal descriptive system)."""

from __future__ import annotations

import unicodedata

from arcaverborum.phonology import (
    apply_profile,
    load_profile,
    normalize_segments,
    resegment,
    segments_are_valid,
)

# A token merkmal genuinely cannot read as IPA (an uncertainty / alternation
# annotation artefact from the source data, not a real sound).
STILL_INVALID = "<?>"


def test_valid_source_segments_kept_as_source():
    segs, src = normalize_segments("t a t a", "tata")
    assert src == "source"
    assert segs == "t a t a"


def test_absent_segments_resegmented_from_form():
    segs, src = normalize_segments("", "tata")
    assert src == "resegmented"
    assert segs == "t a t a"


def test_present_but_invalid_source_ipa_is_kept_not_resegmented():
    # A present-but-unrecognized source token must be preserved verbatim,
    # flagged unclean — never replaced by a guess from the orthography.
    assert not segments_are_valid(f"{STILL_INVALID} a")
    assert resegment("tata") == ("t a t a", True)  # would have resegmented
    segs, src = normalize_segments(f"{STILL_INVALID} a", "tata")
    assert src == "unclean"
    assert segs == f"{STILL_INVALID} a"  # source IPA retained


def test_plain_affricates_validate_and_are_kept_verbatim():
    # merkmal (descriptive) accepts plain tʃ/dʒ compositionally, so the real
    # source IPA is kept verbatim as 'source' — no rewrite to a retracted form.
    assert segments_are_valid("tʃ a")
    assert segments_are_valid("dʒ a")
    assert normalize_segments("tʃ a", "") == ("tʃ a", "source")
    assert normalize_segments("dʒ a", "") == ("dʒ a", "source")


def test_tone_bearing_segments_validate():
    # Tone digits attach to their nucleus (merge_tone_digits) and validate,
    # so a tonal form is 'source', not 'unclean'.
    assert segments_are_valid("k a ³¹")
    assert segments_are_valid("k ə ŋ ³³ + k a ³¹")
    assert normalize_segments("k a ³¹", "") == ("k a ³¹", "source")


def test_clts_slash_notation_resolved_to_bipa():
    # CLTS source/BIPA slash notation: store the consumed BIPA value, no slash.
    assert normalize_segments("y/j a", "") == ("j a", "source")
    assert normalize_segments("sh/ʃ a", "") == ("ʃ a", "source")
    # tone slash notation resolves to the Chao value, still a separate token
    assert normalize_segments("k a ⁶/⁵¹", "") == ("k a ⁵¹", "source")


def test_legacy_ligatures_and_ascii_colon_and_stress_canonicalized():
    assert normalize_segments("ʤ a", "") == ("dʒ a", "source")
    assert normalize_segments("a:", "") == ("aː", "source")
    # leading stress is suprasegmental → stripped
    assert normalize_segments("ˈɛ", "") == ("ɛ", "source")


def test_absent_and_unresegmentable_is_empty_unclean():
    segs, src = normalize_segments("", "")
    assert src == "unclean"
    assert segs == ""


# --- orthographic profiles -------------------------------------------------

def test_apply_profile_longest_match_and_multi_segment_ipa():
    profile = {"d": "d", "h": "h", "dh": "ð", "i": "i"}
    segs, ok = apply_profile("dhi", profile)
    assert ok
    assert segs == "ð i"


def test_apply_profile_empty_ipa_deletes_grapheme():
    profile = {"a": "a", "e": ""}  # silent 'e'
    segs, ok = apply_profile("ae", profile)
    assert ok
    assert segs == "a"


def test_apply_profile_reports_uncovered():
    segs, ok = apply_profile("axb", {"a": "a", "b": "b"})
    assert not ok  # 'x' has no grapheme
    assert segs == "a b"


def test_apply_profile_space_becomes_word_boundary():
    profile = {"i": "i", "l": "l", "k": "k", "ë": "ə"}
    segs, ok = apply_profile("i likë", profile)
    assert ok
    assert segs == "i _ l i k ə"


def test_apply_profile_nfc_normalizes_form():
    precomposed = unicodedata.normalize("NFC", "š")          # š (1 codepoint)
    decomposed = unicodedata.normalize("NFD", "š") + "a"     # s + caron + a
    profile = {precomposed: "ʃ", "a": "a"}
    assert precomposed not in decomposed                     # genuinely decomposed
    segs, ok = apply_profile(decomposed, profile)
    assert ok
    assert segs == "ʃ a"


def test_load_profile_roundtrip(tmp_path):
    p = tmp_path / "profile.tsv"
    p.write_text(
        "Grapheme\tIPA\tnotes\nsh\tʃ\tdigraph\në\tə\t\n# comment\tx\t\n",
        encoding="utf-8",
    )
    prof = load_profile(p)
    assert prof == {"sh": "ʃ", "ë": "ə"}


def test_profile_fills_only_when_source_absent():
    profile = {"s": "s", "h": "h", "sh": "ʃ"}
    # No source segments → profile drives it.
    assert normalize_segments("", "sh", profile) == ("ʃ", "profile")
    # Valid source IPA wins over the profile.
    assert normalize_segments("t a", "sh", profile) == ("t a", "source")
    # Present-but-invalid source IPA is kept, not overridden by the profile.
    assert normalize_segments(STILL_INVALID, "sh", profile) == (STILL_INVALID, "unclean")


def test_profile_is_authoritative_no_orthographic_fallback():
    profile = {"s": "s", "h": "h", "sh": "ʃ"}
    assert resegment("ta") == ("t a", True)
    assert normalize_segments("", "ta", profile) == ("", "unclean")
