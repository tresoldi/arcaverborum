"""Tests for the console data explorer (SQLite-indexed queries)."""

from __future__ import annotations

import csv
import os
import sqlite3

import pytest

from arcaverborum import explore

FORMS_COLUMNS = [
    "av_id", "Glottocode", "Variety_Name", "Concepticon_ID", "Concepticon_Gloss",
    "Value", "Form", "Segments", "Segments_Source", "Cognacy", "canonical_cognate_id",
    "Alignment", "Morpheme_Index", "Segment_Slice", "Doubt", "Cognate_Detection_Method",
    "Cognate_Source", "Loan", "Comment", "transcription_source", "cognate_source",
    "source_form_id", "source_language_id", "source_parameter_id", "bibtex_key",
    "quality_score", "tier",
]

VARIETIES_COLUMNS = [
    "av_id", "Glottocode", "Name", "Family", "Macroarea", "transcription_source",
    "cognate_source", "pinned", "forms_score", "cognates_score", "tier",
]


def _form(**kw) -> dict:
    row = {c: "" for c in FORMS_COLUMNS}
    row.update(kw)
    return row


_VARIETIES = [
    dict(av_id="ine-latin", Glottocode="lati1261", Name="Latin", Family="Indo-European",
         Macroarea="Eurasia", transcription_source="kessler", cognate_source="kessler",
         pinned="false", forms_score="0.99", cognates_score="0.7", tier="bronze"),
    dict(av_id="ine-greek", Glottocode="gree1276", Name="Greek", Family="Indo-European",
         Macroarea="Eurasia", transcription_source="kessler", cognate_source="kessler",
         pinned="false", forms_score="0.95", cognates_score="0.7", tier="silver"),
    dict(av_id="sit-mandarin", Glottocode="mand1415", Name="Mandarin Chinese",
         Family="Sino-Tibetan", Macroarea="Eurasia", transcription_source="beidasinitic",
         cognate_source="beidasinitic", pinned="false", forms_score="0.8",
         cognates_score="0.6", tier="copper"),
]

_FORMS = [
    _form(av_id="ine-latin", Glottocode="lati1261", Variety_Name="Latin",
          Concepticon_ID="948", Concepticon_Gloss="WATER", Value="aqua", Form="aqua",
          Segments="a k w a", Segments_Source="source", canonical_cognate_id="cs1",
          Loan="false", transcription_source="kessler", quality_score="0.99", tier="bronze"),
    _form(av_id="ine-latin", Glottocode="lati1261", Variety_Name="Latin",
          Concepticon_ID="221", Concepticon_Gloss="FIRE", Value="ignis", Form="ignis",
          Segments="i g n i s", Segments_Source="source", canonical_cognate_id="cs2",
          Loan="false", transcription_source="kessler", quality_score="0.99", tier="bronze"),
    _form(av_id="ine-greek", Glottocode="gree1276", Variety_Name="Greek",
          Concepticon_ID="948", Concepticon_Gloss="WATER", Value="hydor", Form="hydor",
          Segments="h y d o r", Segments_Source="source", canonical_cognate_id="cs1",
          Loan="false", transcription_source="kessler", quality_score="0.95", tier="silver"),
    _form(av_id="sit-mandarin", Glottocode="mand1415", Variety_Name="Mandarin Chinese",
          Concepticon_ID="948", Concepticon_Gloss="WATER", Value="shui", Form="shui",
          Segments="ʂ w ei", Segments_Source="resegmented", canonical_cognate_id="cs3",
          Loan="true", transcription_source="beidasinitic", quality_score="0.8", tier="copper"),
    _form(av_id="sit-mandarin", Glottocode="mand1415", Variety_Name="Mandarin Chinese",
          Concepticon_ID="221", Concepticon_Gloss="FIRE", Value="huo", Form="huo",
          Segments="", Segments_Source="unclean", canonical_cognate_id="",
          Loan="false", transcription_source="beidasinitic", quality_score="0.8", tier="copper"),
]


