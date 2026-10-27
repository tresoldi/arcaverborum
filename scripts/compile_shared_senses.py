"""Extend guarded Wiktionary corrections only with agreeing independent reviews.

--write compiles consensus. Conflicts and needs_review block promotion. Existing
rules must still be supported; derived shared decisions do not count as fresh
independent evidence. Source-word IDs remain unchanged.
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

import yaml

from arcaverborum.concepts import load_concept_maps

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    with path.open() as handle:
        return list(csv.DictReader(handle))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    params = {r["ID"]: r for r in read(ROOT / "intake/wiktionary/parameters_raw.csv")}
    concepts = {r["concept_id"]: r for r in read(ROOT / "src/arcaverborum/data/concepts.csv")}
    index, _ = load_concept_maps()
    grouped = defaultdict(dict)
    conflicts = set()
    for custom in sorted((ROOT / "varieties").glob("*/custom")):
        aid = custom.parent.name
        config = yaml.safe_load((custom.parent / "config.yaml").read_text())
        for name in ["core_review.csv", "source_sense_review.csv"]:
            path = custom / name
            if not path.exists():
                continue
            for row in read(path):
                pid = row["Parameter_ID"]
                if not pid.startswith("wikt_") or "shared" in row["rationale"].lower():
                    continue
                source = params[pid]
                if (source["Name"], index.get(source["Concepticon_ID"], ("", ""))[0]) != (
                    row["source_name"],
                    row["source_concept_id"],
                ):
                    raise ValueError("English-sense review source drift: " + pid)
                language = row.get("source_language_id") or config["sources"].get("source_language_id") or aid
                value = (row["decision"], row["target_concept_id"], aid, row["rationale"])
                previous = grouped[pid].get(language)
                if previous and previous[:2] != value[:2]:
                    conflicts.add(pid)
                grouped[pid][language] = value
    rule_path = ROOT / "src/arcaverborum/data/wiktionary_sense_overrides.csv"
    old = {r["Parameter_ID"]: r for r in read(rule_path)}
    baseline = {r["Parameter_ID"] for r in read(ROOT / "docs/shared_sense_impact_2026-10-27.csv")}
    candidates = {}
    held = []
    for pid, by_language in grouped.items():
        rows = list(by_language.values())
        targets = {r[1] for r in rows}
        if pid in conflicts or len(targets) != 1 or any(r[0] == "needs_review" for r in rows):
            held.append(dict(Parameter_ID=pid, reason="conflicting or unresolved independent review"))
            continue
        if len(rows) < 2 or not any(r[0] in ("map", "unmap") for r in rows):
            continue
        target = next(iter(targets))
        source = params[pid]
        action = "map" if target else "unmap"
        if pid in old and (old[pid]["concept_id"], old[pid]["action"]) != (target, action):
            raise ValueError("Consensus contradicts existing rule: " + pid)
        candidates[pid] = dict(
            Parameter_ID=pid,
            expected_source_name=source["Name"],
            expected_source_concepticon_id=source["Concepticon_ID"],
            concept_id=target,
            Concepticon_ID=concepts[target]["concepticon_id"] if target else "",
            action=action,
            notes=old[pid]["notes"] if pid in old else next(r[3] for r in rows if r[0] in ("map", "unmap")),
            reviewed_languages=";".join(sorted({r[2] for r in rows})),
        )
    # Preserve prior reviewed rules when no new independent evidence supersedes
    # them. Conflicts are reported and never silently overwrite authored decisions.
    merged = {**old, **candidates}
    report = ROOT / "docs/shared_sense_followup_2026-10-27.csv"
    with report.open("w", newline="") as handle:
        fields = ["Parameter_ID", "status", "action", "reviewed_languages"]
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for pid, row in sorted(merged.items()):
            writer.writerow(
                dict(
                    Parameter_ID=pid,
                    status="retained" if pid in baseline else "new consensus",
                    action=row["action"],
                    reviewed_languages=row["reviewed_languages"],
                )
            )
    with (ROOT / "docs/shared_sense_conflicts_2026-10-27.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["Parameter_ID", "reason"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(held)
    if args.write:
        with rule_path.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(next(iter(merged.values()))), lineterminator="\n")
            writer.writeheader()
            writer.writerows(merged[k] for k in sorted(merged))
    print(
        len(old),
        "existing;",
        len(merged) - len(old),
        "new consensus corrections;",
        len(held),
        "held conflicts/unknowns",
    )


if __name__ == "__main__":
    main()
