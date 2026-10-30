"""Evidence-bundle export: lawful D, Door-2 cognacy and sealed gold stay partitioned."""

import copy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from arcaverborum import evidence_bundle as eb

ROOT = Path(__file__).resolve().parents[1]

FIELDS = [
    "ID", "av_id", "Glottocode", "Variety_Name", "concept_id", "concept_label", "Concepticon_ID", "Value",
    "Form", "Segments", "Segments_Source", "raw_ipa", "pronunciation_tags", "source_pronunciation_id",
    "Cognacy", "canonical_cognate_id", "Alignment", "Morpheme_Index", "Segment_Slice", "Doubt",
    "Cognate_Detection_Method", "cognate_evidence_source", "Loan", "Comment", "transcription_source",
    "cognate_source", "source_form_id", "source_language_id", "source_parameter_id", "bibtex_key",
    "quality_score", "tier", "is_core_concept", "License", "source_gloss", "cognate_sets", "mapping_review",
    "mapping_note", "preferred_source", "evidence_role", "gled_dependence", "representation_basis",
    "phonological_marks",
]
CCBY = "https://creativecommons.org/licenses/by/4.0/"
HIST = 'Historical reading evidence: {"authority": "iecor", "language_stage": "Hittite", "notes": "n", ' \
       '"reading_basis": "unspecified_historical_reading"}'
RECON = 'Historical reading evidence: {"authority": "streitberggothic", "language_stage": "Gothic reading", ' \
        '"notes": "n", "reading_basis": "source_reported_reconstruction"}'


def row(n, av_id, source, value, *, segs="", seg_src="", concept="phy-ash", licence=CCBY, comment="",
        cognacy="", method="", gloss="ash", loan=""):
    r = dict.fromkeys(FIELDS, "")
    r.update(ID=f"{av_id}:{source}_{n}:{n}", av_id=av_id, Glottocode="xxxx1234", Variety_Name=av_id,
             concept_id=concept, Concepticon_ID="646", Value=value, Form=value.rstrip("*"), Segments=segs,
             Segments_Source=seg_src, transcription_source=source, cognate_source=source,
             source_form_id=f"{source}_{n}", source_language_id=f"{source}_L", source_parameter_id=f"{source}_P",
             License=licence, Comment=comment, Cognacy=cognacy, Cognate_Detection_Method=method,
             cognate_sets=json.dumps([cognacy] if cognacy else []), source_gloss=gloss, Loan=loan,
             mapping_review="source mapping; no local review recorded", gled_dependence="none")
    return r


def fixture_rows():
    return [
        row(1, "ine-hittite", "iecor", "ḫāš(š)-", segs="x aː s s", seg_src="profile", comment=HIST,
            cognacy="iecor_178", method="expert"),
        row(2, "ine-hittite", "iecor", "*ura/i-", comment=HIST),
        row(3, "ine-hittite", "wiktionary", "pahhur", segs="p a x u r", seg_src="source",
            licence="Not recorded; consult upstream source terms", cognacy="w1", method="wiktionary_etymology",
            comment="Cf. *péh₂wr̥"),
        row(4, "ine-gothic", "streitberggothic", "smairþr*", segs="s m ɛ r θ r̥", seg_src="source", comment=RECON),
        row(5, "ine-gothic", "iecor", "azgo", segs="a z ɡ o", seg_src="source", cognacy="iecor_178",
            method="expert", loan="true"),
        row(6, "mix-sayula-popoluca", "mixezoqueanvoices", "nax", segs="n a x", seg_src="source",
            licence="https://creativecommons.org/licenses/by-nc/4.0/", concept="phy-earth-soil"),
        row(7, "ine-italian-x", "rvidinfinitives", "cantare", segs="k a n t a r e", seg_src="source",
            licence="https://www.gnu.org/licenses/gpl-3.0.html", concept="act-sing"),
        row(8, "ine-proto-indo-european", "pokorny", "*h₂eh₁s-", concept="phy-ash"),
        row(9, "mix-proto-mixe", "mixezoqueanvoices", "*na:x", concept="phy-earth-soil",
            licence="https://creativecommons.org/licenses/by-nc/4.0/"),
        row(10, "ine-hittite", "iecor", "ḫašša-", segs="x a s s a", seg_src="profile", comment=HIST,
            gloss="hearth (< *h₂eh₁s-)", concept="hou-hearth"),
    ]


def lang(av_id, name, family, first="", last=""):
    return dict(av_id=av_id, Name=name, Family=family, Glottocode="xxxx1234", first_documented=first,
                last_documented=last, identity_level="language")


