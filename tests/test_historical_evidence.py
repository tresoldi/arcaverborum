"""Historical origin and lexical spelling must not masquerade as phonetic evidence."""

import csv
import importlib.util
from pathlib import Path

import pandas as pd
import pytest

from arcaverborum.catalog import Variety
from arcaverborum.historical_evidence import annotate
from arcaverborum.sources.ancient_lexica import extract
from arcaverborum.supplements import evidence_hash, reviewed_frames, scope_rule
from arcaverborum.tracking import custom_component
from arcaverborum.variety import emit_forms


def save(path, rows):
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def test_historical_rules_scope_precedence_and_freshness(tmp_path):
    before = custom_component(tmp_path)
    rules = [
        dict(source="ids", source_language_id="", reading_basis="automatic_transcription_conversion", notes="default"),
        dict(source="ids", source_language_id="exact", reading_basis="orthographic_transcription_only", notes="exact"),
    ]
    p = tmp_path / "historical_evidence.csv"
    save(p, rules)
    assert custom_component(tmp_path) != before
    rows = [dict(transcription_source="ids", source_language_id=x, Comment="original") for x in ("exact", "other")]
    annotate(rows, tmp_path)
    assert "orthographic_transcription_only" in rows[0]["Comment"] and "original" in rows[0]["Comment"]
    assert "automatic_transcription_conversion" in rows[1]["Comment"]
    save(p, rules + rules[:1])
    with pytest.raises(ValueError, match="duplicate"):
        annotate(rows, tmp_path)


def test_latin_looking_spelling_stays_unpronounced_and_cannot_replace_supplied_reading(tmp_path):
    row = dict(
        ID="s_one",
        Dataset="s",
        Language_ID="s_x",
        Glottocode="xxxx1234",
        Parameter_ID="p",
        Value="hul",
        Form="hul",
        Segments="",
        Comment="",
        Cognacy="",
        Source="reference",
        Loan="",
    )
    decision = dict(
        source="s",
        source_form_id="s_one",
        source_language_id="s_x",
        source_glottocode="xxxx1234",
        evidence_sha256=evidence_hash(row),
        expected_source_concepticon_id="948",
        concept_id="phy-water",
        decision="admit",
        rationale="Synthetic gate test",
        transcription_policy="orthographic_only",
    )
    save(tmp_path / "supplements.csv", [decision])
    source, frame, profile = next(
        reviewed_frames(tmp_path, pd.DataFrame([row]), "xxxx1234", {"p": ("948", "WATER")}, {"phy-water": "948"})
    )
    emitted = emit_forms(
        frame,
        av_id="und-test",
        variety=Variety(av_id="und-test"),
        transcription_source=source,
        cognate_source=source,
        forms_score=0.5,
        tier="bronze",
        param_index={},
        concept_index={},
        concept_labels={"phy-water": "water"},
        profile=profile,
    )[0]
    assert emitted["Form"] == "hul" and emitted["Segments"] == ""
    assert emitted["Segments_Source"] == "unclean"
    row["Segments"] = "h u l"
    decision["evidence_sha256"] = evidence_hash(row)
    save(tmp_path / "supplements.csv", [decision])
    with pytest.raises(ValueError, match="reinterpret"):
        list(reviewed_frames(tmp_path, pd.DataFrame([row]), "xxxx1234", {"p": ("948", "WATER")}, {"phy-water": "948"}))


def test_attic_scope_requires_exact_period_note():
    d = dict(
        pronunciation_scope="grc-Attic5BCE",
        source_glottocode="anci1242",
        source_language_id="wikt_grc",
        pronunciation_tags="[]",
        pronunciation_note="5ᵗʰ BCE Attic",
    )
    scope_rule(d, "anci1242")
    with pytest.raises(ValueError, match="scope"):
        scope_rule({**d, "pronunciation_note": "Koine"}, "anci1242")


def test_all_homographs_and_all_readings_are_required():
    spec = importlib.util.spec_from_file_location("ancient_pronunciations", Path("scripts/ancient_pronunciations.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    entry = dict(sounds=[dict(ipa="/a/", tags=["Classical-Latin"]), dict(ipa="[aː]", tags=["Classical-Latin"])])
    assert set(m.scoped([(1, entry)], ["Classical-Latin"], "")) == {"/a/", "[aː]"}
    with pytest.raises(ValueError, match="homograph"):
        m.scoped([(1, entry), (2, dict(sounds=[]))], ["Classical-Latin"], "")


def test_coptic_requires_form_specific_sahidic_and_exact_gloss():
    payload = b"""<TEI
 xmlns="http://www.tei-c.org/ns/1.0">
<entry xml:id="C1">
<form xml:id="CF1"><orth>a</orth><usg type="geo">B</usg></form>
<cit xml:lang="en"><quote>water</quote></cit></entry></TEI>"""
    review = dict(source_entry_id="C1", source_form_id="CF1", Form="a", source_sense="water")
    with pytest.raises(ValueError, match="Sahidic"):
        extract({"kind": "coptic"}, payload, review)
    assert extract({"kind": "coptic"}, payload.replace(b">B<", b">S<"), review)[:2] == ("a", "water")
    with pytest.raises(ValueError, match="drift"):
        extract({"kind": "coptic"}, payload.replace(b">B<", b">S<"), {**review, "Form": "b"})


def test_frozen_etruscan_slice_is_reproducible_without_rolling_upstream(tmp_path):
    from arcaverborum.sources.ancient_lexica import materialize

    result = materialize(tmp_path, dataset="kaikkietruscan", download=False)
    assert result["forms"] == 24
    with (tmp_path / "lexibank/kaikkietruscan/cldf/forms.csv").open() as f:
        rows = list(csv.DictReader(f))
    assert all(not r["Segments"] and "entry_url" in r["Comment"] for r in rows)
    assert not any("𐌑𐌀" == r["Form"] or "𐌇𐌖𐌈" == r["Form"] for r in rows)
