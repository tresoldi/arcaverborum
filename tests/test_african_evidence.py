"""Original African evidence must survive extraction without guessed readings."""

import csv
import io
import json

import pytest

from arcaverborum.historical_evidence import annotate
from arcaverborum.sources.african_lexica import digest, extract, records
from arcaverborum.tracking import custom_component


def payload(rows, delimiter=","):
    f = io.StringIO()
    w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter=delimiter)
    w.writeheader()
    w.writerows(rows)
    return f.getvalue().encode()


def test_reflex_preserves_alternatives_and_checks_attribution_and_member():
    row = dict(id="1", SOU="39", FRM="ì-vé / wæ̀-ɓé", TRA="chien")
    source = dict(id="39", LANGUE="2", BIB="3")
    language = dict(id="2", glottocode="wame1240")
    reference = dict(id="3", author="Santos", year="1996")
    data = {
        k: payload([r], "\t")
        for k, r in [("records", row), ("sources", source), ("languages", language), ("references", reference)]
    }
    spec = dict(resources=[dict(key="records", kind="reflex")], version="immutable")
    review = dict(
        resource_key="records",
        record_key="1",
        native_sha256=digest(row),
        member="39",
        entry_sha256=digest(dict(source=source, language=language, reference=reference)),
        glottocode="wame1240",
        Form=row["FRM"],
        source_sense="chien",
        rationale="Reviewed",
    )
    result = extract(spec, data, review)
    assert result["original_form"] == row["FRM"]
    assert result["reading_basis"] == "orthographic_transcription_only"
    assert result["original"]["attribution"]["reference"] == reference
    with pytest.raises(ValueError, match="member"):
        extract(spec, data, {**review, "member": "3074"})
    with pytest.raises(ValueError, match="attribution"):
        extract(spec, data, {**review, "entry_sha256": "0" * 64})
    data["records"] = payload([{**row, "TRA": "loup"}], "\t")
    with pytest.raises(ValueError, match="native record"):
        extract(spec, data, review)


def test_bound_gyeli_and_source_tones_remain_native_evidence():
    text = "{\\bfseries -bɔ̃́} ma- {\\itshape n} 6 knee\\\\\n"
    record = records("gyeli", text.encode())["1"]
    assert record["Form"] == "-bɔ̃́" and record["prefix"] == "ma-"
    assert record["source_sense"] == "knee" and record["native"] == text.strip()
    spec = dict(resources=[dict(key="book", kind="gyeli")], version="immutable")
    review = dict(
        resource_key="book",
        record_key="1",
        native_sha256=digest(record),
        Form="-bɔ̃́",
        source_sense="knee",
        member="Gyeli",
        rationale="Reviewed",
    )
    assert extract(spec, {"book": text.encode()}, review)["original_form"] == "-bɔ̃́"
    with pytest.raises(ValueError, match="drift"):
        extract(spec, {"book": text.encode()}, {**review, "Form": "bɔ"})


def test_modern_reading_metadata_is_scoped_and_invalidates_build(tmp_path):
    before = custom_component(tmp_path)
    rule = dict(
        source="tls",
        source_language_id="tls_Nata",
        reading_basis="upstream_profile_conversion",
        authority="frozen-profile",
        notes="Conversion, not independent elicitation",
    )
    (tmp_path / "reading_evidence.csv").write_bytes(payload([rule]))
    assert custom_component(tmp_path) != before
    rows = [
        dict(transcription_source=s, source_language_id=m, Comment="original")
        for s, m in [("tls", "tls_Nata"), ("tls", "tls_Other"), ("gled", "tls_Nata")]
    ]
    annotate(rows, tmp_path)
    assert "Reading evidence: " in rows[0]["Comment"]
    assert json.loads(rows[0]["Comment"].split("Reading evidence: ")[1])["reading_basis"] == rule["reading_basis"]
    assert rows[1]["Comment"] == rows[2]["Comment"] == "original"


def test_hdi_review_guards_headword_and_sense_separately():
    sense = dict(ID="SN1", Entry_ID="LX1", Description="water")
    entry = dict(ID="LX1", Headword="á", Part_Of_Speech="n")
    data = dict(senses=payload([sense]), entries=payload([entry]))
    spec = dict(resources=[dict(key="senses", kind="hdi_senses")], version="immutable")
    review = dict(
        resource_key="senses",
        record_key="SN1",
        native_sha256=digest(sense),
        entry_sha256=digest(entry),
        Form="á",
        source_sense="water",
        member="Hdi",
        rationale="Reviewed",
    )
    assert extract(spec, data, review)["reading_basis"] == "orthographic_transcription_only"
    data["entries"] = payload([{**entry, "Headword": "à"}])
    with pytest.raises(ValueError, match="headword"):
        extract(spec, data, review)


