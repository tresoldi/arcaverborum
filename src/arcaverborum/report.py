"""Selection report: per-variety provenance + aggregate coverage."""

from __future__ import annotations

import json
import logging
from collections import Counter
from pathlib import Path

from arcaverborum.catalog import Variety
from arcaverborum.selection import Selection

logger = logging.getLogger(__name__)


def build_report(
    selections: dict[str, Selection],
    catalog: dict[str, Variety],
    build_stats: dict,
) -> dict:
    by_tier: Counter[str] = Counter()
    by_pinned: Counter[bool] = Counter()
    by_family: Counter[str] = Counter()
    by_macroarea: Counter[str] = Counter()
    by_source: Counter[str] = Counter()
    by_cog_source: Counter[str] = Counter()
    cross_source_count = 0

    per_variety: list[dict] = []

    for av_id in sorted(selections):
        sel = selections[av_id]
        v = catalog.get(av_id)
        family = (v.family if v else "") or "Unknown"
        macroarea = (v.macroarea if v else "") or "Unknown"

        if not sel.transcription_source:
            continue

        by_tier[sel.tier] += 1
        by_pinned[sel.pinned] += 1
        by_family[family] += 1
        by_macroarea[macroarea] += 1
        by_source[sel.transcription_source] += 1
        if sel.cognate_source:
            by_cog_source[sel.cognate_source] += 1
        if sel.cognate_source and sel.cognate_source != sel.transcription_source:
            cross_source_count += 1

        per_variety.append({
            "av_id": av_id,
            "glottocode": v.glottocode if v else "",
            "name": v.name if v else "",
            "family": family,
            "macroarea": macroarea,
            "transcription_source": sel.transcription_source,
            "cognate_source": sel.cognate_source,
            "pinned": sel.pinned,
            "forms_score": round(sel.forms_score, 4),
            "cognates_score": round(sel.cognates_score, 4),
            "tier": sel.tier,
            "rationale": sel.rationale,
            "candidates": [
                {"dataset": ds, "forms_score": round(fs, 4), "cognates_score": round(cs, 4)}
                for (ds, fs, cs) in sel.candidates
            ],
        })

    return {
        "totals": {
            "varieties_selected": len(per_variety),
            "varieties_with_cognates": sum(
                1 for s in selections.values()
                if s.transcription_source and s.cognate_source
            ),
            "manually_pinned": by_pinned.get(True, 0),
            "auto_selected": by_pinned.get(False, 0),
            "cross_source_cognates": cross_source_count,
        },
        "tier_distribution": dict(by_tier),
        "by_family": dict(by_family.most_common(30)),
        "by_macroarea": dict(by_macroarea),
        "top_transcription_sources": dict(by_source.most_common(30)),
        "top_cognate_sources": dict(by_cog_source.most_common(30)),
        "build_stats": {k: v for k, v in build_stats.items() if k != "bibtex_keys_used"},
        "varieties": per_variety,
    }


def write_report(report: dict, output_dir: Path) -> None:
    out_path = output_dir / "selection_report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Wrote selection report to %s", out_path)
