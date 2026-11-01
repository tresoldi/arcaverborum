"""Regression cases exposed by independent adversarial reviews."""

import csv
import json

from test_colexification import csv_file, fixture, form

from arcaverborum.colexification import analytical_exclusion, build, connect, digest
from arcaverborum.colexification_evidence import SemanticEligibility, projection_edges


def test_conflicting_local_targets_are_order_independent_and_fail_closed(tmp_path):
    path = tmp_path / "varieties/a/custom/concept_map.csv"
    row = dict(
        av_id="a",
        transcription_source="wiktionary",
        source_parameter_id="wikt_p",
        source_form_id="native",
        concept_id="x-0",
    )
    for targets in [("x-0", "x-1"), ("x-1", "x-0")]:
        csv_file(path, [dict(Parameter_ID="wikt_p", action="map", concept_id=t) for t in targets])
        assert SemanticEligibility(tmp_path).status(row) == "unreviewed_dictionary_sense"


def test_parameter_hold_and_ambiguity_require_record_scoped_resolution(tmp_path):
    csv_file(
        tmp_path / "varieties/a/custom/concept_map.csv", [dict(Parameter_ID="wikt_p", action="map", concept_id="x-0")]
    )
    csv_file(
        tmp_path / "intake/wiktionary/parameters_raw.csv",
        [dict(ID="wikt_p", Name=n, Concepticon_ID="1") for n in ["sense A", "sense B"]],
    )
    row = dict(
        av_id="a",
        transcription_source="wiktionary",
        source_parameter_id="wikt_p",
        source_form_id="native",
        concept_id="x-0",
    )
    gate = SemanticEligibility(tmp_path)
    assert gate.status(row) == "unreviewed_dictionary_sense"
    gate.records["a", "native"] = "x-0"
    assert gate.status(row) == "reviewed_dictionary_sense"
    gate.record_holds.add(("a", "native"))
    assert gate.status(row) == "unreviewed_dictionary_sense"


def test_known_parser_prefix_failure_is_guarded_across_members():
    for member in ["30", "40", "43", "100"]:
        assert (
            analytical_exclusion(
                dict(
                    transcription_source="huntergatherer",
                    source_language_id="huntergatherer_" + member,
                    Value="k'ete",
                    Form="k",
                )
            )
            == "source_extraction_prefix"
        )
    assert analytical_exclusion(dict(transcription_source="huntergatherer", Value="k'ete", Form="k'ete")) == ""
    assert analytical_exclusion(dict(transcription_source="other", Value="k'ete", Form="k")) == ""


def test_isolate_dialects_share_family_and_pseudo_categories_are_unknown(tmp_path):
    fixture(tmp_path, [form(0), form(1)])
    csv_file(
        tmp_path / "raw/glottolog/languages.csv",
        [
            dict(ID="iso", Name="Isolate", Level="language", Language_ID="iso", Family_ID="", Is_Isolate="true"),
            dict(ID="a", Name="Dialect", Level="dialect", Language_ID="iso", Family_ID="iso", Is_Isolate=""),
            dict(ID="b", Name="Retired", Level="language", Language_ID="b", Family_ID="book1242", Is_Isolate=""),
            dict(ID="book1242", Name="Bookkeeping", Level="family", Language_ID="", Family_ID="", Is_Isolate=""),
        ],
    )
    p = tmp_path / "output/aggregate/varieties.csv"
    vs = list(csv.DictReader(p.open()))
    vs.append(vs[0] | dict(av_id="iso", Glottocode="iso", Name="Isolate"))
    csv_file(p, vs)
    db = connect(build(tmp_path) / "index.sqlite")
    assert db.execute("SELECT family FROM varieties WHERE av='a'").fetchone()[0] == "isolate:iso"
    assert db.execute("SELECT family FROM varieties WHERE av='iso'").fetchone()[0] == "isolate:iso"
    assert db.execute("SELECT family FROM varieties WHERE av='b'").fetchone()[0] == ""
    db.close()


def test_catalog_overlap_preserves_observation_but_excludes_projection(tmp_path):
    concepts = fixture(
        tmp_path, [form(i, av=av, source=s) for av, s in [("a", "source"), ("b", "second")] for i in [0, 1]]
    )
    p = tmp_path / "raw/glottolog/languages.csv"
    rs = list(csv.DictReader(p.open()))
    next(r for r in rs if r["ID"] == "b")["Family_ID"] = "other"
    csv_file(p, rs)
    csv_file(
        tmp_path / "src/arcaverborum/data/colexification/concept_relations.csv",
        [
            dict(
                a="x-0",
                b="x-1",
                relation="overlap",
                a_sha256=digest(concepts[0]),
                b_sha256=digest(concepts[1]),
                rationale="Explicit reviewed overlap fixture",
            )
        ],
    )
    db = connect(build(tmp_path) / "index.sqlite")
    value = json.loads(db.execute("SELECT value FROM assessments WHERE layer='segmented'").fetchone()[0])
    assert value["status"] == "catalog_overlap" and value["clustering_weight"] == 0
    assert db.execute("SELECT COUNT(*) FROM witnesses WHERE layer='segmented'").fetchone()[0] == 2
    assert projection_edges(db, {"x-0": 0, "x-1": 1}) == []
    db.close()


def test_production_projection_resampling_retains_distinct_family_requirement(tmp_path):
    fixture(tmp_path, [form(i, av=av, source=s) for av, s in [("a", "source"), ("b", "second")] for i in [0, 1]])
    p = tmp_path / "raw/glottolog/languages.csv"
    rs = list(csv.DictReader(p.open()))
    next(r for r in rs if r["ID"] == "b")["Family_ID"] = "other"
    csv_file(p, rs)
    db = connect(build(tmp_path) / "index.sqlite")
    index = {"x-0": 0, "x-1": 1}
    assert projection_edges(db, index, {"fam": 100}) == []
    assert projection_edges(db, index, {"fam": 3, "other": 2}) == [(0, 1, 2)]
    db.close()