@pytest.fixture
def snapshot(tmp_path):
    web = tmp_path / "web" / "data"
    web.mkdir(parents=True)
    rows = fixture_rows()
    families = {"Indo-European": [], "Mixe-Zoque": []}
    for r in rows:
        families["Mixe-Zoque" if r["av_id"].startswith("mix") else "Indo-European"].append(r)
    shards = {}
    for i, (fam, frows) in enumerate(families.items()):
        data = gzip.compress(json.dumps([[r[f] for f in FIELDS] for r in frows]).encode(), mtime=0)
        (web / f"shard{i}.json.gz").write_bytes(data)
        shards[fam] = dict(url=f"data/shard{i}.json.gz", forms=len(frows), sha256=hashlib.sha256(data).hexdigest())
    catalog = dict(
        languages=[
            lang("ine-hittite", "Hittite", "Indo-European", "-1650", "-1180"),
            lang("ine-gothic", "Gothic", "Indo-European", "350", "380"),
            lang("ine-italian-x", "Italian X", "Indo-European"),
            lang("ine-proto-indo-european", "Proto-Indo-European", "Indo-European"),
            lang("mix-sayula-popoluca", "Sayula Popoluca", "Mixe-Zoque"),
            lang("mix-proto-mixe", "Proto-Mixe", "Mixe-Zoque"),
        ],
        sources=[dict(Dataset="iecor", Citation="Heggarty et al. 2024", Repository_Version="v1.2", URL="u")],
        concepts=[],
    )
    cat = gzip.compress(json.dumps(catalog).encode(), mtime=0)
    (web / "catalog.json.gz").write_bytes(cat)
    manifest = dict(schema=1, build_date="2026-10-30", counts={}, fields=FIELDS, shards=shards,
                    catalog=dict(url="data/catalog.json.gz", sha256=hashlib.sha256(cat).hexdigest()),
                    source_files={})
    (web / "manifest.json").write_text(json.dumps(manifest))
    varieties = tmp_path / "varieties"
    custom = varieties / "ine-hittite" / "custom"
    custom.mkdir(parents=True)
    (varieties / "ine-hittite" / "config.yaml").write_text("sources:\n  transcription: iecor\n")
    (custom / "profile.tsv").write_text("Grapheme\tIPA\tnotes\nḫ\tx\t→x (FLAG)\nā\taː\t\na\ta\t\nš\ts\t\n"
                                        "(\t\t\n)\t\t\n-\t\t\n")
    (custom / "historical_evidence.csv").write_text("source,source_language_id,reading_basis,notes\n"
                                                    "iecor,,unspecified_historical_reading,n\n")
    return web, varieties


def run(snapshot, av_ids=("ine-hittite", "ine-gothic", "ine-italian-x", "mix-sayula-popoluca"), **kw):
    web, varieties = snapshot
    opts = eb.ExportOptions(av_ids=list(av_ids) if av_ids else None, web_data=web, varieties_dir=varieties, **kw)
    return eb.export(opts)


def test_bundle_shape_and_validation(snapshot):
    res = run(snapshot)
    bundle = res["bundle"]
    for key in ("schema_version", "projection_policy", "evidence", "form_obs", "sense_obs",
                "lect_state_candidates", "conflicts"):
        assert key in bundle
    assert bundle["role"] == "D" and bundle["bundle_id"].startswith("evidence_bundle:sha256:")
    ev = bundle["evidence"][0]
    assert set(ev) >= {"evidence_id", "source_id", "source_class", "cite", "raw_string",
                       "script_or_orthography", "collector", "date", "modality", "meta"}
    fo = bundle["form_obs"][0]
    assert set(fo) >= {"form_obs_id", "derived_from", "segment_hypothesis", "sigma", "pipeline_steps", "blank_type"}
    assert fo["lect_state_ref"] or fo["provisional_variety_ref"]
    so = bundle["sense_obs"][0]
    assert set(so) >= {"sense_obs_id", "form_obs_ref", "gloss_raw", "sense_atom_ref", "concepticon_link",
                       "sigma", "derived_from"}
    assert eb.validate_bundle(bundle) == []
    assert eb.validate_door2(res["door2"], bundle) == []
    shard_hashes = json.loads((snapshot[0] / "manifest.json").read_text())["shards"]
    assert bundle["snapshot"]["shards"] == {f: s["sha256"] for f, s in shard_hashes.items()}


