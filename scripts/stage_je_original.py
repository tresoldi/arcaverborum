"""Materialize and stage the frozen reviewed Jê study slice outside active intake."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from arcaverborum.ingest import ingest_lexibank
from arcaverborum.sources.je_original import conservative_reading, materialize, read

ROOT = Path(__file__).resolve().parents[1]


def compile_profiles(root, *, write=False):
    reviews = read(root / "src/arcaverborum/data/je_original_review.csv")
    targets = {"Xerénte": "nub-xerente", "Xavánte": "nub-xavante", "Ingain": "nub-ingain"}
    for name, aid in targets.items():
        entries = {}
        for row in reviews:
            if row["doculect"] != name or row["decision"] != "admit":
                continue
            ipa = conservative_reading(row["raw_value"])
            if not ipa or ipa != row["ipa_segments"]:
                raise ValueError("Unreviewed profile value")
            key = "^" + row["source_form"] + "$"
            if key in entries and entries[key] != ipa:
                raise ValueError("Ambiguous whole-form profile")
            entries[key] = ipa
        path = root / "varieties" / aid / "custom/profile.tsv"
        if write:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", newline="") as handle:
                writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
                writer.writerow(["Grapheme", "IPA", "notes"])
                writer.writerows(
                    (key, ipa, "Reviewed source notation; broad phonemic value only; no surface-allophone inference.")
                    for key, ipa in entries.items()
                )
        else:
            actual = {r["Grapheme"]: r["IPA"] for r in read(path, delimiter="\t")}
            if actual != entries:
                raise ValueError("Compiled Jê profile differs from authored review: " + aid)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--fetch", action="store_true")
    parser.add_argument("--write-profiles", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    output = (args.output or root / "raw/curation/je-stage").resolve()
    if output == root / "intake" or root / "intake" in output.parents:
        raise ValueError("Staging must be outside active intake")
    print(materialize(root / "raw", download=args.fetch))
    if args.write_profiles:
        compile_profiles(root, write=True)
    result = ingest_lexibank(root / "raw", output, datasets=["gerardije2025"])
    if result["datasets_ingested"] != 1:
        raise ValueError("Reviewed Jê source did not stage successfully")
    print(result)


if __name__ == "__main__":
    main()
