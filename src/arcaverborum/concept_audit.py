"""Drift auditing for the frozen concept catalog (``data/concepts.csv``).

The registry is assigned once and frozen (like ``av_id``); Concepticon
keeps moving. This module *reports* the gap and can *extend* the registry
with freshly minted ids — it never silently re-keys an existing concept.

Findings:

* **new in-use** — Concepticon ids present in the current intake that the
  registry does not cover yet (candidates for minting).
* **now merged** — registry concepts Concepticon has since given a
  ``REPLACEMENT_ID`` (supersession to review).
* **field drift** — registry concepts whose Concepticon ``SEMANTICFIELD``
  no longer matches the one frozen in the registry (the prefix would
  change if re-derived — flagged, never re-keyed).
* **dropped** — registry concepts whose Concepticon id is gone from the
  master list.

Kept out of the build *recipe* (see ``tracking._RECIPE_FILES``) so adding
audit logic does not invalidate every variety's fingerprint.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from arcaverborum import concepts as cc
from arcaverborum.concepticon import ConcepticonEntry

logger = logging.getLogger(__name__)


def collect_inuse_concepticon_ids(intake_root: Path) -> set[str]:
    """Distinct non-empty numeric Concepticon ids across all intake sources."""
    ids: set[str] = set()
    for p in sorted(intake_root.glob("*/parameters_raw.csv")):
        df = pd.read_csv(p, dtype=str, keep_default_na=False)
        if "Concepticon_ID" not in df.columns:
            continue
        col = df["Concepticon_ID"].astype(str).str.strip()
        ids |= {c for c in col.unique() if c.isdigit()}
    return ids


def audit_registry(
    inuse_ids: set[str],
    master: dict[str, ConcepticonEntry],
    registry: list[cc.Concept],
) -> dict:
    """Compare the frozen registry against current intake + Concepticon."""
    covered = {c.concepticon_id for c in registry if c.concepticon_id}

    new_inuse = sorted(inuse_ids - covered, key=lambda c: int(c))
    now_merged, field_drift, dropped = [], [], []
    for c in registry:
        if not c.concepticon_id:
            continue
        m = master.get(c.concepticon_id)
        if m is None:
            dropped.append(c)
            continue
        if m.replacement_id and c.status != "merged":
            now_merged.append((c, m.replacement_id))
        if m.semantic_field and m.semantic_field != c.semantic_field:
            field_drift.append((c, m.semantic_field))

    return {
        "registry_size": len(registry),
        "inuse_count": len(inuse_ids),
        "new_inuse": new_inuse,
        "now_merged": now_merged,
        "field_drift": field_drift,
        "dropped": dropped,
        "clean": not (new_inuse or now_merged or field_drift or dropped),
    }


def mint_missing(
    new_inuse: list[str],
    master: dict[str, ConcepticonEntry],
    registry: list[cc.Concept],
    field_codes: dict[str, str],
) -> list[cc.Concept]:
    """Mint frozen-extension concepts for ``new_inuse`` ids.

    Returns the newly created entries (not yet merged into ``registry``);
    the caller decides whether to write them. Existing ids are respected
    via the live ``taken`` set, so minting never collides.
    """
    taken = {c.concept_id for c in registry}
    minted: list[cc.Concept] = []
    for cid in new_inuse:
        m = master.get(cid)
        if m is None:
            logger.warning("Skipping %s — not in Concepticon master", cid)
            continue
        concept_id = cc.mint_concept_id(m.gloss, m.semantic_field, field_codes, taken, cid)
        taken.add(concept_id)
        label, _qual = cc.normalize_gloss(m.gloss)
        minted.append(cc.Concept(
            concept_id=concept_id,
            concepticon_id=cid,
            label=label,
            pos=cc.pos_for_category(m.ontological_category),
            semantic_field=m.semantic_field,
            definition=m.definition,
            status="merged" if m.replacement_id else "active",
            replacement_id=m.replacement_id,
            notes="minted by audit",
        ))
    return minted


def format_audit(report: dict) -> str:
    lines = [
        f"Concept catalog audit: {report['registry_size']} registry concepts, "
        f"{report['inuse_count']} in-use Concepticon ids.",
    ]
    if report["clean"]:
        lines.append("  ✓ no drift — registry covers every in-use concept, no upstream changes.")
        return "\n".join(lines)

    def section(title, items, render):
        lines.append(f"\n{title}: {len(items)}")
        for it in items[:25]:
            lines.append(f"  {render(it)}")
        if len(items) > 25:
            lines.append(f"  … and {len(items) - 25} more")

    if report["new_inuse"]:
        section("New in-use Concepticon ids (mint with `--mint`)",
                report["new_inuse"], lambda c: c)
    if report["now_merged"]:
        section("Concepticon has merged these (review)",
                report["now_merged"], lambda cm: f"{cm[0].concept_id} ({cm[0].concepticon_id}) "
                f"→ replacement {cm[1]}")
    if report["field_drift"]:
        section("Semantic-field drift (prefix would change; not re-keyed)",
                report["field_drift"], lambda cf: f"{cf[0].concept_id}: "
                f"{cf[0].semantic_field!r} → {cf[1]!r}")
    if report["dropped"]:
        section("Concepts gone from Concepticon master",
                report["dropped"], lambda c: f"{c.concept_id} ({c.concepticon_id})")
    return "\n".join(lines)
