"""Smoke tests for the per-variety pipeline.

Exercises: catalog → scoring → selection → register → build_one →
aggregate.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
import yaml

from arcaverborum.aggregate import aggregate_all
from arcaverborum.catalog import build_catalog
from arcaverborum.glottolog import GlottologEntry
from arcaverborum.score import (
    compute_signals_for_group,
    load_weights,
    score_cognates_block,
    score_forms_block,
)
from arcaverborum.selection import (
    build_universe,
    compute_all_signals,
    load_pins,
    select_all,
    source_priority,
)
from arcaverborum.variety import build_one, load_config, register, VarietyDir


def _stub_glottolog() -> dict[str, GlottologEntry]:
    return {
        "abcd1234": GlottologEntry(
            glottocode="abcd1234", name="TestLang", iso639p3="tst",
            macroarea="Eurasia", latitude=10.0, longitude=20.0, family="Testic",
        ),
    }


def _write_intake(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    forms_path = tmp_path / "forms.csv"
    languages_path = tmp_path / "languages.csv"
    parameters_path = tmp_path / "parameters_raw.csv"
    metadata_path = tmp_path / "metadata.csv"

    forms = pd.DataFrame([
        {
            "ID": "alpha_lang1_water", "Dataset": "alpha", "Language_ID": "alpha_lang1",
            "Glottocode": "abcd1234", "Parameter_ID": "alpha_water",
            "Concepticon_Gloss": "WATER",
            "Value": "wata", "Form": "wata", "Segments": "w a t a",
            "Cognacy": "alpha_42", "Alignment": "w a t a", "Loan": "false",
            "Doubt": "false", "Source": "alpha_Smith2020",
            "Cognate_Detection_Method": "expert",
        },
        {
            "ID": "alpha_lang1_fire", "Dataset": "alpha", "Language_ID": "alpha_lang1",
            "Glottocode": "abcd1234", "Parameter_ID": "alpha_fire",
            "Concepticon_Gloss": "FIRE",
            "Value": "pir", "Form": "pir", "Segments": "p i r",
            "Cognacy": "alpha_77", "Alignment": "p i r", "Loan": "false",
            "Doubt": "false", "Source": "alpha_Smith2020",
            "Cognate_Detection_Method": "expert",
        },
        {
            "ID": "beta_xyz_water", "Dataset": "beta", "Language_ID": "beta_xyz",
            "Glottocode": "abcd1234", "Parameter_ID": "beta_water",
            "Concepticon_Gloss": "WATER",
            "Value": "wata", "Form": "wata", "Segments": "",
            "Cognacy": "", "Alignment": "", "Loan": "",
            "Doubt": "", "Source": "beta_Doe2019",
            "Cognate_Detection_Method": "",
        },
    ])
    forms.to_csv(forms_path, index=False)

    languages = pd.DataFrame([
        {"ID": "alpha_lang1", "Dataset": "alpha", "Name": "TestLang",
         "Glottocode": "abcd1234", "Glottolog_Name": "TestLang",
         "ISO639P3code": "tst", "Macroarea": "Eurasia",
         "Latitude": "10.0", "Longitude": "20.0",
         "Family": "Testic", "Location": "", "Remark": ""},
        {"ID": "beta_xyz", "Dataset": "beta", "Name": "TestLang",
         "Glottocode": "abcd1234", "Glottolog_Name": "TestLang",
         "ISO639P3code": "tst", "Macroarea": "Eurasia",
         "Latitude": "10.0", "Longitude": "20.0",
         "Family": "Testic", "Location": "", "Remark": ""},
    ])
    languages.to_csv(languages_path, index=False)

    parameters = pd.DataFrame([
        {"ID": "alpha_water", "Dataset": "alpha", "Name": "water",
         "Concepticon_ID": "1234", "Concepticon_Gloss": "WATER"},
        {"ID": "alpha_fire", "Dataset": "alpha", "Name": "fire",
         "Concepticon_ID": "5678", "Concepticon_Gloss": "FIRE"},
        {"ID": "beta_water", "Dataset": "beta", "Name": "water",
         "Concepticon_ID": "1234", "Concepticon_Gloss": "WATER"},
    ])
    parameters.to_csv(parameters_path, index=False)

    metadata = pd.DataFrame([
        {"Dataset": "alpha", "Title": "Alpha", "Citation": "Smith 2020",
         "URL": "", "License": "CC-BY-4.0", "CLDF_Module": "Wordlist",
         "Repository_Version": "", "Python_Version": "",
         "Form_Count": "2", "Language_Count": "1", "Parameter_Count": "2",
         "Has_Cognates": "True"},
        {"Dataset": "beta", "Title": "Beta", "Citation": "Doe 2019",
         "URL": "", "License": "CC-BY-4.0", "CLDF_Module": "Wordlist",
         "Repository_Version": "", "Python_Version": "",
         "Form_Count": "1", "Language_Count": "1", "Parameter_Count": "1",
         "Has_Cognates": "False"},
    ])
    metadata.to_csv(metadata_path, index=False)

    return forms_path, languages_path, parameters_path, metadata_path


def test_catalog_builds_from_languages(tmp_path: Path):
    _, languages_path, _, _ = _write_intake(tmp_path)
    catalog = build_catalog(
        languages_path,
        glottolog=_stub_glottolog(),
        overrides_path=tmp_path / "no_overrides.csv",
    )
    assert "abcd1234" in catalog
    v = catalog["abcd1234"]
    assert v.name == "TestLang"
    assert v.in_glottolog is True
    assert "alpha" in v.sources and "beta" in v.sources


def test_enrich_glottocodes_from_iso():
    from arcaverborum.catalog import enrich_glottocodes
    glottolog = {
        "iso:kgg": GlottologEntry("kusu1250", "Kusunda", "kgg", "Eurasia",
                                  28.0, 82.26, "Kusunda"),
    }
    forms = pd.DataFrame([
        {"ID": "wikt_1", "Language_ID": "wikt_kgg", "Glottocode": "", "Form": "x"},
        {"ID": "wikt_2", "Language_ID": "wikt_zzz", "Glottocode": "", "Form": "y"},
    ])
    langs = pd.DataFrame([
        {"ID": "wikt_kgg", "ISO639P3code": "kgg", "Glottocode": ""},
        {"ID": "wikt_zzz", "ISO639P3code": "", "Glottocode": ""},
    ])
    ef, el = enrich_glottocodes(forms, langs, glottolog)
    assert ef.loc[ef.Language_ID == "wikt_kgg", "Glottocode"].iloc[0] == "kusu1250"
    assert ef.loc[ef.Language_ID == "wikt_zzz", "Glottocode"].iloc[0] == ""
    assert el.loc[el.ID == "wikt_kgg", "Glottocode"].iloc[0] == "kusu1250"


def test_score_picks_alpha(tmp_path: Path):
    forms_path, _, _, _ = _write_intake(tmp_path)
    df = pd.read_csv(forms_path, dtype=str, keep_default_na=False)
    weights = load_weights()
    alpha_sig = compute_signals_for_group(df[df["Dataset"] == "alpha"])
    beta_sig = compute_signals_for_group(df[df["Dataset"] == "beta"])
    assert score_forms_block(alpha_sig, weights) > score_forms_block(beta_sig, weights)


def test_source_priority_floor():
    # Lexibank sources are priority 1; GLED and Wiktionary are demoted.
    assert source_priority("grollemundbantu") == 1
    assert source_priority("gled") == 2
    assert source_priority("wiktionary") == 3


def test_fallback_only_wins_when_no_lexibank(tmp_path: Path):
    """A variety covered by both a Lexibank source and Wiktionary picks
    the Lexibank source even if Wiktionary scores higher; a variety
    covered only by Wiktionary picks Wiktionary."""
    weights = load_weights()

    from arcaverborum.score import Signals
    rich = Signals(forms_count=300, distinct_concepts=200, has_segments=1.0,
                   concepticon_mapped=1.0, has_cognates=1.0, expert=1.0)
    poor = Signals(forms_count=10, distinct_concepts=10, has_segments=0.0,
                   concepticon_mapped=1.0)

    # variety A: covered by a lexibank source (poor) AND wiktionary (rich)
    # variety B: covered only by wiktionary (rich)
    signals = {
        ("aaaa1111", "smithborneo"): poor,
        ("aaaa1111", "wiktionary"): rich,
        ("bbbb2222", "wiktionary"): rich,
    }
    selections = select_all(signals, pins={}, weights=weights)
    assert selections["aaaa1111"].transcription_source == "smithborneo"
    assert selections["bbbb2222"].transcription_source == "wiktionary"
    assert selections["bbbb2222"].tier == "copper"  # fallback never above copper


def test_universe_excludes_unmarked_datasets(tmp_path: Path):
    csv_path = tmp_path / "datasets.csv"
    csv_path.write_text(
        "NAME,URL,ExpertCognates,CORE\n"
        "alpha,http://example.com/alpha,TRUE,\n"
        "beta,http://example.com/beta,,\n"
        "gamma,http://example.com/gamma,,TRUE\n",
        encoding="utf-8",
    )
    universe = build_universe(csv_path)
    assert universe == {"alpha", "gamma"}


def test_variety_register_and_build(tmp_path: Path):
    forms_path, languages_path, parameters_path, _ = _write_intake(tmp_path)
    varieties_root = tmp_path / "varieties"

    catalog = build_catalog(
        languages_path,
        glottolog=_stub_glottolog(),
        overrides_path=tmp_path / "no_overrides.csv",
    )

    register(
        av_id="abcd1234",
        varieties_root=varieties_root,
        transcription_source="alpha",
        cognate_source="alpha",
        name="TestLang",
        glottocode="abcd1234",
        family="Testic",
        macroarea="Eurasia",
        forms_score=0.8,
        cognates_score=0.7,
        tier="bronze",
    )

    vd = VarietyDir(av_id="abcd1234", root=varieties_root / "abcd1234")
    assert vd.exists()
    config = load_config(vd)
    assert config["sources"]["transcription"] == "alpha"
    # Config-only by default: custom CSVs are not scaffolded until needed.
    for f in ("transcriptions.csv", "forms.csv", "cognates.csv", "concept_map.csv"):
        assert not (vd.custom_dir / f).exists()
    # Scaffolding creates the templates on demand.
    from arcaverborum.variety import scaffold_custom_files
    scaffold_custom_files(vd)
    for f in ("transcriptions.csv", "forms.csv", "cognates.csv", "concept_map.csv"):
        assert (vd.custom_dir / f).exists()

    n = build_one(
        av_id="abcd1234",
        varieties_root=varieties_root,
        intake_forms=forms_path,
        catalog=catalog,
        parameters_path=parameters_path,
    )
    assert n == 2  # 2 alpha rows, beta excluded
    out_df = pd.read_csv(vd.generated_forms, dtype=str, keep_default_na=False)
    assert set(out_df["av_id"]) == {"abcd1234"}
    assert set(out_df["transcription_source"]) == {"alpha"}
    assert set(out_df["Concepticon_ID"]) == {"1234", "5678"}


def test_custom_transcription_override(tmp_path: Path):
    forms_path, languages_path, parameters_path, _ = _write_intake(tmp_path)
    varieties_root = tmp_path / "varieties"

    catalog = build_catalog(
        languages_path,
        glottolog=_stub_glottolog(),
        overrides_path=tmp_path / "no_overrides.csv",
    )
    register(
        av_id="abcd1234",
        varieties_root=varieties_root,
        transcription_source="alpha",
        name="TestLang", glottocode="abcd1234",
        scaffold_custom=True,
    )
    vd = VarietyDir(av_id="abcd1234", root=varieties_root / "abcd1234")

    # Override segments for one row
    tov = vd.custom_dir / "transcriptions.csv"
    tov.write_text(
        "Concepticon_ID,source_form_id,Value,Form,Segments,Comment,notes\n"
        "1234,alpha_lang1_water,,,w aː t a,override test,\n",
        encoding="utf-8",
    )

    build_one(
        av_id="abcd1234",
        varieties_root=varieties_root,
        intake_forms=forms_path,
        catalog=catalog,
        parameters_path=parameters_path,
    )
    out_df = pd.read_csv(vd.generated_forms, dtype=str, keep_default_na=False)
    water_row = out_df[out_df.Concepticon_ID == "1234"].iloc[0]
    assert water_row.Segments == "w aː t a"


def test_aggregate_unions_varieties(tmp_path: Path):
    forms_path, languages_path, parameters_path, metadata_path = _write_intake(tmp_path)
    varieties_root = tmp_path / "varieties"
    catalog = build_catalog(
        languages_path,
        glottolog=_stub_glottolog(),
        overrides_path=tmp_path / "no_overrides.csv",
    )
    register(
        av_id="abcd1234",
        varieties_root=varieties_root,
        transcription_source="alpha",
        name="TestLang", glottocode="abcd1234",
        family="Testic", macroarea="Eurasia",
    )
    build_one(
        av_id="abcd1234",
        varieties_root=varieties_root,
        intake_forms=forms_path,
        catalog=catalog,
        parameters_path=parameters_path,
    )

    # Intake dir mimics layout
    intake_dir = tmp_path / "intake"
    intake_dir.mkdir()
    parameters_path.rename(intake_dir / "parameters_raw.csv")
    metadata_path.rename(intake_dir / "metadata.csv")
    (intake_dir / "sources.bib").write_text("", encoding="utf-8")

    out_dir = tmp_path / "out"
    stats = aggregate_all(
        varieties_root=varieties_root,
        intake_dir=intake_dir,
        output_dir=out_dir,
    )
    assert stats["forms_emitted"] == 2
    assert stats["varieties_emitted"] == 1
    assert (out_dir / "forms.csv").exists()
    assert (out_dir / "varieties.csv").exists()
