"""Language-specific contrasts in the Afar and Saho spelling profiles."""

from pathlib import Path

import pytest

from arcaverborum.phonology import load_profile, normalize_segments, segments_are_valid

ROOT = Path(__file__).resolve().parents[1]
PROFILES = {name: load_profile(ROOT / f"varieties/afa-{name}/custom/profile.tsv")
            for name in ("afar", "saho")}


@pytest.mark.parametrize(("language", "form", "expected"), [
    ("afar", "caxa", "ħ a ɖ a"),
    ("afar", "qari", "ʕ a ɾ i"),
    ("afar", "lee", "l eː"),
    ("afar", "sagáal", "s a ɡ aː ⁵ l"),
    ("afar", "malcíin", "m a l ħ iː ⁵ n"),
    ("afar", "nammáy", "n a mː a ⁵ j"),
    ("afar", "barra", "b a rː a"),
    ("afar", "sh", "s h"),
    ("afar", "shsh", "s h s h"),
    ("afar", "SH", "s h"),
    ("afar", "QAFÁR AF", "ʕ a f a ⁵ ɾ _ a f"),
    ("saho", "caasa", "ʕ aː s a"),
    ("saho", "dhaa", "ɖ aː"),
    ("saho", "xarha", "ħ a ɽ a"),
    ("saho", "cashsho", "ʕ a ʃː o"),
    ("saho", "sh", "ʃ"),
    ("saho", "barha", "b a ɽ a"),
    ("saho", "barhä", "b a ɽ a ⁵"),
    ("saho", "tsiixil", "sʼ iː ħ i l"),
    ("saho", "qaca", "kʼ a ʕ a"),
    ("saho", "DHAARHAA", "ɖ aː ɽ aː"),
    ("saho", "chiqqa", "tʃʼ i kʼː a"),
    ("saho", "laqhco", "l a xʼ ʕ o"),
])
def test_language_specific_spelling(language, form, expected):
    assert normalize_segments("", form, PROFILES[language]) == (expected, "profile")
    assert segments_are_valid(expected)


@pytest.mark.parametrize("language", ["afar", "saho"])
def test_all_profile_outputs_are_valid(language):
    assert all(segments_are_valid(value) for value in PROFILES[language].values())


@pytest.mark.parametrize("language", ["afar", "saho"])
@pytest.mark.parametrize("form", ["أَف", "dor-ho", "qiraa-a", "hello!"])
def test_unsupported_scripts_and_ambiguous_boundaries_remain_unclean(language, form):
    assert normalize_segments("", form, PROFILES[language]) == ("", "unclean")


@pytest.mark.parametrize("language", ["afar", "saho"])
def test_explicit_source_ipa_precedes_profile(language):
    assert normalize_segments("ʕ a ɖ", "cad", PROFILES[language]) == ("ʕ a ɖ", "source")
