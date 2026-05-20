"""Selection: pin overrides + auto-pick + tier bands.

For each variety in the catalog, decides:
  * transcription_source: which dataset's forms to emit.
  * cognate_source: which dataset's cognate judgments to use. In v1, when
    cognate_source != transcription_source, the discrepancy is recorded
    in the selection report but the emitted cognates still come from
    transcription_source — cross-source cognate relabeling is deferred
    until canonical_cognate_id is populated.
  * tier band: gold/silver/bronze/copper.

Pinned varieties win regardless of score. Auto-picked varieties use the
best per-block score among datasets in the configured universe.
"""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from arcaverborum.phonology import is_valid_grapheme
from arcaverborum.score import (
    Signals,
    compute_signals_for_group,
    score_cognates_block,
    score_forms_block,
    tier_for,
)

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent / "data"
SELECTION_CSV = DATA_DIR / "selection.csv"

# Source priority floor: lower number = preferred. Lexibank datasets are
# priority 1; GLED and Wiktionary only win a variety when no
# higher-priority source covers it. Within a priority tier the composite
# score decides.
SOURCE_PRIORITY = {
    "gled": 2,
    "wiktionary": 3,
}
DEFAULT_PRIORITY = 1


def source_priority(dataset: str) -> int:
    return SOURCE_PRIORITY.get(dataset, DEFAULT_PRIORITY)


@dataclass(slots=True)
class Selection:
    av_id: str
    transcription_source: str
    cognate_source: str = ""
    pinned: bool = False
    forms_score: float = 0.0
    cognates_score: float = 0.0
    tier: str = "copper"
    rationale: str = ""
    candidates: list[tuple[str, float, float]] = field(default_factory=list)


def build_universe(datasets_csv: Path) -> set[str]:
    """Return the set of dataset names eligible for auto-selection.

    Universe = union of CORE (curated) and ExpertCognates datasets.
    """
    universe: set[str] = set()
    if not datasets_csv.exists():
        logger.warning("datasets.csv not found at %s", datasets_csv)
        return universe
    with datasets_csv.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("NAME") or "").strip()
            if not name:
                continue
            if (row.get("ExpertCognates") or "").strip().upper() == "TRUE":
                universe.add(name)
            if (row.get("CORE") or "").strip().upper() == "TRUE":
                universe.add(name)
    logger.info("Universe: %d eligible source datasets", len(universe))
    return universe


def load_pins(path: Path = SELECTION_CSV) -> dict[str, dict[str, str]]:
    pins: dict[str, dict[str, str]] = {}
    if not path.exists():
        return pins
    with path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            av = (row.get("av_id") or "").strip()
            ts = (row.get("transcription_source") or "").strip()
            if not av or not ts:
                continue
            pins[av] = {
                "transcription_source": ts,
                "cognate_source": (row.get("cognate_source") or "").strip(),
                "notes": (row.get("notes") or "").strip(),
            }
    logger.info("Loaded %d manual pins from %s", len(pins), path.name)
    return pins


SIGNAL_COLS = [
    "Dataset", "Glottocode", "Segments", "Form",
    "Concepticon_ID", "Concepticon_Gloss",
    "Cognacy", "Cognate_Detection_Method", "Alignment",
    "Morpheme_Index", "Segment_Slice", "Loan",
]


def compute_all_signals(
    forms_paths: Path | list[Path],
    universe: set[str] | None = None,
    use_clts_check: bool = True,
) -> dict[tuple[str, str], Signals]:
    """Group forms by (Glottocode, Dataset) and compute Signals per group.

    `forms_paths` may be a single Path or a list (e.g. intake/lexibank +
    intake/wiktionary). Datasets are kept distinct by their Dataset column.
    """
    if isinstance(forms_paths, (str, Path)):
        forms_paths = [forms_paths]
    frames = []
    for p in forms_paths:
        p = Path(p)
        if not p.exists():
            logger.warning("Intake forms not found, skipping: %s", p)
            continue
        logger.info("Loading %s (signal-relevant columns only)", p)
        frames.append(pd.read_csv(
            p, dtype=str, keep_default_na=False,
            usecols=lambda c: c in SIGNAL_COLS,
        ))
    if not frames:
        raise FileNotFoundError("No intake forms files found")
    df = pd.concat(frames, ignore_index=True)
    df["Glottocode"] = df["Glottocode"].astype(str).str.strip().str.lower()
    df = df[df["Glottocode"].ne("")]
    if universe:
        df = df[df["Dataset"].isin(universe)]

    grouped = df.groupby(["Glottocode", "Dataset"], sort=False)
    n_groups = grouped.ngroups
    logger.info("Computing signals for %d (variety, dataset) groups", n_groups)

    validator = is_valid_grapheme if use_clts_check else None

    out: dict[tuple[str, str], Signals] = {}
    for (gc, ds), group in grouped:
        out[(gc, ds)] = compute_signals_for_group(group, clts_validator=validator)
    return out


