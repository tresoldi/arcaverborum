"""Compile exact reviewed staged historical lexical slices into additive guards."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from arcaverborum.supplements import evidence_hash

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    with path.open() as f:
        return list(csv.DictReader(f))


def compile_ledgers(dataset, *, write=False):
    spec = next(
        s
        for s in json.loads((ROOT / "src/arcaverborum/data/ancient_lexical_sources.json").read_text())
        if s["dataset"] == dataset
    )
    stage = ROOT / "raw/curation" / ("stage-" + dataset) / "lexibank"
    params = {r["ID"]: r for r in read(stage / "parameters_raw.csv")}
    reviews = {r["source_form_id"]: r for r in read(ROOT / spec["review"]) if r["decision"] == "admit"}
    groups = {}
    for row in read(stage / "forms.csv"):
        review = reviews[row["ID"].removeprefix(dataset + "_")]
        if row["Dataset"] != dataset or row["Form"] != review["Form"] or row["Segments"]:
            raise ValueError("Historical staged evidence mismatch")
        groups.setdefault(review["av_id"], []).append(
            dict(
                source=dataset,
                source_form_id=row["ID"],
                source_language_id=row["Language_ID"],
                source_glottocode=row["Glottocode"],
                evidence_sha256=evidence_hash(row),
                expected_source_concepticon_id=params[row["Parameter_ID"]]["Concepticon_ID"],
                concept_id=review["concept_id"],
                decision="admit",
                mapping_decision="retain",
                rationale=review["rationale"],
                transcription_policy="orthographic_only",
            )
        )
    for aid, records in groups.items():
        p = ROOT / "varieties" / aid / "custom/supplements.csv"
        old = read(p) if p.exists() else []
        new = [r for r in old if r["source"] != dataset] + records
        if write:
            p.parent.mkdir(exist_ok=True)
            with p.open("w") as f:
                w = csv.DictWriter(f, fieldnames=list(dict.fromkeys(k for r in new for k in r)), lineterminator="\n")
                w.writeheader()
                w.writerows(new)
        elif old != new:
            raise ValueError("Historical ledger differs from reviewed stage")
        print(aid, len(records), dataset, "orthographic-only admissions")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dataset", required=True)
    p.add_argument("--write", action="store_true")
    a = p.parse_args()
    compile_ledgers(a.dataset, write=a.write)