def test_materialized_slice_reports_actual_counts_and_never_infers_segments(tmp_path, monkeypatch):
    import hashlib

    from arcaverborum.sources import african_lexica as source

    data = tmp_path / "data"
    data.mkdir()
    raw = tmp_path / "raw"
    book = raw / "lexibank/demo"
    book.mkdir(parents=True)
    text = b"\\fmtLemma{maizi}\\fmtSense{water}"
    (book / "book.txt").write_bytes(text)
    record = records("ruruuli", text)["1"]
    review = dict(
        dataset="demo",
        decision="admit",
        source_form_id="word1",
        resource_key="book",
        record_key="1",
        native_sha256=digest(record),
        Form="maizi",
        source_sense="water",
        member="Ruuli",
        member_name="Ruuli",
        glottocode="ruul1235",
        family="Atlantic-Congo",
        concept_id="phy-water",
        rationale="Reviewed written evidence",
    )
    (tmp_path / "review.csv").write_bytes(payload([review]))
    (data / "concepts.csv").write_bytes(payload([dict(concept_id="phy-water", concepticon_id="948", label="water")]))
    spec = dict(
        dataset="demo",
        resources=[dict(key="book", kind="ruruuli", filename="book.txt", sha256=hashlib.sha256(text).hexdigest())],
        review="review.csv",
        license="CC BY4",
        citation="Original dictionary",
        genealogy="Original",
        version="immutable",
        name="Reviewed slice",
        url="https://example.org/source",
    )
    (data / "african_lexical_sources.json").write_text(json.dumps([spec]))
    monkeypatch.setattr(source, "ROOT", tmp_path)
    monkeypatch.setattr(source, "DATA", data)
    result = source.materialize(raw, dataset="demo")
    assert result == dict(dataset="demo", forms=1, members=1)
    metadata = json.loads((book / "cldf/cldf-metadata.json").read_text())
    assert all(t["dc:extent"] == 1 for t in metadata["tables"])
    with (book / "cldf/forms.csv").open() as f:
        row = next(csv.DictReader(f))
    assert not row["Segments"] and row["Value"] == "maizi"


def test_sidaama_needs_explicit_ipa_on_every_original_homograph():
    from arcaverborum.sources.sidaama_readings import phonemic_witnesses

    raw = "\\lx baalliʧʧo\n\\lx_SidIPA baalliʧʧo\n\\lc_Sid baallichcho\n".encode()
    witnesses = phonemic_witnesses(raw, "baalliʧʧo")
    assert witnesses[0]["source_ipa"] == "baalliʧʧo"
    assert witnesses[0]["official_orthography"] == "baallichcho"
    with pytest.raises(ValueError, match="missing or ambiguous"):
        phonemic_witnesses(raw.replace(b"\\lx_SidIPA", b"\\untyped"), "baalliʧʧo")
    with pytest.raises(ValueError, match="missing or ambiguous"):
        phonemic_witnesses(raw + "\\lx baalliʧʧo\n\\lx_SidIPA baallikoo\n".encode(), "baalliʧʧo")


def test_source_unit_analysis_keeps_prenasalized_phonemes_and_gyeli_clusters_distinct():
    import merkmal

    from arcaverborum.phonology import apply_profile, load_profile

    for unit, place, manner in [
        ("ⁿk", "velar", "stop"),
        ("ŋɡ", "velar", "stop"),
        ("ⁿʃ", "post-alveolar", "fricative"),
        ("ᵐv", "labio-dental", "fricative"),
    ]:
        features = merkmal.get_features(unit, system="descriptive")
        assert {"pre-nasalized", place, manner} <= features
        assert "consonant-cluster" not in features
    from pathlib import Path

    profile = load_profile(Path("varieties/atl-gyele/custom/supplement_profiles/gyelioriginal.tsv"))
    segments, covered = apply_profile("mpàálé", profile)
    assert covered and segments.split()[:2] == ["m", "p"]
    assert not apply_profile("mpàálémpàálé", profile)[1]


@pytest.mark.parametrize(
    "dataset,error",
    [
        ("fweoriginal", "POS mismatch"),
        ("sidaamaoriginal", "POS mismatch"),
        ("reflexoriginal", "POS mismatch"),
        ("hdioriginal", "comparison meaning"),
    ],
)
def test_dictionary_compiler_rejects_noun_verb_homonyms(tmp_path, monkeypatch, dataset, error):
    import importlib.util
    from pathlib import Path

    monkeypatch.syspath_prepend(str(Path("scripts").resolve()))
    spec = importlib.util.spec_from_file_location("african_compiler", Path("scripts/compile_african_lexica.py"))
    compiler = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(compiler)
    data = tmp_path / "src/arcaverborum/data"
    data.mkdir(parents=True)
    (data / "concepts.csv").write_bytes(
        payload([dict(concept_id="ani-fish", concepticon_id="227", label="fish", pos="n")])
    )
    (data / "african_lexical_sources.json").write_text(json.dumps([dict(dataset=dataset, review="review.csv")]))
    stage = tmp_path / ("raw/curation/stage-" + dataset + "/lexibank")
    stage.mkdir(parents=True)
    originals = {
        "fweoriginal": dict(native="head\\relax v \\relax fish"),
        "sidaamaoriginal": dict(entry=dict(Part_Of_Speech="Verb")),
        "reflexoriginal": dict(record=dict(CGR="V")),
        "hdioriginal": dict(entry=dict(Part_Of_Speech="Noun"), sense=dict(Concepticon_ID="999")),
    }
    row = dict(
        ID=dataset + "_v1",
        Parameter_ID="p",
        Form="fish",
        Glottocode="fwee1238",
        Language_ID="fweoriginal_Fwe",
        Comment=json.dumps(dict(native_sha256="guard", source_member="Fwe", original=originals[dataset])),
    )
    (stage / "forms.csv").write_bytes(payload([row]))
    (stage / "parameters_raw.csv").write_bytes(payload([dict(ID="p", Name="fish", Concepticon_ID="227")]))
    review = dict(
        decision="admit",
        source_form_id="v1",
        Form="fish",
        source_sense="fish",
        glottocode="fwee1238",
        native_sha256="guard",
        member="Fwe",
        concept_id="ani-fish",
    )
    (tmp_path / "review.csv").write_bytes(payload([review]))
    with pytest.raises(ValueError, match=error):
        compiler.compile_lexica(root=tmp_path)
