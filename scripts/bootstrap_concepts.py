#!/usr/bin/env python3
"""Bootstrap data/concepts.csv — our frozen, field-prefixed concept catalog.

Pipeline:
  1. Collect the in-use Concepticon ids from the source intake
     (intake/<source>/parameters_raw.csv — deterministic, build-state
     independent, a superset of what is currently emitted).
  2. Load the Concepticon master (gloss, semantic field, ontological
     category, definition, replacement id) for those ids.
  3. Apply any curated fixes from data/concept_overrides.csv.
  4. Assign a semantic-field-prefixed concept_id to each (see
     arcaverborum.concepts), seeding the 24 IDS field codes.
  5. Write data/concepts.csv and data/semantic_field_codes.csv.

`scripts/plan_concepts.py` is the dry-run wrapper: it calls
``build_registry`` and writes the same artifacts to
output/concept_migration/ for review, touching nothing under data/.
"""

from __future__ import annotations

import argparse
import logging
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pandas as pd  # noqa: E402

from arcaverborum import concepts as cc  # noqa: E402
from arcaverborum.concepticon import ConcepticonEntry, load_concepticon_by_id  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("bootstrap-concepts")

ROOT = Path(__file__).resolve().parent.parent
INTAKE = ROOT / "intake"
DATA = ROOT / "src" / "arcaverborum" / "data"
OVERRIDES_CSV = DATA / "concept_overrides.csv"

# Override columns honoured (all optional except concepticon_id).
_OVERRIDE_COLS = ("concepticon_id", "concept_id", "label", "pos",
                  "semantic_field", "definition", "notes")


def collect_inuse_ids(intake_root: Path = INTAKE) -> set[str]:
    """Distinct non-empty numeric Concepticon ids across all intake sources."""
    ids: set[str] = set()
    for p in sorted(intake_root.glob("*/parameters_raw.csv")):
        df = pd.read_csv(p, dtype=str, keep_default_na=False)
        if "Concepticon_ID" not in df.columns:
            continue
        col = df["Concepticon_ID"].astype(str).str.strip()
        ids |= {c for c in col.unique() if c.isdigit()}
    return ids


def load_overrides(path: Path = OVERRIDES_CSV) -> dict[str, dict[str, str]]:
    """Curated per-Concepticon-id fixes. Ignores files lacking concepticon_id."""
    if not path.exists():
        return {}
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    if "concepticon_id" not in df.columns:
        logger.info("Ignoring %s — no concepticon_id column (stale schema)", path)
        return {}
    out: dict[str, dict[str, str]] = {}
    for _, row in df.iterrows():
        cid = str(row.get("concepticon_id", "")).strip()
        if not cid:
            continue
        out[cid] = {c: str(row.get(c, "")).strip() for c in _OVERRIDE_COLS if c != "concepticon_id"}
    return out


