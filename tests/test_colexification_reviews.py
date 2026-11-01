"""Review comparison must fail closed on incomplete or invented evidence."""

import csv
import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "review_comparison", Path(__file__).parents[1] / "scripts/compare_colexification_reviews.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def write(path, rows):
    with path.open("w") as h:
        w = csv.DictWriter(h, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    return path


def test_review_disagreement_is_not_gold(tmp_path):
    worksheet = write(
        tmp_path / "worksheet.csv",
        [
            dict(
                case_id="one",
                original_records_a=json.dumps([dict(source_form_id="native", source_parameter_id="prompt")]),
                original_records_b="[]",
            )
        ],
    )
    row = dict(
        case_id="one",
        reviewer="first",
        identity_evidence="insufficient_evidence",
        sense_evidence="mapping_unverified",
        reading_fidelity="derivation_requires_review",
        interpretation="unresolved",
        evidence_ids="native",
        evidence="native: apostrophe uncertain",
        limitations="No original scan",
    )
    a = write(tmp_path / "a.csv", [row])
    b = write(tmp_path / "b.csv", [row | dict(reviewer="second", reading_fidelity="suspected_truncation")])
    summary = module.compare(worksheet, [a, b], tmp_path / "out")
    assert summary["cases_with_disagreement"] == 1
    assert summary["expert_adjudications"] == 0
    assert summary["model_assisted_only"]
    write(b, [row | dict(reviewer="second", evidence_ids="invented")])
    with pytest.raises(ValueError, match="Unsupported/missing"):
        module.compare(worksheet, [a, b], tmp_path / "bad")
