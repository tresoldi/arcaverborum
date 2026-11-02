"""Compare raw cognacy extensions with structured judgments; report, never infer bridges."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=ROOT / "web/data/catalog.json.gz")
    parser.add_argument("--output", type=Path, required=True,
                        help="New report path; existing historical reports are never overwritten")
    args = parser.parse_args()
    if args.output.exists():
        parser.error(f"Report already exists: {args.output}")
    with gzip.open(args.catalog, "rt") as handle:
        catalog = json.load(handle)
    active = {r["transcription_source"] for r in catalog["languages"]}
    active.add("dictmedialengua")
    report = []
    with (ROOT / "src/arcaverborum/data/cognacy_scope_policies.csv").open() as handle:
        repaired = {r["dataset"] for r in csv.DictReader(handle)}
    for source in sorted(active):
        cldf = ROOT / "raw/lexibank" / source / "cldf"
        if not (cldf / "forms.csv").exists() or not (cldf / "cognates.csv").exists():
            continue
        with (cldf / "forms.csv").open() as handle:
            reader = csv.DictReader(handle)
            if "Cognacy" not in reader.fieldnames:
                continue
            raw = [r for r in reader if r.get("Cognacy", "").strip()]
        if not raw:
            continue
        with (cldf / "cognates.csv").open() as handle:
            structured = {r["Cognateset_ID"] for r in csv.DictReader(handle)}
        counts = Counter()
        for row in raw:
            values = [v.strip() for v in row["Cognacy"].split(";") if v.strip()]
            counts["raw_coded_forms"] += 1
            counts["semicolon_lists"] += len(values) > 1
            counts["comma_labels"] += any("," in v for v in values)
            counts["all_raw_labels_declared_in_structured_table"] += all(v in structured for v in values)
        report.append(
            dict(
                source=source,
                **counts,
                decision=(
                    "authoritative structured memberships; auxiliary raw identifiers retained as source notes"
                    if source == "abvd2026" or source in repaired
                    else "retain source; assess undeclared raw labels individually before repair"
                ),
            )
        )
    path = args.output
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "source",
        "raw_coded_forms",
        "semicolon_lists",
        "comma_labels",
        "all_raw_labels_declared_in_structured_table",
        "decision",
    ]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(report)
    print(len(report), "sources with both raw and structured cognacy; no cross-meaning inference made")


if __name__ == "__main__":
    main()
