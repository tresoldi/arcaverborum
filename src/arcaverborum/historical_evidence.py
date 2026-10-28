"""Source-scoped historical reading metadata, independent of segment origin."""

from __future__ import annotations

import csv
import json
from pathlib import Path

BASES = {
    "unspecified_historical_reading",
    "automatic_transcription_conversion",
    "source_reported_reconstruction",
    "source_reported_historical_reading",
    "orthographic_transcription_only",
    "profile_inferred_broad_reading",
    "upstream_profile_conversion",
    "source_reported_pronunciation",
    "source_reported_phonemic_citation",
}


def annotate(rows, custom_dir: Path):
    for name, label in [
        ("historical_evidence.csv", "Historical reading evidence"),
        ("reading_evidence.csv", "Reading evidence"),
    ]:
        _annotate(rows, custom_dir / name, label)
    return rows


def _annotate(rows, path, label):
    if not path.exists():
        return rows
    with path.open() as f:
        rules = list(csv.DictReader(f))
    seen = set()
    for rule in rules:
        key = rule["source"], rule.get("source_language_id", ""), rule.get("segments_source", "")
        if key in seen or not key[0] or rule["reading_basis"] not in BASES or not rule.get("notes"):
            raise ValueError("Invalid or duplicate historical reading rule")
        seen.add(key)
    for row in rows:
        matches = [
            r
            for r in rules
            if r["source"] == row["transcription_source"]
            and (not r.get("source_language_id") or r["source_language_id"] == row["source_language_id"])
            and (not r.get("segments_source") or r["segments_source"] == row.get("Segments_Source"))
        ]
        exact = [r for r in matches if r.get("source_language_id")]
        matches = exact or matches
        if len(matches) > 1:
            raise ValueError("Ambiguous historical reading rule")
        if matches:
            evidence = {k: v for k, v in matches[0].items() if k not in {"source", "source_language_id"} and v}
            row["Comment"] = "; ".join(
                filter(
                    None,
                    [
                        row.get("Comment", ""),
                        label + ": " + json.dumps(evidence, ensure_ascii=False, sort_keys=True),
                    ],
                )
            )
    return rows