def _select_one(
    av_id: str,
    candidates: dict[str, Signals],
    pin: dict[str, str] | None,
    weights: dict,
) -> Selection:
    scored: dict[str, tuple[float, float]] = {
        ds: (score_forms_block(sig, weights), score_cognates_block(sig, weights))
        for ds, sig in candidates.items()
    }
    candlist = sorted(
        ((ds, fs, cs) for ds, (fs, cs) in scored.items()),
        key=lambda x: -x[1],
    )

    if pin:
        ts = pin["transcription_source"]
        cs_name = pin.get("cognate_source") or ts
        if ts not in scored:
            return Selection(
                av_id=av_id,
                transcription_source=ts,
                cognate_source=cs_name,
                pinned=True,
                tier="copper",
                rationale=f"pin invalid: {ts} has no data for this variety",
                candidates=candlist,
            )
        forms_score = scored[ts][0]
        cog_score = scored.get(cs_name, (0.0, 0.0))[1]
        gold = weights["tiers"]["gold"]
        tier = "gold" if forms_score >= gold and (cog_score >= gold or cog_score == 0.0) else "silver"
        rationale = f"pinned: forms={ts} ({forms_score:.2f}), cognates={cs_name or '—'} ({cog_score:.2f})"
        return Selection(
            av_id=av_id,
            transcription_source=ts,
            cognate_source=cs_name if cog_score > 0 else "",
            pinned=True,
            forms_score=forms_score,
            cognates_score=cog_score,
            tier=tier,
            rationale=rationale,
            candidates=candlist,
        )

    if not candlist:
        return Selection(
            av_id=av_id,
            transcription_source="",
            pinned=False,
            tier="copper",
            rationale="no candidates in universe",
        )

    # Source-priority floor: restrict to the most-preferred priority tier
    # that has any candidate, then pick by score within it. GLED and
    # Wiktionary only win when no Lexibank source covers the variety.
    best_priority = min(source_priority(ds) for ds, _, _ in candlist)
    tier_candidates = [
        (ds, fs, cs) for ds, fs, cs in candlist
        if source_priority(ds) == best_priority
    ]
    tier_candidates.sort(key=lambda x: -x[1])

    ts, forms_score, _ = tier_candidates[0]
    cog_candidates = [(ds, cs) for ds, _, cs in tier_candidates if cs > 0]
    cog_candidates.sort(key=lambda x: -x[1])
    cs_name, cog_score = (cog_candidates[0] if cog_candidates else ("", 0.0))

    auto_tier = tier_for(forms_score, weights)
    if auto_tier in ("gold", "silver"):
        auto_tier = "bronze"
    # Fallback sources never rank above copper.
    if best_priority > DEFAULT_PRIORITY:
        auto_tier = "copper"

    prio_note = "" if best_priority == DEFAULT_PRIORITY else f" [fallback p{best_priority}]"
    rationale = f"auto: forms={ts} ({forms_score:.2f}){prio_note}"
    if cs_name:
        rationale += f"; cognates={cs_name} ({cog_score:.2f})"
        if cs_name != ts:
            rationale += " [cross-source: emitted cognates still come from transcription_source]"

    return Selection(
        av_id=av_id,
        transcription_source=ts,
        cognate_source=cs_name,
        pinned=False,
        forms_score=forms_score,
        cognates_score=cog_score,
        tier=auto_tier,
        rationale=rationale,
        candidates=candlist,
    )


def select_all(
    signals: dict[tuple[str, str], Signals],
    pins: dict[str, dict[str, str]],
    weights: dict,
) -> dict[str, Selection]:
    by_av: dict[str, dict[str, Signals]] = {}
    for (gc, ds), sig in signals.items():
        by_av.setdefault(gc, {})[ds] = sig

    selections: dict[str, Selection] = {}
    for av_id, candidates in by_av.items():
        selections[av_id] = _select_one(av_id, candidates, pins.get(av_id), weights)

    for av_id, pin in pins.items():
        if av_id in selections:
            continue
        selections[av_id] = Selection(
            av_id=av_id,
            transcription_source=pin["transcription_source"],
            cognate_source=pin.get("cognate_source", ""),
            pinned=True,
            tier="copper",
            rationale="pin invalid: variety not present in any source",
        )

    by_tier: dict[str, int] = {}
    for s in selections.values():
        by_tier[s.tier] = by_tier.get(s.tier, 0) + 1
    logger.info("Selected %d varieties; tiers: %s", len(selections), by_tier)
    return selections


def write_selection_summary(selections: dict[str, Selection], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = (
        "av_id", "transcription_source", "cognate_source",
        "pinned", "forms_score", "cognates_score", "tier", "rationale",
    )
    rows = []
    for av_id in sorted(selections):
        s = selections[av_id]
        rows.append({
            "av_id": s.av_id,
            "transcription_source": s.transcription_source,
            "cognate_source": s.cognate_source,
            "pinned": "true" if s.pinned else "false",
            "forms_score": f"{s.forms_score:.4f}",
            "cognates_score": f"{s.cognates_score:.4f}",
            "tier": s.tier,
            "rationale": s.rationale,
        })
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    logger.info("Wrote selection summary to %s", path)
