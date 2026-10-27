"""Only documented, unambiguous source spellings enter the Iquito subset."""

import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("iquito_profile", Path(__file__).parents[1] / "scripts/iquito_profile.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


@pytest.mark.parametrize(
    ("word", "expected"),
    [
        ("aaka", "aː k a"),
        ("májaaka", "m á h aː k a"),
        ("kwaka", "kʷ a k a"),
        ("kiaka", "kʲ a k a"),
        ("niaka", "ɲ a k a"),
        ("siaka", "ʃ a k a"),
        ("járaki", "h á ɾ a k i"),
        ("ja\u0301raki", "h á ɾ a k i"),
    ],
)
def test_documented_subset_and_unicode_equivalence(word, expected):
    assert module.reading(word) == expected


@pytest.mark.parametrize("word", ["aáka", "áaka", "niínaki", "síipa", "na=áka", "nua", "casa", "majaaka?", "", "á́ka"])
def test_ambiguous_tone_length_palatalization_and_foreign_characters_are_held(word):
    assert module.reading(word) == ""
