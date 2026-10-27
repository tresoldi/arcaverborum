"""Per-variety directory: skeleton, config, custom overrides, build.

Each variety lives in `varieties/<av_id>/` with:

  config.yaml                  source choices, extension flags, notes
  custom/transcriptions.csv    per-(Concepticon_ID, source_form_id) col overrides
  custom/forms.csv             additive new (concept, form) rows
  custom/cognates.csv          per-form_id cognate overrides
  custom/concept_map.csv       per-Parameter_ID Concepticon_ID / concept_id fixes
  generated/forms.csv          gitignored output

`build_one(av_id)` reads the intake, applies the variety's source pick
and overlays its custom data, runs phonology normalization, and writes
`generated/forms.csv`.
"""

from __future__ import annotations

import csv
import logging
import sqlite3
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd
import yaml

from arcaverborum.catalog import Variety
from arcaverborum.concepts import load_concept_maps
from arcaverborum.forms_schema import FORMS_OUT_FIELDS, form_quality_score, load_parameter_index
from arcaverborum.fsutil import atomic_path, write_text_atomic
from arcaverborum.intake_db import IntakeDB
from arcaverborum.phonology import load_profile, normalize_segments

logger = logging.getLogger(__name__)

FALLBACK_SOURCE = "gled"
FALLBACK_FORMS_SCORE = 0.05

_INTAKE_USECOLS = frozenset({
    "ID", "Dataset", "Language_ID", "Parameter_ID",
    "Value", "Form", "Segments", "Comment", "Source", "Loan",
    "Cognacy", "Doubt", "Cognate_Detection_Method", "Cognate_Source",
    "Alignment", "Morpheme_Index", "Segment_Slice",
    "Glottocode", "Concepticon_ID", "Concepticon_Gloss",
})

_INTAKE_CHUNKSIZE = 200_000
_VARIETY_BATCH_SIZE = 500
_KEYED_HASH_MAX = 1000  # intake-DB path: per-slice hashing below this many slices


CUSTOM_TRANSCRIPTION_FIELDS = (
    "Concepticon_ID", "source_form_id", "Value", "Form", "Segments", "Comment", "notes",
)
CUSTOM_FORMS_FIELDS = (
    "concept_id", "Concepticon_ID", "Value", "Form", "Segments",
    "Cognacy", "Loan", "Comment", "notes",
)
CUSTOM_COGNATES_FIELDS = (
    "form_id", "Cognacy", "Alignment", "Cognate_Detection_Method", "Doubt", "notes",
)
CUSTOM_CONCEPT_MAP_FIELDS = (
    "Parameter_ID", "Concepticon_ID", "Concepticon_Gloss", "concept_id", "notes",
)


@dataclass(slots=True)
class VarietyDir:
    av_id: str
    root: Path

    @property
    def config_path(self) -> Path:
        return self.root / "config.yaml"

    @property
    def custom_dir(self) -> Path:
        return self.root / "custom"

    @property
    def generated_dir(self) -> Path:
        return self.root / "generated"

    @property
    def generated_forms(self) -> Path:
        return self.generated_dir / "forms.csv"

    def custom_path(self, name: str) -> Path:
        return self.custom_dir / name

    def exists(self) -> bool:
        return self.config_path.exists()


