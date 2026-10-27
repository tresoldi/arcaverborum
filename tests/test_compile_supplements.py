"""Compiling a partial review must retain existing admissions from other sources."""

import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "compile_supplements", Path(__file__).parents[1] / "scripts/compile_supplements.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_partial_review_retains_prior_sources_and_scoped_alternatives():
    old = dict(source="dictionary", source_form_id="s1", source_pronunciation_id="p1", evidence_sha256="a")
    new = dict(source="wiktionary", source_form_id="w1", evidence_sha256="b")
    assert module.merge_reviews([old], [new]) == [old, new]
    with pytest.raises(ValueError, match="evidence changed"):
        module.merge_reviews([new], [{**new, "evidence_sha256": "changed"}])
    with pytest.raises(ValueError, match="Duplicate"):
        module.merge_reviews([], [new, new])
    with pytest.raises(ValueError, match="evidence changed"):
        module.merge_reviews(
            [{**new, "expected_source_concepticon_id": "948"}], [{**new, "expected_source_concepticon_id": "changed"}]
        )
    scoped = {**new, "profile_file": "profile.tsv"}
    with pytest.raises(ValueError, match="own compiler"):
        module.merge_reviews([scoped], [new])


def test_compiler_accepts_explicit_scholarly_source_and_guards_changed_sense(tmp_path, monkeypatch):
    import csv
    import sqlite3
    import sys

    def write(path, rows):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    monkeypatch.setattr(module, "ROOT", tmp_path)
    parameter = tmp_path / "intake/lexibank/parameters_raw.csv"
    write(parameter, [dict(ID="scholar_water", Dataset="scholar", Name="water", Concepticon_ID="948")])
    config = tmp_path / "varieties/und-test/config.yaml"
    config.parent.mkdir(parents=True)
    config.write_text("av_id: und-test\nglottocode: xxxx1234\n")
    row = dict(
        gc_lc="xxxx1234",
        ID="scholar_1",
        Dataset="scholar",
        Language_ID="scholar_member",
        Glottocode="xxxx1234",
        Parameter_ID="scholar_water",
        Form="pa",
        Segments="p a",
    )
    with sqlite3.connect(tmp_path / "intake/intake.sqlite") as db:
        db.execute("CREATE TABLE forms (" + ",".join(key + " TEXT" for key in row) + ")")
        db.execute("INSERT INTO forms VALUES (" + ",".join("?" for _ in row) + ")", list(row.values()))
    review = tmp_path / "review.csv"
    write(
        review,
        [
            dict(
                av_id="und-test",
                source="scholar",
                source_form_id="scholar_1",
                Form="pa",
                source_sense="water",
                concept_id="phy-water",
                decision="admit",
                rationale="Explicit source sense",
            )
        ],
    )
    monkeypatch.setattr(sys, "argv", ["compile_supplements", "--review", str(review), "--write"])
    module.main()
    ledger = module.read(config.parent / "custom/supplements.csv")
    assert ledger[0]["source"] == "scholar"
    assert ledger[0]["source_language_id"] == "scholar_member"
    rows = module.read(review)
    rows[0]["source_language_id"] = "wrong_member"
    write(review, rows)
    with pytest.raises(ValueError, match="source member changed"):
        module.main()
    rows[0]["source_language_id"] = "scholar_member"
    write(review, rows)
    write(parameter, [dict(ID="scholar_water", Dataset="scholar", Name="river", Concepticon_ID="948")])
    with pytest.raises(ValueError, match="sense changed"):
        module.main()
