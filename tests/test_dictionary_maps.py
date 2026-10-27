"""Staged dictionary reviews are validated before any construction is active."""

import csv
import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "dictionary_maps", Path(__file__).parents[1] / "scripts/compile_dictionary_maps.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def write(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_staged_reviews_fail_on_source_drift_and_duplicate_decisions(tmp_path):
    data = tmp_path / "src/arcaverborum/data"
    cldf = tmp_path / "raw/lexibank/staged/cldf"
    review = dict(
        dataset="staged",
        sense_id="s1",
        expected_headword="word",
        expected_description="water",
        expected_pos="noun",
        concept_id="phy-water",
        rationale="Explicit sense",
    )
    write(data / "dictionary_senses.csv", [review])
    write(data / "concepts.csv", [dict(concept_id="phy-water", concepticon_id="948", label="water")])
    write(cldf / "entries.csv", [dict(ID="e1", Headword="word", Part_Of_Speech="noun")])
    write(cldf / "senses.csv", [dict(ID="s1", Entry_ID="e1", Description="water")])
    assert module.reviewed_maps(tmp_path)["staged"][0]["concept_id"] == "phy-water"
    write(cldf / "senses.csv", [dict(ID="s1", Entry_ID="e1", Description="waterfall")])
    with pytest.raises(ValueError, match="source drift"):
        module.reviewed_maps(tmp_path)
    write(data / "dictionary_senses.csv", [review, review])
    with pytest.raises(ValueError, match="Duplicate"):
        module.reviewed_maps(tmp_path)
