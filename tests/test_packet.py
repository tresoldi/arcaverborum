import csv

import yaml

from arcaverborum import packet


def _write_forms(path, rows):
    fields = ["av_id", "concept_id", "Segments", "Segments_Source",
              "Cognacy", "Loan", "transcription_source", "cognate_source"]
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def test_yv_quotes_colons_and_empty():
    assert packet._yv("") == '""'
    assert packet._yv("plain text") == "plain text"
    assert packet._yv("a: b").startswith('"') and ":" in packet._yv("a: b")


def test_diagnose_counts(tmp_path):
    forms = tmp_path / "forms.csv"
    _write_forms(forms, [
        {"av_id": "x", "concept_id": "bod-head", "Segments": "k a",
         "Segments_Source": "source", "Cognacy": "1", "transcription_source": "iecor",
         "cognate_source": "iecor"},
        {"av_id": "x", "concept_id": "phy-water", "Segments": "w a",
         "Segments_Source": "profile", "Cognacy": "", "Loan": "true",
         "transcription_source": "iecor", "cognate_source": "iecor"},
        {"av_id": "x", "concept_id": "", "Segments": "b a",
         "Segments_Source": "unclean", "transcription_source": "iecor"},
    ])
    d = packet.diagnose(forms, core_concepts={"bod-head"})
    assert d["n_forms"] == 3
    assert d["with_cid"] == 2
    assert d["core_hit"] == 1
    assert d["with_cognacy"] == 1
    assert d["with_loan"] == 1
    assert d["seg"]["unclean"] == 1


def test_build_recipe_yaml_parses_and_is_descriptive(tmp_path):
    forms = tmp_path / "forms.csv"
    _write_forms(forms, [
        {"av_id": "x", "concept_id": "bod-head", "Segments": "k a",
         "Segments_Source": "source", "Cognacy": "1", "transcription_source": "iecor",
         "cognate_source": "iecor"},
    ])
    diag = packet.diagnose(forms, core_concepts={"bod-head"})
    config = {
        "name": "Test", "family": "Indo-European", "macroarea": "Eurasia",
        "glottocode": "test1234", "pinned": True,
        "sources": {"transcription": "iecor", "cognates": "iecor"},
        "scoring": {"tier": "silver", "forms_score": 0.9, "cognates_score": 0.7},
    }
    text = packet.build_recipe_yaml("x", config, diag, {"iecor"},
                                    "source", "none", "none", concept_map_used=False)
    parsed = yaml.safe_load(text)
    # enforced fields carry the source picks
    assert parsed["construction"]["lexical_base"]["source"] == "iecor"
    assert parsed["construction"]["cognates"]["source"] == "iecor"
    # expert-cognate dataset with cognacy -> method expert
    assert parsed["construction"]["cognates"]["method"] == "expert"
    # requested additions are present
    assert parsed["quality"]["tier"] == "silver"
    assert "notes" in parsed
    assert "annotated" in parsed["construction"]["loans"]


def test_scaffold_packet_roundtrip(tmp_path):
    root = tmp_path / "ine-x"
    (root / "generated").mkdir(parents=True)
    (root / "config.yaml").write_text(
        yaml.safe_dump({
            "av_id": "ine-x", "name": "X", "family": "Indo-European",
            "sources": {"transcription": "iecor", "cognates": "iecor"},
            "scoring": {"tier": "bronze"},
        }),
        encoding="utf-8",
    )
    _write_forms(root / "generated" / "forms.csv", [
        {"av_id": "ine-x", "concept_id": "bod-head", "Segments": "k a",
         "Segments_Source": "source", "Cognacy": "1", "transcription_source": "iecor",
         "cognate_source": "iecor"},
    ])
    res = packet.scaffold_packet("ine-x", root, {"bod-head"}, {"iecor"})
    assert res["status"] == "written"
    assert (root / "recipe.yaml").exists()
    assert (root / "PACKET.md").exists()
    yaml.safe_load((root / "recipe.yaml").read_text(encoding="utf-8"))
    # second call without force does not overwrite
    assert packet.scaffold_packet("ine-x", root, {"bod-head"}, {"iecor"})["status"] == "exists"
