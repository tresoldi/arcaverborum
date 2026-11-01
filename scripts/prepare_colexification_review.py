"""Prepare a score-blinded source-evidence worksheet from a sealed pilot audit sample."""

import argparse
import csv
import json
import resource
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

from arcaverborum.colexification import digest, sha, verify_database


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument("--build", type=Path, required=True)
    p.add_argument("--pilot", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    resource.setrlimit(resource.RLIMIT_AS, (256 * 1024**2, 256 * 1024**2))
    seal = verify_database(a.build)
    complete = json.loads((a.pilot / "complete.json").read_text())
    if sha(a.pilot / "audit_packet.csv") != complete["files"]["audit_packet.csv"]:
        raise ValueError("Unsealed audit packet")
    if complete["signature"]["database_sha256"] != seal["database_sha256"]:
        raise ValueError("Audit/core binding differs")
    aggregate = a.root / "output/aggregate/forms.csv"
    if sha(aggregate) != complete["signature"]["aggregate_sha256"]:
        raise ValueError("Source evidence aggregate differs")
    audit = list(csv.DictReader((a.pilot / "audit_packet.csv").open()))
    targets = {(r["av"], r["source"], r["member"], r[side]) for r in audit for side in ["a", "b"]}
    originals = defaultdict(list)
    fields = [
        "concept_id",
        "source_form_id",
        "source_parameter_id",
        "Value",
        "Form",
        "Segments",
        "Segments_Source",
        "raw_ipa",
        "pronunciation_tags",
        "bibtex_key",
    ]
    with aggregate.open() as h:
        for row in csv.DictReader(h):
            key = row["av_id"], row["transcription_source"], row["source_language_id"], row["concept_id"]
            if key in targets:
                if len(originals[key]) >= 2048:
                    raise ValueError("Review source-evidence budget exceeded")
                originals[key].append({k: row.get(k, "") for k in fields})
    db = sqlite3.connect(f"file:{a.build / 'index.sqlite'}?mode=ro", uri=True)
    cases = []
    links = []
    for row in audit:
        case = digest(dict(core=seal["build_id"], sid=row["sid"], a=row["a"], b=row["b"]))[:24]
        review = {
            k: row[k]
            for k in [
                "av",
                "source",
                "member",
                "tags",
                "basis",
                "language",
                "family",
                "area",
                "a",
                "b",
                "definition_a",
                "definition_b",
            ]
        }
        review["case_id"] = case
        for side in ["a", "b"]:
            original = originals[row["av"], row["source"], row["member"], row[side]]
            review["original_records_" + side] = json.dumps(original, ensure_ascii=False)
            labels = []
            if row["source"].startswith("wiktionary"):
                for pid in sorted({r["source_parameter_id"] for r in original}):
                    labels.extend(
                        dict(parameter_id=pid, source_name=name)
                        for (name,) in db.execute("SELECT name FROM source_senses WHERE param=? ORDER BY name", (pid,))
                    )
            review["native_senses_" + side] = json.dumps(labels, ensure_ascii=False)
        review.update(
            review_status="pending_independent_review",
            reviewer="",
            decision="",
            source_evidence="",
            sense_equivalence="",
            reading_fidelity="",
            lexeme_relation="",
            notes="",
        )
        cases.append(review)
        links.append(dict(case_id=case, sid=int(row["sid"]), pair=int(row["pair"]), y=row["y"], role=row["role"]))
    cases.sort(key=lambda r: r["case_id"])
    a.output.mkdir(parents=True, exist_ok=False)
    with (a.output / "blinded_worksheet.csv").open("w") as h:
        w = csv.DictWriter(h, fieldnames=list(cases[0]))
        w.writeheader()
        w.writerows(cases)
    (a.output / "analyst_key.json").write_text(json.dumps(links, indent=2) + "\n")
    report = dict(
        core=seal["build_id"],
        pilot_signature=complete["signature"],
        cases=len(cases),
        independent_adjudications=0,
        areas=dict(Counter(area for r in cases for area in r["area"].split(";"))),
        audit_status_counts=dict(Counter(r["y"] or "unknown" for r in audit)),
        source_evidence="All accepted original rows for the same variety/source/member/concept, including "
        "analytically excluded or unreviewed rows. Pronunciation tags remain explicit; "
        "other tags/bases are not evidence of comparability in the target scope.",
        blinding="Hash-ordered worksheet omits y, role, model probabilities, null statistics, curation comments "
        "and semantic-gate decisions. "
        "Analyst key is separate. Familiar pairs and source evidence limit complete blinding.",
        source_sha256=sha(aggregate),
        script_sha256=sha(Path(__file__)),
        files={p.name: sha(p) for p in a.output.iterdir() if p.is_file()},
    )
    (a.output / "manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: v
                for k, v in report.items()
                if k in ["cases", "independent_adjudications", "areas", "audit_status_counts"]
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
