"""Aggregator: union per-variety output into output/aggregate/.

Reads `varieties/<av_id>/generated/forms.csv` for every enrolled variety,
concatenates into a single forms table, and writes:

  output/aggregate/forms.csv        union of all varieties
  output/aggregate/varieties.csv    one row per enrolled variety
  output/aggregate/parameters.csv   concepts actually present
  output/aggregate/metadata.csv     dataset entries actually used
  output/aggregate/sources.bib      BibTeX entries cited
  output/aggregate/build_summary.json

This file also defines:

  FORMS_OUT_FIELDS          canonical column order for emitted forms
  _form_quality_score       per-form quality combining variety+row signals
  _load_parameter_index     Parameter_ID → (Concepticon_ID, Gloss) lookup

— shared by `variety.build_one`.
"""

from __future__ import annotations

import csv
import json
import logging
from pathlib import Path

import pandas as pd
import yaml

from arcaverborum.concepts import CONCEPTS_CSV, load_concepts
from arcaverborum.forms_schema import FORMS_OUT_FIELDS as FORMS_OUT_FIELDS
from arcaverborum.forms_schema import form_quality_score as form_quality_score
from arcaverborum.forms_schema import load_parameter_index as load_parameter_index

logger = logging.getLogger(__name__)


def _split_bibtex(text: str) -> list[str]:
    entries: list[str] = []
    buf: list[str] = []
    depth = 0
    for line in text.splitlines():
        if line.startswith("@") and depth == 0:
            if buf:
                entries.append("\n".join(buf).strip())
            buf = [line]
            depth = line.count("{") - line.count("}")
            continue
        if buf:
            buf.append(line)
            depth += line.count("{") - line.count("}")
            if depth <= 0 and buf:
                entries.append("\n".join(buf).strip())
                buf = []
                depth = 0
    if buf:
        entries.append("\n".join(buf).strip())
    return [e for e in entries if e]


def _bibtex_key(entry: str) -> str:
    if not entry.startswith("@"):
        return ""
    open_brace = entry.find("{")
    if open_brace < 0:
        return ""
    comma = entry.find(",", open_brace)
    if comma < 0:
        return ""
    return entry[open_brace + 1:comma].strip()


def aggregate_all(
    varieties_root: Path,
    intake_dir: Path,
    output_dir: Path,
    extra_intake_dirs: list[Path] | None = None,
) -> dict:
    """Union all `varieties/<av_id>/generated/forms.csv` into output/aggregate/.

    `intake_dir` provides metadata.csv + sources.bib (Lexibank).
    `extra_intake_dirs` supplies additional dataset metadata and bibliography.
    Concepts are emitted from the frozen concept registry.
    """
    extra_intake_dirs = extra_intake_dirs or []
    output_dir.mkdir(parents=True, exist_ok=True)

    av_ids_built: list[str] = []
    av_configs: dict[str, dict] = {}
    if varieties_root.exists():
        for child in sorted(varieties_root.iterdir()):
            if not child.is_dir():
                continue
            gen = child / "generated" / "forms.csv"
            cfg_path = child / "config.yaml"
            if not gen.exists() or not cfg_path.exists():
                continue
            av_ids_built.append(child.name)
            with cfg_path.open(encoding="utf-8") as f:
                av_configs[child.name] = yaml.safe_load(f) or {}

    logger.info("Aggregating %d built varieties", len(av_ids_built))

    out_forms = output_dir / "forms.csv"
    sources_used: set[str] = set()
    bibtex_keys_used: set[str] = set()
    concept_ids_used: set[str] = set()
    total_forms = 0

    first = True
    for av_id in av_ids_built:
        gen = varieties_root / av_id / "generated" / "forms.csv"
        df = pd.read_csv(gen, dtype=str, keep_default_na=False)
        # Optional evidence fields may be absent in older generated slices.
        # Align by column name before appending; positional append corrupts a
        # mixed-schema aggregate after a partial rebuild.
        df = df.reindex(columns=FORMS_OUT_FIELDS, fill_value="")
        if df.empty:
            continue
        df.to_csv(out_forms, index=False, mode="w" if first else "a", header=first)
        first = False
        total_forms += len(df)
        sources_used.update(df["transcription_source"].unique())
        sources_used.update(df["cognate_source"].unique())
        if "concept_id" in df.columns:
            concept_ids_used.update(df["concept_id"].dropna().unique())
        for keys in df["bibtex_key"].dropna().unique():
            for key in str(keys).split(";"):
                key = key.strip()
                if key:
                    bibtex_keys_used.add(key)

    sources_used.discard("")
    sources_used.discard("custom")
    bibtex_keys_used.discard("")
    concept_ids_used.discard("")

    write_varieties(av_configs, output_dir)
    write_parameters(concept_ids_used, output_dir)
    write_metadata(intake_dir / "metadata.csv", sources_used, output_dir,
                   [p / "metadata.csv" for p in extra_intake_dirs])
    write_sources_bib(intake_dir / "sources.bib", bibtex_keys_used, output_dir,
                      [p / "sources.bib" for p in extra_intake_dirs])

    stats = {
        "forms_emitted": total_forms,
        "varieties_emitted": len(av_ids_built),
        "concepts_emitted": len(concept_ids_used),
        "sources_used": sorted(sources_used),
        "bibtex_keys_used_count": len(bibtex_keys_used),
    }
    (output_dir / "build_summary.json").write_text(
        json.dumps(stats, indent=2), encoding="utf-8",
    )
    logger.info("Aggregate done: %s", stats)
    return stats


