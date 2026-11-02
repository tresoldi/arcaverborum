"""Account for every active concept without treating retrieval candidates as decisions."""

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from arcaverborum.wordnet import DATA, load_bundle, read_csv


def audit(output, review_batch="PROJ-03-2026-11-02"):
    bundle = load_bundle()
    concepts = read_csv(DATA / "concepts.csv")
    rows = []
    for concept in concepts:
        if concept["status"] != "active":
            continue
        entry = bundle["concepts"][concept["concept_id"]]
        accepted = [r for r in entry["links"] if r["status"] == "accepted"]
        batch = [r for r in accepted if r.get("reviewer_type", "").startswith("model_assisted")]
        rows.append(dict(concept_id=concept["concept_id"], concept_sha256=entry["concept_sha256"],
                         review_state="model_assisted_definition_review" if batch else
                         "earlier_accepted_links" if accepted else "held" if entry.get("hold_reason") else
                         "pending_sense_review" if entry["candidates"] else "inventory_gap",
                         exact=sum(r["relation"] == "exact" for r in accepted),
                         broader=sum(r["relation"] == "broader" for r in accepted),
                         narrower=sum(r["relation"] == "narrower" for r in accepted),
                         related=sum(r["relation"] == "related" for r in accepted),
                         inherited_associations=sum(r["status"] == "source_association" for r in entry["links"]),
                         unreviewed_candidates=len(entry["candidates"]),
                         hold_reason=entry.get("hold_reason", "")))
    output.mkdir(parents=True, exist_ok=False)
    path = output / "active-catalog.csv"
    with path.open("w") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    summary = dict(active_concepts=len(rows), states=dict(Counter(r["review_state"] for r in rows)),
                   accepted_concepts=sum(bool(sum(r[k] for k in ("exact", "broader", "narrower", "related")))
                                         for r in rows),
                   review_batch=review_batch,
                   new_review_links=sum(r.get("review_batch") == review_batch
                                        for e in bundle["concepts"].values() for r in e["links"]),
                   human_expert_adjudications=0, lexical_records_remapped_by_wordnet=0,
                   links=bundle["summary"]["links"],
                   qualification="All active concepts screened/accounted for; pending candidates are not "
                   "definition-level reviews or accepted equivalences. Typed containment is directional, "
                   "not a calibrated confidence score. Catalog conflicts require native-sense lineage review.",
                   input_hashes={name: hashlib.sha256((DATA / "wordnet" / name).read_bytes()).hexdigest()
                                 for name in ("review.csv", "holds.json", "bundle.json")},
                   coverage_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--review-batch", default="PROJ-03-2026-11-02")
    args = p.parse_args()
    audit(args.output, args.review_batch)