def build_registry(
    inuse_ids: set[str],
    master: dict[str, ConcepticonEntry],
    overrides: dict[str, dict[str, str]] | None = None,
) -> tuple[list[cc.Concept], dict[str, str], dict]:
    """Assemble the concept registry. Returns (concepts, field_codes, report)."""
    overrides = overrides or {}

    # Effective per-concept fields, with overrides folded in.
    records = []
    missing = []
    for cid in inuse_ids:
        e = master.get(cid)
        if e is None:
            missing.append(cid)
            continue
        ov = overrides.get(cid, {})
        sem = ov.get("semantic_field") or e.semantic_field
        gloss_eff = ov.get("label") or e.gloss
        pos = ov.get("pos") or cc.pos_for_category(e.ontological_category)
        definition = ov.get("definition") or e.definition
        records.append({
            "concepticon_id": cid,
            "gloss": gloss_eff,
            "semantic_field": sem,
            "pos": pos,
            "definition": definition,
            "replacement_id": e.replacement_id,
            "notes": ov.get("notes", ""),
            "concept_id_override": ov.get("concept_id", ""),
        })

    # Field codes: seed the 24 IDS fields; biggest first claims clean codes.
    fam_counts = Counter(r["semantic_field"] for r in records if r["semantic_field"].strip())
    fields = [f for f, _ in fam_counts.most_common()]
    field_codes = cc.build_field_codes(fields)

    mapping = cc.assign_concept_ids(
        [{"concepticon_id": r["concepticon_id"], "gloss": r["gloss"],
          "semantic_field": r["semantic_field"]} for r in records],
        field_codes,
    )
    # Explicit concept_id overrides win over the derived id.
    for r in records:
        if r["concept_id_override"]:
            mapping[r["concepticon_id"]] = r["concept_id_override"]

    concepts = []
    for r in records:
        cid = r["concepticon_id"]
        label, _qual = cc.normalize_gloss(r["gloss"])
        concepts.append(cc.Concept(
            concept_id=mapping[cid],
            concepticon_id=cid,
            label=label,
            pos=r["pos"],
            semantic_field=r["semantic_field"],
            definition=r["definition"],
            status="merged" if r["replacement_id"] else "active",
            replacement_id=r["replacement_id"],
            notes=r["notes"],
        ))

    ids = [c.concept_id for c in concepts]
    dupes = [k for k, n in Counter(ids).items() if n > 1]
    suffixed = [c for c in concepts if c.concept_id.rsplit("-", 1)[-1].isdigit()]
    qualified = [c for c in concepts
                 if not c.concept_id.rsplit("-", 1)[-1].isdigit()
                 and c.concept_id.count("-") >= 2]
    und = [c for c in concepts if c.concept_id.startswith(cc.UNDETERMINED_CODE + "-")]
    report = {
        "concepts": concepts,
        "field_codes": field_codes,
        "n_concepts": len(concepts),
        "n_unique": len(set(ids)),
        "n_collisions": len(dupes),
        "n_suffixed": len(suffixed),
        "n_qualified": len(qualified),
        "n_undetermined": len(und),
        "missing_from_master": missing,
        "pos_counts": Counter(c.pos for c in concepts),
        "field_counts": fam_counts,
        "samples": concepts[:: max(1, len(concepts) // 25)][:25],
        "suffixed": sorted(suffixed, key=lambda c: c.concept_id)[:15],
        "longest": sorted(concepts, key=lambda c: len(c.concept_id), reverse=True)[:10],
    }
    return concepts, field_codes, report


def print_report(report: dict) -> None:
    print(f"\nConcepts: {report['n_concepts']} "
          f"(unique {report['n_unique']}, COLLISIONS {report['n_collisions']})")
    print(f"  qualifier-disambiguated (field-base-qual): {report['n_qualified']}")
    print(f"  numeric-suffixed (-2, -3 …):               {report['n_suffixed']}")
    print(f"  undetermined field ({cc.UNDETERMINED_CODE}-):            {report['n_undetermined']}")
    if report["missing_from_master"]:
        print(f"  WARNING: {len(report['missing_from_master'])} in-use ids not in "
              f"Concepticon master (skipped): {report['missing_from_master'][:10]}")

    print("\nField codes (by concept count):")
    codes = report["field_codes"]
    for fld, n in report["field_counts"].most_common():
        print(f"  {codes.get(fld, '???'):4s} {fld:30s} {n:>5}")

    print("\npos distribution:")
    for pos, n in report["pos_counts"].most_common():
        print(f"  {pos or '(none)':6s} {n:>6}")

    print("\nSample concept_ids:")
    for c in report["samples"]:
        print(f"  {c.concept_id:28s} {c.pos:4s} [{c.semantic_field}]  ({c.concepticon_id})")

    if report["suffixed"]:
        print("\nFirst numeric-suffixed (true within-field homographs):")
        for c in report["suffixed"]:
            print(f"  {c.concept_id:28s} {c.label!r}  ({c.concepticon_id})")

    print("\n10 longest concept_ids:")
    for c in report["longest"]:
        print(f"  {len(c.concept_id):3d}  {c.concept_id}")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out-dir", type=Path, default=DATA,
                   help="Where to write concepts.csv + semantic_field_codes.csv "
                        "(default: the committed data/ dir)")
    p.add_argument("--concepticon", default=None,
                   help="Path/URL to concepticon.tsv (default: raw cache or upstream)")
    args = p.parse_args()

    logger.info("Collecting in-use Concepticon ids from intake …")
    inuse = collect_inuse_ids()
    logger.info("  %d distinct in-use Concepticon ids", len(inuse))

    logger.info("Loading Concepticon master …")
    master = load_concepticon_by_id(args.concepticon)
    logger.info("  %d concepts in master", len(master))

    overrides = load_overrides()
    if overrides:
        logger.info("Applying %d curated overrides", len(overrides))

    concepts, field_codes, report = build_registry(inuse, master, overrides)
    print_report(report)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    cc.write_field_codes(field_codes, args.out_dir / "semantic_field_codes.csv")
    cc.write_concepts(concepts, args.out_dir / "concepts.csv")
    print(f"\nWrote:\n  {args.out_dir / 'concepts.csv'}"
          f"\n  {args.out_dir / 'semantic_field_codes.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
