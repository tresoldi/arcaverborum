"""Validate independent model-assisted worksheets and preserve disagreements.

Agreement is descriptive and is never treated as expert annotation or accuracy.
"""

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

from arcaverborum.colexification import sha

FIELDS = {
    "identity_evidence": {"represented_identity", "sampled_nonmatch", "insufficient_evidence", "ambiguous_scope"},
    "sense_evidence": {
        "source_supported",
        "mapping_unverified",
        "explicit_mismatch",
        "catalog_overlap",
        "insufficient_evidence",
    },
    "reading_fidelity": {
        "retained_consistent",
        "derivation_requires_review",
        "suspected_truncation",
        "inconsistent",
        "insufficient_evidence",
    },
    "interpretation": {
        "unresolved",
        "catalog_overlap",
        "documented_homonymy",
        "documented_polysemy",
        "underspecified_source",
    },
}


def read(path):
    with path.open() as handle:
        rows = list(csv.DictReader(handle))
    result = {r["case_id"]: r for r in rows}
    if len(result) != len(rows):
        raise ValueError("Duplicate review case")
    return result


def compare(worksheet, paths, output):
    cases = read(worksheet)
    reviews = [read(p) for p in paths]
    if len(paths) < 2 or len({sha(p) for p in paths}) != len(paths):
        raise ValueError("Distinct reviewer files required")
    names = [{r["reviewer"] for r in review.values()} for review in reviews]
    if any(len(n) != 1 for n in names) or len(set.union(*names)) != len(names):
        raise ValueError("Distinct, consistent reviewer identities required")
    supplementary = []
    for path, review in zip(paths, reviews, strict=True):
        if set(review) != set(cases):
            raise ValueError(f"Incomplete or unexpected cases: {path}")
        for cid, row in review.items():
            for field, allowed in FIELDS.items():
                if row[field] not in allowed:
                    raise ValueError(f"Unknown {field}: {cid}")
            if not all(row.get(f, "").strip() for f in ["reviewer", "evidence", "limitations"]):
                raise ValueError("Missing reviewer evidence or limitations: " + cid)
            originals = [r for side in ["a", "b"] for r in json.loads(cases[cid]["original_records_" + side])]
            ids = {r[k] for r in originals for k in ["source_form_id", "source_parameter_id"] if r.get(k)}
            cited = {x.strip() for x in row.get("evidence_ids", "").split(";") if x.strip()}
            if ids and not (cited & ids):
                raise ValueError("Unsupported/missing native IDs: " + cid)
            for native_id in sorted(cited - ids):
                supplementary.append(
                    dict(
                        case_id=cid,
                        reviewer=row["reviewer"],
                        native_id=native_id,
                        status="outside_frozen_packet_requires_source_verification",
                    )
                )
    if output.exists():
        raise ValueError("Refuse to overwrite a review comparison")
    output.mkdir(parents=True)
    (output / "supplementary_citations.json").write_text(json.dumps(supplementary, indent=2) + "\n")
    adjudications = []
    agreement = Counter()
    for cid in sorted(cases):
        differences = [f for f in FIELDS if len({r[cid][f] for r in reviews}) > 1]
        agreement.update(f for f in FIELDS if f not in differences)
        adjudications.append(
            dict(
                case_id=cid,
                differing_fields=";".join(differences),
                adjudication="requires_original_source_or_expert_review",
                expert_gold="false",
                rationale="Model agreement cannot establish native senses, pronunciation or lexeme history.",
                **{f"{i}_{f}": review[cid][f] for i, review in enumerate(reviews) for f in FIELDS},
            )
        )
    with (output / "disagreements.csv").open("w") as h:
        writer = csv.DictWriter(h, fieldnames=list(adjudications[0]))
        writer.writeheader()
        writer.writerows(adjudications)
    summary = dict(
        cases=len(cases),
        expert_adjudications=0,
        supplementary_citations=len(supplementary),
        supplementary_citations_sha256=sha(output / "supplementary_citations.json"),
        id_validation="Worksheet anchors checked; supplementary citations remain unverified by this comparator",
        model_assisted_only=True,
        worksheet_sha256=sha(worksheet),
        reviewer_files={str(p): sha(p) for p in paths},
        agreement_counts=dict(agreement),
        cases_with_disagreement=sum(bool(r["differing_fields"]) for r in adjudications),
        reviewer_counts=[{f: dict(Counter(r[f] for r in review.values())) for f in FIELDS} for review in reviews],
        disagreements_sha256=sha(output / "disagreements.csv"),
    )
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--worksheet", type=Path, required=True)
    p.add_argument("--reviews", type=Path, nargs="+", required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if len(a.reviews) < 2:
        p.error("At least two independent first passes required")
    print(json.dumps(compare(a.worksheet, a.reviews, a.output), indent=2))


if __name__ == "__main__":
    main()
