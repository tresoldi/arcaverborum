"""Recording metadata survives without being emitted as a lexical word."""
import csv

import pandas as pd

from arcaverborum.catalog import Variety
from arcaverborum.variety import build_one, register


def test_recording_metadata_is_separate_from_transcribed_forms(tmp_path):
    root = tmp_path / "varieties"
    register("test-language", root, "mixezoqueanvoices", glottocode="abcd1234")
    forms = pd.DataFrame([
        dict(ID="audio", Dataset="mixezoqueanvoices", Language_ID="sample", Glottocode="abcd1234",
             Parameter_ID="water", Value="►", Form="►", Segments="", Source="author"),
        dict(ID="word", Dataset="mixezoqueanvoices", Language_ID="sample", Glottocode="abcd1234",
             Parameter_ID="sun", Value="ta", Form="ta", Segments="t a", Source="author"),
    ])
    catalog = {"test-language": Variety("test-language", glottocode="abcd1234")}
    assert build_one("test-language", root, forms, catalog, param_index={},
                     concept_index={}, concept_labels={}) == 1
    gen = root / "test-language/generated"
    with (gen / "forms.csv").open() as f:
        assert [r["source_form_id"] for r in csv.DictReader(f)] == ["word"]
    with (gen / "recordings.csv").open() as f:
        recording = list(csv.DictReader(f))
    assert len(recording) == 1 and recording[0]["source_form_id"] == "audio"
    assert recording[0]["bibtex_key"] == "author" and recording[0]["source_language_id"] == "sample"


def test_primary_review_limits_scope_and_fails_on_evidence_drift(tmp_path):
    import pytest

    from arcaverborum.supplements import evidence_hash

    root = tmp_path / "varieties"
    vd = register("test-language", root, "alpha", glottocode="abcd1234")
    vd.custom_dir.mkdir()
    rows = [dict(ID=key, Dataset="alpha", Language_ID="sample", Glottocode="abcd1234",
                 Parameter_ID="water", Value=form, Form=form, Segments="t a")
            for key, form in [("reviewed", "ta"), ("unreviewed", "tu")]]
    decision = dict(source="alpha", source_form_id="reviewed", source_language_id="sample",
                    source_glottocode="abcd1234", evidence_sha256=evidence_hash(rows[0]),
                    expected_source_concepticon_id="1", concept_id="phy-water", decision="admit",
                    rationale="Reviewed exact source sense and reading.")
    with (vd.custom_dir / "primary.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(decision))
        writer.writeheader()
        writer.writerow(decision)
    kwargs = dict(av_id="test-language", varieties_root=root,
                  catalog={"test-language": Variety("test-language", glottocode="abcd1234")},
                  param_index={"water": ("1", "WATER")},
                  concept_index={"1": ("phy-water", "water")}, concept_labels={"phy-water": "water"})
    assert build_one(intake_forms=pd.DataFrame(rows).fillna(""), **kwargs) == 1
    rows[0]["Value"] = "changed"
    with pytest.raises(ValueError, match="evidence changed"):
        build_one(intake_forms=pd.DataFrame(rows).fillna(""), **kwargs)


def test_unlinked_member_uses_blank_code_with_exact_sample_and_no_fallback(tmp_path):
    import pytest
    import yaml

    root = tmp_path / "varieties"
    vd = register("test-community", root, "alpha")
    config = yaml.safe_load(vd.config_path.read_text())
    config['sources'].update(member_only=True, source_language_id='alpha_community')
    vd.config_path.write_text(yaml.safe_dump(config))
    rows = pd.DataFrame([
        dict(ID='chosen', Dataset='alpha', Language_ID='alpha_community', Glottocode='',
             Parameter_ID='water', Value='ta', Form='ta', Segments='t a'),
        dict(ID='other', Dataset='alpha', Language_ID='alpha_other', Glottocode='',
             Parameter_ID='water', Value='tu', Form='tu', Segments='t u'),
    ])
    kwargs = dict(av_id='test-community', varieties_root=root, catalog={'test-community': Variety('test-community')},
                  param_index={}, concept_index={}, concept_labels={})
    assert build_one(intake_forms=rows, **kwargs) == 1
    with pytest.raises(ValueError, match='no generic fallback'):
        build_one(intake_forms=rows.iloc[1:], **kwargs)
