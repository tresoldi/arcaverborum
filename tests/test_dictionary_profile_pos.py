"""Dictionary labels must not turn an artifact noun into a verb or the reverse."""
import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "compile_african_profiles", Path(__file__).parents[1] / "scripts/compile_african_profiles.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def original(pos):
    return "Original dictionary evidence: " + json.dumps({"entry": {"Part_Of_Speech": pos}})


@pytest.mark.parametrize("pos,target", [("common noun", "v"), ("noun", "v"), ("Verb", "n")])
def test_sail_and_drill_word_class_conflicts_are_rejected(pos, target):
    with pytest.raises(ValueError, match="POS mismatch"):
        module.reject_dictionary_pos_conflict(original(pos), target)


@pytest.mark.parametrize("pos,target", [("common noun", "n"), ("time adverb", "v")])
def test_matching_nouns_and_unclassified_adverbs_are_not_reinterpreted(pos, target):
    module.reject_dictionary_pos_conflict(original(pos), target)
