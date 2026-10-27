"""Dictionary CLDF adapter: preserve entry/sense evidence and reviewed mappings.

A field called Pronunciation or Phonetic_Form is not automatically IPA. Only
reviewed source-specific representations can supply certified segment input.
"""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path
from urllib.parse import quote

import pandas as pd

from arcaverborum.sources.wiktionary.pronunciations import ipa_segments

DATA = Path(__file__).resolve().parents[1] / "data"


def read(path):
    if not path.exists():
        return []
    with path.open() as handle:
        return list(csv.DictReader(handle))


def source_segments(value):
    # Media Lengua's supplied representation is IPA with ASCII stress marks.
    # Its documented inventory has no glottal-stop apostrophe. Stress survives
    # in raw evidence; canonical Arca output is segmental. Keep word boundaries.
    parts = value.replace("'", "ˈ").split()
    segmented = [ipa_segments(part) for part in parts]
    return " _ ".join(segmented) if parts and all(segmented) else ""


def process_dictionary(dataset, cldf):
    from arcaverborum.ingest import FORM_COLS, LANG_COLS, PARAM_COLS

    specs = {r["dataset"]: r for r in read(DATA / "dictionary_sources.csv")}
    if dataset not in specs:
        raise ValueError("Dictionary source needs an explicit representation/citation review: " + dataset)
    spec = specs[dataset]
    entries = {r["ID"]: r for r in read(cldf / "entries.csv")}
    senses = read(cldf / "senses.csv")
    languages = read(cldf / "languages.csv")
    lang_by_id = {r["ID"]: r for r in languages}
    concept_rows = read(DATA / "concepts.csv")
    cids = {r["concept_id"]: r["concepticon_id"] for r in concept_rows}
    labels = {r["concept_id"]: r["label"] for r in concept_rows}
    reviews = {r["sense_id"]: r for r in read(DATA / "dictionary_senses.csv") if r["dataset"] == dataset}
    unseen = set(reviews) - {r["ID"] for r in senses}
    if unseen:
        raise ValueError("Reviewed dictionary senses disappeared: " + ", ".join(sorted(unseen)))
    forms, parameters = [], []
    for sense in senses:
        entry = entries[sense["Entry_ID"]]
        language = lang_by_id[entry["Language_ID"]]
        review = reviews.get(sense["ID"])
        cid, gloss = sense.get("Concepticon_ID", ""), ""
        if review:
            if (entry["Headword"], sense["Description"], entry.get("Part_Of_Speech", "")) != (
                review["expected_headword"],
                review["expected_description"],
                review["expected_pos"],
            ):
                raise ValueError("Reviewed dictionary sense changed: " + sense["ID"])
            cid = cids[review["concept_id"]]
            gloss = labels[review["concept_id"]]
        pid = dataset + "_" + sense["ID"]
        parameters.append(
            dict(ID=pid, Dataset=dataset, Name=sense["Description"], Concepticon_ID=cid, Concepticon_Gloss=gloss)
        )
        raw = entry.get(spec["ipa_field"], "") if spec["ipa_field"] else ""
        segments = source_segments(raw) if raw else ""
        evidence = dict(
            entry=entry,
            sense=sense,
            entry_url=spec["url"].replace("/contributions/", "/units/") + "-" + quote(entry["ID"], safe=""),
            representation_field=spec["ipa_field"],
            raw_representation=raw,
            representation_policy=spec["representation_policy"],
        )
        row = dict.fromkeys(FORM_COLS, "")
        row.update(
            ID=dataset + "_" + sense["ID"],
            Dataset=dataset,
            Local_ID=sense["ID"],
            Language_ID=dataset + "_" + entry["Language_ID"],
            Parameter_ID=pid,
            Value=entry["Headword"],
            Form=entry["Headword"],
            Segments=segments,
            Comment="Dictionary source evidence: " + json.dumps(evidence, ensure_ascii=False, sort_keys=True),
            Source=dataset + "_dictionary",
            Glottocode=language["Glottocode"],
            Glottolog_Name=language["Name"],
            Concepticon_Gloss=gloss,
        )
        borrowed = entry.get("Borrowed_Word", "").strip().lower()
        row["Loan"] = {"yes": "true", "no": "false", "true": "true", "false": "false"}.get(borrowed, "")
        forms.append(row)
    langs = []
    for language in languages:
        row = dict.fromkeys(LANG_COLS, "")
        row.update({k: v for k, v in language.items() if k in LANG_COLS})
        row.update(ID=dataset + "_" + language["ID"], Dataset=dataset, Glottolog_Name=language["Name"])
        langs.append(row)
    commit = subprocess.check_output(["git", "-C", str(cldf.parent), "rev-parse", "HEAD"], text=True).strip()
    meta = dict(
        Dataset=dataset,
        Title=spec["title"],
        Citation=spec["citation"],
        URL=spec["url"],
        License="https://creativecommons.org/licenses/by/4.0/",
        CLDF_Module="Dictionary",
        Repository_Version=commit,
        Python_Version="",
        Form_Count=str(len(forms)),
        Language_Count=str(len(langs)),
        Parameter_Count=str(len(parameters)),
        Has_Cognates="False",
    )
    raw_meta = (cldf / "cldf-metadata.json").read_bytes()
    note = (
        "Dataset-level citation; original entries and senses retained. CLDF metadata SHA256 "
        + hashlib.sha256(raw_meta).hexdigest()
        + ". "
        + spec["metadata_note"]
    )
    bib = (
        "@misc{" + dataset + "_dictionary,\n  author = {" + spec["authors"] + "},\n"
        "  title = {" + spec["title"] + "},\n  url = {" + spec["url"] + "},\n"
        "  note = {" + note + "}\n}\n"
    )
    return (
        pd.DataFrame(forms, columns=FORM_COLS),
        pd.DataFrame(langs, columns=LANG_COLS),
        pd.DataFrame(parameters, columns=PARAM_COLS),
        meta,
        bib,
    )
