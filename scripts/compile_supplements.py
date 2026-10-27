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


def merge_reviews(existing, additions):
    """A partial review adds evidence without deleting other source admissions."""

    def key(row):
        return row["source"], row["source_form_id"], row.get("source_pronunciation_id", "")

    result = {key(row): row for row in existing}
    if len(result) != len(existing):
        raise ValueError("Duplicate existing supplemental decision")
    seen = set()
    for row in additions:
        identity = key(row)
        if identity in seen:
            raise ValueError("Duplicate new supplemental decision")
        seen.add(identity)
        if identity in result:
            old = result[identity]
            if row["evidence_sha256"] != old["evidence_sha256"] or row.get(
                "expected_source_concepticon_id", ""
            ) != old.get("expected_source_concepticon_id", ""):
                raise ValueError("Previously reviewed evidence changed: " + row["source_form_id"])
            # A source-IPA compiler cannot replace a scoped/profile decision.
            if old.get("profile_file") or old.get("pronunciation_scope"):
                raise ValueError("Scoped/profile decision requires its own compiler")
        result[identity] = row
    return list(result.values())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review", type=Path, default=ROOT / "docs/supplement_pilot_review_2026-10-27.csv")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    parameters = {}
    for path in sorted((ROOT / "intake").glob("*/parameters_raw.csv")):
        parameters.update({r["ID"]: r for r in read(path)})
    ledgers = defaultdict(list)
    with sqlite3.connect((ROOT / "intake/intake.sqlite").as_uri() + "?mode=ro", uri=True) as db:
        db.row_factory = sqlite3.Row
        for review in read(args.review):
            if review["decision"] != "admit":
                continue
            source = review.get("source") or "wiktionary"
            config = yaml.safe_load((ROOT / "varieties" / review["av_id"] / "config.yaml").read_text())
            rows = db.execute(
                "SELECT * FROM forms WHERE gc_lc=? AND Dataset=? AND ID=?",
                (config["glottocode"], source, review["source_form_id"]),
            ).fetchall()
            if len(rows) != 1:
                raise ValueError("Source identity missing or duplicated: " + review["source_form_id"])
            row = dict(rows[0])
            parameter = parameters[row["Parameter_ID"]]
            if row["Form"] != review["Form"] or parameter["Name"] != review["source_sense"]:
                raise ValueError("Reviewed spelling or sense changed: " + row["ID"])
            if review.get("source_language_id") and row["Language_ID"] != review["source_language_id"]:
                raise ValueError("Reviewed source member changed: " + row["ID"])
            ledgers[review["av_id"]].append(
                dict(
                    source=source,
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
        existing = read(path) if path.exists() else []
        records = merge_reviews(existing, records)
        if args.write:
            path.parent.mkdir(exist_ok=True)
            with path.open("w", newline="") as handle:
                fields = list(dict.fromkeys(key for row in records for key in row))
                writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
                writer.writeheader()
                writer.writerows(records)
        print(aid, len(records), "forms;", len({r["concept_id"] for r in records}), "reviewed concepts")


if __name__ == "__main__":
    main()
