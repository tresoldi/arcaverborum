"""Frozen source-linked historical lexical slices; pronunciation is never invented."""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "src/arcaverborum/data"


def read(path):
    with path.open() as f:
        return list(csv.DictReader(f))


def extract(spec, payload, review):
    if spec["kind"] == "coptic":
        root = ET.fromstring(payload)
        ns = {"t": "http://www.tei-c.org/ns/1.0", "xml": "http://www.w3.org/XML/1998/namespace"}
        entries = {e.get("{" + ns["xml"] + "}id"): e for e in root.findall(".//t:entry", ns)}
        entry = entries[review["source_entry_id"]]
        forms = [f for f in entry.findall("t:form", ns) if f.get("{" + ns["xml"] + "}id") == review["source_form_id"]]
        if len(forms) != 1 or not any(u.text == "S" for u in forms[0].findall("t:usg[@type='geo']", ns)):
            raise ValueError("Coptic form lacks exact Sahidic evidence")
        form = "".join(forms[0].find("t:orth", ns).itertext())
        sense = "; ".join(" ".join(q.itertext()).strip() for q in entry.findall('.//t:cit[@xml:lang="en"]/t:quote', ns))
        evidence = dict(
            entry_id=review["source_entry_id"],
            form_id=review["source_form_id"],
            dialect="S",
            lexical_xml=ET.tostring(entry, encoding="unicode"),
        )
    elif spec["kind"] == "egyptian":
        rows = payload.decode().splitlines()
        row = json.loads(rows[int(review["source_entry_id"])])
        if len(row["lemmatization"].split()) != 1 or len(row["transliteration"].split()) != 1:
            raise ValueError("Egyptian pilot requires one lexical unit")
        form, sense, evidence = row["transliteration"], row["translation"], row
    elif spec["kind"] == "reviewed_pdf":
        # Manually reviewed scholarly text, not OCR, an inferred phonetic form,
        # or a claim that an entire inscription was word-aligned automatically.
        if not payload.startswith(b"%PDF") or not all(
            review.get(k) for k in ("source_page", "source_signs", "attestation", "audit_quote")
        ):
            raise ValueError("Historical PDF admission lacks an explicit text audit")
        form, sense = review["Form"], review["source_sense"]
        evidence = {k: review[k] for k in ("source_page", "source_signs", "attestation", "audit_quote")}
        evidence["extraction"] = "Manually reviewed lexical transcription from pinned scholarly PDF; images excluded"
    elif spec["kind"] == "wiktextract":
        row = json.loads(payload.decode().splitlines()[int(review["source_entry_id"])])
        if row["lang_code"] != "ett" or row["pos"] in {"name", "romanization"}:
            raise ValueError("Etruscan pilot requires a lexical Etruscan headword")
        form = row["word"]
        sense = "; ".join(" / ".join(s.get("glosses", [])) for s in row["senses"])
        evidence = dict(
            entry=row,
            entry_url="https://en.wiktionary.org/wiki/" + form + "#Etruscan",
            independence="Same underlying Wiktionary tradition, not an independent attestation",
        )
    else:
        raise ValueError("Unknown historical source extractor")
    if form != review["Form"] or sense != review["source_sense"]:
        raise ValueError("Historical source spelling/sense drift")
    return form, sense, evidence


def write_csv(path, rows):
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def materialize(raw_root, *, dataset, download=False):
    specs = json.loads((DATA / "ancient_lexical_sources.json").read_text())
    spec = next(s for s in specs if s["dataset"] == dataset)
    root = raw_root / "lexibank" / dataset
    root.mkdir(parents=True, exist_ok=True)
    path = root / spec["filename"]
    if spec.get("snapshot"):
        path.write_bytes(gzip.decompress((DATA / spec["snapshot"]).read_bytes()))
    elif download:
        r = requests.get(spec["url"], timeout=30)
        r.raise_for_status()
        if hashlib.sha256(r.content).hexdigest() != spec["sha256"]:
            raise ValueError("Pinned historical source changed")
        path.write_bytes(r.content)
    payload = path.read_bytes()
    if hashlib.sha256(payload).hexdigest() != spec["sha256"]:
        raise ValueError("Historical source hash mismatch")
    concepts = {r["concept_id"]: r for r in read(DATA / "concepts.csv")}
    forms, params, seen = [], {}, set()
    for review in read(ROOT / spec["review"]):
        if review["decision"] != "admit":
            continue
        if review["dataset"] != dataset or review["source_form_id"] in seen or not review["rationale"]:
            raise ValueError("Invalid historical admission")
        seen.add(review["source_form_id"])
        form, sense, evidence = extract(spec, payload, review)
        c = concepts[review["concept_id"]]
        pid = review["concept_id"]
        params[pid] = dict(ID=pid, Name=sense, Concepticon_ID=c["concepticon_id"], Concepticon_Gloss=c["label"])
        # Distinct senses sharing a frozen concept retain their own source gloss in each form.
        evidence.update(
            source_gloss=sense,
            reading_basis="orthographic_transcription_only",
            source_version=spec["version"],
            source_sha256=spec["sha256"],
            mapping_review=review["rationale"],
        )
        forms.append(
            dict(
                ID=review["source_form_id"],
                Language_ID=spec["member"],
                Parameter_ID=pid,
                Value=form,
                Form=form,
                Segments="",
                Source="source",
                Comment=json.dumps(evidence, ensure_ascii=False, sort_keys=True),
            )
        )
    if not forms:
        raise ValueError("No reviewed historical lexical forms")
    languages = [
        dict(
            ID=spec["member"],
            Name=spec["name"],
            Glottocode=spec["glottocode"],
            Glottolog_Name=spec["name"],
            Family=spec.get("family", "Afro-Asiatic"),
            Macroarea=spec.get("macroarea", "Africa"),
        )
    ]
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
    tables = [
        ("forms.csv", forms, "FormTable"),
        ("parameters.csv", list(params.values()), "ParameterTable"),
        ("languages.csv", languages, "LanguageTable"),
    ]
    metadata = {
        "@context": "http://www.w3.org/ns/csvw",
        "dc:conformsTo": term + "Wordlist",
        "dc:title": spec["name"] + " — reviewed orthographic slice",
        "dc:bibliographicCitation": spec["citation"],
        "dc:license": spec["license"],
        "dcat:accessURL": spec["url"],
        "prov:wasDerivedFrom": [{"dc:title": "Repository", "dc:created": spec["version"]}],
        "dc:source": "sources.bib",
        "tables": [],
    }
    for filename, rows, kind in tables:
        write_csv(cldf / filename, rows)
        columns = []
        for k in rows[0]:
            col = dict(name=k, datatype="string")
            if k in props:
                col["propertyUrl"] = term + props[k]
            if k in {"Segments", "Source"}:
                col["separator"] = " " if k == "Segments" else ";"
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
        "@misc{source,\n title = {"
        + spec["citation"]
        + "},\n url = {"
        + spec["url"]
        + "},\n note = {Data licence "
        + spec["license"]
        + "; source SHA256 "
        + spec["sha256"]
        + "}\n}\n"
    )
    return dict(dataset=dataset, forms=len(forms), members=1)
