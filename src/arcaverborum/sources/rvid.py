"""Pinned, reviewed RVID infinitives; no paradigm-cell or closest-code inference."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
from pathlib import Path

import requests

from arcaverborum.sources.wiktionary.pronunciations import ipa_segments

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "src/arcaverborum/data"


def read(path):
    with path.open() as f:
        return list(csv.DictReader(f))


def write_csv(path, rows):
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def reviewed_forms(original, lexemes, reviews, samples, concepts):
    """Reject drift, non-infinitives and etymon-based semantic substitution."""
    original = {r["ID"]: r for r in original}
    lexemes = {r["ID"]: r for r in lexemes}
    forms, parameters, seen = [], {}, set()
    for r in reviews:
        if r["source_form_id"] in seen:
            raise ValueError("Duplicate RVID review")
        seen.add(r["source_form_id"])
        raw, lexeme = original[r["source_form_id"]], lexemes[r["lexeme_id"]]
        if (
            raw["Cell"] != "INF"
            or r["cell"] != "INF"
            or raw["Language_ID"] != r["source_language_id"]
            or raw["Form"] != r["raw_ipa"]
            or raw["Cognateset_ID"] != r["source_cognateset_id"]
            or lexeme["Language_ID"] != raw["Language_ID"]
            or lexeme["Cognateset_ID"] != raw["Cognateset_ID"]
            or lexeme["Meaning"] != r["source_sense"]
            or lexeme["Comment"] != r["lexeme_comment"]
            or samples[raw["Language_ID"]]["av_id"] != r["av_id"]
        ):
            raise ValueError("RVID reviewed lexical/cell evidence changed")
        if r["decision"] == "hold":
            continue
        segments = ipa_segments("/" + raw["Form"] + "/")
        if r["decision"] != "admit" or not r["rationale"] or not segments or segments != r["segments"]:
            raise ValueError("Unreviewed RVID reading")
        c = concepts[r["concept_id"]]
        pid = r["concept_id"]
        parameters[pid] = dict(
            ID=pid, Name=r["source_sense"], Concepticon_ID=c["concepticon_id"], Concepticon_Gloss=c["label"]
        )
        evidence = dict(
            raw_form_id=raw["ID"],
            raw_ipa=raw["Form"],
            morphology_cell="INF",
            lexeme_id=lexeme["ID"],
            modern_meaning=lexeme["Meaning"],
            lexeme_comment=lexeme["Comment"],
            original_etymon=lexeme["Etymon_in_ODRVM"],
            source_cognateset_id=raw["Cognateset_ID"],
            mapping_review=r["rationale"],
            representation=(
                "Supplied broad IPA infinitive; source cognate identifier retained as metadata, "
                "not promoted to expert word cognacy."
            ),
        )
        forms.append(
            dict(
                ID=raw["ID"],
                Language_ID=raw["Language_ID"],
                Parameter_ID=pid,
                Value=raw["Form"],
                Form=raw["Form"],
                Segments=segments,
                Comment=json.dumps(evidence, ensure_ascii=False, sort_keys=True),
                Source="BeniamineMaidenRound2020",
            )
        )
    if not forms:
        raise ValueError("No admitted RVID forms")
    return forms, list(parameters.values())


def materialize(raw_root, *, download=False, source_root=None):
    spec = json.loads((DATA / "rvid_source.json").read_text())
    root = raw_root / "lexibank" / spec["dataset"]
    original = root / "original"
    original.mkdir(parents=True, exist_ok=True)
    for name, digest in spec["sha256"].items():
        path = original / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if source_root is not None:
            shutil.copyfile(source_root / name, path)
        elif download:
            url = spec["repository"] + "/-/raw/" + spec["commit"] + "/" + name
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            path.write_bytes(response.content)
        if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError("RVID pinned source changed: " + name)
    concepts = {r["concept_id"]: r for r in read(DATA / "concepts.csv")}
    reviews = read(ROOT / "docs/romance_r04_review_2026-10-28.csv")
    forms, parameters = reviewed_forms(
        read(original / "cldf/forms.csv"), read(original / "cldf/lexemes.csv"), reviews, spec["samples"], concepts
    )
    originals = {r["ID"]: r for r in read(original / "cldf/languages.csv")}
    languages = []
    for member, sample in spec["samples"].items():
        lang = originals[member]
        evidence = dict(
            source_closest_glottocode=lang["Closest_Glottocode"],
            town=lang["Town"],
            dating=lang["Linguistic_Date"],
            bibliography=lang["Sources"],
            comment=lang["Comment"],
            identity="Closest source code is metadata; only reviewed identity is canonical.",
        )
        for row in forms:
            if row["Language_ID"] == member:
                row["Comment"] += "; sample=" + json.dumps(evidence, ensure_ascii=False, sort_keys=True)
                row["Source"] += ";" + lang["Sources"] if lang["Sources"] else ""
        languages.append(
            dict(
                ID=member,
                Name=lang["Variety"] + (" (" + lang["Town"] + ")" if lang["Town"] else ""),
                Glottocode=sample["glottocode"],
                Glottolog_Name=lang["Variety"],
                Family="Indo-European",
                Macroarea="Eurasia",
                Latitude=lang["Latitude"],
                Longitude=lang["Longitude"],
                Location=lang["Town"],
                Remark=json.dumps(evidence, ensure_ascii=False, sort_keys=True),
            )
        )
    cldf = root / "cldf"
    cldf.mkdir(exist_ok=True)
    tables = [
        ("forms.csv", forms, "FormTable"),
        ("parameters.csv", parameters, "ParameterTable"),
        ("languages.csv", languages, "LanguageTable"),
    ]
    term = "http://cldf.clld.org/v1.0/terms.rdf#"
    properties = dict(
        ID="id",
        Name="name",
        Form="form",
        Value="value",
        Segments="segments",
        Language_ID="languageReference",
        Parameter_ID="parameterReference",
        Source="source",
        Comment="comment",
        Glottocode="glottocode",
        Concepticon_ID="concepticonReference",
    )
    metadata = {
        "@context": "http://www.w3.org/ns/csvw",
        "dc:conformsTo": term + "Wordlist",
        "dc:title": "Reviewed RVID 2.0 infinitives: four Italian-area samples",
        "dc:bibliographicCitation": (
            "Beniamine, Sacha, Martin Maiden and Erich Round. 2020. "
            "Opening the Romance Verbal Inflection Dataset 2.0: A CLDF lexicon. "
            "LREC, 3027–3035. doi:10.5281/zenodo.3611076."
        ),
        "dc:license": "https://www.gnu.org/licenses/gpl-3.0.html",
        "dcat:accessURL": spec["repository"],
        "prov:wasDerivedFrom": [{"dc:title": "Repository", "dc:created": spec["commit"]}],
        "dc:source": "sources.bib",
        "tables": [],
    }
    for filename, rows, kind in tables:
        write_csv(cldf / filename, rows)
        columns = []
        for key in rows[0]:
            col = dict(name=key, datatype="string")
            if key in properties:
                col["propertyUrl"] = term + properties[key]
            if key in {"Segments", "Source"}:
                col["separator"] = " " if key == "Segments" else ";"
            columns.append(col)
        metadata["tables"].append(
            {
                "url": filename,
                "dc:conformsTo": term + kind,
                "dc:extent": len(rows),
                "tableSchema": {"columns": columns, "primaryKey": "ID"},
            }
        )
    (cldf / "cldf-metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n")
    (cldf / "sources.bib").write_text(
        (original / "cldf/sources.bib").read_text()
        + "\n@misc{BeniamineMaidenRound2020,\n author = {Beniamine, Sacha and Maiden, Martin and Round, Erich},\n"
        + " title = {Opening the Romance Verbal Inflection Dataset 2.0: A CLDF lexicon},\n year = {2020},\n"
        + " doi = {10.5281/zenodo.3611076},\n url = {"
        + spec["repository"]
        + "},\n note = {GPLv3; reviewed infinitive derivative; commit "
        + spec["commit"]
        + "}\n}\n"
    )
    shutil.copyfile(original / "LICENSE", root / "LICENSE")
    (root / "NOTICE").write_text(
        "Reviewed infinitive derivative of RVID2.0; modifications: bounded sample/cell/meaning selection, "
        "segmentation, frozen concept mapping, metadata preservation. GPLv3. "
        "Original source and license retained in original/. "
        "Reproduce with scripts/stage_rvid.py and tracked review.\n"
    )
    return dict(forms=len(forms), parameters=len(parameters), languages=len(languages))
