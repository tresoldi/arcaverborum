#!/usr/bin/env python3
"""Wiktionary pipeline: kaikki JSONL dump → intake CSVs.

Streams the kaikki.org raw-wiktextract-data JSONL, extracts translations
and etymology links, builds cognate sets, maps Concepticon, enriches
Glottocodes, and writes intake/wiktionary/{forms,languages,parameters_raw}.csv.
"""

from __future__ import annotations

import argparse
import logging
from collections import defaultdict
from pathlib import Path

from arcaverborum.sources.wiktionary.cognates import CognateBuilder
from arcaverborum.sources.wiktionary.emit import (
    apply_threshold,
    build_forms_df,
    build_languages_df,
    build_parameters_df,
    enrich_forms_with_languages,
    write_output,
)
from arcaverborum.sources.wiktionary.extract import (
    WiktTranslation,
    extract_etymologies,
    extract_translations,
    stream_entries,
)
from arcaverborum.sources.wiktionary.langmap import build_lang_mapper

logger = logging.getLogger(__name__)


def run_pipeline(
    input_path: Path,
    output_dir: Path,
    threshold: int = 10,
    glottolog_tsv: Path | None = None,
    concepticon_tsv: Path | None = None,
    enrich_glottocodes: bool = True,
    dry_run: bool = False,
) -> dict:
    """Run the full Wiktionary pipeline. Returns a stats dict."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input dump not found: {input_path}")

    logger.info("Wiktionary pipeline: %s → %s (threshold=%d)",
                input_path, output_dir, threshold)

    translations_by_param: dict[tuple[str, str, str], list[WiktTranslation]] = defaultdict(list)
    cognate_builder = CognateBuilder()
    entry_count = translation_count = 0

    for entry in stream_entries(input_path):
        entry_count += 1
        if entry_count % 500_000 == 0:
            logger.info("  %dk entries, %dk translations, %d parameters",
                        entry_count // 1000, translation_count // 1000,
                        len(translations_by_param))
        lang_code = entry.get("lang_code", "")
        if lang_code == "en" and "translations" in entry:
            for tr in extract_translations(entry):
                translations_by_param[(tr.english_word, tr.pos, tr.sense)].append(tr)
                translation_count += 1
        if "etymology_templates" in entry or "descendants" in entry:
            for etym in extract_etymologies(entry):
                cognate_builder.add_etymology(etym)

    logger.info("Streamed %d entries, %d translations, %d raw parameters",
                entry_count, translation_count, len(translations_by_param))

    translations_by_param = apply_threshold(translations_by_param, threshold)
    if not translations_by_param:
        raise RuntimeError("No parameters survived threshold filtering")
    cognate_builder.finalize()

    lang_mapper = build_lang_mapper(glottolog_tsv)
    forms = build_forms_df(translations_by_param, cognate_builder)
    languages = build_languages_df(translations_by_param, lang_mapper)
    parameters = build_parameters_df(translations_by_param)

    from arcaverborum.concepticon import load_concepticon, match_parameter
    from arcaverborum.sources.wiktionary.parameters import parse_parameter_name

    concepticon = load_concepticon(concepticon_tsv)
    logger.info("Loaded %d Concepticon concepts for auto-mapping", len(concepticon.by_gloss))
    mapped = 0
    param_cid: dict[str, tuple[str, str]] = {}
    for idx, row in parameters.iterrows():
        word, pos, _sense = parse_parameter_name(str(row.get("Name", "")))
        result = match_parameter(word, pos, concepticon)
        if result:
            cid, cgloss = result
            parameters.at[idx, "Concepticon_ID"] = cid
            parameters.at[idx, "Concepticon_Gloss"] = cgloss
            param_cid[row["ID"]] = (cid, cgloss)
            mapped += 1
    logger.info("Mapped %d/%d parameters to Concepticon", mapped, len(parameters))

    if param_cid and "Concepticon_Gloss" in forms.columns:
        forms["Concepticon_Gloss"] = forms["Parameter_ID"].map(
            lambda pid: param_cid.get(pid, (None, None))[1]
        ).fillna(forms["Concepticon_Gloss"])

    forms = enrich_forms_with_languages(forms, languages)

    if enrich_glottocodes:
        from arcaverborum.catalog import enrich_glottocodes as _enrich
        from arcaverborum.glottolog import load_glottolog
        logger.info("Enriching Wiktionary Glottocodes via ISO → Glottolog")
        glottolog = load_glottolog()
        forms, languages = _enrich(forms, languages, glottolog)
        filled = (forms["Glottocode"].astype(str).str.strip() != "").sum()
        logger.info("Glottocode-filled forms: %d / %d", filled, len(forms))

    if dry_run:
        logger.info("DRY RUN — not writing. forms=%d languages=%d parameters=%d",
                    len(forms), len(languages), len(parameters))
    else:
        write_output(forms, languages, parameters, output_dir)

    return {
        "forms": len(forms),
        "languages": len(languages),
        "parameters": len(parameters),
        "concepticon_mapped": mapped,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("intake/wiktionary"))
    parser.add_argument("--threshold", type=int, default=10)
    parser.add_argument("--glottolog", type=Path, default=None)
    parser.add_argument("--concepticon", type=Path, default=None)
    parser.add_argument("--no-enrich", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    run_pipeline(
        input_path=args.input,
        output_dir=args.output,
        threshold=args.threshold,
        glottolog_tsv=args.glottolog,
        concepticon_tsv=args.concepticon,
        enrich_glottocodes=not args.no_enrich,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
