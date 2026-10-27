"""Validate all authored dictionary senses, including staged sources, then compile active maps."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    with path.open() as handle:
        return list(csv.DictReader(handle))


def reviewed_maps(root):
    """Fail on missing, duplicate or changed evidence even for inactive sources."""
    reviews = read(root / "src/arcaverborum/data/dictionary_senses.csv")
    concepts = {r["concept_id"]: r for r in read(root / "src/arcaverborum/data/concepts.csv")}
    grouped = defaultdict(list)
    seen = set()
    for review in reviews:
        key = review["dataset"], review["sense_id"]
        if key in seen or not review["rationale"].strip():
            raise ValueError("Duplicate or unexplained dictionary decision: " + str(key))
        seen.add(key)
        grouped[review["dataset"]].append(review)
    maps = {}
    for source, selected in grouped.items():
        cldf = root / "raw/lexibank" / source / "cldf"
        entries = {r["ID"]: r for r in read(cldf / "entries.csv")}
        senses = {r["ID"]: r for r in read(cldf / "senses.csv")}
        records = []
        for review in selected:
            sense = senses[review["sense_id"]]
            entry = entries[sense["Entry_ID"]]
            if (entry["Headword"], sense["Description"], entry["Part_Of_Speech"]) != (
                review["expected_headword"],
                review["expected_description"],
                review["expected_pos"],
            ):
                raise ValueError("Reviewed dictionary source drift: " + source + ":" + review["sense_id"])
            concept = concepts[review["concept_id"]]
            records.append(
                dict(
                    Parameter_ID=source + "_" + review["sense_id"],
                    Concepticon_ID=concept["concepticon_id"],
                    Concepticon_Gloss=concept["label"],
                    concept_id=concept["concept_id"],
                    action="map",
                    notes=review["rationale"],
                )
            )
        maps[source] = records
    return maps


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    maps = reviewed_maps(ROOT)
    for source, records in maps.items():
        print(source, len(records), "validated source-sense decisions (not pronunciation admissions)")
    for path in sorted((ROOT / "varieties").glob("*/config.yaml")):
        config = yaml.safe_load(path.read_text())
        records = maps.get(config["sources"]["transcription"])
        if not records:
            continue
        if args.write:
            directory = path.parent / "custom"
            directory.mkdir(exist_ok=True)
            with (directory / "concept_map.csv").open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(records[0]), lineterminator="\n")
                writer.writeheader()
                writer.writerows(records)
        print(config["av_id"], len(records), "guarded active dictionary sense mappings")


if __name__ == "__main__":
    main()
