"""Tests for arcaverborum.concepticon module."""

from arcaverborum.concepticon import ConcepticonEntry, match_parameter


def _make_concepticon():
    return {
        "WATER": ConcepticonEntry(id="1010", gloss="WATER", ontological_category="Person/Thing"),
        "FIRE": ConcepticonEntry(id="221", gloss="FIRE", ontological_category="Person/Thing"),
        "RUN": ConcepticonEntry(id="1253", gloss="RUN", ontological_category="Action/Process"),
        "BIG": ConcepticonEntry(id="1202", gloss="BIG", ontological_category="Property"),
        "TWO": ConcepticonEntry(id="1498", gloss="TWO", ontological_category="Number"),
    }


def test_match_noun():
    c = _make_concepticon()
    result = match_parameter("water", "noun", c)
    assert result == ("1010", "WATER")


def test_match_verb():
    c = _make_concepticon()
    result = match_parameter("run", "verb", c)
    assert result == ("1253", "RUN")


def test_match_adj():
    c = _make_concepticon()
    result = match_parameter("big", "adj", c)
    assert result == ("1202", "BIG")


def test_match_num():
    c = _make_concepticon()
    result = match_parameter("two", "num", c)
    assert result == ("1498", "TWO")


def test_pos_mismatch():
    c = _make_concepticon()
    result = match_parameter("water", "verb", c)
    assert result is None


def test_unmapped_pos_matches():
    """POS types not in POS_TO_CATEGORIES still match (no category filter)."""
    c = _make_concepticon()
    assert match_parameter("water", "name", c) == ("1010", "WATER")
    assert match_parameter("water", "intj", c) == ("1010", "WATER")
    assert match_parameter("water", "prep", c) == ("1010", "WATER")


def test_unknown_word():
    c = _make_concepticon()
    result = match_parameter("xyzzy", "noun", c)
    assert result is None


def test_case_insensitive():
    c = _make_concepticon()
    result = match_parameter("Water", "noun", c)
    assert result == ("1010", "WATER")


def test_empty_word():
    c = _make_concepticon()
    result = match_parameter("", "noun", c)
    assert result is None
