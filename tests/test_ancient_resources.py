"""A second original file must preserve earlier evidence and fail on unpinned input."""

import csv
import hashlib
import json

import pytest

from arcaverborum.sources import ancient_lexica as ancient


def fixture_source(tmp_path, monkeypatch):
    data = tmp_path / "data"
    data.mkdir()
    root = tmp_path / "raw/lexibank/pilot"
    root.mkdir(parents=True)
    resources = []
    reviews = []
    for name, entry, form in [("alpha.xml", "A", "one"), ("beta.xml", "B", "two")]:
        payload = (
            f'<TEI xmlns="http://www.tei-c.org/ns/1.0"><entry xml:id="{entry}">'
            f'<form xml:id="F{entry}"><orth>{form}</orth><usg type="geo">S</usg></form>'
            '<cit xml:lang="en"><quote>literal</quote></cit></entry></TEI>'
        ).encode()
        (root / name).write_bytes(payload)
        resources.append(
            dict(filename=name, url="https://example.org/" + name, sha256=hashlib.sha256(payload).hexdigest())
        )
        reviews.append(
            dict(
                dataset="pilot",
                source_entry_id=entry,
                source_form_id="F" + entry,
                source_filename=name,
                source_parameter_id=entry,
                Form=form,
                source_sense="literal",
                concept_id="test",
                decision="admit",
                rationale="Exact sense.",
            )
        )
    spec = dict(
        dataset="pilot",
        kind="coptic",
        **resources[0],
        resources=resources,
        version="frozen",
        review="review.csv",
        member="S",
        name="Pilot",
        glottocode="test1234",
        license="CC-BY",
        citation="Source",
    )
    (data / "ancient_lexical_sources.json").write_text(json.dumps([spec]))
    ancient.write_csv(data / "concepts.csv", [dict(concept_id="test", concepticon_id="1", label="literal")])
    ancient.write_csv(tmp_path / "review.csv", reviews)
    monkeypatch.setattr(ancient, "ROOT", tmp_path)
    monkeypatch.setattr(ancient, "DATA", data)
    return root, reviews


def test_second_file_preserves_original_form_evidence(tmp_path, monkeypatch):
    root, _ = fixture_source(tmp_path, monkeypatch)
    ancient.materialize(tmp_path / "raw", dataset="pilot")
    rows = list(csv.DictReader((root / "cldf/forms.csv").open()))
    assert [r["Form"] for r in rows] == ["one", "two"]
    contexts = [json.loads(r["Comment"]) for r in rows]
    assert contexts[0]["source_sha256"] == hashlib.sha256((root / "alpha.xml").read_bytes()).hexdigest()
    assert contexts[1]["source_sha256"] == hashlib.sha256((root / "beta.xml").read_bytes()).hexdigest()
    assert [r["Parameter_ID"] for r in rows] == ["A", "B"]
    (root / "beta.xml").write_bytes(b"changed")
    with pytest.raises(ValueError, match="hash mismatch"):
        ancient.materialize(tmp_path / "raw", dataset="pilot")


def test_review_cannot_select_unpinned_file(tmp_path, monkeypatch):
    _, reviews = fixture_source(tmp_path, monkeypatch)
    reviews[1]["source_filename"] = "unreviewed.xml"
    ancient.write_csv(tmp_path / "review.csv", reviews)
    with pytest.raises(ValueError, match="unpinned resource"):
        ancient.materialize(tmp_path / "raw", dataset="pilot")
