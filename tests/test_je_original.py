"""Original Jê notation remains profile-derived and automatic cognacy stays raw."""

import importlib.util
import json
from pathlib import Path

import pytest

from arcaverborum.ingest import _process_one
from arcaverborum.phonology import apply_profile, load_profile, normalize_segments
from arcaverborum.sources import je_original as source

spec = importlib.util.spec_from_file_location(
    "stage_je_original", Path(__file__).parents[1] / "scripts/stage_je_original.py"
)
stage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stage)
compile_profiles = stage.compile_profiles

CONCEPTS = {"phy-water": dict(concepticon_id="948", label="water")}
LANGUAGES = {"Xerénte": dict(ID="Xerente", Glottocode="xere1240", Name="Xerénte", Glottolog_Name="Xerénte")}


def example():
    original = dict(id="1", DOCULECT="Xerénte", CONCEPT="WATER", VALUE="k u", FORM="k u", COGID="7")
    review = dict(
        ID="1",
        doculect="Xerénte",
        source_concept="WATER",
        raw_value="k u",
        source_form="k u",
        row_sha256=source.row_hash(original),
        concept_id="phy-water",
        decision="admit",
        ipa_segments="k u",
        rationale="Reviewed broad phonemic reading.",
    )
    return original, review


def test_notation_is_not_silently_supplied_ipa_or_expert_cognacy():
    original, review = example()
    forms, params = source.reviewed_rows([original], [review], CONCEPTS, LANGUAGES)
    assert forms[0]["Segments"] == ""
    assert "Cognacy" not in forms[0] and "COGID" in forms[0]["Comment"]
    assert params[0]["Concepticon_ID"] == "948"
    assert normalize_segments("", forms[0]["Form"], {"^k u$": "k u"}) == ("k u", "profile")


@pytest.mark.parametrize(
    "change",
    [
        dict(doculect="Ingain"),
        dict(raw_value="k a"),
        dict(source_concept="FIRE"),
        dict(ipa_segments="k a"),
        dict(row_sha256="changed"),
    ],
)
def test_identity_source_or_profile_drift_fails_closed(change):
    original, review = example()
    with pytest.raises(ValueError):
        source.reviewed_rows([original], [{**review, **change}], CONCEPTS, LANGUAGES)


@pytest.mark.parametrize(
    "notation", ["c a", "ĵ a", "j a", "r a", "y a", "m/b a", "a nan", "̃ə", "k api", "*k a", "e", "ô"]
)
def test_ambiguous_notation_is_held_even_if_a_symbol_is_valid_ipa(notation):
    assert source.conservative_reading(notation) == ""


def test_compiled_profiles_match_every_authored_admission():
    root = Path(__file__).resolve().parents[1]
    compile_profiles(root)
    reviews = source.read(source.DATA / "je_original_review.csv")
    expected = {
        "Xerénte": (120, 86), "Xavánte": (107, 73), "Ingain": (26, 24),
        "Panará": (59, 58), "Apinayé": (151, 116),
    }
    for name, (forms, concepts) in expected.items():
        rows = [r for r in reviews if r["doculect"] == name and r["decision"] == "admit"]
        assert len(rows) == forms and len({r["concept_id"] for r in rows}) == concepts
    profile = load_profile(root / "varieties/nub-ingain/custom/profile.tsv")
    assert apply_profile("unreviewed", profile) == ("", False)


def test_precomposed_and_decomposed_nasal_vowels_have_identical_readings():
    assert source.conservative_reading("k ẽ ɾ") == "k ẽ ɾ"
    assert source.conservative_reading("k e\u0303 ɾ") == "k ẽ ɾ"
    assert source.conservative_reading("n ũ n d a") == "n ũ n d a"


