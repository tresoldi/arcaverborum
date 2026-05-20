#!/usr/bin/env python3
"""Bootstrap varieties/<av_id>/ from the current source intake.

Pipeline:
  1. Build the catalog from intake languages.csv.
  2. Build the source universe from datasets.csv (CORE + ExpertCognates).
  3. Compute signals from intake forms.csv.
  4. Run auto-selection — pin nobody, just rank.
  5. For each selected variety, call variety.register(...) with its auto-pick.

The result is 1,000–2,000 varieties/ subdirs, each with config.yaml and
empty custom/* CSVs, ready for hand-curation.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd

from arcaverborum.catalog import build_catalog, enrich_glottocodes
from arcaverborum.glottolog import load_glottolog
from arcaverborum.score import load_weights
from arcaverborum.selection import (
    compute_all_signals,
    load_pins,
    select_all,
)
from arcaverborum.variety import register

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("bootstrap")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INTAKE_ROOT = PROJECT_ROOT / "intake"
LEXIBANK_INTAKE = INTAKE_ROOT / "lexibank"
WIKTIONARY_INTAKE = INTAKE_ROOT / "wiktionary"
VARIETIES_DIR = PROJECT_ROOT / "varieties"
DATASETS_CSV = PROJECT_ROOT / "datasets.csv"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--varieties-dir", type=Path, default=VARIETIES_DIR)
    p.add_argument("--no-clts-check", action="store_true",
                   help="Skip merkmal-based CLTS-compliance signal (faster)")
    p.add_argument("--overwrite", action="store_true",
                   help="Re-register varieties even if their dir already exists")
    args = p.parse_args()

    lexibank_forms = LEXIBANK_INTAKE / "forms.csv"
    lexibank_langs = LEXIBANK_INTAKE / "languages.csv"
    wiktionary_forms = WIKTIONARY_INTAKE / "forms.csv"
    wiktionary_langs = WIKTIONARY_INTAKE / "languages.csv"
    if not lexibank_forms.exists():
        logger.error("Missing lexibank intake at %s", lexibank_forms)
        return 1

    forms_paths = [lexibank_forms]
    langs_paths = [lexibank_langs]
    if wiktionary_forms.exists():
        forms_paths.append(wiktionary_forms)
        langs_paths.append(wiktionary_langs)
        logger.info("Including Wiktionary intake as a fallback source")

    logger.info("Loading Glottolog")
    glottolog = load_glottolog()
    logger.info("Building variety catalog from %d languages files", len(langs_paths))
    catalog = build_catalog(langs_paths, glottolog=glottolog)

    logger.info("Computing signals across full source universe")
    signals = compute_all_signals(
        forms_paths, universe=None, use_clts_check=not args.no_clts_check,
    )
    weights = load_weights()
    pins = load_pins()
    selections = select_all(signals, pins, weights)

    args.varieties_dir.mkdir(parents=True, exist_ok=True)
    registered = 0
    for av_id in sorted(selections):
        sel = selections[av_id]
        if not sel.transcription_source:
            continue
        variety = catalog.get(av_id)
        if variety is None:
            entry = glottolog.get(av_id)
            if entry is None:
                continue
            from arcaverborum.catalog import Variety, _from_glottolog
            variety = _from_glottolog(entry)
            catalog[av_id] = variety
        register(
            av_id=av_id,
            varieties_root=args.varieties_dir,
            transcription_source=sel.transcription_source,
            cognate_source=sel.cognate_source,
            name=variety.name,
            glottocode=variety.glottocode,
            family=variety.family,
            macroarea=variety.macroarea,
            forms_score=sel.forms_score,
            cognates_score=sel.cognates_score,
            tier=sel.tier,
            pinned=sel.pinned,
            notes=sel.rationale,
            overwrite=args.overwrite,
        )
        registered += 1
        if registered % 200 == 0:
            logger.info("Registered %d varieties so far", registered)

    logger.info("Bootstrap done. %d varieties registered.", registered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
