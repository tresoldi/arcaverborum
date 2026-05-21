import pandas as pd

from arcaverborum.curation import (
    REPORT_FIELDS,
    TONE_RE,
    _source_class,
    build_curation_report,
)


def _forms():
    # Variety aaa: 4 forms — 2 clean, 2 unclean (1 tone-blocked), 3 concepts.
    # Variety bbb: 1 form — resegmented, 1 concept.
    return pd.DataFrame([
        {"av_id": "aaa", "Segments": "k a", "Segments_Source": "source",
         "concept_id": "bod-head", "Cognacy": "1"},
        {"av_id": "aaa", "Segments": "t a", "Segments_Source": "source",
         "concept_id": "bod-hand", "Cognacy": "1"},
        {"av_id": "aaa", "Segments": "k a ⁵", "Segments_Source": "unclean",
         "concept_id": "phy-water", "Cognacy": ""},
        {"av_id": "aaa", "Segments": "x y z", "Segments_Source": "unclean",
         "concept_id": "", "Cognacy": ""},
        {"av_id": "bbb", "Segments": "p a", "Segments_Source": "resegmented",
         "concept_id": "bod-head", "Cognacy": ""},
    ])


def _varieties():
    return pd.DataFrame([
        {"av_id": "aaa", "Glottocode": "aaaa1234", "Name": "Aaa", "Family": "Fam",
         "Macroarea": "Eurasia", "transcription_source": "somelexibank",
         "cognate_source": "somelexibank", "pinned": "false",
         "forms_score": "0.5", "cognates_score": "0.3", "tier": "copper"},
        {"av_id": "bbb", "Glottocode": "bbbb1234", "Name": "Bbb", "Family": "Fam",
         "Macroarea": "Eurasia", "transcription_source": "gled",
         "cognate_source": "gled", "pinned": "false",
         "forms_score": "0.9", "cognates_score": "0.0", "tier": "copper"},
    ])


def test_tone_regex():
    assert TONE_RE.search("ka⁵")
    assert TONE_RE.search("ka5")
    assert TONE_RE.search("a˧")
    assert not TONE_RE.search("kʰa")


def test_source_class():
    assert _source_class("gled") == "GLED"
    assert _source_class("wiktionary") == "Wiktionary"
    assert _source_class("wikt_xyz") == "Wiktionary"
    assert _source_class("northeuralex") == "Lexibank"


def test_per_variety_metrics():
    rows, _ = build_curation_report(_forms(), _varieties())
    by_id = {r["av_id"]: r for r in rows}

    a = by_id["aaa"]
    assert a["n_forms"] == 4
    assert a["n_unclean"] == 2
    assert a["n_tone_blocked"] == 1
    assert a["n_concepts"] == 3
    assert a["pct_unclean"] == 0.5
    assert a["pct_tone_blocked"] == 0.25
    assert a["pct_clean"] == 0.5
    assert a["pct_cognacy"] == 0.5
    assert a["source_class"] == "Lexibank"

    b = by_id["bbb"]
    assert b["n_forms"] == 1
    assert b["pct_resegmented"] == 1.0
    assert b["source_class"] == "GLED"


def test_priority_ordering_and_fields():
    rows, _ = build_curation_report(_forms(), _varieties())
    # aaa (more data, weaker forms_score) outranks bbb.
    assert rows[0]["av_id"] == "aaa"
    assert rows[0]["priority_score"] > rows[1]["priority_score"]
    assert set(rows[0]) == set(REPORT_FIELDS)


def test_summary():
    _, summary = build_curation_report(_forms(), _varieties())
    assert summary["total_forms"] == 5
    assert summary["total_varieties"] == 2
    assert summary["segments_source"]["unclean"]["forms"] == 2
    assert summary["tone_blocked"]["forms"] == 1
    assert summary["tone_blocked"]["pct_of_unclean"] == 0.5
    assert summary["source_class_distribution"]["GLED"] == 1
    assert summary["cross_source_cognate_varieties"] == 0


def test_profile_counts_as_clean_and_zero_priority():
    # A fully orthographic-profiled variety is clean (not unclean) and has
    # no hand-curation priority left.
    forms = pd.DataFrame([
        {"av_id": "ccc", "Segments": "ʃ ə", "Segments_Source": "profile",
         "concept_id": "phy-water", "Cognacy": "1"},
        {"av_id": "ccc", "Segments": "ɟ a k", "Segments_Source": "profile",
         "concept_id": "bod-head", "Cognacy": "1"},
    ])
    varieties = pd.DataFrame([
        {"av_id": "ccc", "Glottocode": "cccc1234", "Name": "Ccc", "Family": "Fam",
         "Macroarea": "Eurasia", "transcription_source": "iecor",
         "cognate_source": "iecor", "pinned": "true",
         "forms_score": "0.2", "cognates_score": "0.7", "tier": "silver"}],
    )
    rows, summary = build_curation_report(forms, varieties)
    c = rows[0]
    assert c["pct_clean"] == 1.0       # profile counts as clean
    assert c["pct_profile"] == 1.0
    assert c["pct_unclean"] == 0.0
    assert c["priority_score"] == 0.0  # done, despite stale forms_score=0.2
    assert summary["segments_source"]["profile"]["forms"] == 2
    assert summary["clean_pct"] == 1.0
