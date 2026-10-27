"""Original Bangru admission preserves speaker identity and all IPA alternatives."""

import csv
import hashlib
import json

import pytest

from arcaverborum.ingest import _process_one
from arcaverborum.sources import bangru_original as source


def entry(raw="wiʔ", text=None):
    text = text or f"water {raw} [A], other [C], Root: tentative Dammai: foreign [A]"
    return dict(
        ID="p23-water",
        source_page="23",
        source_gloss="water",
        source_entry=text,
        entry_sha256=hashlib.sha256(text.encode()).hexdigest(),
        speaker="A",
        raw_transcriptions=json.dumps(raw.split(", ")),
        concept_id="phy-water",
        decision="admit",
        rationale="Explicit source sense and speaker; keep supplied IPA.",
    )


CONCEPTS = {"phy-water": dict(concept_id="phy-water", concepticon_id="948", label="water")}


def test_original_speaker_span_and_all_alternatives_are_retained():
    forms, params = source.reviewed_rows([entry("wiʔ, wiː")], CONCEPTS)
    assert [r["Form"] for r in forms] == ["wiʔ", "wiː"]
    assert [r["Segments"] for r in forms] == ["w i ʔ", "w iː"]
    assert len(params) == 1
    assert all(r["Language_ID"] == "BangruA" and r["Source"] == "Bodt2017" for r in forms)
    assert "tentative" in forms[0]["Comment"]  # preserved evidence is not an inferred judgment
    assert not any("Cognacy" in r for r in forms)
    from arcaverborum.phonology import canonicalize_token

    assert source.reading("podʒuː").split() == ["p", "o", canonicalize_token("d͡ʒ"), "uː"]
    assert source.reading("goː məpja") == "ɡ oː _ m ə p j a"


@pytest.mark.parametrize(
    "change",
    [
        {"speaker": "C"},
        {"raw_transcriptions": '["foreign"]'},
        {"source_page": "25"},
        {"source_entry": "changed"},
    ],
)
def test_source_identity_or_evidence_drift_fails_closed(change):
    with pytest.raises(ValueError):
        source.reviewed_rows([{**entry(), **change}], CONCEPTS)


def test_reconstructions_foreign_labels_and_partial_alternatives_cannot_be_admitted():
    for row in [entry(text="water Root: wiʔ [A]"), entry(text="water wiʔ [China], Root: wiʔ [A]"), entry("wiʔ, (wiː)")]:
        with pytest.raises(ValueError):
            source.reviewed_rows([row], CONCEPTS)
    assert source.reading("'nedi") == ""
    assert source.reading("mətɛ̃") == "m ə t ɛ̃"
    assert source.reading("dzɨ") == ""  # not silently split into a speculative cluster


def write(path, rows):
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_materialized_document_ingests_with_real_source_version_and_no_git(tmp_path, monkeypatch):
    data = tmp_path / "data"
    data.mkdir()
    spec = json.loads((source.DATA / "bangru_original_source.json").read_text())
    spec["sha256"] = hashlib.sha256(b"frozen original").hexdigest()
    (data / "bangru_original_source.json").write_text(json.dumps(spec))
    write(data / "bangru_original_forms.csv", [entry()])
    write(data / "concepts.csv", list(CONCEPTS.values()))
    monkeypatch.setattr(source, "DATA", data)
    directory = tmp_path / "raw/lexibank/bodtbangru"
    directory.mkdir(parents=True)
    pdf = directory / spec["filename"]
    pdf.write_bytes(b"frozen original")
    source.materialize(tmp_path / "raw")
    forms, langs, parameters, metadata, bib = _process_one("bodtbangru", directory / "cldf")
    assert forms.iloc[0].Segments == "w i ʔ" and forms.iloc[0].Glottocode == "bang1369"
    assert langs.iloc[0].ID == "bodtbangru_BangruA"
    assert parameters.iloc[0].Concepticon_ID == "948"
    assert metadata["License"] == spec["license"] and spec["doi"] in metadata["Repository_Version"]
    assert "Bodt2017" in bib and spec["sha256"] in forms.iloc[0].Comment
    pdf.write_bytes(b"changed original")
    with pytest.raises(ValueError, match="exact reviewed"):
        source.materialize(tmp_path / "raw")


def test_all_authored_admissions_validate_without_network():
    concepts = {r["concept_id"]: r for r in source.read(source.DATA / "concepts.csv")}
    forms, params = source.reviewed_rows(source.read(source.DATA / "bangru_original_forms.csv"), concepts)
    assert len(forms) == 99 and len(params) == 95


def test_document_fetch_route_never_attempts_git_clone(tmp_path, monkeypatch):
    from arcaverborum.sources import lexibank

    registry = tmp_path / "datasets.csv"
    registry.write_text("NAME,URL,ExpertCognates,CORE\nbodtbangru,https://zenodo.org/records/1116263,,\n")
    calls = []
    monkeypatch.setattr(source, "materialize", lambda root, download=False: calls.append((root, download)))

    def reject_clone(*args):
        raise AssertionError("A document deposit is not a Git remote")

    monkeypatch.setattr(lexibank, "_clone", reject_clone)
    stats = lexibank.fetch(tmp_path / "raw", datasets_csv=registry)
    assert stats == {"cloned": 1, "updated": 0, "failed": 0}
    assert calls == [(tmp_path / "raw", True)]


def test_changed_deposit_license_does_not_replace_cached_document(tmp_path, monkeypatch):
    spec = json.loads((source.DATA / "bangru_original_source.json").read_text())
    directory = tmp_path / "lexibank/bodtbangru"
    directory.mkdir(parents=True)
    pdf = directory / spec["filename"]
    pdf.write_bytes(b"preserved cached source")

    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return {"metadata": {"license": {"id": "unknown"}}}

    monkeypatch.setattr(source.requests, "get", lambda *args, **kwargs: Response())
    with pytest.raises(ValueError, match="license changed"):
        source.materialize(tmp_path, download=True)
    assert pdf.read_bytes() == b"preserved cached source"
