#!/usr/bin/env python3
"""Migrate varieties/ to the family-prefixed av_id scheme.

End to end:
  1. Backfill blank families by walking the Glottolog tree (subgroup/
     family-node glottocodes -> top family).
  2. Build the family->code registry  -> data/family_codes.csv.
  3. Mint av_ids and write the frozen registry -> data/varieties.csv.
  4. Rewrite each config.yaml (av_id + backfilled family) and rename
     varieties/<glottocode>/ -> varieties/<av_id>/.

Idempotent enough to re-run after a `git checkout`. Run on a branch.

    python scripts/migrate_avid.py [--apply]

Without --apply it only plans + writes the registry/codes (no renames).
"""

from __future__ import annotations

import argparse
import csv
import io
import sys
import urllib.request
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import yaml  # noqa: E402

from arcaverborum import avid  # noqa: E402
from arcaverborum.catalog import VARIETY_FIELDS, VARIETIES_OUT  # noqa: E402
from arcaverborum.glottolog import GLOTTOLOG_CSV_URL, load_glottolog  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
VARIETIES = ROOT / "varieties"


def load_raw_glottolog_rows() -> dict[str, dict]:
    cache = ROOT / "raw" / "glottolog" / "languages.csv"
    if cache.exists():
        data = cache.read_text(encoding="utf-8")
    else:
        data = urllib.request.urlopen(GLOTTOLOG_CSV_URL, timeout=120).read().decode("utf-8")
    return {r["ID"]: r for r in csv.DictReader(io.StringIO(data))}


def top_family(gc: str, by_id: dict[str, dict], fam_name: dict[str, str]) -> str:
    """Top-level family name for any glottocode level, or '' if none."""
    r = by_id.get(gc)
    if not r:
        return ""
    if r.get("Is_Isolate", "") == "true":
        return r.get("Name", "").strip()
    fid = r.get("Family_ID", "").strip()
    if fid and fid in fam_name:
        return fam_name[fid]
    if r.get("Level") == "family":
        return r.get("Name", "").strip()
    return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="Perform the dir renames + config rewrites")
    args = ap.parse_args()

    gl = load_glottolog()
    by_id = load_raw_glottolog_rows()
    fam_name = {r["ID"]: r["Name"] for r in by_id.values() if r.get("Level") == "family"}

    # ---- 1. read configs, resolve final family ----
    records = []  # dict per variety
    backfilled = []
    for cfg_path in sorted(VARIETIES.glob("*/config.yaml")):
        cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
        gc = str(cfg.get("glottocode") or cfg_path.parent.name).strip().lower()
        fam = str(cfg.get("family") or "").strip()
        macro = str(cfg.get("macroarea") or "").strip()
        if not fam:
            tf = top_family(gc, by_id, fam_name)
            if tf:
                fam = tf
                backfilled.append((gc, tf))
        e = gl.get(gc)
        records.append({
            "cfg_path": cfg_path,
            "cfg": cfg,
            "old_av_id": cfg_path.parent.name,
            "glottocode": gc,
            "name": str(cfg.get("name") or "").strip(),
            "family": fam,
            "macroarea": macro or (e.macroarea if e else ""),
            "iso639p3": (e.iso639p3 if e else ""),
            "latitude": (str(e.latitude) if e and e.latitude is not None else ""),
            "longitude": (str(e.longitude) if e and e.longitude is not None else ""),
            "in_glottolog": "true" if e else "false",
        })

    # ---- 2. family codes (biggest family first) ----
    fam_counts = Counter(r["family"] for r in records if r["family"])
    codes = avid.build_family_codes([f for f, _ in fam_counts.most_common()])
    avid.write_family_codes(codes)
    print(f"family_codes.csv: {len(codes)} families -> {avid.FAMILY_CODES_CSV}")

    # ---- 3. mint av_ids ----
    mapping = avid.assign_av_ids(records, codes)
    for r in records:
        r["av_id"] = mapping[r["glottocode"]]
    new_ids = [r["av_id"] for r in records]
    dupes = [k for k, c in Counter(new_ids).items() if c > 1]
    assert not dupes, f"av_id collisions: {dupes[:10]}"
    und = sum(1 for r in records if r["av_id"].startswith(avid.UNDETERMINED_CODE + "-"))
    print(f"av_ids: {len(new_ids)} unique; backfilled families: {len(backfilled)}; "
          f"und-: {und}")

    # ---- 3b. frozen registry data/varieties.csv ----
    VARIETIES_OUT.parent.mkdir(parents=True, exist_ok=True)
    with VARIETIES_OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=VARIETY_FIELDS)
        w.writeheader()
        for r in sorted(records, key=lambda r: r["av_id"]):
            w.writerow({
                "av_id": r["av_id"], "glottocode": r["glottocode"],
                "iso639p3": r["iso639p3"], "name": r["name"],
                "parent_av_id": "", "family": r["family"],
                "macroarea": r["macroarea"], "latitude": r["latitude"],
                "longitude": r["longitude"], "in_glottolog": r["in_glottolog"],
                "notes": "",
            })
    print(f"registry: {VARIETIES_OUT}")

    if not args.apply:
        print("\n(dry run — pass --apply to rename dirs + rewrite configs)")
        return 0

    # ---- 4. rewrite configs + rename dirs ----
    renamed = 0
    for r in records:
        cfg = r["cfg"]
        cfg["av_id"] = r["av_id"]
        cfg["family"] = r["family"]
        if r["macroarea"]:
            cfg["macroarea"] = r["macroarea"]
        r["cfg_path"].write_text(
            yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True),
            encoding="utf-8")
        old_dir = r["cfg_path"].parent
        new_dir = VARIETIES / r["av_id"]
        if old_dir != new_dir:
            assert not new_dir.exists(), f"target exists: {new_dir}"
            old_dir.rename(new_dir)
            renamed += 1
    print(f"\nrenamed {renamed} dirs; rewrote {len(records)} configs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
