"""Rank missing supported core slots against member-specific intake alternatives.

This read-only report measures additive potential against accepted output, not
whole-source replacement gains. Supplied IPA is distinguished from spelling
potential. Identity, sense and citation review remain mandatory; scores are
triage priorities, never an admission decision. South America sorts first.
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import resource
import sqlite3
from collections import defaultdict
from pathlib import Path

import yaml

from arcaverborum.phonology import normalize_segments
from arcaverborum.source_evidence import is_recording_placeholder

ROOT = Path(__file__).resolve().parents[1]
SUPPORTED = {"source", "profile"}


def read(path):
    with path.open() as handle:
        yield from csv.DictReader(handle)


def baseline(forms, core):
    mapped, supported = set(), set()
    for row in forms:
        cid = row['concept_id']
        if cid in core:
            mapped.add(cid)
            if row['Segments_Source'] in SUPPORTED:
                supported.add(cid)
    return mapped, supported


def opportunity(target, source, member, forms, parameters, concepts, core, reviewed, metadata):
    mapped, supplied = set(), set()
    invalid = 0
    for form in forms:
        if is_recording_placeholder(source, form["Form"], form["Value"]):
            continue
        cid = reviewed.get((source, form["Parameter_ID"]), concepts.get(parameters.get(form["Parameter_ID"], ""), ""))
        if cid not in core or cid in target["supported"]:
            continue
        mapped.add(cid)
        _, status = normalize_segments(form["Segments"], form["Form"] or form["Value"])
        if status == "source":
            supplied.add(cid)
        else:
            invalid += bool(form["Segments"])
    if not mapped:
        return None
    needs_profile = mapped - supplied
    blockers = ["source_member_identity_review", "sense_review"]
    if needs_profile:
        blockers.append("source_specific_profile_or_pronunciation_evidence")
    if invalid:
        blockers.append("invalid_supplied_segments")
    if not metadata.get("Citation") or not metadata.get("License"):
        blockers.append("citation_or_license_incomplete")
    return dict(
        av_id=target["av_id"],
        name=target["name"],
        macroarea=target["macroarea"],
        glottocode=target["glottocode"],
        primary_source=target["primary"],
        source=source,
        source_language_id=member,
        supported_core=len(target["supported"]),
        missing_supported_core=len(core - target["supported"]),
        additive_source_core_potential=len(supplied),
        orthographic_core_potential=len(needs_profile),
        supplied_concepts=";".join(sorted(supplied)),
        orthographic_concepts=";".join(sorted(needs_profile)),
        source_citation=metadata.get("Citation", ""),
        source_url=metadata.get("URL", ""),
        license=metadata.get("License", ""),
        source_version=metadata.get("Repository_Version", ""),
        blockers=";".join(blockers),
        status="unreviewed_additive_potential",
    )


def rank_key(row):
    return (
        {"South America": 0, "North America": 1}.get(row["macroarea"], 2),
        0 if row["additive_source_core_potential"] else 1,
        -row["additive_source_core_potential"],
        -row["orthographic_core_potential"],
        row["av_id"],
        row["source"],
        row["source_language_id"],
    )


def build(root, output):
    core = {r["concept_id"] for r in read(root / "src/arcaverborum/data/concept_core.csv")}
    concepts = {r["concepticon_id"]: r["concept_id"] for r in read(root / "src/arcaverborum/data/concepts.csv")}
    targets = defaultdict(list)
    for path in sorted((root / "varieties").glob("*/config.yaml")):
        built = path.parent / "generated/forms.csv"
        if not built.exists():
            continue
        config = yaml.safe_load(path.read_text())
        if not str(config.get("glottocode", "")).strip():
            continue  # A shared blank code cannot establish alternative-source identity.
        _, supported = baseline(read(built), core)
        if supported == core:
            continue
        target = dict(
            av_id=config["av_id"],
            name=config["name"],
            glottocode=config["glottocode"],
            macroarea=config["macroarea"],
            primary=config["sources"]["transcription"],
            supported=supported,
        )
        targets[config["glottocode"].strip().lower()].append(target)
    parameters, metadata = {}, {}
    for path in sorted((root / "intake").glob("*/parameters_raw.csv")):
        parameters.update({r["ID"]: r["Concepticon_ID"] for r in read(path)
                           if concepts.get(r["Concepticon_ID"]) in core})
    for path in sorted((root / "intake").glob("*/metadata.csv")):
        metadata.update({r["Dataset"]: r for r in read(path)})
    reviewed = {
        (r["dataset"], r["dataset"] + "_" + r["sense_id"]): r["concept_id"]
        for r in read(root / "src/arcaverborum/data/dictionary_senses.csv") if r["concept_id"] in core
    }
    rows = []
    with sqlite3.connect((root / "intake/intake.sqlite").as_uri() + "?mode=ro", uri=True) as db:
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA cache_size=-16384')
        db.execute('PRAGMA mmap_size=0')
        db.execute('PRAGMA temp_store=FILE')
        for gc, choices in sorted(targets.items()):
            for target in choices:
                query = db.execute(
                    'SELECT Dataset, Language_ID, Parameter_ID, Form, Value, Segments FROM forms '
                    "WHERE gc_lc=? AND Dataset NOT IN (?, 'gled', 'asjp') ORDER BY Dataset,Language_ID",
                    (gc, target['primary']))
                for (source, member), forms in itertools.groupby(query, key=lambda r: (r['Dataset'],r['Language_ID'])):
                    row = opportunity(target, source, member, forms, parameters, concepts, core,
                                      reviewed, metadata.get(source, {}))
                    if row:
                        rows.append(row)
    rows.sort(key=rank_key)
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else ["av_id", "source", "status"]
    with output.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["rank", *fields], lineterminator="\n")
        writer.writeheader()
        writer.writerows(dict(rank=i, **row) for i, row in enumerate(rows, 1))
    summary = dict(
        accepted_targets_with_gaps=sum(map(len, targets.values())),
        member_opportunities=len(rows),
        south_american_opportunities=sum(r["macroarea"] == "South America" for r in rows),
        american_opportunities=sum(r["macroarea"] in {"South America", "North America"} for r in rows),
        method=("Additive potential against supported accepted concepts. "
                "Member rows overlap; do not sum as unique gains."),
        source_policy=("Valid supplied/upstream-converted segments count as source-reading potential, "
                       "not independent IPA certification. "
                       "Resegmented spelling is orthographic potential, never supported evidence."),
        limitations=("Raw upstream mappings require sense review. Same Glottocode does not certify sample identity. "
                     "Primary-source profile recovery is outside this alternatives report."),
    )
    output.with_suffix(".json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=ROOT / "output/report/coverage_opportunities.csv")
    parser.add_argument("--memory-mb", type=int, default=256)
    args = parser.parse_args()
    if args.memory_mb < 128:
        parser.error("Memory budget must be at least 128 MiB")
    resource.setrlimit(resource.RLIMIT_AS, (args.memory_mb * 1024 * 1024,) * 2)
    build(args.root.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
