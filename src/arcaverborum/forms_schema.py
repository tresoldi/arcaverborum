"""Shared forms infrastructure: output field list, quality scoring, parameter index.

Used by variety.build_one (per-variety emit), aggregate (union), and
build.py (batch update). Extracted from aggregate.py so the three
consumers import from a public module instead of reaching into private
functions across the seam.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

FORMS_OUT_FIELDS = (
    "av_id", "Glottocode", "Variety_Name",
    "concept_id", "concept_label", "Concepticon_ID",
    "Value", "Form", "Segments", "Segments_Source",
    "Cognacy", "canonical_cognate_id",
    "Alignment", "Morpheme_Index", "Segment_Slice", "Doubt",
    "Cognate_Detection_Method", "Cognate_Source",
    "Loan", "Comment",
    "transcription_source", "cognate_source",
    "source_form_id", "source_language_id", "source_parameter_id",
    "bibtex_key", "quality_score", "tier",
)


def form_quality_score(row: dict, base_score: float) -> float:
    """Per-form quality: combines variety-level forms_score with per-form
    feature presence. Bounded to [0, 1].
    """
    score = base_score
    bonus = 0.0
    if (row.get("Segments") or "").strip():
        bonus += 0.05
    if (row.get("Concepticon_ID") or "").strip():
        bonus += 0.05
    if (row.get("Cognacy") or "").strip():
        bonus += 0.05
    if (row.get("Alignment") or "").strip():
        bonus += 0.03
    if (row.get("Cognate_Detection_Method") or "").strip().lower() == "expert":
        bonus += 0.05
    return min(score + bonus * (1 - score), 1.0)


def load_parameter_index(parameters_path: Path) -> dict[str, tuple[str, str]]:
    """Build {Parameter_ID: (Concepticon_ID, Concepticon_Gloss)} lookup."""
    if not parameters_path.exists():
        return {}
    df = pd.read_csv(
        parameters_path, dtype=str, keep_default_na=False,
        usecols=lambda c: c in {"ID", "Concepticon_ID", "Concepticon_Gloss"},
    )
    if "ID" not in df.columns:
        return {}
    cid_col = df.get("Concepticon_ID", pd.Series([""] * len(df)))
    gloss_col = df.get("Concepticon_Gloss", pd.Series([""] * len(df)))
    return {
        pid: (str(cid_col.iat[i]).strip(), str(gloss_col.iat[i]).strip())
        for i, pid in enumerate(df["ID"])
    }
