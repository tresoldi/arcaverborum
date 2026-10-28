"""Frozen, reviewed slice of the licensed Jê 2025 study supplement.

Raw source notation is not IPA merely because tokens resemble IPA. A separate
exact-form profile produces conservative broad phonemic readings. Automatic
cognate IDs survive only in provenance, never as expert/accepted judgments.
"""

from __future__ import annotations

import csv
import hashlib
import json
import unicodedata
from pathlib import Path

import requests

from arcaverborum.phonology import segments_are_valid

DATA = Path(__file__).resolve().parents[1] / "data"


def read(path, **kwargs):
    with path.open() as handle:
        return list(csv.DictReader(handle, **kwargs))


def row_hash(row):
    return hashlib.sha256(json.dumps(row, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def conservative_reading(raw, doculect=""):
    """Read unambiguous symbols, with separately documented language scopes.

    Already explicit IPA symbols retain their broad source value; no surface
    allophony or vowel precision beyond that source representation is inferred.
    The default leaves c/j/r/y unresolved; scoped mappings never generalize to
    other doculects or choose between slash alternatives.
    """
    allowed = set("p b t d k g m n ŋ ɲ ɾ h s z ç w ʔ a i u ə ɛ ɔ ɨ ɘ ẽ õ".split())
    allowed |= {unicodedata.normalize("NFC", v + mark) for v in "aiuəɛɔɨɘ" for mark in ("̃", "ː", "̃ː")}
    allowed |= {"ẽː", "õː"}
    allowed.add("+")
    tokens = unicodedata.normalize("NFC", raw).split()
    # These language-specific readings are separately documented. They never
    # generalize to the other Macro-Jê samples or expand slash alternatives.
    scoped = {
        "Panará": {"j": "j", "ĭ": "ĭ"},
        "Apinayé": {"c": "t͡ʃ", "r": "ɾ", "j": "j", "ñ": "ɲ", "ê": "e", "ô": "o", "ə̂": "ɘ", "y": "ɨ", "ỹ": "ɨ̃"},
        "Ingain": {"ɾi": "ɾ i", "kəɾ": "k ə ɾ"},
    }.get(doculect, {})
    if not tokens or any(t not in allowed and t not in scoped for t in tokens):
        return ""
    result = " ".join(scoped.get(t, t) for t in tokens)
    return result if segments_are_valid(result) else ""


def reviewed_rows(originals, reviews, concepts, languages):
    indexed = {r["id"]: r for r in originals}
    if len(indexed) != len(originals):
        raise ValueError("Duplicate original Jê ID")
    originals = indexed
    seen = set()
    forms, parameters = [], {}
    for row in reviews:
        if row["ID"] in seen:
            raise ValueError("Duplicate reviewed Jê ID")
        seen.add(row["ID"])
        original = originals[row["ID"]]
        if row_hash(original) != row["row_sha256"]:
            raise ValueError("Reviewed Jê source row changed")
        if (original["DOCULECT"], original["CONCEPT"], original["VALUE"], original["FORM"]) != (
            row["doculect"],
            row["source_concept"],
            row["raw_value"],
            row["source_form"],
        ) or row["doculect"] not in languages:
            raise ValueError("Jê sample or sense identity changed")
        if row["decision"] == "hold":
            continue
        reading = conservative_reading(row["raw_value"], row["doculect"])
        if row["decision"] != "admit" or not reading or reading != row["ipa_segments"] or not row["rationale"]:
            raise ValueError("Unreviewed Jê reading")
        concept = concepts[row["concept_id"]]
        parameter_id = row["concept_id"]
        parameters[parameter_id] = dict(
            ID=parameter_id,
            Name=row["source_concept"],
            Concepticon_ID=concept["concepticon_id"],
            Concepticon_Gloss=concept["label"],
        )
        evidence = dict(
            original_row=original,
            original_row_sha256=row["row_sha256"],
            review=row["rationale"],
            representation="Source notation; separate exact-form phonemic profile required.",
            cognacy="Original automatic COGID/COGIDS are provenance only; no accepted cognacy inferred.",
        )
        forms.append(
            dict(
                ID=row["ID"],
                Language_ID=languages[row["doculect"]]["ID"],
                Parameter_ID=parameter_id,
                Value=row["raw_value"],
                Form=row["source_form"],
                Segments="",
                Comment="Jê study source evidence: " + json.dumps(evidence, ensure_ascii=False, sort_keys=True),
                Source="FerrazGerardi2025",
            )
        )
    return forms, list(parameters.values())


def write_csv(path, rows):
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def materialize(raw_root, *, download=False):
    spec = json.loads((DATA / "je_original_source.json").read_text())
    directory = raw_root / "lexibank" / spec["dataset"]
    directory.mkdir(parents=True, exist_ok=True)
    for filename, sha in spec["files"].items():
        path = directory / Path(filename).name
        if download:
            response = requests.get(
                f"https://raw.githubusercontent.com/{spec['repository']}/{spec['commit']}/{filename}", timeout=30
            )
            response.raise_for_status()
            if hashlib.sha256(response.content).hexdigest() != sha:
                raise ValueError("Frozen Jê source file changed: " + filename)
            path.write_bytes(response.content)
        if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != sha:
            raise ValueError("Fetch exact reviewed Jê source first: " + filename)
    concepts = {r["concept_id"]: r for r in read(DATA / "concepts.csv")}
    languages = {r["Source_Doculect"]: r for r in spec["languages"]}
    forms, parameters = reviewed_rows(
        read(directory / "auto_cogids.tsv", delimiter="\t"), read(DATA / "je_original_review.csv"), concepts, languages
    )
    for row in forms:
        row["Comment"] += (
            "; repository commit " + spec["commit"] + "; TSV SHA256 " + spec["files"]["data/auto_cogids.tsv"]
        )
    if not forms:
        raise ValueError("Empty Jê reviewed slice")
    cldf = directory / "cldf"
    cldf.mkdir(exist_ok=True)
    tables = [
        ("forms.csv", forms, "FormTable"),
        ("parameters.csv", parameters, "ParameterTable"),
        ("languages.csv", list(languages.values()), "LanguageTable"),
    ]
    metadata = {
        "@context": "http://www.w3.org/ns/csvw",
        "dc:conformsTo": "http://cldf.clld.org/v1.0/terms.rdf#Wordlist",
        "dc:title": "Reviewed source-notation slice of the Jê phylogeny study supplement",
        "dc:bibliographicCitation": spec["citation"],
        "dc:license": spec["license"],
        "dcat:accessURL": spec["url"],
        "dc:source": "sources.bib",
        "prov:wasDerivedFrom": [{"dc:title": "Source document", "dc:created": spec["commit"]}],
        "tables": [],
    }
    properties = {
        "ID": "id",
        "Name": "name",
        "Language_ID": "languageReference",
        "Parameter_ID": "parameterReference",
        "Form": "form",
        "Value": "value",
        "Segments": "segments",
        "Comment": "comment",
        "Source": "source",
        "Glottocode": "glottocode",
        "Concepticon_ID": "concepticonReference",
    }
    term = "http://cldf.clld.org/v1.0/terms.rdf#"
    for filename, rows, component in tables:
        write_csv(cldf / filename, rows)
        columns = []
        for key in rows[0]:
            column = dict(name=key, datatype="string")
            if key in properties:
                column["propertyUrl"] = term + properties[key]
            if key in ("Segments", "Source"):
                column["separator"] = " " if key == "Segments" else ";"
            columns.append(column)
        table = {
            "url": filename,
            "dc:conformsTo": term + component,
            "tableSchema": dict(columns=columns, primaryKey="ID"),
            "dc:extent": len(rows),
        }
        if filename == "forms.csv":
            table["tableSchema"]["foreignKeys"] = [
                dict(columnReference=col, reference=dict(resource=res, columnReference="ID"))
                for col, res in [("Language_ID", "languages.csv"), ("Parameter_ID", "parameters.csv")]
            ]
        metadata["tables"].append(table)
    (cldf / "cldf-metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")
    (cldf / "sources.bib").write_text(
        "@misc{FerrazGerardi2025,\n  author = {Ferraz Gerardi, Fabrício and Wientzek, Tim and "
        "Roksandic, Ivan and Gregorio de Souza, Jonas and Orphão de Carvalho, Fernando},\n"
        "  title = {A phylogenetic classification of the Je language family: Supplementary data},\n"
        "  year = {2025},\n  doi = {10.5281/zenodo.15041553},\n  url = {" + spec["url"] + "},\n"
        "  note = {CC BY 4.0. Dataset-level citation; no individual fieldwork authorship inferred. "
        "Automatic cognacy retained only in raw provenance. Related article doi:10.12688/openreseurope.19346.3.}\n}\n"
    )
    return dict(forms=len(forms), concepts=len(parameters), cldf=str(cldf))