def test_hittite_lemma_class_profile_steps_and_sigma(snapshot):
    bundle = run(snapshot)["bundle"]
    hit = [e for e in bundle["evidence"] if e["raw_string"] == "ḫāš(š)-"][0]
    assert hit["source_class"] == "normalized_lemma_db" and hit["modality"] == "written_document"
    assert hit["meta"]["reading_basis"] == "unspecified_historical_reading"
    assert hit["meta"]["language_stage"] == "Hittite" and hit["meta"]["source_note_withheld"] is False
    fo = [f for f in bundle["form_obs"] if f["derived_from"] == [hit["evidence_id"]]][0]
    assert any(s.startswith("profile:varieties/ine-hittite/custom/profile.tsv@sha256:") for s in fo["pipeline_steps"])
    assert "flag:ḫ→x (→x (FLAG))" in fo["pipeline_steps"]
    assert fo["profile_check"]["profile_replay_matches_snapshot"] is True
    assert fo["sigma"]["level"] == 3  # normalized classical lemmata are never low-sigma spoken tips


def test_no_cognacy_or_proto_forms_in_bundle(snapshot):
    res = run(snapshot)
    bundle, gold, door2 = res["bundle"], res["sealed"], res["door2"]
    text = json.dumps(bundle, ensure_ascii=False)
    for forbidden in ("iecor_178", "Cognacy", "cognate_sets", "*ura", "smairþr", "*h₂eh₁s-", "*na:x", "*péh₂wr̥"):
        assert forbidden not in text
    reasons = {(g["av_id"], g["reason"]) for g in gold["entries"]}
    assert ("ine-hittite", "starred_form") in reasons
    assert ("ine-gothic", "reconstruction_reading_basis") in reasons
    assert ("ine-proto-indo-european", "proto_variety") in reasons
    assert ("mix-proto-mixe", "proto_variety") in reasons
    assert gold["sealed"] is True and gold["evidence_bundle_ref"] == bundle["bundle_id"]
    hyp = {h["label"]: h for h in door2["hypotheses"]}
    iecor = hyp["iecor cognacy (expert)"]
    assert iecor["door"] == 2 and iecor["taint_label"] == f"conditional_on:{iecor['hypothesis_id']}"
    assert iecor["prior_mass"] is None and iecor["sets"][0]["set_id"] == "iecor:iecor_178"
    assert len(iecor["sets"][0]["members"]) == 2
    assert "wiktionary cognacy (wiktionary_etymology)" in hyp
    assert len(door2["loan_annotations"]["items"]) == 1
    notes = " ".join(n["note"] for n in door2["source_notes"]["items"])
    assert "*péh₂wr̥" in notes and "hearth (< *h₂eh₁s-)" in notes
    withheld = [s for s in bundle["sense_obs"] if s["gloss_withheld"]]
    assert len(withheld) == 1 and withheld[0]["gloss_raw"] is None


def test_requested_proto_variety_is_excluded_not_exported(snapshot):
    res = run(snapshot, av_ids=("ine-hittite", "mix-proto-mixe"))
    assert "mix-proto-mixe" in res["bundle"]["selection"]["excluded_proto_varieties"]
    assert all(e["meta"]["av_id"] != "mix-proto-mixe" for e in res["bundle"]["evidence"])


@pytest.mark.parametrize("mutate, message", [
    (lambda b: b["evidence"][0].__setitem__("raw_string", "*kʷetwóres"), "starred form"),
    (lambda b: b["evidence"][0]["meta"].__setitem__("Cognacy", "x"), "forbidden key"),
    (lambda b: b["evidence"][0]["meta"].__setitem__("reading_basis", "source_reported_reconstruction"),
     "reconstruction reading basis"),
    (lambda b: b["form_obs"][0].__setitem__("provisional_variety_ref", "mix-proto-mixe"), "proto variety"),
    (lambda b: b["sense_obs"][0].__setitem__("gloss_raw", "from *h₂eh₁s-"), "starred token"),
])
def test_validator_refuses_leaks(snapshot, mutate, message):
    bundle = copy.deepcopy(run(snapshot)["bundle"])
    mutate(bundle)
    errors = eb.validate_bundle(bundle)
    assert any(message in e for e in errors), errors


def test_licence_flags(snapshot):
    bundle = run(snapshot)["bundle"]
    lic = {e["source_id"]: e["meta"]["licence"] for e in bundle["evidence"]}
    assert lic["wiktionary"]["spdx"] == "CC-BY-SA-4.0" and lic["wiktionary"]["flags"]["sa"]
    assert lic["wiktionary"]["flags"]["presumed"] and "share-alike" in lic["wiktionary"]["note"]
    assert lic["mixezoqueanvoices"]["spdx"] == "CC-BY-NC-4.0" and lic["mixezoqueanvoices"]["flags"]["nc"]
    assert lic["rvidinfinitives"]["flags"]["gpl"] and not lic["rvidinfinitives"]["flags"]["nc"]
    assert lic["iecor"]["spdx"] == "CC-BY-4.0" and not any(lic["iecor"]["flags"].values())
    assert eb.classify_licence("", "unknownsource")["flags"]["unrecorded"]


