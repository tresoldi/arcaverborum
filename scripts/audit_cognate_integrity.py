"""Audit native cognacy membership and export small source-separated downstream fixtures.

Unmatched raw labels are conventions to investigate, never automatic repairs.
"""

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024**2), b""):
            h.update(b)
    return h.hexdigest()


def audit(root, datasets):
    reports, fixtures = [], []
    for dataset in datasets:
        directory = root / "raw/lexibank" / dataset / "cldf"
        paths = {name: directory / name for name in ("forms.csv", "cognates.csv")}
        ids, raw_labels = set(), Counter()
        samples = {}
        with paths["forms.csv"].open(newline="") as f:
            for row in csv.DictReader(f):
                if row["ID"] in ids:
                    raise ValueError(f"Duplicate source form: {dataset}/{row['ID']}")
                ids.add(row["ID"])
                raw_labels.update(x.strip() for x in row.get("Cognacy", "").split(";") if x.strip())
                if len(samples) < 3 and row.get("Cognacy"):
                    samples[row["ID"]] = {k: row.get(k, "") for k in (
                        "ID", "Language_ID", "Parameter_ID", "Value", "Form", "Segments", "Cognacy",
                        "Source", "Comment", "Alignment", "Morpheme_Index", "Segment_Slice")}
        declared, methods, missing, judgments = set(), Counter(), 0, 0
        sample_judgments = defaultdict(list)
        with paths["cognates.csv"].open(newline="") as f:
            for row in csv.DictReader(f):
                judgments += 1
                missing += row["Form_ID"] not in ids
                declared.add(row["Cognateset_ID"])
                methods[row.get("Cognate_Detection_Method", "") or "undeclared"] += 1
                if row["Form_ID"] in samples:
                    sample_judgments[row["Form_ID"]].append(row)
        hashes = {name: sha(path) for name, path in paths.items()}
        reports.append(dict(dataset=dataset, source_forms=len(ids), structured_judgments=judgments,
                            missing_form_references=missing, distinct_raw_labels=len(raw_labels),
                            distinct_structured_labels=len(declared),
                            raw_labels_not_structured=sum(n for k, n in raw_labels.items() if k not in declared),
                            methods=dict(methods), inputs=hashes,
                            decision="Retain source namespaces and structured judgments; no raw-label "
                            "reconciliation or alignment/slice repair without source-specific evidence."))
        for identity, row in samples.items():
            fixtures.append(dict(dataset=dataset, source_form=row, judgments=sample_judgments[identity],
                                 input_sha256=hashes, namespace=dataset,
                                 equivalence_scope="Source-defined; no cross-source or cross-meaning bridge inferred",
                                 reading_mutated=False,
                                 phonological_input_eligible=bool(row["Segments"]),
                                 downstream_contract="Retain whole cited form and source segmentation. If reading "
                                 "changes, revalidate alignments and morpheme/segment slices; "
                                 "never carry them blindly."))
    return {"schema": 1, "sources": reports, "fixtures": fixtures, "automatic_repairs": 0}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dataset", action="append", required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        p.error("Use a new evidence path; never overwrite an earlier audit")
    result = audit(ROOT, a.dataset)
    a.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"sources": len(result["sources"]), "fixtures": len(result["fixtures"]),
                      "missing_form_references": sum(r["missing_form_references"] for r in result["sources"])}))
