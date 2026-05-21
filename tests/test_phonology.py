"""Phonology normalization policy (merkmal phoible system)."""

from __future__ import annotations

from arcaverborum.phonology import (
    apply_profile,
    load_profile,
    normalize_segments,
    resegment,
    segments_are_valid,
)


def test_valid_source_segments_kept_as_source():
    segs, src = normalize_segments("t a t a", "tata")
    assert src == "source"
    assert segs == "t a t a"


def test_absent_segments_resegmented_from_form():
    segs, src = normalize_segments("", "tata")
    assert src == "resegmented"
    assert segs == "t a t a"


def test_present_but_invalid_source_ipa_is_kept_not_resegmented():
    # merkmal's phoible rejects the plain affricate `tʃ` (it wants `t̠ʃ`).
    # Even though the orthographic form would re-segment cleanly, the real
    # IECOR IPA must be preserved verbatim, flagged unclean — never
    # replaced by a guess from the orthography.
    assert not segments_are_valid("tʃ a")
    assert resegment("tata") == ("t a t a", True)  # would have resegmented
    segs, src = normalize_segments("tʃ a", "tata")
    assert src == "unclean"
    assert segs == "tʃ a"  # source IPA retained, not "t a t a"


def test_absent_and_unresegmentable_is_empty_unclean():
    segs, src = normalize_segments("", "")
    assert src == "unclean"
    assert segs == ""


# --- orthographic profiles -------------------------------------------------

def test_apply_profile_longest_match_and_multi_segment_ipa():
    # 'dh' is a digraph; longest match must beat 'd' + 'h'.
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
    assert ok  # the space is handled, not uncovered
    assert segs == "i _ l i k ə"  # boundary token, no leading/trailing _


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
    assert normalize_segments("tʃ", "sh", profile) == ("tʃ", "unclean")


def test_profile_is_authoritative_no_orthographic_fallback():
    # With a profile present, a form it does not cover is 'unclean' — not
    # re-segmented from the orthography (which the profile replaces). The
    # bare form "ta" would otherwise resegment cleanly to "t a".
    profile = {"s": "s", "h": "h", "sh": "ʃ"}
    assert resegment("ta") == ("t a", True)
    assert normalize_segments("", "ta", profile) == ("", "unclean")
