#!/usr/bin/env python3
"""Arca Verborum build CLI.

Subcommands:

  fetch         Download raw sources into raw/.
  ingest        Read raw/<source>/ → produce intake/<source>/ CSVs.
  register      Create varieties/<av_id>/ skeletons.
  extend        Scaffold custom/*.csv templates for hand-curating a variety.
  update        Rebuild generated/forms.csv for one or more varieties.
  aggregate     Merge per-variety output into output/aggregate/.
  status        Show enrollment, freshness, source coverage stats.

Examples:

  build.py fetch --source lexibank
  build.py ingest --source lexibank
  build.py register lati1261
  build.py update lati1261 hitt1242
  build.py update --all --family Indo-European
  build.py aggregate
  build.py status
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("build")

PROJECT_ROOT = Path(__file__).resolve().parent
RAW_DIR = PROJECT_ROOT / "raw"
INTAKE_DIR = PROJECT_ROOT / "intake"
VARIETIES_DIR = PROJECT_ROOT / "varieties"
OUTPUT_DIR = PROJECT_ROOT / "output"
DATASETS_CSV = PROJECT_ROOT / "datasets.csv"


def _intake_paths(source: str = "lexibank") -> dict[str, Path]:
    base = INTAKE_DIR / source
    return {
        "forms": base / "forms.csv",
        "languages": base / "languages.csv",
        "parameters": base / "parameters_raw.csv",
        "metadata": base / "metadata.csv",
        "bib": base / "sources.bib",
    }


def _all_intake_sources() -> list[str]:
    """Intake sources present on disk (lexibank always first)."""
    sources = []
    for name in ("lexibank", "wiktionary"):
        if (INTAKE_DIR / name / "forms.csv").exists():
            sources.append(name)
    return sources or ["lexibank"]


def _combined_intake() -> dict[str, list[Path]]:
    """Forms/languages/parameters paths across all present intake sources."""
    sources = _all_intake_sources()
    return {
        "forms": [INTAKE_DIR / s / "forms.csv" for s in sources],
        "languages": [INTAKE_DIR / s / "languages.csv" for s in sources],
        "parameters": [INTAKE_DIR / s / "parameters_raw.csv" for s in sources],
    }


def cmd_fetch(args: argparse.Namespace) -> int:
    from arcaverborum.sources import dispatch_fetch

    if args.source == "all":
        targets = ["glottolog", "concepticon", "lexibank", "gled", "wiktionary"]
    else:
        targets = [args.source]
    for src in targets:
        logger.info("Fetching %s …", src)
        dispatch_fetch(src, RAW_DIR)
    return 0


def cmd_ingest(args: argparse.Namespace) -> int:
    if args.source == "lexibank":
        from arcaverborum.ingest import ingest_lexibank
        stats = ingest_lexibank(RAW_DIR, INTAKE_DIR)
    elif args.source == "wiktionary":
        from arcaverborum.sources import wiktionary
        stats = wiktionary.ingest(RAW_DIR, INTAKE_DIR, threshold=args.threshold)
    else:
        logger.error("Ingest for source %r not yet implemented.", args.source)
        return 1
    logger.info("Ingest stats: %s", stats)
    return 0


def cmd_register(args: argparse.Namespace) -> int:
    from arcaverborum.catalog import build_catalog
    from arcaverborum.glottolog import load_glottolog
    from arcaverborum.variety import register

    combined = _combined_intake()
    if not any(p.exists() for p in combined["languages"]):
        logger.error("No intake languages.csv found. Run ingest first.")
        return 1

    glottolog = load_glottolog()
    catalog = build_catalog(combined["languages"], glottolog=glottolog)

    for av_id in args.av_ids:
        if av_id not in catalog:
            logger.warning("Skipping %s — not in catalog", av_id)
            continue
        variety = catalog[av_id]
        vd = register(
            av_id=av_id,
            varieties_root=VARIETIES_DIR,
            transcription_source=args.transcription_source or "",
            cognate_source=args.cognate_source or "",
            name=variety.name,
            glottocode=variety.glottocode,
            family=variety.family,
            macroarea=variety.macroarea,
            pinned=bool(args.pin),
            overwrite=args.overwrite,
        )
        logger.info("Registered %s at %s", av_id, vd.root)
    return 0


def cmd_extend(args: argparse.Namespace) -> int:
    from arcaverborum.variety import VarietyDir, scaffold_custom_files

    for av_id in args.av_ids:
        vd = VarietyDir(av_id=av_id, root=VARIETIES_DIR / av_id)
        if not vd.exists():
            logger.warning("Skipping %s — not registered", av_id)
            continue
        paths = scaffold_custom_files(vd)
        logger.info("Scaffolded custom templates for %s:", av_id)
        for p in paths:
            logger.info("  %s", p)
    return 0


def _resolve_av_ids(args: argparse.Namespace) -> list[str]:
    av_ids: list[str] = list(args.av_ids or [])

    if args.all_varieties or args.family or args.macroarea or args.changed:
        import yaml

        for child in sorted(VARIETIES_DIR.iterdir() if VARIETIES_DIR.exists() else []):
            if not child.is_dir():
                continue
            config_path = child / "config.yaml"
            if not config_path.exists():
                continue
            with config_path.open(encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
            if args.family and cfg.get("family") != args.family:
                continue
            if args.macroarea and cfg.get("macroarea") != args.macroarea:
                continue
            if args.changed:
                gen = child / "generated" / "forms.csv"
                if gen.exists() and gen.stat().st_mtime >= config_path.stat().st_mtime:
                    continue
            av_ids.append(child.name)

    return sorted(set(av_ids))


def cmd_update(args: argparse.Namespace) -> int:
    import pandas as pd
    from arcaverborum.aggregate import _load_parameter_index
    from arcaverborum.catalog import build_catalog
    from arcaverborum.glottolog import load_glottolog
    from arcaverborum.variety import build_one, update_config_extension_flags, VarietyDir

    av_ids = _resolve_av_ids(args)
    if not av_ids:
        logger.error("No varieties to update. Specify av_ids or --all/--family/--macroarea.")
        return 1
    logger.info("Updating %d varieties", len(av_ids))

    combined = _combined_intake()
    glottolog = load_glottolog()
    catalog = build_catalog(combined["languages"], glottolog=glottolog)

    logger.info("Loading intake forms (%d sources) …", len(combined["forms"]))
    frames = []
    for fp in combined["forms"]:
        if fp.exists():
            frames.append(pd.read_csv(fp, dtype=str, keep_default_na=False))
    intake_df = pd.concat(frames, ignore_index=True).fillna("")
    intake_df["_glottocode_lc"] = intake_df["Glottocode"].astype(str).str.strip().str.lower()

    param_index: dict = {}
    for pp in combined["parameters"]:
        if pp.exists():
            param_index.update(_load_parameter_index(pp))
    logger.info("Loaded %d intake rows, %d parameter entries",
                len(intake_df), len(param_index))

    total = 0
    for i, av_id in enumerate(av_ids, 1):
        try:
            total += build_one(
                av_id=av_id,
                varieties_root=VARIETIES_DIR,
                intake_forms=intake_df,
                catalog=catalog,
                param_index=param_index,
            )
            update_config_extension_flags(VarietyDir(av_id=av_id, root=VARIETIES_DIR / av_id))
        except Exception as exc:
            logger.error("Failed to build %s: %s", av_id, exc)
        if i % 50 == 0:
            logger.info("Progress: %d/%d varieties built", i, len(av_ids))
    logger.info("Built %d total forms across %d varieties", total, len(av_ids))
    return 0


def cmd_aggregate(args: argparse.Namespace) -> int:
    from arcaverborum.aggregate import aggregate_all

    extra = []
    wikt = INTAKE_DIR / "wiktionary"
    if (wikt / "parameters_raw.csv").exists():
        extra.append(wikt)

    stats = aggregate_all(
        varieties_root=VARIETIES_DIR,
        intake_dir=INTAKE_DIR / "lexibank",
        output_dir=OUTPUT_DIR / "aggregate",
        extra_intake_dirs=extra,
    )
    logger.info("Aggregation summary: %s", stats)
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    import yaml

    if not VARIETIES_DIR.exists():
        print("No varieties registered.")
        return 0

    total = 0
    fresh = 0
    stale = 0
    with_extensions = 0
    pinned = 0
    families: dict[str, int] = {}

    for child in sorted(VARIETIES_DIR.iterdir()):
        if not child.is_dir():
            continue
        config_path = child / "config.yaml"
        if not config_path.exists():
            continue
        total += 1
        with config_path.open(encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        gen = child / "generated" / "forms.csv"
        if gen.exists() and gen.stat().st_mtime >= config_path.stat().st_mtime:
            fresh += 1
        else:
            stale += 1
        if any((cfg.get("extensions") or {}).values()):
            with_extensions += 1
        if cfg.get("pinned"):
            pinned += 1
        fam = cfg.get("family") or "Unknown"
        families[fam] = families.get(fam, 0) + 1

    print(f"Varieties enrolled:  {total}")
    print(f"  fresh (generated/ newer than config):  {fresh}")
    print(f"  stale (need rebuild):                  {stale}")
    print(f"  pinned (manual sources):               {pinned}")
    print(f"  with custom extensions:                {with_extensions}")
    print()
    print("Top families:")
    for fam, n in sorted(families.items(), key=lambda kv: -kv[1])[:10]:
        print(f"  {fam:30s} {n}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    p_fetch = sub.add_parser("fetch", help="Download raw sources into raw/")
    p_fetch.add_argument("--source",
                         choices=["glottolog", "concepticon", "lexibank", "gled", "wiktionary", "all"],
                         default="all")
    p_fetch.set_defaults(fn=cmd_fetch)

    p_ing = sub.add_parser("ingest", help="Read raw/ → produce intake/ CSVs")
    p_ing.add_argument("--source",
                       choices=["lexibank", "wiktionary"],
                       default="lexibank")
    p_ing.add_argument("--threshold", type=int, default=10,
                       help="Wiktionary: min distinct languages per parameter")
    p_ing.set_defaults(fn=cmd_ingest)

    p_reg = sub.add_parser("register", help="Create varieties/<av_id>/ skeletons")
    p_reg.add_argument("av_ids", nargs="+")
    p_reg.add_argument("--transcription-source", default=None)
    p_reg.add_argument("--cognate-source", default=None)
    p_reg.add_argument("--pin", action="store_true")
    p_reg.add_argument("--overwrite", action="store_true")
    p_reg.set_defaults(fn=cmd_register)

    p_ext = sub.add_parser("extend", help="Scaffold custom/*.csv templates for varieties")
    p_ext.add_argument("av_ids", nargs="+")
    p_ext.set_defaults(fn=cmd_extend)

    p_up = sub.add_parser("update", help="Rebuild generated/forms.csv for varieties")
    p_up.add_argument("av_ids", nargs="*")
    p_up.add_argument("--all", dest="all_varieties", action="store_true")
    p_up.add_argument("--family", default=None)
    p_up.add_argument("--macroarea", default=None)
    p_up.add_argument("--changed", action="store_true",
                      help="Only build varieties whose generated/ is stale vs config.yaml")
    p_up.set_defaults(fn=cmd_update)

    p_agg = sub.add_parser("aggregate", help="Union per-variety output into output/aggregate/")
    p_agg.set_defaults(fn=cmd_aggregate)

    p_st = sub.add_parser("status", help="Show enrollment/freshness summary")
    p_st.set_defaults(fn=cmd_status)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
