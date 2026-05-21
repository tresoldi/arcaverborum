"""Phonology normalization policy (merkmal phoible system)."""

from __future__ import annotations

from arcaverborum.phonology import normalize_segments, resegment, segments_are_valid


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
