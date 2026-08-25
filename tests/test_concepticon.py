"""Tests for arcaverborum.concepticon module."""

from arcaverborum.concepticon import (
    ConcepticonEntry,
    ConcepticonIndex,
    match_parameter,
)


def _entry(id, gloss, category="Person/Thing", **kw):
    return ConcepticonEntry(id=id, gloss=gloss, ontological_category=category, **kw)


def _make_index(
    by_gloss=None,
    by_base=None,
    by_alias=None,
    pos_blocklist=None,
):
    if by_gloss is None:
        by_gloss = {
            "WATER": _entry("1010", "WATER"),
            "FIRE": _entry("221", "FIRE"),
            "RUN": _entry("1253", "RUN", "Action/Process"),
            "BIG": _entry("1202", "BIG", "Property"),
            "TWO": _entry("1498", "TWO", "Number"),
        }
    return ConcepticonIndex(
        by_gloss=by_gloss,
        by_base=by_base or {},
        by_alias=by_alias or {},
        pos_blocklist=pos_blocklist or set(),
    )


# --- Tier 1: exact gloss ---

def test_match_noun():
    idx = _make_index()
    assert match_parameter("water", "noun", idx) == ("1010", "WATER")


def test_match_verb():
    idx = _make_index()
    assert match_parameter("run", "verb", idx) == ("1253", "RUN")


def test_match_adj():
    idx = _make_index()
    assert match_parameter("big", "adj", idx) == ("1202", "BIG")


def test_match_num():
    idx = _make_index()
    assert match_parameter("two", "num", idx) == ("1498", "TWO")


def test_cross_pos_allowed():
    """POS relaxation: "water" as verb matches WATER (same concept)."""
    idx = _make_index()
    assert match_parameter("water", "verb", idx) == ("1010", "WATER")


def test_unmapped_pos_matches():
    """POS types not in POS_TO_CATEGORIES still match (no category filter)."""
    idx = _make_index()
    assert match_parameter("water", "name", idx) == ("1010", "WATER")
    assert match_parameter("water", "intj", idx) == ("1010", "WATER")
    assert match_parameter("water", "prep", idx) == ("1010", "WATER")


def test_unknown_word():
    idx = _make_index()
    assert match_parameter("xyzzy", "noun", idx) is None


def test_case_insensitive():
    idx = _make_index()
    assert match_parameter("Water", "noun", idx) == ("1010", "WATER")


def test_empty_word():
    idx = _make_index()
    assert match_parameter("", "noun", idx) is None


# --- POS blocklist ---

def test_blocklist_rejects():
    idx = _make_index(pos_blocklist={("WATER", "verb")})
    assert match_parameter("water", "verb", idx) is None


def test_blocklist_does_not_affect_other_pos():
    idx = _make_index(pos_blocklist={("WATER", "verb")})
    assert match_parameter("water", "noun", idx) == ("1010", "WATER")


# --- Tier 2: base-form match ---

def test_base_form_unique():
    """Single parenthetical entry matched by its base form."""
    idx = _make_index(
        by_gloss={},
        by_base={"BLOW": [_entry("720", "BLOW (OF WIND)", "Action/Process")]},
    )
    assert match_parameter("blow", "noun", idx) == ("720", "BLOW (OF WIND)")


def test_base_form_not_used_when_exact_exists():
    """Exact gloss takes priority over base form."""
    idx = _make_index(
        by_gloss={"BLOW": _entry("999", "BLOW", "Action/Process")},
        by_base={"BLOW": [_entry("720", "BLOW (OF WIND)", "Action/Process")]},
    )
    assert match_parameter("blow", "verb", idx) == ("999", "BLOW")


def test_base_form_ambiguous_same_category():
    """Multiple base-form candidates with same category → ambiguous, skipped."""
    idx = _make_index(
        by_gloss={},
        by_base={"BLOW": [
            _entry("720", "BLOW (OF WIND)", "Action/Process"),
            _entry("721", "BLOW (WITH MOUTH)", "Action/Process"),
        ]},
    )
    assert match_parameter("blow", "verb", idx) is None


def test_base_form_pos_disambiguates():
    """POS disambiguates when base-form candidates span different categories."""
    light_color = _entry("800", "LIGHT (COLOR)", "Property")
    light_radiation = _entry("801", "LIGHT (RADIATION)", "Person/Thing")
    idx = _make_index(
        by_gloss={},
        by_base={"LIGHT": [light_color, light_radiation]},
    )
    assert match_parameter("light", "adj", idx) == ("800", "LIGHT (COLOR)")
    assert match_parameter("light", "noun", idx) == ("801", "LIGHT (RADIATION)")


def test_base_form_pos_no_match():
    """POS filter finds no compatible candidate → no match."""
    idx = _make_index(
        by_gloss={},
        by_base={"LIGHT": [
            _entry("800", "LIGHT (COLOR)", "Property"),
            _entry("801", "LIGHT (RADIATION)", "Person/Thing"),
        ]},
    )
    assert match_parameter("light", "verb", idx) is None


# --- Tier 3: alias match ---

def test_alias_match():
    noon = _entry("1268", "MIDDAY")
    idx = _make_index(by_gloss={}, by_alias={"NOON": noon})
    assert match_parameter("noon", "noun", idx) == ("1268", "MIDDAY")


def test_alias_lower_priority_than_exact():
    idx = _make_index(
        by_gloss={"NOON": _entry("9999", "NOON")},
        by_alias={"NOON": _entry("1268", "MIDDAY")},
    )
    assert match_parameter("noon", "noun", idx) == ("9999", "NOON")


def test_alias_lower_priority_than_base():
    idx = _make_index(
        by_gloss={},
        by_base={"NOON": [_entry("5555", "NOON (TIME)", "Person/Thing")]},
        by_alias={"NOON": _entry("1268", "MIDDAY")},
    )
    assert match_parameter("noon", "noun", idx) == ("5555", "NOON (TIME)")


def test_alias_blocklisted():
    noon = _entry("1268", "MIDDAY")
    idx = _make_index(
        by_gloss={},
        by_alias={"NOON": noon},
        pos_blocklist={("NOON", "verb")},
    )
    assert match_parameter("noon", "verb", idx) is None
    assert match_parameter("noon", "noun", idx) == ("1268", "MIDDAY")
