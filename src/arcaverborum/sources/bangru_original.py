"""Reviewed speaker-A slice of Bodt's licensed original Bangru fieldwork wordlist.

The original supplied IPA is preserved. Comparative languages and tentative root
reconstructions in the same PDF are never treated as Bangru lexical forms.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path

import requests

from arcaverborum.phonology import segments_are_valid
from arcaverborum.sources.wiktionary.pronunciations import ipa_segments

DATA = Path(__file__).resolve().parents[1] / "data"


def read(path):
    with path.open() as handle:
        return list(csv.DictReader(handle))


def reading(raw):
    # The source phonology presentation explicitly lists ʧ and ʤ (slide 9).
    # Tie their unpacked IPA equivalents before tokenization. Other untied
    # affricate-like sequences need their own review, not silent cluster guesses.
    if any(value in raw for value in ("ts", "dz", "tɕ", "dʑ")):
        return ""
    if not raw or any(c in raw for c in "()[]/'\"{}‘’"):
        return ""
    parts = [ipa_segments(w.replace("tʃ", "t͡ʃ").replace("dʒ", "d͡ʒ")) for w in raw.split()]
    return " _ ".join(parts) if parts and all(parts) else ""


def reviewed_rows(rows, concepts):
    """Validate speaker, original source span and every supplied alternative."""
    seen = set()
    forms, parameters = [], []
    for row in rows:
        if row["ID"] in seen:
            raise ValueError("Duplicate Bangru source entry")
        seen.add(row["ID"])
        entry = row["source_entry"]
        if hashlib.sha256(entry.encode()).hexdigest() != row["entry_sha256"]:
            raise ValueError("Bangru reviewed source entry changed")
        if not entry.startswith(row["source_gloss"] + " ") or not 1 <= int(row["source_page"]) <= 24:
            raise ValueError("Bangru original page/gloss mismatch")
        before_root = entry[len(row["source_gloss"]) :].split("Root:", 1)[0]
        first = re.search(r"\[([^]]+)\]", before_root)
        if row["speaker"] != "A" or not first or first[1] != "A":
            raise ValueError("Bangru admission requires speaker A, not a comparative language or reconstruction")
        originals = [part.strip() for part in before_root[: first.start()].strip().rstrip(",").split(",")]
        raw = json.loads(row["raw_transcriptions"])
        if originals != raw:
            raise ValueError("Bangru readings differ from the original speaker span")
        if row["decision"] == "hold":
            continue
        if row["decision"] != "admit" or not row["rationale"].strip():
            raise ValueError("Bangru entry lacks an explicit decision")
        concept = concepts[row["concept_id"]]
        segments = [reading(value) for value in raw]
        if not all(segments) or not all(segments_are_valid(value) for value in segments):
            raise ValueError("Every supplied Bangru alternative must validate")
        parameters.append(
            dict(
                ID=row["ID"],
                Name=row["source_gloss"],
                Concepticon_ID=concept["concepticon_id"],
                Concepticon_Gloss=concept["label"],
            )
        )
        for index, (value, segmented) in enumerate(zip(raw, segments, strict=True), 1):
            evidence = dict(
                source_page=row["source_page"],
                source_entry=entry,
                entry_sha256=row["entry_sha256"],
                raw_ipa=value,
                speaker="A",
                mapping_review=row["rationale"],
                representation=(
                    "Supplied original fieldwork IPA; tʃ/dʒ tied per source inventory. No orthographic inference."
                ),
            )
            forms.append(
                dict(
                    ID=row["ID"] + "-" + str(index),
                    Language_ID="BangruA",
                    Parameter_ID=row["ID"],
                    Value=", ".join(raw),
                    Form=value,
                    Segments=segmented,
                    Comment=json.dumps(evidence, ensure_ascii=False, sort_keys=True),
                    Source="Bodt2017",
                )
            )
    return forms, parameters


def write_csv(path, rows):
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def materialize(raw_root, *, download=False):
    spec = json.loads((DATA / "bangru_original_source.json").read_text())
    root = raw_root / "lexibank" / spec["dataset"]
    root.mkdir(parents=True, exist_ok=True)
    pdf = root / spec["filename"]
    if download:
        response = requests.get("https://zenodo.org/api/records/" + spec["record"], timeout=30)
        response.raise_for_status()
        metadata = response.json()
        if metadata["metadata"].get("license", {}).get("id") != "cc-by-4.0":
            raise ValueError("Reviewed Bangru license changed")
        file = next(f for f in metadata["files"] if f["key"] == spec["filename"])
        response = requests.get(file["links"]["self"], timeout=30)
        response.raise_for_status()
        if hashlib.sha256(response.content).hexdigest() != spec["sha256"]:
            raise ValueError("Reviewed Bangru original PDF changed")
        pdf.write_bytes(response.content)
        (root / "zenodo-record.json").write_text(json.dumps(metadata, indent=2) + "\n")
    if not pdf.exists() or hashlib.sha256(pdf.read_bytes()).hexdigest() != spec["sha256"]:
        raise ValueError("Fetch the exact reviewed Bangru original PDF first")
    concepts = {r["concept_id"]: r for r in read(DATA / "concepts.csv")}
    forms, parameters = reviewed_rows(read(DATA / "bangru_original_forms.csv"), concepts)
    if not forms:
        raise ValueError("No reviewed Bangru forms")
    # Add the immutable document reference to every row, not only dataset metadata.
    for row in forms:
        evidence = json.loads(row["Comment"])
        evidence.update(
            document_doi=spec["doi"],
            pdf_sha256=spec["sha256"],
            source_dialect_glottocode=spec["source_dialect_glottocode"],
            sample=spec["sample"],
        )
        row["Comment"] = "Original Bangru source evidence: " + json.dumps(evidence, ensure_ascii=False, sort_keys=True)
    cldf = root / "cldf"
    cldf.mkdir(exist_ok=True)
    write_csv(cldf / "forms.csv", forms)
    write_csv(cldf / "parameters.csv", parameters)
    write_csv(
        cldf / "languages.csv",
        [
            dict(
                ID="BangruA",
                Name="Bangru (Sarli, speaker A)",
                Glottocode=spec["glottocode"],
                Glottolog_Name="Bangru",
                ISO639P3code="",
                Macroarea="Eurasia",
                Family="Sino-Tibetan",
                Location="Sarli circle, Arunachal Pradesh, India",
                Remark=spec["sample"] + "; " + spec["speaker_name"] + "; no exact speaker coordinates supplied.",
            )
        ],
    )
    citation = (
        "Bodt, Timotheus Adrianus. 2017. Bangru Language Data - various descriptions and analyses. Zenodo. doi:"
        + spec["doi"]
    )
    metadata = {
        "dc:conformsTo": "http://cldf.clld.org/v1.0/terms.rdf#Wordlist",
        "dc:title": "Reviewed speaker-A slice of Bodt's original Bangru fieldwork wordlist",
        "dc:bibliographicCitation": citation,
        "dc:license": spec["license"],
        "dcat:accessURL": spec["url"],
        "prov:wasDerivedFrom": [
            {"dc:title": "Source document", "dc:created": spec["doi"] + ";sha256:" + spec["sha256"]}
        ],
        "tables": [
            {"url": name, "dc:extent": len(rows)}
            for name, rows in [("forms.csv", forms), ("parameters.csv", parameters), ("languages.csv", [1])]
        ],
    }
    # Publish proper CSVW/CLDF column identities, not just matching filenames.
    term = "http://cldf.clld.org/v1.0/terms.rdf#"
    properties = {
        "ID": "id",
        "Name": "name",
        "Language_ID": "languageReference",
        "Parameter_ID": "parameterReference",
        "Value": "value",
        "Form": "form",
        "Segments": "segments",
        "Comment": "comment",
        "Source": "source",
        "Glottocode": "glottocode",
        "Concepticon_ID": "concepticonReference",
    }
    for table, rows in zip(metadata["tables"], [forms, parameters, read(cldf / "languages.csv")], strict=True):
        table["dc:conformsTo"] = term + {
            "forms.csv": "FormTable", "languages.csv": "LanguageTable", "parameters.csv": "ParameterTable"
        }[table["url"]]
        columns = []
        for key in rows[0]:
            column = dict(name=key, datatype="string")
            if key in properties:
                column["propertyUrl"] = term + properties[key]
            if key == "Segments":
                column["separator"] = " "
            if key == "Source":
                column["separator"] = ";"
            columns.append(column)
        table["tableSchema"] = dict(columns=columns, primaryKey="ID")
        if table["url"] == "forms.csv":
            table["tableSchema"]["foreignKeys"] = [
                dict(columnReference=column, reference=dict(resource=resource, columnReference="ID"))
                for column, resource in [("Language_ID", "languages.csv"), ("Parameter_ID", "parameters.csv")]
            ]
    metadata["@context"] = "http://www.w3.org/ns/csvw"
    metadata["dc:source"] = "sources.bib"
    (cldf / "cldf-metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")
    (cldf / "sources.bib").write_text(
        "@misc{Bodt2017,\n  author = {Bodt, Timotheus Adrianus},\n"
        "  title = {Bangru Language Data - various descriptions and analyses},\n"
        "  year = {2017},\n  publisher = {Zenodo},\n  doi = {" + spec["doi"] + "},\n"
        "  url = {" + spec["url"] + "},\n  note = {CC BY 4.0. December 2013 fieldwork; "
        "reviewed speaker A subset. Original PDF SHA256 " + spec["sha256"] + ". "
        "Related analysis: Bodt and Lieberherr 2015, doi:10.1075/ltba.38.1.03bod.}\n}\n"
    )
    return dict(forms=len(forms), concepts=len(parameters), cldf=str(cldf))
