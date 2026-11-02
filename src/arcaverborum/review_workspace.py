"""Offline linguistic adjudication packets. Decisions never mutate lexical data."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

SCOPE_FIELDS = (
    "field_collection", "original_publication", "edition", "local_variety",
    "historical_stage", "reading_convention",
)
DECISIONS = {"unresolved", "same_lexeme", "homophony", "mapping_error", "reading_error", "mixed_scope"}


def scope_comparability(left, right):
    """A diagnostic for attested witness scopes, not a graph weight or absence.

    Editions/publications can reproduce the same field collection. Their labels
    alone establish neither comparability nor independent confirmation.
    """
    axes = ("field_collection", "local_variety", "historical_stage", "reading_convention")
    if any(left.get(k) and right.get(k) and left[k] != right[k] for k in axes):
        return "different_scope"
    if not all(left.get(k) and right.get(k) for k in axes):
        return "unknown"
    return "matched_scope"


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def packet_from_csv(path, *, reviews=(), native_labels=None):
    path = Path(path)
    inputs = [path, *(Path(p) for p in reviews), *([Path(native_labels)] if native_labels else [])]
    if sum(p.stat().st_size for p in inputs) > 16 * 1024**2:
        raise ValueError("Combined review inputs exceed 16 MiB budget")
    with path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    annotations = {}
    for review in reviews:
        with Path(review).open(newline="") as handle:
            for annotation in csv.DictReader(handle):
                annotations.setdefault(annotation["case_id"], []).append(annotation)
    labels = {}
    if native_labels:
        for row in json.loads(Path(native_labels).read_text()):
            labels.setdefault(row["case_id"], {})[row["side"]] = row["labels"]
    seen = set()
    for row in rows:
        identity = row.get("case_id")
        if not identity or identity in seen:
            raise ValueError("Missing or duplicate case identity")
        seen.add(identity)
        for side in ("a", "b"):
            originals = json.loads(row.get("original_records_" + side) or "[]")
            if not isinstance(originals, list) or not all(isinstance(r, dict) for r in originals):
                raise ValueError("Invalid original evidence")
        row["review_annotations"] = annotations.get(identity, [])
        row["source_parameter_evidence"] = labels.get(identity, {})
        row["case_sha256"] = digest(row)
    packet = {"schema": 1, "cases": rows, "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    packet["packet_sha256"] = digest(packet)
    return packet


def validate_decisions(packet, submission):
    """Fail closed on stale evidence, invented record scopes and absent provenance."""
    unsigned = {k: v for k, v in packet.items() if k != "packet_sha256"}
    if packet.get("packet_sha256") != digest(unsigned):
        raise ValueError("Packet seal mismatch")
    if submission.get("schema") != 1 or submission.get("packet_sha256") != packet["packet_sha256"]:
        raise ValueError("Submission belongs to a different packet")
    cases = {r["case_id"]: r for r in packet["cases"]}
    seen = set()
    for decision in submission.get("decisions", []):
        identity = decision.get("case_id")
        if identity not in cases or identity in seen:
            raise ValueError("Unknown or duplicate reviewed case")
        seen.add(identity)
        case = cases[identity]
        if decision.get("case_sha256") != case["case_sha256"]:
            raise ValueError("Case evidence changed")
        if (decision.get("decision") not in DECISIONS
                or decision.get("reviewer_type") not in {"human", "model_assisted"}
                or not decision.get("reviewer", "").strip()
                or not decision.get("evidence_locator", "").strip()
                or not decision.get("rationale", "").strip()):
            raise ValueError("Decision lacks explicit reviewer, evidence or rationale")
        originals = [r for side in ("a", "b") for r in json.loads(case["original_records_" + side])]
        ids = {r.get("source_form_id") for r in originals} - {None, ""}
        scoped = set()
        for scope in decision.get("record_scopes", []):
            sid = scope.get("source_form_id")
            if sid not in ids or sid in scoped:
                raise ValueError("Unknown or duplicate original record scope")
            scoped.add(sid)
            if (not scope.get("evidence_locator", "").strip()
                    or any(not isinstance(scope.get(k, ""), str) for k in SCOPE_FIELDS)
                    or not any(scope.get(k, "").strip() for k in SCOPE_FIELDS)):
                raise ValueError("Scope assertion requires a locator and at least one known scope")
    # Human provenance is not a claim of specialist competence or independent gold.
    return {"decisions": len(seen), "human_expert_gold": 0, "automatic_lexical_changes": 0}


def render_workspace(packet):
    payload = json.dumps(packet, ensure_ascii=False).replace("<", "\\u003c")
    template = Path(__file__).parent / "data/review_workspace.html"
    return template.read_text().replace("__ARCA_REVIEW_PACKET__", payload)
