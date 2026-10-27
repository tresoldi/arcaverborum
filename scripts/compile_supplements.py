"""Compile explicit source-form/sense reviews into guarded additive ledgers.

Default validates only. --write compiles admitted rows; changed existing source
evidence requires a new explicit review rather than silently refreshing hashes.
"""

from __future__ import annotations

import argparse
import csv
import sqlite3
from collections import defaultdict
from pathlib import Path

import yaml

from arcaverborum.supplements import evidence_hash

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    with path.open() as handle:
        return list(csv.DictReader(handle))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review", type=Path, default=ROOT / "docs/supplement_pilot_review_2026-10-27.csv")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    parameters = {r["ID"]: r for r in read(ROOT / "intake/wiktionary/parameters_raw.csv")}
    ledgers = defaultdict(list)
    with sqlite3.connect((ROOT / "intake/intake.sqlite").as_uri() + "?mode=ro", uri=True) as db:
        db.row_factory = sqlite3.Row
        for review in read(args.review):
            if review["decision"] != "admit":
                continue
            config = yaml.safe_load((ROOT / "varieties" / review["av_id"] / "config.yaml").read_text())
            rows = db.execute(
                "SELECT * FROM forms WHERE gc_lc=? AND Dataset=? AND ID=?",
                (config["glottocode"], "wiktionary", review["source_form_id"]),
            ).fetchall()
            if len(rows) != 1:
                raise ValueError("Source identity missing or duplicated: " + review["source_form_id"])
            row = dict(rows[0])
            parameter = parameters[row["Parameter_ID"]]
            if row["Form"] != review["Form"] or parameter["Name"] != review["source_sense"]:
                raise ValueError("Reviewed spelling or sense changed: " + row["ID"])
            ledgers[review["av_id"]].append(
                dict(
                    source="wiktionary",
                    source_form_id=row["ID"],
                    source_language_id=row["Language_ID"],
                    source_glottocode=row["Glottocode"],
                    evidence_sha256=evidence_hash(row),
                    expected_source_concepticon_id=parameter["Concepticon_ID"],
                    concept_id=review["concept_id"],
                    decision="admit",
                    mapping_decision="retain",
                    rationale=review["rationale"],
                )
            )
    for aid, records in ledgers.items():
        path = ROOT / "varieties" / aid / "custom/supplements.csv"
        if path.exists():
            old = {r["source_form_id"]: r for r in read(path)}
            for row in records:
                if (
                    row["source_form_id"] in old
                    and row["evidence_sha256"] != old[row["source_form_id"]]["evidence_sha256"]
                ):
                    raise ValueError("Previously reviewed evidence changed: " + row["source_form_id"])
        if args.write:
            path.parent.mkdir(exist_ok=True)
            with path.open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(records[0]), lineterminator="\n")
                writer.writeheader()
                writer.writerows(records)
        print(aid, len(records), "forms;", len({r["concept_id"] for r in records}), "reviewed concepts")


if __name__ == "__main__":
    main()
