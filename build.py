#!/usr/bin/env python3
"""Arca Verborum build CLI.

Subcommands:

  fetch         Download raw sources into raw/.
  ingest        Read raw/<source>/ → produce intake/<source>/ CSVs.
  register      Create varieties/<av_id>/ skeletons.
  extend        Scaffold custom/*.csv templates for hand-curating a variety.
  update        Rebuild generated/forms.csv for varieties whose inputs
                changed (config/custom/intake/recipe); --force rebuilds all.
  aggregate     Merge per-variety output into output/aggregate/.
  report        Rank varieties by curation priority into output/report/.
  concepts      Audit (and optionally extend) the frozen concept catalog.
  status        Show enrollment, freshness, source coverage stats.

Examples:

  build.py fetch --source lexibank
  build.py ingest --source lexibank
  build.py register lati1261            # Glottocode or av_id; creates varieties/ine-latin/
  build.py update ine-latin hitt1242
  build.py update --all --family Indo-European
  build.py aggregate
  build.py report
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
    from arcaverborum.catalog import build_catalog, load_avid_registry
    from arcaverborum.glottolog import load_glottolog
    from arcaverborum.variety import register

    combined = _combined_intake()
    if not any(p.exists() for p in combined["languages"]):
        logger.error("No intake languages.csv found. Run ingest first.")
        return 1

    glottolog = load_glottolog()
    registry = load_avid_registry()
    catalog = build_catalog(combined["languages"], glottolog=glottolog, avid_registry=registry)
    by_gc = {v.glottocode: v for v in catalog.values() if v.glottocode}

    for ident in args.av_ids:
        # Accept either a Glottocode (legacy) or a new-scheme av_id.
        variety = catalog.get(ident) or by_gc.get(ident.strip().lower())
        if variety is None:
            logger.warning("Skipping %s — not in catalog", ident)
            continue
        av_id = variety.av_id
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

    if args.all_varieties or args.family or args.macroarea:
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
            av_ids.append(child.name)

    return sorted(set(av_ids))


def cmd_update(args: argparse.Namespace) -> int:
    import pandas as pd

    from arcaverborum import tracking
    from arcaverborum.aggregate import _load_parameter_index
    from arcaverborum.catalog import build_catalog, load_avid_registry
    from arcaverborum.concepts import load_concept_maps
    from arcaverborum.glottolog import load_glottolog
    from arcaverborum.variety import (
        VarietyDir,
        build_one,
        load_config,
        update_config_extension_flags,
    )

    av_ids = _resolve_av_ids(args)
    if not av_ids:
        logger.error("No varieties to update. Specify av_ids or --all/--family/--macroarea.")
        return 1
    logger.info("Updating %d varieties%s", len(av_ids), " (--force)" if args.force else "")

    combined = _combined_intake()
    glottolog = load_glottolog()
    registry = load_avid_registry()
    catalog = build_catalog(combined["languages"], glottolog=glottolog, avid_registry=registry)

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
    concept_index, concept_labels = load_concept_maps()
    logger.info("Loaded %d intake rows, %d parameter entries, %d catalog concepts",
                len(intake_df), len(param_index), len(concept_labels))

    recipe = tracking.recipe_hash()
    logger.info("Computing intake slice fingerprints …")
    slice_hashes = tracking.compute_intake_slice_hashes(intake_df, param_index)

    total = built = skipped = failed = 0
    for i, av_id in enumerate(av_ids, 1):
        vd = VarietyDir(av_id=av_id, root=VARIETIES_DIR / av_id)
        try:
            cfg = load_config(vd)
            gc = (catalog[av_id].glottocode if av_id in catalog else "") or av_id
            ts = (cfg.get("sources") or {}).get("transcription", "")
            slice_h = slice_hashes.get((gc.lower(), ts), "")
            digest, components = tracking.fingerprint(
                tracking.config_component(cfg),
                tracking.custom_component(vd.custom_dir),
                slice_h,
                recipe,
            )
            if not args.force and tracking.is_fresh(vd.generated_dir, digest, vd.generated_forms):
                skipped += 1
                continue
            n = build_one(
                av_id=av_id,
                varieties_root=VARIETIES_DIR,
                intake_forms=intake_df,
                catalog=catalog,
                param_index=param_index,
                concept_index=concept_index,
                concept_labels=concept_labels,
            )
            update_config_extension_flags(vd)
            tracking.write_manifest(vd.generated_dir, digest, components, n)
            total += n
            built += 1
        except Exception as exc:
            failed += 1
            logger.error("Failed to build %s: %s", av_id, exc)
        if i % 50 == 0:
            logger.info("Progress: %d/%d (built %d, skipped %d)",
                        i, len(av_ids), built, skipped)
    logger.info(
        "Done: %d built (%d forms), %d skipped (unchanged), %d failed",
        built, total, skipped, failed,
    )
    return 0


def cmd_release(args: argparse.Namespace) -> int:
    from arcaverborum.release import build_release

    agg = OUTPUT_DIR / "aggregate"
    if not (agg / "forms.csv").exists():
        logger.error("Aggregate missing in %s — run `build.py aggregate` first.", agg)
        return 1
    stats = build_release(
        aggregate_dir=agg,
        out_root=OUTPUT_DIR / "release",
        version=args.version,
    )
    logger.info("Release built: %s", stats["out_dir"])
    logger.info("  %d forms · %d languages · %d concepts · %d cognate sets",
                stats["forms"], stats["languages"], stats["parameters"], stats["cognatesets"])
    logger.info("  sources: %s", ", ".join(stats["datasets"]))
    return 0


def cmd_packet(args: argparse.Namespace) -> int:
    from arcaverborum import packet

    av_ids = _resolve_av_ids(args)
    if not av_ids:
        logger.error("No varieties selected. Give av_ids or --all/--family/--macroarea.")
        return 1
    core = packet.load_core_concepts()
    experts = packet.load_expert_datasets()
    counts = {"written": 0, "exists": 0, "not-built": 0, "no-config": 0}
    for av_id in av_ids:
        res = packet.scaffold_packet(av_id, VARIETIES_DIR / av_id, core, experts,
                                     overwrite=args.force)
        counts[res["status"]] = counts.get(res["status"], 0) + 1
        if res["status"] == "written":
            d = res["diag"]
            logger.info("packet %s: %d forms, core %d/%d, %d unclean",
                        av_id, d["n_forms"], d["core_hit"], d["core_total"],
                        d["seg"].get("unclean", 0))
        elif res["status"] == "exists":
            logger.info("packet %s: exists (use --force to overwrite)", av_id)
        elif res["status"] == "not-built":
            logger.warning("packet %s: not built — run `build.py update %s` first", av_id, av_id)
    logger.info("Packets: %s", {k: v for k, v in counts.items() if v})
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


def cmd_report(args: argparse.Namespace) -> int:
    import pandas as pd

    from arcaverborum.curation import build_curation_report, write_curation_report

    agg = OUTPUT_DIR / "aggregate"
    forms_path = agg / "forms.csv"
    varieties_path = agg / "varieties.csv"
    if not forms_path.exists() or not varieties_path.exists():
        logger.error("Aggregate output missing in %s — run `build.py aggregate` first.", agg)
        return 1

    logger.info("Loading aggregate forms for curation report …")
    forms = pd.read_csv(
        forms_path, dtype=str, keep_default_na=False,
        usecols=["av_id", "Segments", "Segments_Source", "concept_id", "Cognacy"],
    )
    varieties = pd.read_csv(varieties_path, dtype=str, keep_default_na=False)

    rows, summary = build_curation_report(forms, varieties)
    write_curation_report(rows, summary, OUTPUT_DIR / "report")

    ss = summary["segments_source"]
    print(f"\nForms: {summary['total_forms']:,} across {summary['total_varieties']:,} varieties")
    print(f"  clean (source):  {ss['source']['forms']:>9,}  {ss['source']['pct']:6.1%}")
    print(f"  resegmented:     {ss['resegmented']['forms']:>9,}  {ss['resegmented']['pct']:6.1%}")
    print(f"  unclean:         {ss['unclean']['forms']:>9,}  {ss['unclean']['pct']:6.1%}")
    tb = summary["tone_blocked"]
    print(f"    of which tonal+malformed (residual): {tb['forms']:,} "
          f"({tb['pct_of_unclean']:.0%} of unclean)")
    print("\nTop curation targets (priority = data volume x forms-block weakness):")
    for r in rows[:15]:
        print(f"  {r['av_id']:12s} {str(r['tier']):7s} prio={r['priority_score']:.3f} "
              f"forms={r['n_forms']:>5} unclean={r['pct_unclean']:.0%} "
              f"tone={r['pct_tone_blocked']:.0%}  {r['name']}")
    return 0


def cmd_concepts(args: argparse.Namespace) -> int:
    from arcaverborum import concept_audit
    from arcaverborum.concepticon import load_concepticon_by_id
    from arcaverborum.concepts import (
        CONCEPTS_CSV,
        build_field_codes,
        load_concepts,
        write_concepts,
    )

    registry = load_concepts()
    if not registry:
        logger.error("No concept registry at %s — run scripts/bootstrap_concepts.py first.",
                     CONCEPTS_CSV)
        return 1
    inuse = concept_audit.collect_inuse_concepticon_ids(INTAKE_DIR)
    master = load_concepticon_by_id(args.concepticon)
    report = concept_audit.audit_registry(inuse, master, registry)
    print(concept_audit.format_audit(report))

    if args.mint and report["new_inuse"]:
        field_codes = build_field_codes(
            [c.semantic_field for c in registry if c.semantic_field]
        )
        minted = concept_audit.mint_missing(
            report["new_inuse"], master, registry, field_codes,
        )
        write_concepts(registry + minted, CONCEPTS_CSV)
        logger.info("Minted %d new concepts → %s (now %d total). "
                    "Re-run `update` to fold them into builds.",
                    len(minted), CONCEPTS_CSV, len(registry) + len(minted))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    import yaml

    from arcaverborum import tracking

    if not VARIETIES_DIR.exists():
        print("No varieties registered.")
        return 0

    recipe = tracking.recipe_hash()
    total = 0
    fresh = 0
    stale = 0
    not_built = 0
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
        gen_dir = child / "generated"
        manifest = tracking.load_manifest(gen_dir)
        if not (gen_dir / "forms.csv").exists() or not manifest:
            not_built += 1
        else:
            comps = manifest.get("components", {})
            cfg_ok = comps.get("config") == tracking.config_component(cfg)
            cus_ok = comps.get("custom") == tracking.custom_component(child / "custom")
            rec_ok = comps.get("recipe") == recipe
            if cfg_ok and cus_ok and rec_ok:
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
    print(f"  fresh (config/custom/recipe match manifest):  {fresh}")
    print(f"  stale (config/custom/recipe changed):         {stale}")
    print(f"  not built (no output/manifest):               {not_built}")
    print(f"  pinned (manual sources):                      {pinned}")
    print(f"  with custom extensions:                       {with_extensions}")
    print("  note: source-data (intake) changes are detected on `update`,")
    print("        not here (status does not load intake).")
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
    p_up.add_argument("--force", action="store_true",
                      help="Rebuild even when the fingerprint is unchanged")
    p_up.set_defaults(fn=cmd_update)

    p_pkt = sub.add_parser("packet",
                           help="Scaffold recipe.yaml + PACKET.md (authority recipe/curation packet)")
    p_pkt.add_argument("av_ids", nargs="*")
    p_pkt.add_argument("--all", dest="all_varieties", action="store_true")
    p_pkt.add_argument("--family", default=None)
    p_pkt.add_argument("--macroarea", default=None)
    p_pkt.add_argument("--force", action="store_true",
                       help="Overwrite existing recipe.yaml / PACKET.md")
    p_pkt.set_defaults(fn=cmd_packet)

    p_agg = sub.add_parser("aggregate", help="Union per-variety output into output/aggregate/")
    p_agg.set_defaults(fn=cmd_aggregate)

    p_rel = sub.add_parser("release", help="Build the versioned Arca Verborum Core dataset release")
    p_rel.add_argument("--version", default="0.1.0", help="Release version (semver), default 0.1.0")
    p_rel.set_defaults(fn=cmd_release)

    p_rep = sub.add_parser("report", help="Rank varieties by curation priority into output/report/")
    p_rep.set_defaults(fn=cmd_report)

    p_con = sub.add_parser("concepts",
                           help="Audit the frozen concept catalog against intake + Concepticon")
    p_con.add_argument("--mint", action="store_true",
                       help="Mint concept_ids for new in-use Concepticon ids and extend the registry")
    p_con.add_argument("--concepticon", default=None,
                       help="Path/URL to concepticon.tsv (default: raw cache or upstream)")
    p_con.set_defaults(fn=cmd_concepts)

    p_st = sub.add_parser("status", help="Show enrollment/freshness summary")
    p_st.set_defaults(fn=cmd_status)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
