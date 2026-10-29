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
    source, frame, profile = next(
        reviewed_frames(
            tmp_path, pd.DataFrame([row]), "xxxx1234", {"wikt_water": ("948", "WATER")}, {"phy-water": "948"}
        )
    )
    assert source == "wiktionary" and profile is None
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


def test_source_scoped_profile_is_guarded_and_keeps_derived_status(tmp_path):
    import hashlib

    from arcaverborum.catalog import Variety
    from arcaverborum.variety import emit_forms

    row = fixture(tmp_path)
    row["Segments"] = ""
    path = tmp_path / "supplements.csv"
    with path.open() as handle:
        review = next(csv.DictReader(handle))
    review.update(evidence_sha256=evidence_hash(row), profile_file="dictionary.tsv")
    profiles = tmp_path / "supplement_profiles"
    profiles.mkdir()
    profile_path = profiles / "dictionary.tsv"
    profile_path.write_text("Grapheme\tIPA\n^á$\tiː\n")
    review["profile_sha256"] = hashlib.sha256(profile_path.read_bytes()).hexdigest()

    def save():
        with path.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(review))
            writer.writeheader()
            writer.writerow(review)

    def frames():
        return list(
            reviewed_frames(
                tmp_path, pd.DataFrame([row]), "xxxx1234", {"wikt_water": ("948", "WATER")}, {"phy-water": "948"}
            )
        )

    save()
    source, frame, profile = frames()[0]
    emitted = emit_forms(
        frame,
        av_id="und-test",
        variety=Variety(av_id="und-test"),
        transcription_source=source,
        cognate_source=source,
        forms_score=0.5,
        tier="bronze",
        param_index={},
        concept_index={},
        concept_labels={"phy-water": "water"},
        profile=profile,
    )[0]
    assert emitted["Segments"] == "iː" and emitted["Segments_Source"] == "profile"
    assert emitted["source_form_id"] == row["ID"]
    before = custom_component(tmp_path)
    profile_path.write_text("Grapheme\tIPA\n^á$\tuː\n")
    assert custom_component(tmp_path) != before
    with pytest.raises(ValueError, match="profile changed"):
        frames()
    review["profile_file"] = "../profile.tsv"
    save()
    with pytest.raises(ValueError, match="local TSV"):
        frames()
    review["profile_file"] = "dictionary.tsv"
    profile_path.write_text("Grapheme\tIPA\ná\ta\n")
    review["profile_sha256"] = hashlib.sha256(profile_path.read_bytes()).hexdigest()
    save()
    with pytest.raises(ValueError, match="whole-form"):
        frames()
    profile_path.write_text("Grapheme\tIPA\n^á$\tTHIS_IS_NOT_IPA\n")
    review["profile_sha256"] = hashlib.sha256(profile_path.read_bytes()).hexdigest()
    save()
    with pytest.raises(ValueError, match="validated"):
        frames()


def test_original_bracketed_ipa_recovers_tone_and_nasality_without_losing_cognacy(tmp_path):
    row = fixture(tmp_path)
    row.update(Value='[ˈw̃ã́ɲɛ̃̀] (A)', Segments='w ã́ ɲ ɛ̃̀')
    review = next(csv.DictReader((tmp_path / 'supplements.csv').open()))
    review.update(evidence_sha256=evidence_hash(row), original_ipa='ˈw̃ã́ɲɛ̃̀',
                  source_pronunciation_id='original-test', pronunciation_tags='["A"]',
                  pronunciation_note='Exact original source IPA; upstream nasal glide loss corrected.')
    args = (tmp_path, pd.DataFrame([row]), 'xxxx1234', {'wikt_water': ('948', 'WATER')}, {'phy-water': '948'})
    result = next(reviewed_frames(*args, decisions=[review]))[1].iloc[0]
    assert result.Segments == 'w̃ ã́ ɲ ɛ̃̀'
    assert result['_raw_ipa'] == 'ˈw̃ã́ɲɛ̃̀'
    assert result.Cognacy == row['Cognacy'] and result.Value == row['Value']
    for changed in [
        dict(original_ipa='wãɲɛ'),
        dict(source_pronunciation_id=''),
        dict(pronunciation_note=''),
        dict(raw_ipa='ˈw̃ã́ɲɛ̃̀'),
        dict(transcription_policy='orthographic_only'),
    ]:
        with pytest.raises(ValueError, match='one exact bracketed'):
            list(reviewed_frames(*args, decisions=[{**review, **changed}]))
    for value in ['[ˈw̃ã́ɲɛ̃̀ ~ wãɲɛ] (A)', '[ˈw̃ã́ɲɛ̃̀] (A), [wãɲɛ] (C)', 'ˈw̃ã́ɲɛ̃̀']:
        different = {**row, 'Value': value}
        decision = {**review, 'evidence_sha256': evidence_hash(different)}
        with pytest.raises(ValueError, match='one exact bracketed'):
            list(reviewed_frames(tmp_path, pd.DataFrame([different]), *args[2:], decisions=[decision]))
