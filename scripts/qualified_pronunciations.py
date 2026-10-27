"""Index explicit regional IPA alternatives without choosing a single reading.

The pilot scope is exactly Brazil-tagged Portuguese, not narrower regional or
register labels. Every homograph must supply eligible scope evidence. --index
creates a regenerable evidence table; the default reports lexical candidates.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import sqlite3
from collections import Counter
from pathlib import Path

import pandas as pd

from arcaverborum.concepts import load_concept_maps
from arcaverborum.sources.wiktionary.parameters import parse_parameter_name
from arcaverborum.sources.wiktionary.pronunciations import ipa_segments, key
from arcaverborum.wiktionary_senses import apply_shared

ROOT = Path(__file__).resolve().parents[1]


def scoped_readings(entries, tags):
    variants = {}
    for line, entry in entries:
        readings = [
            s
            for s in entry.get("sounds", [])
            if s.get("ipa") and s.get("tags", []) == tags and not any(s.get(k) for k in ("raw_tags", "note", "form"))
        ]
        if not readings:
            return "incomplete_scope_homograph", {}
        for sound in readings:
            ipa = sound["ipa"].strip()
            segments = ipa_segments(ipa)
            if not segments:
                return "unsupported_ipa", {}
            item = variants.setdefault(ipa, dict(segments=segments, lines=[]))
            item["lines"].append(str(line))
    return ("accept_alternatives" if variants else "unsupported_ipa"), variants


def index(cache, output):
    evidence = sqlite3.connect(cache.resolve().as_uri() + "?mode=ro", uri=True)
    metadata = json.loads(evidence.execute("SELECT payload FROM metadata").fetchone()[0])
    dump = ROOT / "raw/wiktionary/raw.jsonl.gz"
    if (dump.stat().st_size, dump.stat().st_mtime_ns) != (metadata['dump_bytes'], metadata['dump_mtime_ns']):
        raise ValueError('Pronunciation snapshot changed; reindex/review before admission')
    metadata['parent_policy'] = metadata.pop('policy', '')
    metadata['parent_decisions'] = metadata.pop('decisions', {})
    metadata['policy'] = ('Exact language/NFC/POS and registered tags; every homograph supplies valid scope IPA; '
                          'all raw alternatives retained, including phonemic and phonetic representations')
    work = output.with_suffix(".building.sqlite")
    if work.exists():
        work.unlink()
    with sqlite3.connect(work) as db:
        db.execute("CREATE TABLE variants(lang,word,pos,scope,tags,raw_ipa,segments,source_lines,pronunciation_id)")
        counts = Counter()
        groups = itertools.groupby(
            evidence.execute(
                "SELECT lang,word,pos,line,payload FROM entries WHERE lang='pt' ORDER BY lang,word,pos,line"
            ),
            lambda row: row[:3],
        )
        for k, grouped in groups:
            rows = list(grouped)
            status, variants = scoped_readings([(r[3], json.loads(r[4])) for r in rows], ["Brazil"])
            counts[status] += 1
            for ipa, variant in variants.items():
                stable = json.dumps([*k, "pt-Brazil", ipa], ensure_ascii=False)
                pid = "ipa-" + hashlib.sha256(stable.encode()).hexdigest()[:16]
                db.execute(
                    "INSERT INTO variants VALUES(?,?,?,?,?,?,?,?,?)",
                    (
                        *k,
                        "pt-Brazil",
                        '["Brazil"]',
                        ipa,
                        variant["segments"],
                        ";".join(dict.fromkeys(variant["lines"])),
                        pid,
                    ),
                )
        db.execute("CREATE INDEX variant_key ON variants(lang,word,pos)")
        db.execute("CREATE TABLE metadata(payload)")
        metadata.update(scope="pt-Brazil", scope_counts=dict(counts))
        db.execute("INSERT INTO metadata VALUES(?)", (json.dumps(metadata),))
    evidence.close()
    work.replace(output)
    report = ROOT / "docs/qualified_pronunciation_snapshot_2026-10-27.json"
    report.write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps(dict(counts), indent=2))


def candidates(output):
    with sqlite3.connect(output) as db:
        db.row_factory = sqlite3.Row
        alternatives = {}
        for row in db.execute("SELECT * FROM variants ORDER BY rowid"):
            alternatives.setdefault(tuple(row[k] for k in ("lang", "word", "pos")), []).append(dict(row))
    with (ROOT / "intake/wiktionary/parameters_raw.csv").open() as f:
        params = {r["ID"]: r for r in csv.DictReader(f)}
    with (ROOT / "src/arcaverborum/data/concept_core.csv").open() as f:
        core = {r["concept_id"] for r in csv.DictReader(f)}
    with (ROOT / "varieties/ine-brazilian-portuguese/generated/forms.csv").open() as f:
        covered = {
            r["concept_id"]
            for r in csv.DictReader(f)
            if r["Segments_Source"] in ("source", "profile") and r["transcription_source"] == "iecor"
        }
    concepts, _ = load_concept_maps()
    with sqlite3.connect((ROOT / "intake/intake.sqlite").as_uri() + "?mode=ro", uri=True) as db:
        db.row_factory = sqlite3.Row
        rows = [
            dict(r)
            for r in db.execute(
                "SELECT * FROM forms WHERE gc_lc=? AND Dataset=? AND Language_ID=? ORDER BY seq",
                ("port1283", "wiktionary", "wikt_pt"),
            )
        ]
    out = []
    for row in apply_shared(pd.DataFrame(rows), "wiktionary").to_dict("records"):
        parameter = params[row["Parameter_ID"]]
        cid = (
            ""
            if row.get("_concept_mapping_blocked")
            else row.get("_concept_id_override") or concepts.get(parameter["Concepticon_ID"], ("", ""))[0]
        )
        pos = parse_parameter_name(parameter["Name"])[1]
        variants = alternatives.get(key("pt", row["Form"], pos))
        if variants and cid in core - covered:
            out.append(
                dict(
                    source_form_id=row["ID"],
                    Form=row["Form"],
                    Parameter_ID=row["Parameter_ID"],
                    source_sense=parameter["Name"],
                    concept_id=cid,
                    variants=variants,
                )
            )
    path = ROOT / "raw/curation/qualified-ipa-candidates.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(len(out), "candidate translation forms;", len({r["concept_id"] for r in out}), "core gaps")

    return out


def compile_reviewed(candidates, review_path, write):
    from arcaverborum.supplements import evidence_hash

    by_id = {r["source_form_id"]: r for r in candidates}
    with review_path.open() as handle:
        reviews = [r for r in csv.DictReader(handle) if r["decision"] == "admit"]
    with (ROOT / "intake/wiktionary/parameters_raw.csv").open() as handle:
        parameters = {r["ID"]: r for r in csv.DictReader(handle)}
    with (ROOT / "src/arcaverborum/data/concepts.csv").open() as handle:
        cids = {r["concept_id"]: r["concepticon_id"] for r in csv.DictReader(handle)}
    with sqlite3.connect((ROOT / "intake/intake.sqlite").as_uri() + "?mode=ro", uri=True) as db:
        db.row_factory = sqlite3.Row
        source = {
            r["ID"]: dict(r)
            for r in db.execute(
                "SELECT * FROM forms WHERE gc_lc='port1283' AND Dataset='wiktionary' AND Language_ID='wikt_pt'"
            )
        }
    metadata = json.loads((ROOT / "docs/qualified_pronunciation_snapshot_2026-10-27.json").read_text())
    records = []
    for review in reviews:
        candidate = by_id.get(review["source_form_id"])
        if not candidate or (candidate["Form"], candidate["source_sense"], candidate["concept_id"]) != (
            review["Form"],
            review["source_sense"],
            review["concept_id"],
        ):
            raise ValueError("Qualified pronunciation review drift: " + review["source_form_id"])
        row = source[review["source_form_id"]]
        parameter = parameters[row["Parameter_ID"]]
        for variant in candidate["variants"]:
            records.append(
                dict(
                    source="wiktionary",
                    source_form_id=row["ID"],
                    source_language_id=row["Language_ID"],
                    source_glottocode=row["Glottocode"],
                    evidence_sha256=evidence_hash(row),
                    expected_source_concepticon_id=parameter["Concepticon_ID"],
                    concept_id=review["concept_id"],
                    decision="admit",
                    mapping_decision="retain" if cids[review["concept_id"]] == parameter["Concepticon_ID"] else "map",
                    rationale=review["rationale"],
                    raw_ipa=variant["raw_ipa"],
                    pronunciation_tags=variant["tags"],
                    source_pronunciation_id=variant["pronunciation_id"],
                    pronunciation_scope=variant["scope"],
                    pronunciation_lines=variant["source_lines"],
                    dump_sha256=metadata["dump_sha256"],
                )
            )
    path = ROOT / "varieties/ine-brazilian-portuguese/custom/supplements.csv"
    if path.exists():
        with path.open() as handle:
            old = {(r["source_form_id"], r["source_pronunciation_id"]): r for r in csv.DictReader(handle)}
        for row in records:
            prior = old.get((row["source_form_id"], row["source_pronunciation_id"]))
            if prior and prior["evidence_sha256"] != row["evidence_sha256"]:
                raise ValueError("Previously admitted source evidence changed")
    if write:
        with path.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(records[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(records)
    print(len(records), "reviewed qualified pronunciation variants")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", action="store_true")
    parser.add_argument("--compile-reviewed", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    cache = ROOT / "raw/curation/wiktionary-pronunciations.sqlite"
    output = ROOT / "raw/curation/wiktionary-pronunciation-alternatives.sqlite"
    if args.index:
        index(cache, output)
    proposal = candidates(output)
    if args.compile_reviewed:
        compile_reviewed(proposal, ROOT / "docs/qualified_pronunciation_review_2026-10-27.csv", args.write)


if __name__ == "__main__":
    main()