def _write_csv(path, columns, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader()
        w.writerows(rows)


@pytest.fixture()
def agg_dir(tmp_path):
    d = tmp_path / "aggregate"
    d.mkdir()
    _write_csv(d / "forms.csv", FORMS_COLUMNS, _FORMS)
    _write_csv(d / "varieties.csv", VARIETIES_COLUMNS, _VARIETIES)
    _write_csv(d / "parameters.csv", ["Concepticon_ID", "Concepticon_Gloss", "Name"],
               [{"Concepticon_ID": "948", "Concepticon_Gloss": "WATER", "Name": "water"},
                {"Concepticon_ID": "221", "Concepticon_Gloss": "FIRE", "Name": "fire"}])
    _write_csv(d / "metadata.csv", ["Dataset", "Title"],
               [{"Dataset": "kessler", "Title": "Kessler"}])
    return d


@pytest.fixture()
def con(tmp_path, agg_dir):
    db = tmp_path / "explore.sqlite"
    explore.build_index(agg_dir, db, force=True)
    return explore.connect(db)


# --- index building -------------------------------------------------------

def test_build_index_counts_and_skip(tmp_path, agg_dir):
    db = tmp_path / "explore.sqlite"
    res = explore.build_index(agg_dir, db)
    assert res["status"] == "built"
    assert res["counts"]["forms"] == 5
    assert res["counts"]["varieties"] == 3
    # Second call with no source change → skipped.
    assert explore.build_index(agg_dir, db)["status"] == "up-to-date"
    # Forced rebuild always rebuilds.
    assert explore.build_index(agg_dir, db, force=True)["status"] == "built"


def test_build_index_requires_aggregate(tmp_path):
    with pytest.raises(FileNotFoundError):
        explore.build_index(tmp_path / "missing", tmp_path / "x.sqlite")


def test_index_staleness(tmp_path, agg_dir, con):
    assert explore.index_is_stale(con, agg_dir) is False
    # Bump the forms.csv mtime into the future → signature changes.
    forms = agg_dir / "forms.csv"
    future = forms.stat().st_mtime + 1000
    os.utime(forms, (future, future))
    assert explore.index_is_stale(con, agg_dir) is True


# --- variety resolution ---------------------------------------------------

def test_resolve_variety_by_avid_glottocode_name(con):
    assert explore.resolve_variety(con, "ine-latin") == "ine-latin"
    assert explore.resolve_variety(con, "lati1261") == "ine-latin"
    assert explore.resolve_variety(con, "Latin") == "ine-latin"
    assert explore.resolve_variety(con, "mandarin") == "sit-mandarin"  # substring, ci


def test_resolve_variety_miss(con):
    with pytest.raises(LookupError):
        explore.resolve_variety(con, "nonexistent-zzz")


# --- queries --------------------------------------------------------------

def test_q_lang(con):
    cols, rows = explore.q_lang(con, "ine-latin")
    assert len(rows) == 2
    assert "Concepticon_Gloss" in cols
    cols, rows = explore.q_lang(con, "ine-latin", concept="WATER")
    assert len(rows) == 1


def test_q_concept_by_gloss_id_and_family(con):
    _, rows = explore.q_concept(con, "WATER")
    assert len(rows) == 3
    _, rows = explore.q_concept(con, "948")  # numeric ID path
    assert len(rows) == 3
    _, rows = explore.q_concept(con, "WATER", family="Sino")
    assert len(rows) == 1


def test_q_cognate_set_members(con):
    _, rows = explore.q_cognate(con, "cs1")
    assert len(rows) == 2  # Latin + Greek WATER


def test_q_cognate_sets_for_concept(con):
    cols, rows = explore.q_cognate_sets(con, "WATER")
    assert [r[0] for r in rows] == ["cs1", "cs3"]  # cs1 (2 varieties) first
    assert "n_varieties" in cols
    assert rows[0][3] == 2


def test_q_form_search(con):
    _, rows = explore.q_form_search(con, "shui", exact=True)
    assert len(rows) == 1
    _, rows = explore.q_form_search(con, "hu")  # substring → huo
    assert any(r[cols_index(con, "Form")] == "huo" for r in rows)


def cols_index(con, name):  # helper: position of a forms column
    return explore._table_columns(con, "forms").index(name)


def test_q_concepts_coverage(con):
    _, rows = explore.q_concepts(con)
    assert rows[0][1] == "WATER"  # 3 varieties → first
    assert rows[0][3] == 3


def test_q_stats_all(con):
    s = explore.q_stats(con)
    assert s["forms"] == 5
    assert s["varieties"] == 3
    assert s["concepts"] == 2
    assert s["with_segments"] == 4   # Mandarin FIRE has no segments
    assert s["with_cognate"] == 4    # Mandarin FIRE has no cognate
    assert s["cognate_sets"] == 3    # cs1, cs2, cs3
    assert s["loans"] == 1
    assert "by_family" in s


def test_q_stats_family_scope(con):
    s = explore.q_stats(con, family="Indo-European")
    assert s["forms"] == 3
    assert s["varieties"] == 2
    assert "by_family" not in s      # omitted when already scoped


# --- raw SQL guard --------------------------------------------------------

def test_run_sql_select_ok(con):
    cols, rows = explore.run_sql(con, "SELECT av_id FROM forms")
    assert cols == ["av_id"]
    assert len(rows) == 5


def test_run_sql_appends_limit(con):
    _, rows = explore.run_sql(con, "SELECT * FROM forms", limit=2)
    assert len(rows) == 2


@pytest.mark.parametrize("bad", [
    "DROP TABLE forms",
    "DELETE FROM forms",
    "UPDATE forms SET Form='x'",
    "SELECT 1; DROP TABLE forms",
])
def test_run_sql_rejects_writes(con, bad):
    with pytest.raises(ValueError):
        explore.run_sql(con, bad)


def test_query_only_blocks_writes(con):
    # PRAGMA query_only on the connection itself rejects writes.
    with pytest.raises(sqlite3.Error):
        con.execute("DELETE FROM forms")


# --- formatting -----------------------------------------------------------

def test_print_table_truncation_note(capsys):
    cols = ["a", "b"]
    rows = [(1, 2), (3, 4), (5, 6)]  # limit=2 + sentinel row
    explore.print_table(cols, rows, limit=2)
    out = capsys.readouterr().out
    assert "more exist" in out
    assert "2 row(s)" in out


def test_cognate_falls_back_to_cognacy(tmp_path):
    """When canonical_cognate_id is empty (current data), Cognacy is the key."""
    d = tmp_path / "aggregate"
    d.mkdir()
    rows = [
        _form(av_id="ine-latin", Concepticon_ID="948", Concepticon_Gloss="WATER",
              Form="aqua", Segments="a", Cognacy="raw9", canonical_cognate_id=""),
        _form(av_id="ine-greek", Concepticon_ID="948", Concepticon_Gloss="WATER",
              Form="hydor", Segments="h", Cognacy="raw9", canonical_cognate_id=""),
    ]
    _write_csv(d / "forms.csv", FORMS_COLUMNS, rows)
    _write_csv(d / "varieties.csv", VARIETIES_COLUMNS, _VARIETIES[:2])
    _write_csv(d / "parameters.csv", ["Concepticon_ID", "Concepticon_Gloss", "Name"],
               [{"Concepticon_ID": "948", "Concepticon_Gloss": "WATER", "Name": "water"}])
    _write_csv(d / "metadata.csv", ["Dataset", "Title"], [])
    db = tmp_path / "explore.sqlite"
    explore.build_index(d, db, force=True)
    c = explore.connect(db)

    _, members = explore.q_cognate(c, "raw9")
    assert len(members) == 2                       # both matched via Cognacy
    cols, sets = explore.q_cognate_sets(c, "WATER")
    assert sets[0][0] == "raw9" and sets[0][3] == 2  # one set, 2 varieties
    s = explore.q_stats(c)
    assert s["with_cognate"] == 2 and s["cognate_sets"] == 1


def test_main_no_args_prints_help(capsys):
    rc = explore.main([])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Examples" in out                       # the worked-examples epilog
    assert "python explore.py index" in out
    assert "<command>" in out                       # subcommand list


def test_index_info(con, agg_dir):
    info = explore.index_info(con, agg_dir)
    assert info["schema"]["forms"]["rows"] == 5
    assert "av_id" in info["schema"]["forms"]["columns"]
    assert info["stale"] is False
