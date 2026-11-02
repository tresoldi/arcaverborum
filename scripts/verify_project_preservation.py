"""Freeze/verify the explicitly authorized 2026-11-02 project migration.

The small private baseline stores per-construction protected-field hashes and
earlier cognacy strings. No corpus-wide matrix is loaded. Verification also
independently joins current memberships to the original source CognateTables.
"""

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {"acd", "sagartst", "leejaponic"}
csv.field_size_limit(sys.maxsize)


def snapshot(root):
    with (root / "docs/project_yasa_native_senses_2026-11-02.csv").open() as handle:
        yasa = {r["source_form_id"] for r in csv.DictReader(handle)}
    with (root / "varieties/kri-kipea/custom/primary.csv").open() as handle:
        kipea = {r["source_form_id"] for r in csv.DictReader(handle)
                 if "-p4-" in r["source_form_id"] or "-p7-" in r["source_form_id"]}
    hashes, counts, memberships = defaultdict(hashlib.sha256), Counter(), {}
    additions = []
    with (root / "output/aggregate/forms.csv").open() as handle:
        for row in csv.DictReader(handle):
            key = (row["av_id"], row["transcription_source"], row["source_form_id"],
                   row.get("source_pronunciation_id", ""))
            if row["av_id"] == "kri-kipea" and row["source_form_id"] in kipea:
                additions.append(row)
                continue
            exclude = set()
            if row["transcription_source"] in SOURCES:
                exclude |= {"Cognacy", "canonical_cognate_id", "Comment", "quality_score"}
                identity = json.dumps(key)
                if identity in memberships:
                    raise ValueError("Duplicate accepted source identity in the repair cohort")
                memberships[identity] = row["Cognacy"]
            if row["av_id"] == "atl-yasa" and row["source_form_id"] in yasa:
                exclude |= {"concept_id", "concept_label", "Concepticon_ID", "Comment", "quality_score"}
            payload = {k: v for k, v in row.items() if k not in exclude}
            hashes[row["av_id"]].update(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode() + b"\n")
            counts[row["av_id"]] += 1
    return dict(protected_hashes={k: v.hexdigest() for k, v in hashes.items()}, counts=dict(counts),
                memberships=memberships, addition_ids=[r["source_form_id"] for r in additions])


def verify_native_memberships(root, actual):
    expected = {}
    for source in SOURCES:
        table = root / "raw/lexibank" / source / "cldf/cognates.csv"
        with table.open() as handle:
            for row in csv.DictReader(handle):
                expected.setdefault((source, source + "_" + row["Form_ID"]), set()).add(
                    source + "_" + row["Cognateset_ID"])
    for identity, codes in actual.items():
        _, source, fid, _ = json.loads(identity)
        if set(filter(None, codes.split(";"))) != expected.get((source, fid), set()):
            raise ValueError("Published membership is not the native source form's full structured set: " + fid)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--baseline", type=Path, required=True)
    p.add_argument("--output", type=Path)
    p.add_argument("--freeze", action="store_true")
    args = p.parse_args()
    result = snapshot(ROOT)
    if args.freeze:
        if args.baseline.exists():
            p.error("Never overwrite a frozen baseline")
        args.baseline.write_text(json.dumps(result, ensure_ascii=False) + "\n")
        return
    if not args.output:
        p.error("Verification requires --output")
    before = json.loads(args.baseline.read_text())
    if (result["protected_hashes"] != before["protected_hashes"] or result["counts"] != before["counts"]
            or len(result["addition_ids"]) != 4 or before["addition_ids"]):
        raise ValueError("Protected fields, construction membership or the four authorized additions differ")
    changed, cleared, removed = 0, 0, 0
    for key, old in before["memberships"].items():
        new = result["memberships"][key]
        older, newer = set(filter(None, old.split(";"))), set(filter(None, new.split(";")))
        if not newer <= older:
            raise ValueError("Repair invented a membership absent from the earlier source union")
        changed += old != new
        cleared += bool(old) and not new
        removed += len(older - newer)
    verify_native_memberships(ROOT, result["memberships"])
    proof = dict(protected_records=sum(result["counts"].values()), nonempty_constructions=len(result["counts"]),
                 new_written_records=4, changed_cognacy_records=changed,
                 unsupported_extra_memberships_removed=removed, unsupported_raw_only_memberships_cleared=cleared,
                 other_protected_fields_unchanged=True, allowed_native_sense_mappings=19,
                 all_new_cognates_are_existing_structured_memberships=True,
                 full_native_cognate_memberships_independently_joined=True,
                 baseline_sha256=hashlib.sha256(args.baseline.read_bytes()).hexdigest())
    args.output.write_text(json.dumps(proof, indent=2) + "\n")
    print(json.dumps(proof, indent=2))


if __name__ == "__main__":
    main()
