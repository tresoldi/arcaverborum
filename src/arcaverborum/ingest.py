"""Ingest: raw/<source>/ → intake/<source>/.

Reads CLDF Wordlist datasets from `raw/lexibank/<dataset>/cldf/` and
produces a single per-source intake bundle at `intake/lexibank/`:

  forms.csv              all forms across datasets, prefixed IDs
  languages.csv          all languages, prefixed IDs
  parameters_raw.csv     all parameters (Concepticon mappings preserved)
  metadata.csv           one row per dataset
  sources.bib            all BibTeX entries, prefixed citation keys

Cognate handling: when `cognates.csv` exists, cognate set IDs are
aggregated into the form row's `Cognacy` column (semicolon-separated).
Forms with multiple alignments / morpheme indices are duplicated so
each combination survives.
"""

from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from typing import Iterable

import pandas as pd

from arcaverborum.bibtex import prefix_bibtex_file, prefix_bibtex_keys

logger = logging.getLogger(__name__)

FORM_COLS = (
    "ID", "Dataset", "Local_ID", "Language_ID", "Parameter_ID",
    "Value", "Form", "Segments", "Comment", "Source", "Loan",
    "Graphemes", "Profile",
    "Cognacy", "Doubt", "Cognate_Detection_Method", "Cognate_Source",
    "Alignment", "Morpheme_Index", "Segment_Slice",
    "Glottocode", "Glottolog_Name", "Concepticon_Gloss",
)

LANG_COLS = (
    "ID", "Dataset", "Name", "Glottocode", "Glottolog_Name",
    "ISO639P3code", "Macroarea", "Latitude", "Longitude",
    "Family", "Location", "Remark",
)

PARAM_COLS = (
    "ID", "Dataset", "Name", "Concepticon_ID", "Concepticon_Gloss",
)

META_COLS = (
    "Dataset", "Title", "Citation", "URL", "License", "CLDF_Module",
    "Repository_Version", "Python_Version",
    "Form_Count", "Language_Count", "Parameter_Count", "Has_Cognates",
)


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def _prefix(series: pd.Series, dataset: str) -> pd.Series:
    return series.astype(str).map(lambda v: f"{dataset}_{v}" if v else v)


def _process_cognates(cognates: pd.DataFrame, dataset: str) -> pd.DataFrame:
    """Prefix IDs, prefix BibTeX keys, return as-is dataframe."""
    if cognates.empty:
        return cognates
    cognates = cognates.copy()
    cognates["Form_ID"] = _prefix(cognates["Form_ID"], dataset)
    cognates["Cognateset_ID"] = _prefix(cognates["Cognateset_ID"], dataset)
    if "Source" in cognates.columns:
        cognates["Source"] = cognates["Source"].apply(
            lambda s: prefix_bibtex_keys(s, dataset)
        )
    return cognates


def _merge_cognates(forms: pd.DataFrame, cognates: pd.DataFrame, dataset: str) -> pd.DataFrame:
    """Attach cognate columns to forms.

    One output row per source form. Multiple cognate set IDs for the
    same form are semicolon-joined into Cognacy. Per-cognate-row fields
    (Alignment, Cognate_Detection_Method, Doubt, Morpheme_Index,
    Segment_Slice, Source) take the first value when multiple rows
    exist — partial-cognacy detail is preserved at the (form, cognate
    set) level inside the joined Cognacy column but not blown up into
    extra form rows.
    """
    cog_cols = ("Doubt", "Cognate_Detection_Method", "Cognate_Source",
                "Alignment", "Morpheme_Index", "Segment_Slice")
    forms = forms.copy()
    for col in cog_cols:
        if col not in forms.columns:
            forms[col] = ""

    if cognates.empty:
        return forms

    cognateset_per_form = (
        cognates.groupby("Form_ID")["Cognateset_ID"]
        .apply(lambda s: ";".join(s.astype(str)))
        .to_dict()
    )
    # A dataset often codes cognates in BOTH forms.csv (a Cognacy column) and
    # cognates.csv (the CognateTable). Union the two, splitting on ";" and
    # de-duplicating exact repeats order-preservingly: this collapses the common
    # "X;X" redundancy while keeping genuine multi-cognate codings ("X;Y").
    original_cognacy = forms.get("Cognacy", pd.Series([""] * len(forms)))
    new_cognacy = forms["ID"].map(cognateset_per_form).fillna("")
    combined = []
    for orig, new in zip(original_cognacy, new_cognacy):
        codes: list[str] = []
        for src in (orig, new):
            if isinstance(src, str):
                for code in src.split(";"):
                    code = code.strip()
                    if code and code not in codes:
                        codes.append(code)
        combined.append(";".join(codes))
    forms["Cognacy"] = combined

    agg_cols = [c for c in ("Doubt", "Cognate_Detection_Method", "Source",
                            "Alignment", "Morpheme_Index", "Segment_Slice")
                if c in cognates.columns]
    if agg_cols:
        first = cognates.groupby("Form_ID")[agg_cols].first().reset_index()
        first = first.rename(columns={"Form_ID": "ID", "Source": "Cognate_Source"})
        forms = forms.merge(first, on="ID", how="left", suffixes=("", "_cog"))
        for col in first.columns:
            if col == "ID":
                continue
            cog_col = f"{col}_cog"
            if cog_col in forms.columns:
                non_empty = forms[cog_col].astype(str).str.strip().ne("")
                forms.loc[non_empty, col] = forms.loc[non_empty, cog_col]
                del forms[cog_col]
    return forms


