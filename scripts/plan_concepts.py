#!/usr/bin/env python3
"""Dry-run planner for the semantic-field-prefixed concept catalog.

Assembles the proposed concept_id registry from the source intake +
Concepticon master and writes review artifacts to
output/concept_migration/. Writes NOTHING under data/.

    python scripts/plan_concepts.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from bootstrap_concepts import (  # noqa: E402
    build_registry,
    collect_inuse_ids,
    load_overrides,
    print_report,
)

from arcaverborum import concepts as cc  # noqa: E402
from arcaverborum.concepticon import load_concepticon_by_id  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "concept_migration"


def main() -> int:
    inuse = collect_inuse_ids()
    print(f"Collected {len(inuse)} in-use Concepticon ids")
    master = load_concepticon_by_id()
    print(f"Loaded {len(master)} Concepticon master concepts")
    overrides = load_overrides()

    concepts, field_codes, report = build_registry(inuse, master, overrides)
    print_report(report)

    OUT.mkdir(parents=True, exist_ok=True)
    cc.write_field_codes(field_codes, OUT / "semantic_field_codes.csv")
    cc.write_concepts(concepts, OUT / "concepts.csv")
    print(f"\nWrote (review only, data/ untouched):"
          f"\n  {OUT / 'concepts.csv'}"
          f"\n  {OUT / 'semantic_field_codes.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
