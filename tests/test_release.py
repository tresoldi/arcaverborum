import csv
import json

from arcaverborum import release


def _write(path, fieldnames, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})


def _make_aggregate(tmp_path):
    agg = tmp_path / "aggregate"
    agg.mkdir()
    form_fields = [
        "av_id", "Glottocode", "Variety_Name", "concept_id", "concept_label",
        "Concepticon_ID", "Value", "Form", "Segments", "Segments_Source", "Cognacy",
        "canonical_cognate_id", "Alignment", "Morpheme_Index", "Segment_Slice", "Doubt",
        "Cognate_Detection_Method", "Cognate_Source", "Loan", "Comment",
        "transcription_source", "cognate_source", "source_form_id", "source_language_id",
        "source_parameter_id", "bibtex_key", "quality_score", "tier",
    ]
    _write(agg / "forms.csv", form_fields, [
        # CORE (mycore) form, core concept, with cognacy
        {"av_id": "x-a", "concept_id": "phy-water", "Form": "wai", "Segments": "w a i",
         "Segments_Source": "source", "Cognacy": "1", "Cognate_Detection_Method": "expert",
         "transcription_source": "mycore", "cognate_source": "mycore", "bibtex_key": "k1", "tier": "silver"},
        # CORE form, non-core concept, no cognacy
        {"av_id": "x-a", "concept_id": "zzz-nonce-not-core", "Form": "foo", "Segments": "f o o",
         "Segments_Source": "source", "transcription_source": "mycore", "cognate_source": "mycore",
         "bibtex_key": "k1", "tier": "silver"},
        # NON-CORE dataset — must be excluded
        {"av_id": "y-b", "concept_id": "phy-water", "Form": "aqua", "Segments": "a k w a",
         "Segments_Source": "source", "transcription_source": "notcore", "cognate_source": "notcore"},
    ])
    _write(agg / "varieties.csv",
           ["av_id", "Glottocode", "Name", "Family", "Macroarea", "transcription_source",
            "cognate_source", "pinned", "forms_score", "cognates_score", "tier"],
           [{"av_id": "x-a", "Name": "Alpha", "Family": "Testish", "transcription_source": "mycore",
             "tier": "silver"},
            {"av_id": "y-b", "Name": "Beta", "Family": "Other", "transcription_source": "notcore"}])
    _write(agg / "parameters.csv",
           ["concept_id", "concepticon_id", "label", "pos", "semantic_field", "definition"],
           [{"concept_id": "phy-water", "concepticon_id": "948", "label": "water", "pos": "n",
             "semantic_field": "The physical world"},
            {"concept_id": "zzz-nonce-not-core", "label": "nonce", "pos": "n"}])
    (agg / "sources.bib").write_text("@misc{k1, title={T}}\n", encoding="utf-8")
    return agg


def test_build_release_filters_core_and_flags(tmp_path):
    agg = _make_aggregate(tmp_path)
    datasets = tmp_path / "datasets.csv"
    _write(datasets, ["NAME", "URL", "ExpertCognates", "CORE"],
           [{"NAME": "mycore", "URL": "http://x", "CORE": "TRUE"},
            {"NAME": "notcore", "URL": "http://y", "CORE": ""}])
    metadata = tmp_path / "metadata.csv"
    _write(metadata, ["Dataset", "Title", "Citation", "URL", "License", "Repository_Version"],
           [{"Dataset": "mycore", "License": "https://creativecommons.org/licenses/by/4.0/",
             "Repository_Version": "v1.0"}])

    stats = release.build_release(agg, tmp_path / "release", "9.9.9",
                                  datasets_csv=datasets, metadata_csv=metadata)

    # only the 2 mycore forms survive; notcore excluded
    assert stats["forms"] == 2
    assert stats["languages"] == 1
    assert stats["datasets"] == ["mycore"]

    out = tmp_path / "release" / "arca-verborum-core-9.9.9"
    for name in ("forms.csv", "languages.csv", "parameters.csv", "cognates.csv",
                 "sources.bib", "cldf-metadata.json", "MANIFEST.json", "README.md"):
        assert (out / name).exists(), name

    rows = list(csv.DictReader((out / "forms.csv").open(encoding="utf-8")))
    by_concept = {r["Parameter_ID"]: r for r in rows}
    assert by_concept["phy-water"]["is_core_concept"] == "true"
    assert by_concept["zzz-nonce-not-core"]["is_core_concept"] == "false"
    assert by_concept["phy-water"]["License"] == "https://creativecommons.org/licenses/by/4.0/"
    # unique synthesized IDs
    ids = [r["ID"] for r in rows]
    assert len(ids) == len(set(ids))

    # one cognate row (only the cognacy-bearing form)
    cog = list(csv.DictReader((out / "cognates.csv").open(encoding="utf-8")))
    assert len(cog) == 1 and cog[0]["Form_ID"] == by_concept["phy-water"]["ID"]

    # metadata + manifest valid
    meta = json.loads((out / "cldf-metadata.json").read_text(encoding="utf-8"))
    assert meta["dc:conformsTo"].endswith("Wordlist")
    assert {t["url"] for t in meta["tables"]} == {"forms.csv", "languages.csv",
                                                  "parameters.csv", "cognates.csv"}
    man = json.loads((out / "MANIFEST.json").read_text(encoding="utf-8"))
    assert man["counts"]["forms"] == 2
