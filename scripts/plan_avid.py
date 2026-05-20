#!/usr/bin/env python3
"""Dry-run planner for the family-prefixed av_id scheme.

Reads every varieties/<gc>/config.yaml, builds the family-code registry
and the proposed Glottocode -> av_id mapping, and writes review artifacts
to output/avid_migration/. Renames NOTHING.

    python scripts/plan_avid.py
"""

from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import yaml  # noqa: E402

from arcaverborum import avid  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
VARIETIES = ROOT / "varieties"
OUT = ROOT / "output" / "avid_migration"


def load_varieties() -> list[dict[str, str]]:
    rows = []
    for cfg_path in sorted(VARIETIES.glob("*/config.yaml")):
        with cfg_path.open(encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        rows.append(
            {
                "old_av_id": str(cfg.get("av_id") or cfg_path.parent.name),
                "glottocode": str(cfg.get("glottocode") or "").strip().lower(),
                "name": str(cfg.get("name") or "").strip(),
                "family": str(cfg.get("family") or "").strip(),
                "macroarea": str(cfg.get("macroarea") or "").strip(),
            }
        )
    return rows


def main() -> int:
    varieties = load_varieties()
    print(f"Loaded {len(varieties)} varieties")

    # Biggest families first, so they claim the clean 3-letter code.
    fam_counts = Counter(v["family"] for v in varieties if v["family"].strip())
    families = [fam for fam, _ in fam_counts.most_common()]
    codes = avid.build_family_codes(families)
    mapping = avid.assign_av_ids(varieties, codes)

    OUT.mkdir(parents=True, exist_ok=True)
    avid.write_family_codes(codes, OUT / "family_codes.csv")

    rows = []
    for v in varieties:
        gc = v["glottocode"]
        new_id = mapping.get(gc, "")
        rows.append({**v, "family_code": avid.family_code_for(v["family"], codes),
                     "new_av_id": new_id})
    rows.sort(key=lambda r: r["new_av_id"])

    with (OUT / "avid_mapping.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "old_av_id", "glottocode", "family", "family_code",
            "macroarea", "name", "new_av_id"])
        w.writeheader()
        w.writerows(rows)

    # ---- report ----
    new_ids = [r["new_av_id"] for r in rows]
    dupes = [k for k, c in Counter(new_ids).items() if c > 1]
    suffixed = [r for r in rows if r["new_av_id"].rsplit("-", 1)[-1].isdigit()]
    lengths = sorted(rows, key=lambda r: len(r["new_av_id"]), reverse=True)
    und = [r for r in rows if r["family_code"] == avid.UNDETERMINED_CODE]

    print(f"\nFamilies: {len(codes)}  ->  family_codes.csv")
    print(f"Proposed IDs: {len(new_ids)}, unique: {len(set(new_ids))}, "
          f"COLLISIONS: {len(dupes)}")
    print(f"Collision-suffixed (-2, -3 ...): {len(suffixed)}")
    print(f"Undetermined family ({avid.UNDETERMINED_CODE}-): {len(und)}")

    print("\nSample (random-ish, by new_av_id):")
    for r in rows[::max(1, len(rows) // 25)][:25]:
        print(f"  {r['old_av_id']:10s} -> {r['new_av_id']:28s} "
              f"[{r['family']}]")

    print("\nFamily codes (top families by member count):")
    fam_counts = Counter(v["family"] for v in varieties if v["family"])
    for fam, n in fam_counts.most_common(20):
        print(f"  {codes.get(fam, '???'):4s} {fam:28s} {n:>5}")

    print("\n10 longest IDs:")
    for r in lengths[:10]:
        print(f"  {len(r['new_av_id']):3d}  {r['new_av_id']}")

    if suffixed:
        print("\nFirst 15 collision-suffixed IDs:")
        for r in sorted(suffixed, key=lambda r: r["new_av_id"])[:15]:
            print(f"  {r['new_av_id']:30s} [{r['name']}]")

    print(f"\nWrote:\n  {OUT/'family_codes.csv'}\n  {OUT/'avid_mapping.csv'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
