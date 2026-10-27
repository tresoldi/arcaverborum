"""Validate authored dictionary sense decisions and compile active construction maps."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    with path.open() as handle:
        return list(csv.DictReader(handle))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    reviews = read(ROOT / "src/arcaverborum/data/dictionary_senses.csv")
    concepts = {r["concept_id"]: r for r in read(ROOT / "src/arcaverborum/data/concepts.csv")}
    for path in sorted((ROOT / "varieties").glob("*/config.yaml")):
        config = yaml.safe_load(path.read_text())
        source = config["sources"]["transcription"]
        selected = [r for r in reviews if r["dataset"] == source]
        if not selected:
            continue
        cldf = ROOT / "raw/lexibank" / source / "cldf"
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
                raise ValueError("Reviewed dictionary source drift: " + review["sense_id"])
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
        if args.write:
            with (path.parent / "custom/concept_map.csv").open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(records[0]), lineterminator="\n")
                writer.writeheader()
                writer.writerows(records)
        print(config["av_id"], len(records), "guarded dictionary sense mappings")


if __name__ == "__main__":
    main()
