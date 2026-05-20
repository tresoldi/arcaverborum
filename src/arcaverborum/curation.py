"""Curation report: rank varieties by how much hand-curation would help.

Surfaces the weak end of the database (copper tier, high `unclean` segment
fraction, low concept coverage) so curation effort can be aimed where it pays
off — e.g. broad phonological transcription for ancient IE languages.

Reads the aggregate product (`output/aggregate/forms.csv` + `varieties.csv`),
so run `build.py aggregate` first.

Tone is deferred. ~37% of `unclean` forms are blocked only by tone marks
(digits / superscripts / Chao letters) that merkmal does not yet tokenise.
That fix is being handled in merkmal upstream, not by hand — so the report
carries a `pct_tone_blocked` column to keep the eventual recovery measurable,
and those forms are not manual-curation targets today. Filter or de-prioritise
tone-heavy varieties when picking what to curate now.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

import pandas as pd

from arcaverborum.score import _form_density

logger = logging.getLogger(__name__)

# Heuristic: in CLDF segment strings bare digits 0-5, tone superscripts/
# subscripts, and Chao tone letters almost always encode tone. Marks merkmal
# (phoible) does not tokenise → the form lands in `unclean`.
TONE_RE = re.compile(r"[0-5⁰¹²³⁴⁵"
                     r"₀₁₂₃₄₅"
                     r"˥˦˧˨˩]")

# Columns emitted to curation.csv, in order.
REPORT_FIELDS = (
    "av_id", "name", "glottocode", "family", "macroarea", "source_class",
    "transcription_source", "cognate_source", "tier", "pinned",
    "forms_score", "cognates_score",
    "n_forms", "n_concepts", "concept_coverage",
    "pct_clean", "pct_resegmented", "pct_unclean", "pct_tone_blocked",
    "n_unclean", "n_tone_blocked", "pct_cognacy",
    "priority_score",
)


def _source_class(source: str) -> str:
    s = (source or "").strip().lower()
    if s == "gled":
        return "GLED"
    if s == "wiktionary" or s.startswith("wikt"):
        return "Wiktionary"
    return "Lexibank"


def build_curation_report(
    forms: pd.DataFrame, varieties: pd.DataFrame
) -> tuple[list[dict], dict]:
    """Compute per-variety curation metrics + a database-wide summary.

    `forms` needs columns av_id, Segments, Segments_Source, Concepticon_ID,
    Cognacy. `varieties` is the aggregate varieties.csv. Returns
    (rows sorted by descending priority, summary dict).

    `priority_score = form_density(n_forms) * (1 - forms_score)` — a variety
    with substantial data and a weak forms-block ranks highest; tiny or
    already-good varieties rank low.
    """
    seg = forms["Segments"].fillna("").astype(str)
    ss = forms["Segments_Source"].fillna("").astype(str)
    cid = forms["Concepticon_ID"].fillna("").astype(str).str.strip()
    cog = forms["Cognacy"].fillna("").astype(str).str.strip()
    is_unclean = ss.eq("unclean")

    work = pd.DataFrame({
        "av_id": forms["av_id"].astype(str),
        "_unclean": is_unclean,
        "_reseg": ss.eq("resegmented"),
        "_source": ss.eq("source"),
        "_tone_blocked": is_unclean & seg.str.contains(TONE_RE, na=False),
        "_cid": cid,
        "_has_cid": cid.ne(""),
        "_has_cog": cog.ne(""),
    })

    g = work.groupby("av_id", sort=False)
    per = g.agg(
        n_forms=("_unclean", "size"),
        n_unclean=("_unclean", "sum"),
        n_resegmented=("_reseg", "sum"),
        n_source=("_source", "sum"),
        n_tone_blocked=("_tone_blocked", "sum"),
        n_cognacy=("_has_cog", "sum"),
    )
    n_concepts = (
        work[work["_has_cid"]].groupby("av_id")["_cid"].nunique()
    )
    per["n_concepts"] = n_concepts.reindex(per.index).fillna(0).astype(int)

    v = varieties.set_index("av_id")
    per = per.join(
        v[["Name", "Glottocode", "Family", "Macroarea",
           "transcription_source", "cognate_source", "pinned",
           "forms_score", "cognates_score", "tier"]],
        how="left",
    )
    per["forms_score"] = pd.to_numeric(per["forms_score"], errors="coerce").fillna(0.0)
    per["cognates_score"] = pd.to_numeric(per["cognates_score"], errors="coerce").fillna(0.0)

    per["concept_coverage"] = (per["n_concepts"] / 200.0).clip(upper=1.0).round(4)
    per["pct_clean"] = (per["n_source"] / per["n_forms"]).round(4)
    per["pct_resegmented"] = (per["n_resegmented"] / per["n_forms"]).round(4)
    per["pct_unclean"] = (per["n_unclean"] / per["n_forms"]).round(4)
    per["pct_tone_blocked"] = (per["n_tone_blocked"] / per["n_forms"]).round(4)
    per["pct_cognacy"] = (per["n_cognacy"] / per["n_forms"]).round(4)
    per["priority_score"] = (
        per["n_forms"].map(_form_density) * (1.0 - per["forms_score"])
    ).round(4)
    per["source_class"] = per["transcription_source"].fillna("").map(_source_class)

    per = per.reset_index().rename(
        columns={"Name": "name", "Glottocode": "glottocode",
                 "Family": "family", "Macroarea": "macroarea"}
    )
    per = per.sort_values(
        ["priority_score", "n_unclean"], ascending=[False, False]
    )
    rows = [
        {k: r[k] for k in REPORT_FIELDS}
        for r in per.fillna("").to_dict("records")
    ]

    summary = _summarize(per, varieties)
    return rows, summary


def _summarize(per: pd.DataFrame, varieties: pd.DataFrame) -> dict:
    n_forms = int(per["n_forms"].sum())
    n_source = int(per["n_source"].sum())
    n_reseg = int(per["n_resegmented"].sum())
    n_unclean = int(per["n_unclean"].sum())
    n_tone = int(per["n_tone_blocked"].sum())

    cs = varieties["cognate_source"].fillna("")
    ts = varieties["transcription_source"].fillna("")
    cross = int(((cs != "") & (cs != ts)).sum())

    return {
        "total_varieties": int(len(per)),
        "total_forms": n_forms,
        "segments_source": {
            "source": {"forms": n_source, "pct": round(n_source / n_forms, 4)},
            "resegmented": {"forms": n_reseg, "pct": round(n_reseg / n_forms, 4)},
            "unclean": {"forms": n_unclean, "pct": round(n_unclean / n_forms, 4)},
        },
        "tone_blocked": {
            "forms": n_tone,
            "pct_of_unclean": round(n_tone / n_unclean, 4) if n_unclean else 0.0,
            "pct_of_forms": round(n_tone / n_forms, 4) if n_forms else 0.0,
            "note": "deferred to merkmal upstream; not a manual-curation target",
        },
        "tier_distribution": per["tier"].value_counts().to_dict(),
        "source_class_distribution": per["source_class"].value_counts().to_dict(),
        "cross_source_cognate_varieties": cross,
        "forms_score": {
            "median": round(float(per["forms_score"].median()), 4),
            "mean": round(float(per["forms_score"].mean()), 4),
            "min": round(float(per["forms_score"].min()), 4),
        },
        "top_curation_targets": [
            {"av_id": r["av_id"], "name": r["name"], "tier": r["tier"],
             "priority_score": r["priority_score"], "n_forms": r["n_forms"],
             "pct_unclean": r["pct_unclean"], "pct_tone_blocked": r["pct_tone_blocked"]}
            for r in per.head(20).to_dict("records")
        ],
    }


def write_curation_report(rows: list[dict], summary: dict, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "curation.csv"
    pd.DataFrame(rows, columns=list(REPORT_FIELDS)).to_csv(csv_path, index=False)
    json_path = output_dir / "curation_summary.json"
    json_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    logger.info("Wrote curation report (%d varieties) to %s", len(rows), csv_path)
    logger.info("Wrote curation summary to %s", json_path)