def _parse_metadata(metadata_json: dict, dataset: str, has_cognates: bool) -> dict:
    derived = metadata_json.get("prov:wasDerivedFrom", []) or []
    repo_version = next(
        (item.get("dc:created", "") for item in derived
         if item.get("dc:title") == "Repository"),
        "",
    )
    generated_by = metadata_json.get("prov:wasGeneratedBy", []) or []
    py_version = next(
        (item.get("dc:created", "") for item in generated_by
         if item.get("dc:title") == "python"),
        "",
    )

    tables = metadata_json.get("tables", []) or []
    counts = {t.get("url"): int(t.get("dc:extent", 0) or 0) for t in tables}

    cldf_module = metadata_json.get("dc:conformsTo", "")
    if "#" in cldf_module:
        cldf_module = cldf_module.rsplit("#", 1)[1]

    return {
        "Dataset": dataset,
        "Title": metadata_json.get("dc:title", ""),
        "Citation": metadata_json.get("dc:bibliographicCitation", ""),
        "URL": metadata_json.get("dcat:accessURL", ""),
        "License": metadata_json.get("dc:license", ""),
        "CLDF_Module": cldf_module,
        "Repository_Version": repo_version,
        "Python_Version": py_version,
        "Form_Count": counts.get("forms.csv", 0),
        "Language_Count": counts.get("languages.csv", 0),
        "Parameter_Count": counts.get("parameters.csv", 0),
        "Has_Cognates": has_cognates,
    }


def _process_one(dataset: str, cldf_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict, str]:
    forms = _read_csv(cldf_dir / "forms.csv")
    languages = _read_csv(cldf_dir / "languages.csv")
    parameters = _read_csv(cldf_dir / "parameters.csv")
    cognates = _read_csv(cldf_dir / "cognates.csv")
    metadata_path = cldf_dir / "cldf-metadata.json"
    bib_path = cldf_dir / "sources.bib"

    if forms.empty or languages.empty or parameters.empty or not metadata_path.exists():
        raise FileNotFoundError(f"{dataset}: missing required CLDF file")

    forms["Dataset"] = dataset
    languages["Dataset"] = dataset
    parameters["Dataset"] = dataset

    forms["ID"] = _prefix(forms["ID"], dataset)
    forms["Language_ID"] = _prefix(forms["Language_ID"], dataset)
    forms["Parameter_ID"] = _prefix(forms["Parameter_ID"], dataset)
    if "Source" in forms.columns:
        forms["Source"] = forms["Source"].apply(lambda s: prefix_bibtex_keys(s, dataset))
    if "Cognacy" in forms.columns:
        forms["Cognacy"] = forms["Cognacy"].apply(
            lambda v: f"{dataset}_{v}" if v and str(v).strip() else v
        )

    languages["ID"] = _prefix(languages["ID"], dataset)
    parameters["ID"] = _prefix(parameters["ID"], dataset)

    cognates = _process_cognates(cognates, dataset)
    has_cognates = not cognates.empty
    forms = _merge_cognates(forms, cognates, dataset)

    lang_meta = languages[["ID", "Glottocode", "Glottolog_Name"]].rename(
        columns={"ID": "Language_ID"}
    )
    forms = forms.merge(lang_meta, on="Language_ID", how="left", suffixes=("", "_lang"))
    if "Glottocode_lang" in forms.columns:
        forms["Glottocode"] = forms["Glottocode_lang"].combine_first(
            forms.get("Glottocode", pd.Series([""] * len(forms)))
        )
        del forms["Glottocode_lang"]
    if "Glottolog_Name_lang" in forms.columns:
        forms["Glottolog_Name"] = forms["Glottolog_Name_lang"].combine_first(
            forms.get("Glottolog_Name", pd.Series([""] * len(forms)))
        )
        del forms["Glottolog_Name_lang"]

    param_meta = parameters[["ID", "Concepticon_Gloss"]].rename(
        columns={"ID": "Parameter_ID"}
    )
    forms = forms.merge(param_meta, on="Parameter_ID", how="left", suffixes=("", "_param"))
    if "Concepticon_Gloss_param" in forms.columns:
        forms["Concepticon_Gloss"] = forms["Concepticon_Gloss_param"].combine_first(
            forms.get("Concepticon_Gloss", pd.Series([""] * len(forms)))
        )
        del forms["Concepticon_Gloss_param"]

    for col in FORM_COLS:
        if col not in forms.columns:
            forms[col] = ""
    forms = forms[list(FORM_COLS)]

    for col in LANG_COLS:
        if col not in languages.columns:
            languages[col] = ""
    languages = languages[list(LANG_COLS)]

    for col in PARAM_COLS:
        if col not in parameters.columns:
            parameters[col] = ""
    parameters = parameters[list(PARAM_COLS)]

    with metadata_path.open(encoding="utf-8") as f:
        metadata_json = json.load(f)
    meta_row = _parse_metadata(metadata_json, dataset, has_cognates)

    bib_text = bib_path.read_text(encoding="utf-8") if bib_path.exists() else ""
    bib_text = prefix_bibtex_file(bib_text, dataset) if bib_text else ""

    return forms, languages, parameters, meta_row, bib_text


