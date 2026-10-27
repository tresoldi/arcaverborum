"""Reviewed meaning-local raw labels are notes, not extra global cognate sets."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

POLICIES = Path(__file__).resolve().parents[1] / "data/cognacy_scope_policies.csv"


def apply_policy(forms, cognates, dataset, cldf):
    with POLICIES.open() as handle:
        policies = {r["dataset"]: r for r in csv.DictReader(handle)}
    policy = policies.get(dataset)
    if not policy:
        return forms
    for table, key in [("forms.csv", "forms_sha256"), ("cognates.csv", "cognates_sha256")]:
        with (cldf / table).open("rb") as handle:
            if hashlib.file_digest(handle, "sha256").hexdigest() != policy[key]:
                raise ValueError("Reviewed cognacy scope snapshot changed: " + dataset)
    if cognates.empty or "Cognacy" not in forms:
        raise ValueError("Structured cognacy scope requires its source CognateTable")
    result = forms.copy()
    if "Comment" not in result:
        result["Comment"] = ""
    for i, row in result.iterrows():
        if row.get("Cognacy", ""):
            note = dict(
                raw_cognacy=row["Cognacy"], scope_policy="structured_only", cognates_sha256=policy["cognates_sha256"]
            )
            result.at[i, "Comment"] = "; ".join(
                filter(
                    None,
                    [
                        row.get("Comment", ""),
                        "Structured cognacy evidence: " + json.dumps(note, ensure_ascii=False, sort_keys=True),
                    ],
                )
            )
    result["Cognacy"] = ""
    return result
