"""Admission boundaries for a paradigm source used as lexical evidence."""

import copy
import csv
from pathlib import Path

import pytest

from arcaverborum.sources.rvid import reviewed_forms

ROOT = Path(__file__).resolve().parents[1]


def fixture():
    with (ROOT / "docs/romance_r04_review_2026-10-28.csv").open() as f:
        r = next(r for r in csv.DictReader(f) if r["decision"] == "admit")
    raw = dict(
        ID=r["source_form_id"],
        Language_ID=r["source_language_id"],
        Cell="INF",
        Form=r["raw_ipa"],
        Cognateset_ID=r["source_cognateset_id"],
    )
    lx = dict(
        ID=r["lexeme_id"],
        Language_ID=r["source_language_id"],
        Cognateset_ID=r["source_cognateset_id"],
        Meaning=r["source_sense"],
        Comment=r["lexeme_comment"],
        Etymon_in_ODRVM="UELLE",
    )
    samples = {r["source_language_id"]: dict(av_id=r["av_id"])}
    concepts = {r["concept_id"]: dict(concepticon_id="1", label="want")}
    return raw, lx, r, samples, concepts


def test_infinitive_preserves_source_morphology_and_reading():
    raw, lx, r, samples, concepts = fixture()
    forms, _ = reviewed_forms([raw], [lx], [r], samples, concepts)
    assert forms[0]["Form"] == r["raw_ipa"]
    assert '"morphology_cell": "INF"' in forms[0]["Comment"]
    assert '"modern_meaning": "want"' in forms[0]["Comment"]
    assert "Cognacy" not in forms[0]


@pytest.mark.parametrize(
    "table,key,value",
    [
        ("raw", "Cell", "1SG.PRS"),
        ("raw", "Form", "invented"),
        ("lexeme", "Meaning", "Latin etymon guessed meaning"),
        ("lexeme", "Comment", "changed source caveat"),
    ],
)
def test_review_rejects_paradigm_and_lexical_drift(table, key, value):
    raw, lx, r, samples, concepts = copy.deepcopy(fixture())
    (raw if table == "raw" else lx)[key] = value
    with pytest.raises(ValueError, match="evidence changed"):
        reviewed_forms([raw], [lx], [r], samples, concepts)


def test_duplicate_reviews_fail():
    raw, lx, r, samples, concepts = fixture()
    with pytest.raises(ValueError, match="Duplicate"):
        reviewed_forms([raw], [lx], [r, r], samples, concepts)