def _empty_csv(path: Path, fields: tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()


def scaffold_custom_files(vd: VarietyDir) -> list[Path]:
    """Create the empty custom/*.csv templates for hand-curation.

    Idempotent — existing files are left untouched. Returns the paths
    that now exist.
    """
    vd.custom_dir.mkdir(parents=True, exist_ok=True)
    created = []
    for name, fields in (
        ("transcriptions.csv", CUSTOM_TRANSCRIPTION_FIELDS),
        ("forms.csv", CUSTOM_FORMS_FIELDS),
        ("cognates.csv", CUSTOM_COGNATES_FIELDS),
        ("concept_map.csv", CUSTOM_CONCEPT_MAP_FIELDS),
    ):
        path = vd.custom_path(name)
        _empty_csv(path, fields)
        created.append(path)

    profile = vd.custom_path("profile.tsv")
    if not profile.exists():
        profile.write_text("Grapheme\tIPA\tnotes\n", encoding="utf-8")
    created.append(profile)
    return created


def register(
    av_id: str,
    varieties_root: Path,
    transcription_source: str,
    cognate_source: str = "",
    name: str = "",
    glottocode: str = "",
    family: str = "",
    macroarea: str = "",
    forms_score: float = 0.0,
    cognates_score: float = 0.0,
    tier: str = "copper",
    pinned: bool = False,
    notes: str = "",
    overwrite: bool = False,
    scaffold_custom: bool = False,
    source_language_id: str = "",
    source_glottocode: str = "",
) -> VarietyDir:
    """Create varieties/<av_id>/ with config.yaml.

    Custom CSV templates are only written when scaffold_custom=True
    (otherwise create them on demand via scaffold_custom_files / the
    `build.py extend` command). The build treats missing custom files
    as 'no extension'.
    """
    vd = VarietyDir(av_id=av_id, root=varieties_root / av_id)
    if vd.exists() and not overwrite:
        return vd

    vd.root.mkdir(parents=True, exist_ok=True)

    config = {
        "av_id": av_id,
        "name": name,
        "glottocode": glottocode,
        "family": family,
        "macroarea": macroarea,
        "sources": {
            "transcription": transcription_source,
            "cognates": cognate_source or transcription_source,
            **({"source_language_id": source_language_id} if source_language_id else {}),
            **({"source_glottocode": source_glottocode} if source_glottocode else {}),
        },
        "extensions": {
            "transcriptions": False,
            "forms": False,
            "cognates": False,
            "concept_map": False,
            "profile": False,
        },
        "scoring": {
            "forms_score": round(float(forms_score), 4),
            "cognates_score": round(float(cognates_score), 4),
            "tier": str(tier),
        },
        "pinned": pinned,
        "registered_on": date.today().isoformat(),
        "notes": notes,
    }
    with atomic_path(vd.config_path) as tmp, tmp.open("w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, sort_keys=False, allow_unicode=True)

    if scaffold_custom:
        scaffold_custom_files(vd)

    return vd


def load_config(vd: VarietyDir) -> dict:
    with vd.config_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _read_custom(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    if df.empty:
        return df
    non_empty = df.apply(lambda col: col.astype(str).str.strip() != "", axis=0)
    return df[non_empty.any(axis=1)]


def _apply_concept_map(forms: pd.DataFrame, concept_map: pd.DataFrame) -> pd.DataFrame:
    """Fix wrong source concept mappings, per Parameter_ID.

    A row may correct the Concepticon_ID/Gloss (re-resolved to our
    concept_id downstream) and/or pin our ``concept_id`` directly. The
    pinned concept_id is stashed in the ``_concept_id_override`` column
    that ``build_one`` consumes. ``action=unmap`` preserves the lexical row
    but blocks a wrong concept assignment, including parameter-index fallback.
    """
    if concept_map.empty or forms.empty:
        return forms
    def payload(row: pd.Series) -> tuple[str, str, str, str]:
        return (
            str(row.get("Concepticon_ID", "")).strip(),
            str(row.get("Concepticon_Gloss", "")).strip(),
            str(row.get("concept_id", "")).strip(),
            str(row.get("action", "") or "map").strip().lower() or "map",
        )

    cmap = {
        str(row.get("Parameter_ID", "")).strip(): payload(row)
        for _, row in concept_map.iterrows()
        if str(row.get("Parameter_ID", "")).strip() and not str(row.get("source_form_id", "")).strip()
    }
    form_maps = {
        str(row.get("source_form_id", "")).strip(): (
            payload(row), str(row.get("Parameter_ID", "")).strip(), str(row.get("expected_form", "")),
        )
        for _, row in concept_map.iterrows() if str(row.get("source_form_id", "")).strip()
    }
    if not cmap and not form_maps:
        return forms
    if form_maps:
        present = {str(row.get("ID", "") or row.get("source_form_id", "")).strip()
                   for _, row in forms.iterrows()}
        missing = form_maps.keys() - present
        if missing:
            raise ValueError(f"Reviewed concept source forms disappeared: {', '.join(sorted(missing))}")
    validations = [*cmap.items(), *((fid, values[0]) for fid, values in form_maps.items())]
    for pid, (cid, gloss, concept_id, action) in validations:
        if action not in ("map", "unmap"):
            raise ValueError(f"Unknown concept-map action {action!r} for {pid}")
        if action == "unmap" and any((cid, gloss, concept_id)):
            raise ValueError(f"Unmap action must not assign a concept for {pid}")

    forms = forms.copy()
    # Intake may carry only parameter IDs, with Concepticon resolved later.
    # Ensure mapped rows do not introduce NaN columns into untouched rows
    # when pandas combines the Series returned by apply below.
    for column in ("Concepticon_ID", "Concepticon_Gloss"):
        if column not in forms.columns:
            forms[column] = ""
    if "_concept_id_override" not in forms.columns:
        forms["_concept_id_override"] = ""
    if "_concept_mapping_blocked" not in forms.columns:
        forms["_concept_mapping_blocked"] = False

    def _fix_row(row: pd.Series) -> pd.Series:
        pid = str(row.get("Parameter_ID", "")).strip()
        fid = str(row.get("ID", "") or row.get("source_form_id", "")).strip()
        correction = cmap.get(pid)
        if fid in form_maps:
            correction, expected_pid, expected_form = form_maps[fid]
            if (expected_pid and pid != expected_pid) or (expected_form and row.get("Form", "") != expected_form):
                raise ValueError(f"Concept correction no longer matches source form {fid}")
        if correction is not None:
            cid, gloss, concept_id, action = correction
            row["_concept_mapping_blocked"] = action == "unmap"
            if action == "unmap":
                row["Concepticon_ID"] = ""
                row["Concepticon_Gloss"] = ""
                row["_concept_id_override"] = ""
                return row
            if cid:
                row["Concepticon_ID"] = cid
            if gloss:
                row["Concepticon_Gloss"] = gloss
            if concept_id:
                row["_concept_id_override"] = concept_id
        return row

    return forms.apply(_fix_row, axis=1)


def _apply_transcription_overrides(forms: pd.DataFrame, overrides: pd.DataFrame) -> pd.DataFrame:
    """Override transcription columns by source_form_id (primary) or by
    (Concepticon_ID, _) when no source_form_id is given.
    """
    if overrides.empty or forms.empty:
        return forms

    by_form_id: dict[str, dict] = {}
    by_concept: dict[str, dict] = {}
    for _, row in overrides.iterrows():
        fid = str(row.get("source_form_id", "")).strip()
        cid = str(row.get("Concepticon_ID", "")).strip()
        payload = {col: str(row.get(col, "")).strip()
                   for col in ("Value", "Form", "Segments", "Comment")}
        if not any(payload.values()):
            continue
        if fid:
            by_form_id[fid] = payload
        elif cid:
            by_concept[cid] = payload

    if not by_form_id and not by_concept:
        return forms

    forms = forms.copy()
    for col in ("Value", "Form", "Segments", "Comment"):
        if col not in forms.columns:
            forms[col] = ""
    for idx, row in forms.iterrows():
        fid = (str(row.get("ID", "")).strip()
               or str(row.get("source_form_id", "")).strip())
        cid = str(row.get("Concepticon_ID", "")).strip()
        override = by_form_id.get(fid) or by_concept.get(cid)
        if override is None:
            continue
        for col, val in override.items():
            if val:
                forms.at[idx, col] = val
    return forms


def _apply_cognate_overrides(forms: pd.DataFrame, overrides: pd.DataFrame) -> pd.DataFrame:
    if overrides.empty or forms.empty:
        return forms
    ov_index: dict[str, dict] = {}
    for _, row in overrides.iterrows():
        fid = str(row.get("form_id", "")).strip()
        if not fid:
            continue
        ov_index[fid] = {
            col: str(row.get(col, "")).strip()
            for col in ("Cognacy", "Alignment", "Cognate_Detection_Method", "Doubt")
        }
    if not ov_index:
        return forms
    forms = forms.copy()
    for col in ("Cognacy", "Alignment", "Cognate_Detection_Method", "Doubt"):
        if col not in forms.columns:
            forms[col] = ""
    for idx, row in forms.iterrows():
        fid = (str(row.get("ID", "")).strip()
               or str(row.get("source_form_id", "")).strip())
        if fid not in ov_index:
            continue
        for col, val in ov_index[fid].items():
            if val:
                forms.at[idx, col] = val
    return forms


def _additive_custom_rows(
    custom_forms: pd.DataFrame,
    av_id: str,
    variety: Variety,
    forms_score: float,
    tier: str,
    concept_index: dict[str, tuple[str, str]],
    concept_labels: dict[str, str],
    profile: dict[str, str] | None = None,
) -> list[dict]:
    if custom_forms.empty:
        return []
    rows = []
    for i, row in custom_forms.iterrows():
        form = str(row.get("Form", "")).strip()
        if not form:
            continue
        src_segments = str(row.get("Segments", "")).strip()
        src_form = str(row.get("Form", "")).strip() or str(row.get("Value", "")).strip()
        segments, seg_source = normalize_segments(src_segments, src_form, profile)
        custom_id = f"custom_{av_id}_{i + 1}"
        concepticon_id = str(row.get("Concepticon_ID", "")).strip()
        explicit = str(row.get("concept_id", "")).strip()
        if explicit:
            concept_id = explicit
            concept_label = concept_labels.get(explicit, "")
        else:
            concept_id, concept_label = concept_index.get(concepticon_id, ("", ""))
        out_row = {
            "av_id": av_id,
            "Glottocode": variety.glottocode,
            "Variety_Name": variety.name or variety.av_id,
            "concept_id": concept_id,
            "concept_label": concept_label,
            "Concepticon_ID": concepticon_id,
            "Value": str(row.get("Value", "")).strip(),
            "Form": form,
            "Segments": segments,
            "Segments_Source": seg_source,
            "Cognacy": str(row.get("Cognacy", "")).strip(),
            "canonical_cognate_id": "",
            "Alignment": "",
            "Morpheme_Index": "",
            "Segment_Slice": "",
            "Doubt": "",
            "Cognate_Detection_Method": "custom",
            "Cognate_Source": "",
            "Loan": str(row.get("Loan", "")).strip(),
            "Comment": str(row.get("Comment", "")).strip(),
            "transcription_source": "custom",
            "cognate_source": "custom",
            "source_form_id": custom_id,
            "source_language_id": av_id,
            "source_parameter_id": "",
            "bibtex_key": "",
            "quality_score": f"{form_quality_score(row.to_dict(), forms_score):.4f}",
            "tier": tier,
        }
        rows.append(out_row)
    return rows


def apply_overlays(
    df: pd.DataFrame,
    vd: VarietyDir,
) -> tuple[pd.DataFrame, list | None]:
    """Apply the variety's custom overrides and return (modified_df, profile)."""
    cmap = _read_custom(vd.custom_path("concept_map.csv"))
    if not cmap.empty:
        df = _apply_concept_map(df, cmap)

    tov = _read_custom(vd.custom_path("transcriptions.csv"))
    if not tov.empty:
        df = _apply_transcription_overrides(df, tov)

    cov = _read_custom(vd.custom_path("cognates.csv"))
    if not cov.empty:
        df = _apply_cognate_overrides(df, cov)

    profile = load_profile(vd.custom_path("profile.tsv"))
    return df, profile


def emit_forms(
    df: pd.DataFrame,
    *,
    av_id: str,
    variety: Variety,
    transcription_source: str,
    cognate_source: str,
    forms_score: float,
    tier: str,
    param_index: dict[str, tuple[str, str]],
    concept_index: dict[str, tuple[str, str]],
    concept_labels: dict[str, str],
    profile: list | None,
) -> list[dict]:
    """Transform overlaid intake rows into output dicts."""
    out_rows: list[dict] = []
    for _, row in df.iterrows():
        param_id = row.get("Parameter_ID", "")
        looked_cid, _looked_gloss = param_index.get(param_id, ("", ""))
        concepticon_id = row.get("Concepticon_ID", "") or looked_cid
        override = str(row.get("_concept_id_override", "") or "").strip()
        if row.get("_concept_mapping_blocked", False):
            concepticon_id = concept_id = concept_label = ""
        elif override:
            concept_id = override
            concept_label = concept_labels.get(override, "")
        else:
            concept_id, concept_label = concept_index.get(concepticon_id, ("", ""))
        src_segments = row.get("Segments", "") or ""
        src_form = row.get("Form", "") or row.get("Value", "") or ""
        segments, seg_source = normalize_segments(src_segments, src_form, profile)
        out_rows.append({
            "av_id": av_id,
            "Glottocode": variety.glottocode,
            "Variety_Name": variety.name or variety.av_id,
            "concept_id": concept_id,
            "concept_label": concept_label,
            "Concepticon_ID": concepticon_id,
            "Value": row.get("Value", ""),
            "Form": row.get("Form", ""),
            "Segments": segments,
            "Segments_Source": seg_source,
            "Cognacy": row.get("Cognacy", ""),
            "canonical_cognate_id": "",
            "Alignment": row.get("Alignment", ""),
            "Morpheme_Index": row.get("Morpheme_Index", ""),
            "Segment_Slice": row.get("Segment_Slice", ""),
            "Doubt": row.get("Doubt", ""),
            "Cognate_Detection_Method": row.get("Cognate_Detection_Method", ""),
            "Cognate_Source": row.get("Cognate_Source", ""),
            "Loan": row.get("Loan", ""),
            "Comment": row.get("Comment", ""),
            "transcription_source": transcription_source,
            "cognate_source": cognate_source,
            "source_form_id": row.get("ID", ""),
            "source_language_id": row.get("Language_ID", ""),
            "source_parameter_id": param_id,
            "bibtex_key": row.get("Source", ""),
            "quality_score": f"{form_quality_score(row.to_dict(), forms_score):.4f}",
            "tier": tier,
        })
    return out_rows


def build_one(
    av_id: str,
    varieties_root: Path,
    intake_forms: Path | pd.DataFrame | IntakeDB,
    catalog: dict[str, Variety],
    parameters_path: Path | None = None,
    param_index: dict[str, tuple[str, str]] | None = None,
    concept_index: dict[str, tuple[str, str]] | None = None,
    concept_labels: dict[str, str] | None = None,
) -> int:
    """Build varieties/<av_id>/generated/forms.csv. Returns row count."""
    vd = VarietyDir(av_id=av_id, root=varieties_root / av_id)
    if not vd.exists():
        raise FileNotFoundError(f"Variety {av_id} not registered")
    if av_id not in catalog:
        raise KeyError(f"Variety {av_id} not in catalog")

    config = load_config(vd)
    variety = catalog[av_id]
    transcription_source = config["sources"]["transcription"]
    cognate_source = config["sources"].get("cognates", "") or transcription_source
    source_language_id = str(config["sources"].get("source_language_id", "") or "").strip()
    source_glottocode = str(config["sources"].get("source_glottocode", "") or "").strip()
    forms_score = float(config.get("scoring", {}).get("forms_score", 0.0))
    tier = config.get("scoring", {}).get("tier", "copper")
    gc = (source_glottocode or variety.glottocode or av_id).lower()
    extra_codes = config["sources"].get("source_glottocodes", [])
    member_ids = config["sources"].get("source_language_ids", [])
    if (not isinstance(extra_codes, list) or not isinstance(member_ids, list)
            or any(not isinstance(x, str) or not x.strip() for x in [*extra_codes, *member_ids])):
        raise ValueError("Reviewed source selectors must be lists of nonempty strings")
    if extra_codes and not member_ids:
        raise ValueError("A source-code union requires explicit reviewed source members")
    if source_language_id and member_ids:
        raise ValueError("Use either a single source member or a reviewed member list")
    source_codes = sorted({gc, *(code.strip().lower() for code in extra_codes)})

    if param_index is None:
        param_index = load_parameter_index(parameters_path) if parameters_path else {}
    if concept_index is None or concept_labels is None:
        concept_index, concept_labels = load_concept_maps()

    if isinstance(intake_forms, IntakeDB):
        df = (intake_forms.slice_many(source_codes, transcription_source) if len(source_codes) > 1
              else intake_forms.slice(gc, transcription_source))
    elif isinstance(intake_forms, pd.DataFrame):
        df = intake_forms
        if "_glottocode_lc" in df.columns:
            df = df[(df["_glottocode_lc"].isin(source_codes)) & (df["Dataset"] == transcription_source)].copy()
        else:
            df = df[(df["Glottocode"].astype(str).str.strip().str.lower().isin(source_codes))
                    & (df["Dataset"] == transcription_source)].copy()
    else:
        df = pd.read_csv(intake_forms, dtype=str, keep_default_na=False)
        df["Glottocode"] = df["Glottocode"].astype(str).str.strip().str.lower()
        df = df[(df["Glottocode"].isin(source_codes)) & (df["Dataset"] == transcription_source)].copy()

    if source_language_id and not df.empty:
        df = df[df["Language_ID"].astype(str).str.strip() == source_language_id].copy()

    if member_ids:
        missing = set(member_ids) - set(df["Language_ID"])
        if missing:
            raise ValueError("Reviewed source members disappeared: " + ', '.join(sorted(missing)))
        df = df[df["Language_ID"].isin(member_ids)].copy()

    if df.empty and transcription_source != FALLBACK_SOURCE and isinstance(intake_forms, (pd.DataFrame, IntakeDB)):
        if isinstance(intake_forms, IntakeDB):
            fb = intake_forms.slice(gc, FALLBACK_SOURCE)
        elif "_glottocode_lc" in intake_forms.columns:
            fb = intake_forms[(intake_forms["_glottocode_lc"] == gc)
                              & (intake_forms["Dataset"] == FALLBACK_SOURCE)].copy()
        else:
            fb = intake_forms[(intake_forms["Glottocode"].astype(str).str.strip().str.lower() == gc)
                              & (intake_forms["Dataset"] == FALLBACK_SOURCE)].copy()
        if not fb.empty:
            df = fb
            transcription_source = FALLBACK_SOURCE
            cognate_source = FALLBACK_SOURCE
            forms_score = FALLBACK_FORMS_SCORE
            tier = "copper"
            logger.info("Fallback to %s for %s (%d forms)", FALLBACK_SOURCE, av_id, len(df))

    if df.empty and not vd.custom_path("forms.csv").exists():
        write_text_atomic(vd.generated_forms, ",".join(FORMS_OUT_FIELDS) + "\n")
        return 0

    from arcaverborum.wiktionary_senses import apply_shared

    df = apply_shared(df, transcription_source)
    df, profile = apply_overlays(df, vd)

    out_rows = emit_forms(
        df,
        av_id=av_id,
        variety=variety,
        transcription_source=transcription_source,
        cognate_source=cognate_source,
        forms_score=forms_score,
        tier=tier,
        param_index=param_index,
        concept_index=concept_index,
        concept_labels=concept_labels,
        profile=profile,
    )

    custom_forms_df = _read_custom(vd.custom_path("forms.csv"))
    out_rows.extend(_additive_custom_rows(
        custom_forms_df, av_id, variety, forms_score, tier,
        concept_index, concept_labels, profile,
    ))

    out_df = pd.DataFrame(out_rows, columns=list(FORMS_OUT_FIELDS))
    with atomic_path(vd.generated_forms) as tmp:
        out_df.to_csv(tmp, index=False)
    logger.info("Built %s: %d forms → %s", av_id, len(out_rows), vd.generated_forms)
    return len(out_rows)


def update_config_extension_flags(vd: VarietyDir) -> None:
    """Refresh extensions.* flags in config.yaml — but only write when
    the flags actually changed (preserves config.yaml mtime so
    freshness checks in build.py status work correctly)."""
    config = load_config(vd)
    existing = config.get("extensions") or {}
    new_flags = {}
    for name, path_basename in (
        ("transcriptions", "transcriptions.csv"),
        ("forms", "forms.csv"),
        ("cognates", "cognates.csv"),
        ("concept_map", "concept_map.csv"),
    ):
        df = _read_custom(vd.custom_path(path_basename))
        new_flags[name] = not df.empty
    new_flags["profile"] = bool(load_profile(vd.custom_path("profile.tsv")))

    if existing == new_flags:
        return

    config["extensions"] = new_flags
    with atomic_path(vd.config_path) as tmp, tmp.open("w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, sort_keys=False, allow_unicode=True)


def _load_intake_for_glottocodes(
    paths: list[Path],
    glottocodes: set[str],
) -> pd.DataFrame:
    """Stream intake CSVs and return only rows matching *glottocodes*."""
    frames: list[pd.DataFrame] = []
    for path in paths:
        if not path.exists():
            continue
        for chunk in pd.read_csv(
            path, dtype=str, keep_default_na=False,
            chunksize=_INTAKE_CHUNKSIZE,
            usecols=lambda c: c in _INTAKE_USECOLS,
        ):
            chunk = chunk.fillna("")
            gc = chunk["Glottocode"].astype(str).str.strip().str.lower()
            mask = gc.isin(glottocodes)
            if mask.any():
                filtered = chunk[mask].copy()
                filtered["_glottocode_lc"] = gc[mask]
                frames.append(filtered)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def update_many(
    av_ids: list[str],
    varieties_root: Path,
    intake_forms_paths: list[Path],
    intake_parameters_paths: list[Path],
    intake_languages_paths: list[Path],
    force: bool = False,
    intake_db: Path | None = None,
) -> dict:
    """Load shared context once, then build every stale variety.

    Intake data is streamed in chunks to keep memory bounded, rather
    than loading the full ~10 GB DataFrame at once.

    Returns a stats dict with built/skipped/failed counts.
    """
    from arcaverborum import tracking
    from arcaverborum.catalog import build_catalog, load_avid_registry
    from arcaverborum.glottolog import load_glottolog

    glottolog = load_glottolog()
    registry = load_avid_registry()
    catalog = build_catalog(
        [p for p in intake_languages_paths if p.exists()],
        glottolog=glottolog,
        avid_registry=registry,
    )

    param_index: dict[str, tuple[str, str]] = {}
    for pp in intake_parameters_paths:
        if pp.exists():
            param_index.update(load_parameter_index(pp))
    concept_index, concept_labels = load_concept_maps()

    recipe = tracking.recipe_hash()

    existing_paths = [p for p in intake_forms_paths if p.exists()]
    db: IntakeDB | None = None
    if intake_db is not None and existing_paths:
        db = open_intake_db(intake_db, existing_paths)
        wanted: set[tuple[str, str]] = set()
        for av_id in av_ids:
            vd = VarietyDir(av_id=av_id, root=varieties_root / av_id)
            if not vd.exists():
                continue
            try:
                cfg = load_config(vd)
            except Exception:
                continue
            src_gc = str((cfg.get("sources") or {}).get("source_glottocode", "") or "").strip()
            gc = src_gc or (catalog[av_id].glottocode if av_id in catalog else "") or av_id
            for input_code in {gc.lower(), *((cfg.get("sources") or {}).get("source_glottocodes", []))}:
                wanted.add((input_code.strip().lower(), (cfg.get("sources") or {}).get("transcription", "")))
            wanted.add((gc.lower(), FALLBACK_SOURCE))  # see _slice_component
        # Few varieties: one indexed query per slice. Many: one sequential
        # scan is cheaper. Both give the same digest for every wanted key.
        slice_hashes = tracking.compute_slice_hashes_from_db(
            db, param_index, keys=wanted if len(wanted) <= _KEYED_HASH_MAX else None,
        )
    else:
        slice_hashes = tracking.compute_slice_hashes_from_files(existing_paths, param_index)
    logger.info("Computed slice hashes for %d (glottocode, dataset) groups", len(slice_hashes))

    stale: list[tuple[str, str, dict]] = []
    skipped = 0
    for av_id in av_ids:
        vd = VarietyDir(av_id=av_id, root=varieties_root / av_id)
        if not vd.exists():
            continue
        try:
            cfg = load_config(vd)
        except Exception:
            continue
        src_gc = str((cfg.get("sources") or {}).get("source_glottocode", "") or "").strip()
        gc = src_gc or (catalog[av_id].glottocode if av_id in catalog else "") or av_id
        slice_h = _slice_component(cfg, gc, slice_hashes)
        digest, components = tracking.fingerprint(
            tracking.config_component(cfg),
            tracking.custom_component(vd.custom_dir),
            slice_h,
            recipe,
        )
        if not force and tracking.is_fresh(vd.generated_dir, digest, vd.generated_forms):
            skipped += 1
            continue
        stale.append((av_id, digest, components))

    logger.info("Stale: %d varieties to build, %d skipped (unchanged)", len(stale), skipped)

    if db is not None:
        try:
            return _build_stale_from_db(
                stale, skipped, varieties_root, db, catalog,
                param_index, concept_index, concept_labels,
            )
        finally:
            db.close()

    gc_to_avids: dict[str, list[tuple[str, str, dict]]] = {}
    for av_id, digest, components in stale:
        vd_tmp = VarietyDir(av_id=av_id, root=varieties_root / av_id)
        cfg_tmp = load_config(vd_tmp)
        src_gc = str((cfg_tmp.get("sources") or {}).get("source_glottocode", "") or "").strip()
        gc = src_gc or (catalog[av_id].glottocode if av_id in catalog else "") or av_id
        gc_to_avids.setdefault(gc.lower(), []).append((av_id, digest, components))

    gc_list = list(gc_to_avids.keys())
    total_forms = built = failed = 0
    processed = 0

    for batch_start in range(0, len(gc_list), _VARIETY_BATCH_SIZE):
        batch_gcs = set(gc_list[batch_start:batch_start + _VARIETY_BATCH_SIZE])
        input_gcs = set(batch_gcs)
        for batch_gc in batch_gcs:
            for batch_aid, _, _ in gc_to_avids[batch_gc]:
                batch_cfg = load_config(VarietyDir(av_id=batch_aid, root=varieties_root / batch_aid))
                input_gcs.update(code.strip().lower() for code in
                                 (batch_cfg.get("sources") or {}).get("source_glottocodes", []))
        intake_df = _load_intake_for_glottocodes(existing_paths, input_gcs)
        batch_num = batch_start // _VARIETY_BATCH_SIZE + 1
        total_batches = (len(gc_list) + _VARIETY_BATCH_SIZE - 1) // _VARIETY_BATCH_SIZE
        logger.info("Batch %d/%d: %d glottocodes, %d intake rows loaded",
                     batch_num, total_batches, len(batch_gcs),
                     len(intake_df) if not intake_df.empty else 0)

        for gc in batch_gcs:
            for av_id, digest, components in gc_to_avids[gc]:
                vd = VarietyDir(av_id=av_id, root=varieties_root / av_id)
                try:
                    n = build_one(
                        av_id=av_id,
                        varieties_root=varieties_root,
                        intake_forms=intake_df if not intake_df.empty else pd.DataFrame(),
                        catalog=catalog,
                        param_index=param_index,
                        concept_index=concept_index,
                        concept_labels=concept_labels,
                    )
                    update_config_extension_flags(vd)
                    tracking.write_manifest(vd.generated_dir, digest, components, n)
                    total_forms += n
                    built += 1
                except Exception as exc:
                    failed += 1
                    logger.error("Failed to build %s: %s", av_id, exc)
                processed += 1
                if processed % 200 == 0:
                    logger.info("Progress: %d/%d (built %d, skipped %d)",
                                processed, len(stale), built, skipped)

        del intake_df

    logger.info("Done: %d built (%d forms), %d skipped (unchanged), %d failed",
                built, total_forms, skipped, failed)
    return {"built": built, "total_forms": total_forms, "skipped": skipped, "failed": failed}


def _slice_component(cfg: dict, gc: str, slice_hashes: dict[tuple[str, str], str]) -> str:
    """The intake rows a variety's build can read, as one tracking component.

    That is its (glottocode, transcription source) slice and, whenever
    `build_one` might fall back to GLED, the GLED slice too: when the
    primary slice is empty, or when a source_language_id filter could
    empty it. Without this, a GLED-fallback variety did not notice GLED
    changes.
    """
    sources = cfg.get("sources") or {}
    ts = sources.get("transcription", "")
    extra_codes = sources.get("source_glottocodes", [])
    if extra_codes:
        primary = "|".join(code + ':' + slice_hashes.get((code, ts), '')
                           for code in sorted({gc.lower(), *(c.strip().lower() for c in extra_codes)}))
    else:
        primary = slice_hashes.get((gc.lower(), ts), "")
    lid = str(sources.get("source_language_id", "") or "").strip()
    if ts != FALLBACK_SOURCE and (not primary or lid or sources.get("source_language_ids")):
        return f"{primary}|{FALLBACK_SOURCE}:{slice_hashes.get((gc.lower(), FALLBACK_SOURCE), '')}"
    return primary


def open_intake_db(db_path: Path, forms_paths: list[Path]) -> IntakeDB:
    """Open the intake DB, (re)building it first when missing or stale."""
    from arcaverborum.intake_db import build_intake_db

    db_path = Path(db_path)
    try:
        db = IntakeDB(db_path)
    except FileNotFoundError:
        logger.info("Intake DB %s missing; building", db_path)
    except (sqlite3.Error, ValueError, KeyError) as exc:
        logger.warning("Intake DB %s unreadable (%s); rebuilding", db_path, exc)
    else:
        if db.is_current(forms_paths):
            return db
        db.close()
        logger.info("Intake DB %s is stale; rebuilding", db_path)
    build_intake_db(forms_paths, db_path, _INTAKE_USECOLS)
    return IntakeDB(db_path)


def _build_stale_from_db(
    stale: list[tuple[str, str, dict]],
    skipped: int,
    varieties_root: Path,
    db: IntakeDB,
    catalog: dict[str, Variety],
    param_index: dict[str, tuple[str, str]],
    concept_index: dict[str, tuple[str, str]],
    concept_labels: dict[str, str],
) -> dict:
    """Build each stale variety, reading its slice from the intake DB."""
    from arcaverborum import tracking

    total_forms = built = failed = 0
    for processed, (av_id, digest, components) in enumerate(stale, start=1):
        vd = VarietyDir(av_id=av_id, root=varieties_root / av_id)
        try:
            n = build_one(
                av_id=av_id,
                varieties_root=varieties_root,
                intake_forms=db,
                catalog=catalog,
                param_index=param_index,
                concept_index=concept_index,
                concept_labels=concept_labels,
            )
            update_config_extension_flags(vd)
            tracking.write_manifest(vd.generated_dir, digest, components, n)
            total_forms += n
            built += 1
        except Exception as exc:
            failed += 1
            logger.error("Failed to build %s: %s", av_id, exc)
        if processed % 200 == 0:
            logger.info("Progress: %d/%d (built %d, skipped %d)",
                        processed, len(stale), built, skipped)

    logger.info("Done: %d built (%d forms), %d skipped (unchanged), %d failed",
                built, total_forms, skipped, failed)
    return {"built": built, "total_forms": total_forms, "skipped": skipped, "failed": failed}