def ingest_lexibank(
    raw_root: Path,
    intake_root: Path,
    datasets: Iterable[str] | None = None,
) -> dict:
    raw_dir = raw_root / "lexibank"
    if not raw_dir.exists():
        raise FileNotFoundError(f"No raw lexibank at {raw_dir}")
    intake_dir = intake_root / "lexibank"
    intake_dir.mkdir(parents=True, exist_ok=True)

    if datasets is None:
        datasets = sorted(
            d.name for d in raw_dir.iterdir()
            if d.is_dir() and (d / "cldf" / "cldf-metadata.json").exists()
        )
    datasets = list(datasets)
    logger.info("Ingesting %d datasets from %s", len(datasets), raw_dir)

    forms_path = intake_dir / "forms.csv"
    langs_path = intake_dir / "languages.csv"
    params_path = intake_dir / "parameters_raw.csv"
    meta_path = intake_dir / "metadata.csv"
    bib_path = intake_dir / "sources.bib"

    total_forms = 0
    metadata_rows: list[dict] = []
    bib_chunks: list[str] = []
    first_write = True

    with langs_path.open("w", encoding="utf-8", newline="") as lf, \
         params_path.open("w", encoding="utf-8", newline="") as pf:
        lang_writer = csv.DictWriter(lf, fieldnames=list(LANG_COLS))
        param_writer = csv.DictWriter(pf, fieldnames=list(PARAM_COLS))
        lang_writer.writeheader()
        param_writer.writeheader()

        for i, dataset in enumerate(datasets, 1):
            cldf_dir = raw_dir / dataset / "cldf"
            try:
                forms, langs, params, meta_row, bib_text = _process_one(dataset, cldf_dir)
            except FileNotFoundError as exc:
                logger.warning("Skipping %s: %s", dataset, exc)
                continue
            except Exception as exc:
                logger.error("Failed to ingest %s: %s", dataset, exc)
                continue

            forms.to_csv(
                forms_path,
                mode="w" if first_write else "a",
                header=first_write,
                index=False,
            )
            first_write = False
            total_forms += len(forms)

            for row in langs.to_dict("records"):
                lang_writer.writerow(row)
            for row in params.to_dict("records"):
                param_writer.writerow(row)

            metadata_rows.append(meta_row)
            if bib_text:
                bib_chunks.append(bib_text.strip())

            if i % 20 == 0:
                logger.info("Ingested %d/%d datasets (%d total forms)",
                            i, len(datasets), total_forms)

    pd.DataFrame(metadata_rows, columns=list(META_COLS)).to_csv(meta_path, index=False)
    bib_path.write_text("\n\n".join(bib_chunks), encoding="utf-8")

    logger.info("Ingest complete: %d forms, %d languages files, %d datasets",
                total_forms, sum(1 for _ in langs_path.open()), len(metadata_rows))
    return {
        "datasets_ingested": len(metadata_rows),
        "datasets_skipped": len(datasets) - len(metadata_rows),
        "total_forms": total_forms,
        "intake_dir": str(intake_dir),
    }


def ingest(source: str, raw_root: Path, intake_root: Path, **kwargs) -> dict:
    """Unified entry point: dispatch to the per-source adapter and return stats."""
    if source == "lexibank":
        return ingest_lexibank(raw_root, intake_root, datasets=kwargs.get("datasets"))
    if source == "wiktionary":
        from arcaverborum.sources import wiktionary
        return wiktionary.ingest(raw_root, intake_root, threshold=kwargs.get("threshold", 10))
    raise ValueError(f"Ingest for source {source!r} not implemented")