def test_materialized_source_ingests_with_raw_evidence_and_frozen_hash(tmp_path, monkeypatch):
    data = tmp_path / "data"
    data.mkdir()
    original, review = example()
    source.write_csv(data / "je_original_review.csv", [review])
    source.write_csv(data / "concepts.csv", [dict(concept_id="phy-water", **CONCEPTS["phy-water"])])
    directory = tmp_path / "raw/lexibank/gerardije2025"
    directory.mkdir(parents=True)
    import csv
    import hashlib

    with (directory / "auto_cogids.tsv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(original), delimiter="\t")
        writer.writeheader()
        writer.writerow(original)
    spec = json.loads((source.DATA / "je_original_source.json").read_text())
    spec["files"] = {"data/auto_cogids.tsv": hashlib.sha256((directory / "auto_cogids.tsv").read_bytes()).hexdigest()}
    spec["languages"] = [dict(Source_Doculect="Xerénte", **LANGUAGES["Xerénte"])]
    (data / "je_original_source.json").write_text(json.dumps(spec))
    monkeypatch.setattr(source, "DATA", data)
    source.materialize(tmp_path / "raw")
    forms, langs, params, meta, bib = _process_one("gerardije2025", directory / "cldf")
    assert forms.iloc[0].Segments == "" and forms.iloc[0].Glottocode == "xere1240"
    assert forms.iloc[0].Cognacy == "" and forms.iloc[0].Cognate_Detection_Method == ""
    assert langs.iloc[0].ID == "gerardije2025_Xerente"
    assert params.iloc[0].Concepticon_ID == "948" and spec["commit"] in meta["Repository_Version"]
    assert "FerrazGerardi2025" in bib and spec["files"]["data/auto_cogids.tsv"] in forms.iloc[0].Comment
    (directory / "auto_cogids.tsv").write_text("changed")
    with pytest.raises(ValueError, match="Fetch exact"):
        source.materialize(tmp_path / "raw")


def test_duplicate_original_identity_cannot_overwrite_evidence():
    original, review = example()
    with pytest.raises(ValueError, match="Duplicate original"):
        source.reviewed_rows([original, original], [review], CONCEPTS, LANGUAGES)


def test_generic_fetch_materializes_frozen_source_without_git(tmp_path, monkeypatch):
    from arcaverborum.sources import lexibank

    registry = tmp_path / "datasets.csv"
    registry.write_text("NAME,URL\ngerardije2025,https://github.com/TGH-2020/Je_Phylogeny\n")
    calls = []
    monkeypatch.setattr(source, "materialize", lambda root, download=False: calls.append((root, download)))
    monkeypatch.setattr(lexibank, "_clone", lambda *args: pytest.fail("Frozen source must not clone"))
    monkeypatch.setattr(lexibank, "_update", lambda *args: pytest.fail("Frozen source must not pull"))
    stats = lexibank.fetch(tmp_path / "raw", datasets_csv=registry)
    assert calls == [(tmp_path / "raw", True)]
    assert stats == dict(cloned=1, updated=0, failed=0)


def test_xerente_cross_is_the_attested_traverse_verb():
    row = next(r for r in source.read(source.DATA / "je_original_review.csv") if r["ID"] == "658")
    assert row["source_concept"] == "CROSS" and row["raw_value"] == "t b ɾ ɔ"
    assert row["concept_id"] == "mot-traverse" and "p.453" in row["rationale"]


def test_language_specific_profiles_do_not_leak_to_other_samples():
    assert source.conservative_reading("c r j ñ ê ô y", "Apinayé") == "t͡ʃ ɾ j ɲ e o ɨ"
    assert source.conservative_reading("c r j ñ ê ô y", "Panará") == ""
    assert source.conservative_reading("j ĭ", "Panará") == "j ĭ"
    assert source.conservative_reading("j ĭ", "Ingain") == ""
    assert source.conservative_reading("ɾi", "Ingain") == "ɾ i"
    assert source.conservative_reading("ɾi", "Apinayé") == ""
    assert source.conservative_reading("m/b a", "Apinayé") == ""
    assert source.conservative_reading("e o", "Apinayé") == ""


def test_non_core_semantic_holds_are_not_profile_admissions():
    reviews = source.read(source.DATA / "je_original_review.csv")
    rattle = [r for r in reviews if r["doculect"] == "Apinayé" and r["source_concept"] == "RATTLE"]
    assert rattle and all(r["decision"] == "hold" and not r["ipa_segments"] for r in rattle)
    assert any("football" in r["rationale"] for r in rattle)
