"""Reviewed meaning-local raw labels are notes, not extra global cognate sets."""

from __future__ import annotations

import csv
import hashlib
import json
from functools import lru_cache
from pathlib import Path

POLICIES = Path(__file__).resolve().parents[1] / "data/cognacy_scope_policies.csv"
RAW = Path(__file__).resolve().parents[3] / "raw/lexibank"


@lru_cache(maxsize=16)
def emission_memberships(dataset, policies_path, raw_root):
    with policies_path.open() as handle:
        policy = next((r for r in csv.DictReader(handle)
                       if r["dataset"] == dataset and r.get("emission_guard") == "true"), None)
    if policy is None:
        return None
    cldf = raw_root / dataset / "cldf"
    for table, key in [("forms.csv", "forms_sha256"), ("cognates.csv", "cognates_sha256")]:
        with (cldf / table).open("rb") as handle:
            if hashlib.file_digest(handle, "sha256").hexdigest() != policy[key]:
                raise ValueError("Reviewed cognacy emission snapshot changed: " + dataset)
    members, raw = {}, {}
    with (cldf / "forms.csv").open(newline="") as handle:
        for row in csv.DictReader(handle):
            raw[dataset + "_" + row["ID"]] = row.get("Cognacy", "")
    with (cldf / "cognates.csv").open(newline="") as handle:
        for row in csv.DictReader(handle):
            fid, cog = dataset + "_" + row["Form_ID"], dataset + "_" + row["Cognateset_ID"]
            if fid not in raw:
                raise ValueError("Structured cognate refers to missing native form")
            values = members.setdefault(fid, [])
            if cog not in values:
                values.append(cog)
    return members, raw


def apply_emission_policy(forms, dataset):
    """Repair cached unions using per-form native judgments, preserving raw labels as notes.

    This is also needed before a fresh intake is available: changing an ingest
    policy alone cannot repair already cached/generated memberships.
    """
    data = emission_memberships(dataset, POLICIES, RAW)
    if data is None or forms.empty:
        return forms
    members, originals = data
    result = forms.copy()
    for index, row in result.iterrows():
        fid = row.get("ID", "")
        if fid not in originals:
            raise ValueError("Unknown form under reviewed cognacy emission policy")
        target = members.get(fid, [])
        old = [x.strip() for x in row.get("Cognacy", "").split(";") if x.strip()]
        raw = dataset + "_" + originals[fid] if originals[fid] else ""
        # An old cache unions the raw field and structured memberships. A new
        # ingest already contains only the structured memberships. Anything
        # else needs a separate review; do not clobber a curated override.
        expected = set(target) | ({raw} if raw else set())
        if set(old) not in (expected, set(target)):
            raise ValueError("Cached cognacy differs from reviewed raw/structured union: " + fid)
        if old == target:
            continue
        result.at[index, "Cognacy"] = ";".join(target)
        note = "Reviewed source cognacy scope: " + json.dumps(dict(
            raw_cognacy=originals[fid], previous_memberships=row.get("Cognacy", ""),
            policy="structured_only", rationale="Native raw labels are not additional global cognate sets; "
            "retain every structured membership of this exact source form, including multiple assignments."),
            ensure_ascii=False, sort_keys=True)
        result.at[index, "Comment"] = "; ".join(filter(None, [row.get("Comment", ""), note]))
    return result


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
