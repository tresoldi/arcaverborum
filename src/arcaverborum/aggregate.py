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

logger = logging.getLogger(__name__)

FORMS_OUT_FIELDS = (
    "av_id", "Glottocode", "Variety_Name",
    "concept_id", "concept_label", "Concepticon_ID",
    "Value", "Form", "Segments", "Segments_Source",
    "Cognacy", "canonical_cognate_id",
    "Alignment", "Morpheme_Index", "Segment_Slice", "Doubt",
    "Cognate_Detection_Method", "Cognate_Source",
    "Loan", "Comment",
    "transcription_source", "cognate_source",
    "source_form_id", "source_language_id", "source_parameter_id",
    "bibtex_key", "quality_score", "tier",
)


def _form_quality_score(row: dict, base_score: float) -> float:
    """Per-form quality: combines variety-level forms_score with per-form
    feature presence. Bounded to [0, 1].
    """
    score = base_score
    bonus = 0.0
    if (row.get("Segments") or "").strip():
        bonus += 0.05
    if (row.get("Concepticon_ID") or "").strip():
        bonus += 0.05
    if (row.get("Cognacy") or "").strip():
        bonus += 0.05
    if (row.get("Alignment") or "").strip():
        bonus += 0.03
    if (row.get("Cognate_Detection_Method") or "").strip().lower() == "expert":
        bonus += 0.05
    return min(score + bonus * (1 - score), 1.0)


def _load_parameter_index(parameters_path: Path) -> dict[str, tuple[str, str]]:
    """Build {Parameter_ID: (Concepticon_ID, Concepticon_Gloss)} lookup."""
    if not parameters_path.exists():
        return {}
    df = pd.read_csv(
        parameters_path, dtype=str, keep_default_na=False,
        usecols=lambda c: c in {"ID", "Concepticon_ID", "Concepticon_Gloss"},
    )
    if "ID" not in df.columns:
        return {}
    cid_col = df.get("Concepticon_ID", pd.Series([""] * len(df)))
    gloss_col = df.get("Concepticon_Gloss", pd.Series([""] * len(df)))
    return {
        pid: (str(cid_col.iat[i]).strip(), str(gloss_col.iat[i]).strip())
        for i, pid in enumerate(df["ID"])
    }


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
    `extra_intake_dirs` is accepted for call-site compatibility; the
    concept table is now emitted from the frozen concept registry, so no
    parameters_raw.csv join is needed here.
    """
    _ = extra_intake_dirs  # retained for API stability; no longer used here
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
    write_metadata(intake_dir / "metadata.csv", sources_used, output_dir)
    write_sources_bib(intake_dir / "sources.bib", bibtex_keys_used, output_dir)

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


def write_metadata(metadata_path: Path, sources_used: set[str], output_dir: Path) -> int:
    if not metadata_path.exists():
        logger.warning("Metadata file missing: %s", metadata_path)
        return 0
    df = pd.read_csv(metadata_path, dtype=str, keep_default_na=False)
    df = df[df["Dataset"].isin(sources_used)].copy()
    df.to_csv(output_dir / "metadata.csv", index=False)
    logger.info("Wrote %d metadata entries", len(df))
    return len(df)


def write_sources_bib(bib_path: Path, keys_used: set[str], output_dir: Path) -> int:
    if not bib_path.exists():
        logger.warning("Source BibTeX not found: %s", bib_path)
        return 0
    text = bib_path.read_text(encoding="utf-8")
    entries = _split_bibtex(text)
    keep = [e for e in entries if _bibtex_key(e) in keys_used]
    (output_dir / "sources.bib").write_text("\n\n".join(keep), encoding="utf-8")
    logger.info("Wrote %d BibTeX entries (of %d)", len(keep), len(entries))
    return len(keep)
