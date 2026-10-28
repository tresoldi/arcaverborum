"""Compile reviewed lexical evidence while explicitly withholding pronunciation."""

from __future__ import annotations

import argparse
import csv
import sqlite3
from pathlib import Path

import yaml

from arcaverborum.supplements import evidence_hash

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    with path.open() as f:
        return list(csv.DictReader(f))


def compile_review(review, *, write=False):
    params = {r["ID"]: r for p in (ROOT / "intake").glob("*/parameters_raw.csv") for r in read(p)}
    groups = {}
    with sqlite3.connect((ROOT / "intake/intake.sqlite").as_uri() + "?mode=ro", uri=True) as db:
        db.row_factory = sqlite3.Row
        for r in read(review):
            if r["decision"] != "admit":
                continue
            config = yaml.safe_load((ROOT / "varieties" / r["av_id"] / "config.yaml").read_text())
            found = db.execute(
                "select * from forms where gc_lc=? and Dataset=? and ID=?",
                (config["glottocode"], r["source"], r["source_form_id"]),
            ).fetchall()
            if len(found) != 1:
                raise ValueError("Historical orthographic source missing or duplicated")
            row = dict(found[0])
            p = params[row["Parameter_ID"]]
            if (
                row["Form"] != r["Form"]
                or row["Language_ID"] != r["source_language_id"]
                or p["Name"] != r["source_sense"]
                or row["Segments"]
            ):
                raise ValueError("Historical spelling/sense/reading drift")
            groups.setdefault(r["av_id"], []).append(
                dict(
                    source=r["source"],
                    source_form_id=row["ID"],
                    source_language_id=row["Language_ID"],
                    source_glottocode=row["Glottocode"],
                    evidence_sha256=evidence_hash(row),
                    expected_source_concepticon_id=p["Concepticon_ID"],
                    concept_id=r["concept_id"],
                    decision="admit",
                    mapping_decision="retain",
                    rationale=r["rationale"],
                    transcription_policy="orthographic_only",
                )
            )
    for aid, records in groups.items():
        path = ROOT / "varieties" / aid / "custom/supplements.csv"
        old = read(path) if path.exists() else []
        keys = {(r["source"], r["source_form_id"]) for r in records}
        combined = [r for r in old if (r["source"], r["source_form_id"]) not in keys] + records
        if write:
            path.parent.mkdir(exist_ok=True)
            with path.open("w") as f:
                w = csv.DictWriter(
                    f, fieldnames=list(dict.fromkeys(k for r in combined for k in r)), lineterminator="\n"
                )
                w.writeheader()
                w.writerows(combined)
        elif [{k: v for k, v in r.items() if v} for r in old] != [
            {k: v for k, v in r.items() if v} for r in combined
        ]:
            raise ValueError('Historical orthography ledger differs from reviewed evidence')
        print(aid, len(records), "reviewed orthographic-only forms")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--review", type=Path, required=True)
    p.add_argument("--write", action="store_true")
    a = p.parse_args()
    compile_review(a.review, write=a.write)
