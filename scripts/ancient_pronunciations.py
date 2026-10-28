"""Compile reviewed exact historical Wiktionary scopes; retain supplied alternatives."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
from pathlib import Path

from arcaverborum.sources.wiktionary.parameters import parse_parameter_name
from arcaverborum.sources.wiktionary.pronunciations import ipa_segments
from arcaverborum.supplements import evidence_hash

ROOT = Path(__file__).resolve().parents[1]


def scoped(entries, tags, note):
    variants = {}
    for line, entry in entries:
        sounds = [
            s
            for s in entry.get("sounds", [])
            if s.get("ipa")
            and s.get("tags", []) == tags
            and s.get("note", "") == note
            and not any(s.get(k) for k in ("raw_tags", "form"))
        ]
        if not sounds:
            raise ValueError("Historical scope missing in a matching homograph")
        for sound in sounds:
            if not ipa_segments(sound["ipa"]):
                raise ValueError("Unsupported historical IPA alternative")
            variants.setdefault(sound["ipa"], []).append(str(line))
    if not variants:
        raise ValueError("Historical pronunciation entry missing")
    return variants


def read(path):
    with path.open() as f:
        return list(csv.DictReader(f))


def compile_reviewed(root=ROOT, *, write=False):
    reviews = read(root / "docs/ancient_an02_review_2026-10-28.csv")
    params = {r["ID"]: r for r in read(root / "intake/wiktionary/parameters_raw.csv")}
    concepts = {r["concept_id"]: r["concepticon_id"] for r in read(root / "src/arcaverborum/data/concepts.csv")}
    groups = {}
    with (
        sqlite3.connect(
            (root / "raw/curation/wiktionary-pronunciations.sqlite").as_uri() + "?mode=ro", uri=True
        ) as cache,
        sqlite3.connect((root / "intake/intake.sqlite").as_uri() + "?mode=ro", uri=True) as db,
    ):
        db.row_factory = sqlite3.Row
        metadata = json.loads(cache.execute("select payload from metadata").fetchone()[0])
        spec = json.loads((root / "docs/ancient_investigation_2026-10-28.json").read_text())
        if metadata["dump_sha256"] != spec["qualified_scope_snapshot"]["dump_sha256"]:
            raise ValueError("Historical pronunciation snapshot changed")
        sources = {}
        for gc in ("sans1269", "anci1242", "lati1261"):
            sources.update(
                {
                    r["ID"]: dict(r)
                    for r in db.execute("select * from forms where gc_lc=? and Dataset='wiktionary'", (gc,))
                }
            )
        for r in reviews:
            if r["decision"] != "admit":
                continue
            row = sources[r["source_form_id"]]
            parameter = params[row["Parameter_ID"]]
            if row["Form"] != r["Form"] or parameter["Name"] != r["source_sense"]:
                raise ValueError("Historical lexical review drift")
            lang = row["Language_ID"].removeprefix("wikt_")
            pos = parse_parameter_name(parameter["Name"])[1]
            entries = [
                (line, json.loads(payload))
                for line, payload in cache.execute(
                    "select line,payload from entries where lang=? and word=? and pos=?", (lang, row["Form"], pos)
                )
            ]
            variants = scoped(entries, json.loads(r["tags"]), r["note"])
            if set(variants) != set(json.loads(r["raw_alternatives"])):
                raise ValueError("Reviewed historical alternatives changed")
            for ipa, lines in variants.items():
                pid = (
                    "ipa-"
                    + hashlib.sha256(
                        json.dumps([lang, row["Form"], pos, r["scope"], ipa], ensure_ascii=False).encode()
                    ).hexdigest()[:16]
                )
                groups.setdefault(r["av_id"], []).append(
                    dict(
                        source="wiktionary",
                        source_form_id=row["ID"],
                        source_language_id=row["Language_ID"],
                        source_glottocode=row["Glottocode"],
                        evidence_sha256=evidence_hash(row),
                        expected_source_concepticon_id=parameter["Concepticon_ID"],
                        concept_id=r["concept_id"],
                        decision="admit",
                        mapping_decision="retain"
                        if concepts[r["concept_id"]] == parameter["Concepticon_ID"]
                        else "map",
                        rationale=r["rationale"],
                        raw_ipa=ipa,
                        pronunciation_tags=r["tags"],
                        pronunciation_note=r["note"],
                        source_pronunciation_id=pid,
                        pronunciation_scope=r["scope"],
                        pronunciation_lines=";".join(dict.fromkeys(lines)),
                        dump_sha256=metadata["dump_sha256"],
                    )
                )
    for aid, records in groups.items():
        path = root / "varieties" / aid / "custom/supplements.csv"
        old = read(path) if path.exists() else []
        # Preserve unrelated admissions; the frozen dump and alternatives were validated above.
        keys = {(r["source"], r["source_form_id"], r["source_pronunciation_id"]) for r in records}
        earlier = [
            r for r in old if (r["source"], r["source_form_id"], r.get("source_pronunciation_id", "")) not in keys
        ]
        compiled = earlier + records
        if write:
            path.parent.mkdir(exist_ok=True)
            with path.open("w", newline="") as f:
                fields = list(dict.fromkeys(k for r in compiled for k in r))
                w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
                w.writeheader()
                w.writerows(compiled)
        elif old != compiled:
            raise ValueError("Historical compiled ledger differs from review")
        print(aid, len(records), "qualified source readings")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--write", action="store_true")
    compile_reviewed(write=p.parse_args().write)
