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
