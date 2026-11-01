"""Add native questionnaire labels without presenting them as lexical sense validation."""

import argparse
import csv
import json
from pathlib import Path

from arcaverborum.colexification import sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--worksheet", type=Path, required=True)
    p.add_argument("--parameters", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    rows = list(csv.DictReader(a.worksheet.open()))
    wanted = {
        r["source_parameter_id"]
        for row in rows
        for side in ["a", "b"]
        for r in json.loads(row["original_records_" + side])
        if r["source_parameter_id"]
    }
    labels = {}
    for row in csv.DictReader(a.parameters.open()):
        if row["ID"] in wanted:
            payload = {k: row.get(k, "") for k in ["ID", "Dataset", "Name", "Concepticon_ID"]}
            if row["ID"] in labels and labels[row["ID"]] != payload:
                raise ValueError("Ambiguous native parameter label: " + row["ID"])
            labels[row["ID"]] = payload
    if a.output.exists():
        raise ValueError("Refuse to overwrite evidence supplement")
    a.output.mkdir(parents=True)
    evidence = []
    for row in rows:
        for side in ["a", "b"]:
            ids = sorted({r["source_parameter_id"] for r in json.loads(row["original_records_" + side])})
            evidence.append(
                dict(
                    case_id=row["case_id"],
                    side=side,
                    labels=[labels[pid] for pid in ids if pid in labels],
                    missing_parameter_ids=[pid for pid in ids if pid and pid not in labels],
                    evidence_type="native_questionnaire_label_not_independent_lexeme_gloss",
                )
            )
    target = a.output / "native_labels.json"
    target.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n")
    summary = dict(
        worksheet_sha256=sha(a.worksheet),
        parameters_sha256=sha(a.parameters),
        native_labels_sha256=sha(target),
        cases=len(rows),
        target_parameters=len(wanted),
        recovered_parameters=len(labels),
        independent_expert_adjudications=0,
        caveat="A questionnaire prompt is not proof of the exact meaning of a recorded lexeme.",
    )
    (a.output / "manifest.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
