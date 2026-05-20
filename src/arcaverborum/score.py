"""Composite quality scoring per (variety, source, block).

Two blocks are scored independently for each (variety, source) pair:

* forms_block — the transcription/segmentation side.
* cognates_block — the cognate-judgment side. A source only competes for
  the cognates block when it also provides forms for the variety (the
  two-block rule: cognate IDs are tied to specific form strings).

Signals are computed from intake forms; a per-block weighted sum produces
a score in [0, 1]. Weights live in data/score_weights.yaml so they are
auditable and tunable.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import yaml

logger = logging.getLogger(__name__)

WEIGHTS_PATH = Path(__file__).parent / "data" / "score_weights.yaml"


@dataclass(slots=True)
class Signals:
    forms_count: int = 0
    distinct_concepts: int = 0
    has_segments: float = 0.0
    clts_compliant: float = 0.0
    concepticon_mapped: float = 0.0
    loan_annotated: float = 0.0
    has_cognates: float = 0.0
    expert: float = 0.0
    alignment_present: float = 0.0
    partial_cognacy: float = 0.0

    def to_dict(self) -> dict[str, float | int]:
        return {
            "forms_count": self.forms_count,
            "distinct_concepts": self.distinct_concepts,
            "has_segments": self.has_segments,
            "clts_compliant": self.clts_compliant,
            "concepticon_mapped": self.concepticon_mapped,
            "loan_annotated": self.loan_annotated,
            "has_cognates": self.has_cognates,
            "expert": self.expert,
            "alignment_present": self.alignment_present,
            "partial_cognacy": self.partial_cognacy,
        }


def load_weights(path: Path = WEIGHTS_PATH) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _non_empty(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip().ne("")


def _clts_fraction(segments: pd.Series, validator) -> float:
    """Fraction of forms whose Segments look like valid IPA per merkmal.

    Uses a small per-group sample to keep cost bounded. Returns 0 if no
    non-empty Segments at all.
    """
    if validator is None:
        return 0.0
    seg = segments.fillna("").astype(str).str.strip()
    seg = seg[seg.ne("")]
    if seg.empty:
        return 0.0
    sample = seg.sample(min(50, len(seg)), random_state=0) if len(seg) > 50 else seg
    ok = 0
    total = 0
    for s in sample:
        tokens = [t for t in s.split() if t and t not in ("+", "_")]
        if not tokens:
            continue
        total += 1
        if all(validator(tok) for tok in tokens):
            ok += 1
    return ok / total if total else 0.0


def compute_signals_for_group(group: pd.DataFrame, clts_validator=None) -> Signals:
    """Compute signals from forms belonging to a single (variety, dataset)."""
    n = len(group)
    if n == 0:
        return Signals()

    sig = Signals(forms_count=n)

    if "Concepticon_ID" in group.columns:
        cids = group["Concepticon_ID"].fillna("").astype(str).str.strip()
        cids = cids[cids.ne("")]
        sig.distinct_concepts = cids.nunique()
        sig.concepticon_mapped = len(cids) / n
    elif "Concepticon_Gloss" in group.columns:
        gl = group["Concepticon_Gloss"].fillna("").astype(str).str.strip()
        gl = gl[gl.ne("")]
        sig.distinct_concepts = gl.nunique()
        sig.concepticon_mapped = len(gl) / n

    if "Segments" in group.columns:
        sig.has_segments = _non_empty(group["Segments"]).mean()
        sig.clts_compliant = _clts_fraction(group["Segments"], clts_validator)

    if "Loan" in group.columns:
        loan = group["Loan"].fillna("").astype(str).str.strip().str.lower()
        sig.loan_annotated = 1.0 if loan.isin({"true", "false"}).any() else 0.0

    if "Cognacy" in group.columns:
        cog = group["Cognacy"].fillna("").astype(str).str.strip()
        sig.has_cognates = (cog.ne("").mean())

    if "Cognate_Detection_Method" in group.columns:
        cdm = group["Cognate_Detection_Method"].fillna("").astype(str).str.strip().str.lower()
        sig.expert = (cdm == "expert").mean()

    if "Alignment" in group.columns:
        sig.alignment_present = _non_empty(group["Alignment"]).mean()

    has_morpheme = "Morpheme_Index" in group.columns and _non_empty(group["Morpheme_Index"]).any()
    has_slice = "Segment_Slice" in group.columns and _non_empty(group["Segment_Slice"]).any()
    sig.partial_cognacy = 1.0 if (has_morpheme or has_slice) else 0.0

    return sig


def _form_density(forms_count: int) -> float:
    if forms_count <= 0:
        return 0.0
    # log-scaled, saturates around 500 forms.
    return min(math.log10(forms_count + 1) / math.log10(500), 1.0)


def score_forms_block(sig: Signals, weights: dict) -> float:
    w = weights["forms_block"]
    contribs = {
        "has_segments": sig.has_segments,
        "clts_compliant": sig.clts_compliant,
        "concepticon_mapped": sig.concepticon_mapped,
        "concept_coverage": min(sig.distinct_concepts / 200.0, 1.0),
        "loan_annotated": sig.loan_annotated,
        "form_density": _form_density(sig.forms_count),
    }
    total = sum(w.get(k, 0.0) for k in contribs)
    if total <= 0:
        return 0.0
    return sum(w.get(k, 0.0) * v for k, v in contribs.items()) / total


def score_cognates_block(sig: Signals, weights: dict) -> float:
    if sig.has_cognates <= 0:
        return 0.0
    w = weights["cognates_block"]
    contribs = {
        "has_cognates": sig.has_cognates,
        "expert": sig.expert,
        "alignment_present": sig.alignment_present,
        "partial_cognacy": sig.partial_cognacy,
    }
    total = sum(w.get(k, 0.0) for k in contribs)
    if total <= 0:
        return 0.0
    return sum(w.get(k, 0.0) * v for k, v in contribs.items()) / total


def tier_for(score: float, weights: dict) -> str:
    t = weights["tiers"]
    if score >= t["gold"]:
        return "gold"
    if score >= t["silver"]:
        return "silver"
    if score >= t["bronze"]:
        return "bronze"
    return "copper"
