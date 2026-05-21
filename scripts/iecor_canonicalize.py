#!/usr/bin/env python3
"""Pin every IECOR-covered Indo-European variety to IECOR.

For each Glottocode IECOR covers, set transcription = cognates = iecor and
mark the variety pinned. The 7 Glottocodes that hold several distinct IECOR
languages (Old Czech vs Czech, Middle/Late Cornish, two Kurdish dialects,
Macedonian + two dialects, Old Polish, Old Swedish, Early Modern Slovene)
are split into one variety per language via sources.source_language_id; the
registry edits for those live in data/varieties.csv + variety_overrides.csv.

Idempotent: re-running overwrites the same configs and rewrites the pin
table. Run `python build.py update --family Indo-European` afterwards.
"""

from __future__ import annotations

import csv
import logging
import shutil
from datetime import date
from pathlib import Path

from arcaverborum.catalog import build_catalog, load_avid_registry
from arcaverborum.glottolog import load_glottolog
from arcaverborum.score import (
    load_weights,
    score_cognates_block,
    score_forms_block,
)
from arcaverborum.selection import SELECTION_CSV, compute_all_signals
from arcaverborum.variety import register

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("iecor")

ROOT = Path(__file__).resolve().parent.parent
LEXIBANK_LANGS = ROOT / "intake" / "lexibank" / "languages.csv"
LEXIBANK_FORMS = ROOT / "intake" / "lexibank" / "forms.csv"
VARIETIES_DIR = ROOT / "varieties"

# Glottocodes with several distinct IECOR languages → one variety each.
# av_id -> IECOR Language_ID. av_ids are registered in data/varieties.csv
# (the two repointed bases) and variety_overrides.csv (the rest).
SPLITS: dict[str, str] = {
    "ine-czech": "iecor_18", "ine-old-czech": "iecor_243",
    "ine-polish": "iecor_55", "ine-old-polish": "iecor_238",
    "ine-swedish": "iecor_69", "ine-old-swedish": "iecor_157",
    "ine-slovenian": "iecor_97", "ine-early-modern-slovene": "iecor_259",
    "ine-macedonian": "iecor_92", "ine-macedonian-visoka": "iecor_253",
    "ine-macedonian-suho": "iecor_254",
    "ine-middle-cornish": "iecor_231", "ine-late-cornish": "iecor_230",
    "ine-southern-kurdish-elami": "iecor_285",
    "ine-southern-kurdish-qorveh": "iecor_308",
}
# Variety dirs made obsolete by the splits (merged bases now retired).
RETIRED = ("ine-old-south-west-british", "ine-southern-kurdish")


def main() -> int:
    glottolog = load_glottolog()
    registry = load_avid_registry()
    catalog = build_catalog(LEXIBANK_LANGS, glottolog=glottolog, avid_registry=registry)
    weights = load_weights()

    # IECOR-covered Glottocodes from intake.
    iecor_gcs: set[str] = set()
    with LEXIBANK_LANGS.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if (row.get("Dataset") or "").strip() == "iecor":
                gc = (row.get("Glottocode") or "").strip().lower()
                if gc:
                    iecor_gcs.add(gc)
    logger.info("IECOR covers %d Glottocodes", len(iecor_gcs))

    logger.info("Scoring IECOR blocks per Glottocode …")
    signals = compute_all_signals([LEXIBANK_FORMS], universe={"iecor"}, use_clts_check=True)
    scores = {
        gc: (score_forms_block(sig, weights), score_cognates_block(sig, weights))
        for (gc, ds), sig in signals.items() if ds == "iecor"
    }
    gold = weights["tiers"]["gold"]

    # Build the target list: every catalog variety whose Glottocode IECOR
    # covers. Splits carry a source_language_id; single-language Glottocodes
    # don't need one.
    targets: list[tuple[str, str]] = []  # (av_id, source_language_id)
    for av_id, v in catalog.items():
        if v.glottocode not in iecor_gcs:
            continue
        targets.append((av_id, SPLITS.get(av_id, "")))
    targets.sort()
    logger.info("Pinning %d IECOR varieties", len(targets))

    pins: list[dict[str, str]] = []
    for av_id, src_lang in targets:
        v = catalog[av_id]
        fs, cs = scores.get(v.glottocode, (0.0, 0.0))
        tier = "gold" if fs >= gold and (cs >= gold or cs == 0.0) else "silver"
        note = (
            f"IECOR canonical: forms+cognates=iecor ({fs:.2f}/{cs:.2f})"
            + (f"; language={src_lang}" if src_lang else "")
        )
        register(
            av_id=av_id, varieties_root=VARIETIES_DIR,
            transcription_source="iecor", cognate_source="iecor",
            name=v.name, glottocode=v.glottocode,
            family=v.family, macroarea=v.macroarea,
            forms_score=fs, cognates_score=cs, tier=tier,
            pinned=True, notes=note, overwrite=True,
            source_language_id=src_lang,
        )
        pins.append({
            "av_id": av_id, "transcription_source": "iecor",
            "cognate_source": "iecor", "locked_at": date.today().isoformat(),
            "notes": note,
        })

    for av_id in RETIRED:
        d = VARIETIES_DIR / av_id
        if d.exists():
            shutil.rmtree(d)
            logger.info("Retired merged base %s", av_id)

    with SELECTION_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "av_id", "transcription_source", "cognate_source", "locked_at", "notes"])
        w.writeheader()
        w.writerows(sorted(pins, key=lambda r: r["av_id"]))
    logger.info("Wrote %d pins to %s", len(pins), SELECTION_CSV.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