def write_varieties(av_configs: dict[str, dict], output_dir: Path) -> int:
    out_path = output_dir / "varieties.csv"
    fields = (
        "av_id", "Glottocode", "Name", "Family", "Macroarea",
        "transcription_source", "cognate_source",
        "pinned", "forms_score", "cognates_score", "tier",
    )
    rows = []
    for av_id in sorted(av_configs):
        cfg = av_configs[av_id]
        sources = cfg.get("sources", {})
        scoring = cfg.get("scoring", {})
        rows.append({
            "av_id": av_id,
            "Glottocode": cfg.get("glottocode", ""),
            "Name": cfg.get("name", ""),
            "Family": cfg.get("family", ""),
            "Macroarea": cfg.get("macroarea", ""),
            "transcription_source": sources.get("transcription", ""),
            "cognate_source": sources.get("cognates", ""),
            "pinned": "true" if cfg.get("pinned") else "false",
            "forms_score": str(scoring.get("forms_score", "")),
            "cognates_score": str(scoring.get("cognates_score", "")),
            "tier": scoring.get("tier", ""),
        })
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    logger.info("Wrote %d variety entries to %s", len(rows), out_path)
    return len(rows)


def write_parameters(concept_ids: set[str], output_dir: Path,
                     registry_path: Path = CONCEPTS_CSV) -> int:
    """Emit output/aggregate/parameters.csv as the concept-catalog view of
    the concepts actually present, straight from the frozen registry."""
    cols = ("concept_id", "concepticon_id", "label", "pos",
            "semantic_field", "definition")
    rows = [
        {
            "concept_id": c.concept_id,
            "concepticon_id": c.concepticon_id,
            "label": c.label,
            "pos": c.pos,
            "semantic_field": c.semantic_field,
            "definition": c.definition,
        }
        for c in load_concepts(registry_path)
        if c.concept_id in concept_ids
    ]
    rows.sort(key=lambda r: r["concept_id"])
    with (output_dir / "parameters.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    logger.info("Wrote %d parameters (concept catalog view)", len(rows))
    return len(rows)


def write_metadata(metadata_path: Path, sources_used: set[str], output_dir: Path,
                   extra_paths: list[Path] | None = None) -> int:
    paths = [p for p in [metadata_path, *(extra_paths or [])] if p.exists()]
    if not paths:
        logger.warning("Metadata files missing")
        return 0
    df = pd.concat([pd.read_csv(p, dtype=str, keep_default_na=False) for p in paths], ignore_index=True).fillna("")
    if df["Dataset"].duplicated().any():
        raise ValueError("Duplicate source metadata across intake namespaces")
    df = df[df["Dataset"].isin(sources_used)].copy()
    df.to_csv(output_dir / "metadata.csv", index=False)
    logger.info("Wrote %d metadata entries", len(df))
    return len(df)


def write_sources_bib(bib_path: Path, keys_used: set[str], output_dir: Path,
                      extra_paths: list[Path] | None = None) -> int:
    paths = [p for p in [bib_path, *(extra_paths or [])] if p.exists()]
    if not paths:
        logger.warning("Source BibTeX files not found")
        return 0
    entries = [entry for path in paths for entry in _split_bibtex(path.read_text(encoding="utf-8"))]
    # CLDF citation locators belong to the form reference, not the BibTeX key.
    # Keep the original form value untouched, resolving only its base key here.
    base_keys = {key.split("[", 1)[0].strip() for key in keys_used}
    keep = [e for e in entries if _bibtex_key(e) in base_keys]
    (output_dir / "sources.bib").write_text("\n\n".join(keep), encoding="utf-8")
    logger.info("Wrote %d BibTeX entries (of %d)", len(keep), len(entries))
    return len(keep)
