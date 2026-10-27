"""Additive evidence cannot rewrite the primary block or lose source identity."""

import csv

import pandas as pd
import pytest

from arcaverborum.supplements import evidence_hash, reviewed_frames
from arcaverborum.tracking import config_component, custom_component


def fixture(tmp_path):
    row = dict(
        ID="wikt_123",
        Dataset="wiktionary",
        Language_ID="wikt_xx",
        Glottocode="xxxx1234",
        Parameter_ID="wikt_water",
        Value="á",
        Form="á",
        Segments="aː",
        Cognacy="wikt_etym7",
        Source="wiktionary_snapshot",
        Comment="Native pronunciation evidence",
        Loan="false",
    )
    review = dict(
        source="wiktionary",
        source_form_id=row["ID"],
        source_language_id="wikt_xx",
        source_glottocode="xxxx1234",
        evidence_sha256=evidence_hash(row),
        expected_source_concepticon_id="948",
        concept_id="phy-water",
        decision="admit",
        rationale="Reviewed water sense and exact member",
    )
    with (tmp_path / "supplements.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(review))
        writer.writeheader()
        writer.writerow(review)
    return row


def test_retains_raw_ids_cognacy_and_supplied_segments_without_primary_profile(tmp_path):
    row = fixture(tmp_path)
    source, frame = next(
        reviewed_frames(
            tmp_path, pd.DataFrame([row]), "xxxx1234", {"wikt_water": ("948", "WATER")}, {"phy-water": "948"}
        )
    )
    assert source == "wiktionary"
    result = frame.iloc[0]
    assert (result.ID, result.Language_ID, result.Cognacy, result.Source) == (
        row["ID"],
        row["Language_ID"],
        row["Cognacy"],
        row["Source"],
    )
    assert result.Form == "á" and result.Segments == "aː"
    assert result["_concept_id_override"] == "phy-water"
    assert row["Comment"] == "Native pronunciation evidence"


def test_changed_or_disappeared_evidence_and_identity_fail_closed(tmp_path):
    row = fixture(tmp_path)
    for changed, message in [
        ({**row, "Segments": "i"}, "evidence changed"),
        ({**row, "ID": "missing"}, "missing or duplicated"),
    ]:
        with pytest.raises(ValueError, match=message):
            list(
                reviewed_frames(
                    tmp_path,
                    pd.DataFrame([changed]),
                    "xxxx1234",
                    {"wikt_water": ("948", "WATER")},
                    {"phy-water": "948"},
                )
            )
    with pytest.raises(ValueError, match="canonical Glottocode"):
        list(reviewed_frames(tmp_path, pd.DataFrame([row]), "yyyy1234", {}, {}))
    with pytest.raises(ValueError, match="concept changed"):
        list(
            reviewed_frames(
                tmp_path, pd.DataFrame([row]), "xxxx1234", {"wikt_water": ("other", "")}, {"phy-water": "948"}
            )
        )


def test_reviewed_members_and_supplement_ledgers_affect_freshness(tmp_path):
    a = config_component({"sources": {"source_language_ids": ["one"], "source_glottocodes": ["xxxx1234"]}})
    b = config_component({"sources": {"source_language_ids": ["two"], "source_glottocodes": ["xxxx1234"]}})
    assert a != b
    before = custom_component(tmp_path)
    fixture(tmp_path)
    assert custom_component(tmp_path) != before