def test_licence_filter(snapshot):
    full = run(snapshot)
    filtered = run(snapshot, exclude_licence={"nc", "gpl"})
    sources = {e["source_id"] for e in filtered["bundle"]["evidence"]}
    assert "mixezoqueanvoices" not in sources and "rvidinfinitives" not in sources
    assert len(filtered["bundle"]["evidence"]) == len(full["bundle"]["evidence"]) - 2
    assert all(not g["licence"]["flags"]["nc"] for g in filtered["sealed"]["entries"])
    assert filtered["bundle"]["filters"]["exclude_licence"] == ["gpl", "nc"]
    by_spdx = run(snapshot, exclude_licence={"CC-BY-SA-4.0"})
    assert "wiktionary" not in {e["source_id"] for e in by_spdx["bundle"]["evidence"]}


def test_deterministic_ids_across_runs(snapshot, tmp_path):
    a, b = run(snapshot), run(snapshot)
    assert a["bundle"]["bundle_id"] == b["bundle"]["bundle_id"]
    assert a["door2"]["package_id"] == b["door2"]["package_id"]
    assert a["sealed"]["gold_id"] == b["sealed"]["gold_id"]
    pa = eb.write_export(a, tmp_path / "a")
    pb = eb.write_export(b, tmp_path / "b")
    for key in pa:
        assert pa[key].read_bytes() == pb[key].read_bytes()
    # Evidence ids depend on (source, source_form_id, pronunciation id, av_id) only.
    r = fixture_rows()[0]
    moved = dict(r, ID="ine-hittite:iecor_1:999999", Comment="")
    assert eb.stable_id("av-ev", *eb.evidence_key(r)) == eb.stable_id("av-ev", *eb.evidence_key(moved))
    hit = [e for e in a["bundle"]["evidence"] if e["raw_string"] == "ḫāš(š)-"][0]
    assert hit["evidence_id"] == eb.stable_id("av-ev", "v1", "iecor", "iecor_1", "", "ine-hittite")


def test_conflicts_retained_and_lect_states(snapshot):
    rows_ok = run(snapshot)["bundle"]
    kinds = {c["kind"] for c in rows_ok["conflicts"]}
    assert kinds == {"cross_source_divergence"}  # Hittite ash: iecor vs wiktionary, both retained
    assert all(c["resolution"] is None for c in rows_ok["conflicts"])
    stages = {c["provisional_variety_ref"]: c for c in rows_ok["lect_state_candidates"]}
    assert stages["ine-hittite"]["status"] == "provisional"


def test_source_class_table_is_unambiguous():
    rules = eb.load_source_class_table()
    for source in ("iecor", "wiktionary", "diacl", "ids", "gled", "lexibankx"):
        for seg in ("source", "profile", "resegmented", "unclean", ""):
            for basis in sorted(eb.BASES) + [""]:
                eb.classify_source(rules, source, seg, basis)
    assert eb.classify_source(rules, "iecor", "profile", "")["source_class"] == "normalized_lemma_db"
    assert eb.classify_source(rules, "wiktionary", "source", eb.RECONSTRUCTION_BASIS)["source_class"] == \
        eb.EXCLUDE_CLASS


def test_comment_parsing_separates_reading_rule_from_source_note():
    reading, note = eb.parse_comment("Cf. HW² Ḫ 388; " + HIST)
    assert reading["reading_basis"] == "unspecified_historical_reading" and note == "Cf. HW² Ḫ 388"


def test_real_snapshot_hittite_and_gothic(tmp_path):
    """Smoke test on the committed web snapshot (tracked in git)."""
    if not (ROOT / "web" / "data" / "manifest.json").exists():
        pytest.skip("web snapshot not present")
    spec = importlib.util.spec_from_file_location("arca_build", ROOT / "build.py")
    build = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build)
    assert build.main(["export-evidence", "ine-hittite", "ine-gothic", "--gold-scope", "selected",
                       "--out", str(tmp_path)]) == 0
    bundle = json.loads((tmp_path / "evidence_bundle.json").read_text())
    gold = json.loads((tmp_path / "sealed" / "sealed_gold_proto.json").read_text())
    assert eb.validate_bundle(bundle) == []
    hit = [f for f in bundle["form_obs"] if f["provisional_variety_ref"] == "ine-hittite"]
    assert hit and any("flag:ḫ→x" in s for f in hit for s in f["pipeline_steps"])
    assert any(g["source_id"] == "streitberggothic" for g in gold["entries"])
    assert not any(e["source_id"] == "streitberggothic" for e in bundle["evidence"])
