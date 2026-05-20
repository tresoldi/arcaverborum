"""Transform Wiktionary intermediate data into output schema CSVs."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Callable

import pandas as pd

from arcaverborum.schema import OUTPUT_SCHEMA

from .cognates import CognateBuilder
from .extract import WiktTranslation
from .langmap import LangMapping
from .parameters import make_parameter_id, make_parameter_name

logger = logging.getLogger(__name__)

DATASET_NAME = "wiktionary"
SOURCE_KEY = "wiktionary_kaikki2026"


def apply_threshold(
    translations_by_param: dict[tuple[str, str, str], list[WiktTranslation]],
    threshold: int,
) -> dict[tuple[str, str, str], list[WiktTranslation]]:
    before = len(translations_by_param)
    surviving = {}
    for key, trs in translations_by_param.items():
        lang_codes = {tr.target_lang_code for tr in trs}
        if len(lang_codes) >= threshold:
            surviving[key] = trs
    logger.info(
        "Threshold %d: %d → %d parameters (%.0f%% kept)",
        threshold, before, len(surviving),
        100 * len(surviving) / before if before else 0,
    )
    return surviving


def build_forms_df(
    translations_by_param: dict[tuple[str, str, str], list[WiktTranslation]],
    cognate_builder: CognateBuilder,
) -> pd.DataFrame:
    rows: list[dict] = []
    counter = 0
    for (word, pos, sense), trs in translations_by_param.items():
        param_id = make_parameter_id(word, pos, sense)
        for tr in trs:
            counter += 1
            lang_id = f"wikt_{tr.target_lang_code}"

            all_tags = list(tr.tags) + list(tr.raw_tags)
            if tr.note:
                all_tags.append(tr.note)
            comment = ";".join(all_tags) if all_tags else pd.NA

            cognacy = cognate_builder.get_cognate_ids(tr.target_lang_code, tr.target_word)
            loan = cognate_builder.is_loan(tr.target_lang_code, tr.target_word)

            rows.append({
                "ID": f"wikt_{counter}",
                "Dataset": DATASET_NAME,
                "Language_ID": lang_id,
                "Glottocode": pd.NA,
                "Glottolog_Name": pd.NA,
                "Parameter_ID": param_id,
                "Concepticon_Gloss": pd.NA,
                "Value": tr.target_word,
                "Form": tr.target_word,
                "Segments": pd.NA,
                "Cognacy": cognacy if cognacy else pd.NA,
                "Alignment": pd.NA,
                "Loan": loan,
                "Morpheme_Index": pd.NA,
                "Segment_Slice": pd.NA,
                "Doubt": pd.NA,
                "Comment": comment,
                "Source": SOURCE_KEY,
                "Cognate_Detection_Method": "wiktionary_etymology" if cognacy else pd.NA,
                "Cognate_Source": SOURCE_KEY if cognacy else pd.NA,
            })

    df = pd.DataFrame(rows, columns=list(OUTPUT_SCHEMA.forms_output))
    logger.info("Built forms DataFrame: %d rows", len(df))
    return df


def build_languages_df(
    translations_by_param: dict[tuple[str, str, str], list[WiktTranslation]],
    lang_mapper: Callable[[str, str], LangMapping],
) -> pd.DataFrame:
    seen: dict[str, tuple[str, str]] = {}
    for trs in translations_by_param.values():
        for tr in trs:
            key = tr.target_lang_code
            if key not in seen:
                seen[key] = (tr.target_lang, tr.target_lang_code)

    rows: list[dict] = []
    for lang_name, lang_code in sorted(seen.values(), key=lambda x: x[1]):
        mapping = lang_mapper(lang_code, lang_name)
        rows.append({
            "ID": f"wikt_{lang_code}",
            "Dataset": DATASET_NAME,
            "Name": lang_name,
            "Glottocode": mapping.glottocode or pd.NA,
            "Glottolog_Name": mapping.glottolog_name or pd.NA,
            "ISO639P3code": mapping.iso639p3 or pd.NA,
            "Macroarea": mapping.macroarea or pd.NA,
            "Latitude": mapping.latitude,
            "Longitude": mapping.longitude,
            "Family": mapping.family or pd.NA,
            "Location": pd.NA,
            "Remark": pd.NA,
        })

    df = pd.DataFrame(rows, columns=list(OUTPUT_SCHEMA.languages))
    logger.info("Built languages DataFrame: %d rows", len(df))
    return df


def build_parameters_df(
    translations_by_param: dict[tuple[str, str, str], list[WiktTranslation]],
) -> pd.DataFrame:
    rows: list[dict] = []
    for word, pos, sense in sorted(translations_by_param.keys()):
        rows.append({
            "ID": make_parameter_id(word, pos, sense),
            "Dataset": DATASET_NAME,
            "Name": make_parameter_name(word, pos, sense),
            "Concepticon_ID": pd.NA,
            "Concepticon_Gloss": pd.NA,
        })

    df = pd.DataFrame(rows, columns=list(OUTPUT_SCHEMA.parameters))
    logger.info("Built parameters DataFrame: %d rows", len(df))
    return df


def enrich_forms_with_languages(
    forms: pd.DataFrame,
    languages: pd.DataFrame,
) -> pd.DataFrame:
    lang_lookup = {}
    for _, row in languages.iterrows():
        lang_lookup[row["ID"]] = (row.get("Glottocode", pd.NA), row.get("Glottolog_Name", pd.NA))

    glottocodes = []
    glottonames = []
    for lid in forms["Language_ID"]:
        gc, gn = lang_lookup.get(lid, (pd.NA, pd.NA))
        glottocodes.append(gc)
        glottonames.append(gn)

    forms = forms.copy()
    forms["Glottocode"] = glottocodes
    forms["Glottolog_Name"] = glottonames
    return forms


def write_output(
    forms: pd.DataFrame,
    languages: pd.DataFrame,
    parameters: pd.DataFrame,
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    forms.to_csv(output_dir / "forms.csv", index=False, encoding="utf-8")
    languages.to_csv(output_dir / "languages.csv", index=False, encoding="utf-8")
    parameters.to_csv(output_dir / "parameters_raw.csv", index=False, encoding="utf-8")

    stats = {
        "dataset": DATASET_NAME,
        "forms": len(forms),
        "languages": len(languages),
        "parameters": len(parameters),
        "forms_with_cognacy": int((forms["Cognacy"].notna()).sum()),
        "forms_with_loan": int((forms["Loan"].notna()).sum()),
    }
    (output_dir / "stats.json").write_text(
        json.dumps(stats, indent=2), encoding="utf-8"
    )

    logger.info("Wrote output to %s/", output_dir)
    logger.info("  forms:      %8d", stats["forms"])
    logger.info("  languages:  %8d", stats["languages"])
    logger.info("  parameters: %8d", stats["parameters"])
    logger.info("  with cognacy: %d (%.1f%%)",
                stats["forms_with_cognacy"],
                100 * stats["forms_with_cognacy"] / stats["forms"] if stats["forms"] else 0)
