"""Frozen, individually reviewed African lexical sources; never infer IPA on ingest."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import unicodedata
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "src/arcaverborum/data"


def digest(record):
    return hashlib.sha256(json.dumps(record, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def clean_tex(text):
    return unicodedata.normalize("NFC", text.replace("\\-", "").replace("~", " ").strip())


def records(kind, payload, wanted=None):
    """Return source records, retaining their complete native evidence."""
    text = payload.decode("utf-8-sig")
    if kind == "ruruuli":
        out = {}
        blocks = re.split(r"(?=\\fmtLemma\{)", text)[1:]
        for i, block in enumerate(blocks, 1):
            word = re.match(r"\\fmtLemma\{([^}]+)\}", block)[1]
            senses = re.findall(r"\\fmtSense\{([^}]+)\}", block)
            out[str(i)] = dict(Form=clean_tex(word), source_sense="; ".join(clean_tex(s) for s in senses), native=block)
        return out
    if kind == "fwe":
        out = {}
        for line in text.splitlines():
            if not line.startswith("{{\\bfseries\\itshape "):
                continue
            parts = line.split("\\relax")
            if len(parts) < 3:
                continue
            word = parts[0].removeprefix("{{\\bfseries\\itshape ").removesuffix("}} ").strip()
            sense = parts[2].strip().removeprefix("{").removesuffix("}")
            out[str(len(out) + 1)] = dict(Form=clean_tex(word), source_sense=clean_tex(sense), native=line)
        return out
    if kind == "gyeli":
        out = {}
        for line in text.splitlines():
            match = re.search(r"\{\\bfseries\s+([^}]+)\}\s*(.*?)\{\\itshape ([^}]+)\}\s*(.*)", line)
            if not match:
                continue
            word, prefix, pos, tail = match.groups()
            if len(word.strip()) == 1 and not tail:
                continue
            sense = re.split(r"\{\\itshape", tail)[0]
            sense = re.sub(r"^\s*[0-9]+(?:/[0-9]+)?\s+", "", sense).strip().removesuffix("\\\\").strip()
            # Keep a bound stem and its prefix distinct; no automatic concatenation.
            out[str(len(out) + 1)] = dict(
                Form=clean_tex(word), source_sense=clean_tex(sense), prefix=prefix.strip(), pos=pos, native=line
            )
        return out
    if kind in {"reflex", "tsv_metadata", "hdi_senses", "entries", "intake"}:
        delimiter = "\t" if kind in {"reflex", "tsv_metadata"} else ","
        rows = csv.DictReader(io.StringIO(text), delimiter=delimiter)
        key = "id" if "id" in rows.fieldnames else "ID"
        return {r[key]: r for r in rows if wanted is None or r[key] in wanted}
    raise ValueError("Unknown African source record format")


def extract(spec, payloads, review, index=None):
    resource = next(r for r in spec["resources"] if r["key"] == review["resource_key"])
    record = (index[resource["key"]] if index is not None else records(resource["kind"], payloads[resource["key"]]))[
        review["record_key"]
    ]
    if digest(record) != review["native_sha256"]:
        raise ValueError("Reviewed African native record changed")
    kind = resource["kind"]
    if kind in {"ruruuli", "fwe", "gyeli"}:
        form, sense = record["Form"], record["source_sense"]
    elif kind == "reflex":
        if record["SOU"] != review["member"]:
            raise ValueError("RefLex source member changed")
        form, sense = record["FRM"], record["TRA"]
        source = records("tsv_metadata", payloads["sources"])[record["SOU"]]
        language = records("tsv_metadata", payloads["languages"])[source["LANGUE"]]
        reference = records("tsv_metadata", payloads["references"])[source["BIB"]]
        attribution = dict(source=source, language=language, reference=reference)
        if digest(attribution) != review["entry_sha256"] or language["glottocode"] != review["glottocode"]:
            raise ValueError("RefLex lexical attribution or language identity changed")
        record = dict(record=record, attribution=attribution)
    elif kind == "hdi_senses":
        entry = records("entries", payloads["entries"])[record["Entry_ID"]]
        if digest(entry) != review["entry_sha256"]:
            raise ValueError("African dictionary headword record changed")
        form, sense = entry["Headword"], record["Description"]
        record = dict(sense=record, entry=entry)
    elif kind == "entries":
        senses = [r for r in records("hdi_senses", payloads["senses"]).values() if r["Entry_ID"] == record["ID"]]
        form, sense = record["Headword"], "; ".join(r["Description"] for r in senses)
        if digest(senses) != review["entry_sha256"]:
            raise ValueError("African dictionary sense records changed")
        record = dict(entry=record, senses=senses)
    else:
        parameter = records("entries", payloads[resource["key"] + "-parameters"])[record["Parameter_ID"]]
        if digest(parameter) != review["entry_sha256"] or record["Language_ID"] != review["member"]:
            raise ValueError("Original African wordlist member or sense changed")
        form, sense = record["Value"], parameter["Name"]
        record = dict(form=record, parameter=parameter)
    reviewed_form = (
        clean_tex(form) if kind in {"ruruuli", "fwe", "gyeli"} else unicodedata.normalize("NFC", form).strip()
    )
    if reviewed_form != review["Form"] or sense != review["source_sense"]:
        raise ValueError("African spelling or source-sense review drift")
    return dict(
        original=record,
        original_form=form,
        source_gloss=sense,
        source_record=review["record_key"],
        source_member=review["member"],
        source_version=spec["version"],
        native_sha256=review["native_sha256"],
        reading_basis="orthographic_transcription_only",
        mapping_review=review["rationale"],
    )


def write_csv(path, rows):
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def materialize(raw_root, *, dataset, download=False):
    spec = next(s for s in json.loads((DATA / "african_lexical_sources.json").read_text()) if s["dataset"] == dataset)
    root = raw_root / "lexibank" / dataset
    root.mkdir(parents=True, exist_ok=True)
    payloads = {}
    for r in spec["resources"]:
        p = root / r["filename"]
        if download:
            response = requests.get(r["url"], timeout=60)
            response.raise_for_status()
            if hashlib.sha256(response.content).hexdigest() != r["sha256"]:
                raise ValueError("Pinned African source resource changed")
            p.write_bytes(response.content)
        payloads[r["key"]] = p.read_bytes()
        if hashlib.sha256(payloads[r["key"]]).hexdigest() != r["sha256"]:
            raise ValueError("African original resource hash mismatch")
    with (ROOT / spec["review"]).open() as f:
        review = list(csv.DictReader(f))
    index = {
        r["key"]: records(
            r["kind"], payloads[r["key"]], {x["record_key"] for x in review if x["resource_key"] == r["key"]}
        )
        for r in spec["resources"]
        if any(x["resource_key"] == r["key"] for x in review)
    }
    concepts = {r["concept_id"]: r for r in csv.DictReader((DATA / "concepts.csv").open())}
    forms = []
    params = []
    members = {}
    seen = set()
    for r in review:
        if r["decision"] != "admit":
            continue
        if r["dataset"] != dataset or r["source_form_id"] in seen or not r["rationale"]:
            raise ValueError("Invalid African admission")
        seen.add(r["source_form_id"])
        evidence = extract(spec, payloads, r, index)
        evidence.update(license=spec["license"], source_citation=spec["citation"], source_genealogy=spec["genealogy"])
        c = concepts[r["concept_id"]]
        pid = r["source_form_id"]
        params.append(
            dict(ID=pid, Name=r["source_sense"], Concepticon_ID=c["concepticon_id"], Concepticon_Gloss=c["label"])
        )
        forms.append(
            dict(
                ID=r["source_form_id"],
                Language_ID=r["member"],
                Parameter_ID=pid,
                Value=r["Form"],
                Form=r["Form"],
                Segments="",
                Source="original",
                Comment=json.dumps(evidence, ensure_ascii=False, sort_keys=True),
            )
        )
        members[r["member"]] = dict(
            ID=r["member"],
            Name=r["member_name"],
            Glottocode=r["glottocode"],
            Glottolog_Name=r["member_name"],
            Family=r["family"],
            Macroarea="Africa",
        )
    if not forms:
        raise ValueError("Empty African reviewed slice")
    cldf = root / "cldf"
    cldf.mkdir(exist_ok=True)
    term = "http://cldf.clld.org/v1.0/terms.rdf#"
    props = dict(
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
    meta = {
        "@context": "http://www.w3.org/ns/csvw",
        "dc:conformsTo": term + "Wordlist",
        "dc:title": spec["name"],
        "dc:bibliographicCitation": spec["citation"],
        "dc:license": spec["license"],
        "dcat:accessURL": spec["url"],
        "prov:wasDerivedFrom": [{"dc:title": "Repository", "dc:created": spec["version"]}],
        "dc:source": "sources.bib",
        "tables": [],
    }
    for name, rows, kind in [
        ("forms.csv", forms, "FormTable"),
        ("parameters.csv", params, "ParameterTable"),
        ("languages.csv", list(members.values()), "LanguageTable"),
    ]:
        write_csv(cldf / name, rows)
        cols = []
        for k in rows[0]:
            col = dict(name=k, datatype="string")
            if k in props:
                col["propertyUrl"] = term + props[k]
            if k in {"Source", "Segments"}:
                col["separator"] = ";" if k == "Source" else " "
            cols.append(col)
        meta["tables"].append(
            {
                "url": name,
                "dc:conformsTo": term + kind,
                "dc:extent": len(rows),
                "tableSchema": {"columns": cols, "primaryKey": "ID"},
            }
        )
    (cldf / "cldf-metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n")
    (cldf / "sources.bib").write_text(
        "@misc{original,\n title = {"
        + spec["citation"]
        + "},\n url = {"
        + spec["url"]
        + "},\n note = {Data licence "
        + spec["license"]
        + "}\n}\n"
    )
    return dict(dataset=dataset, forms=len(forms), members=len(members))
