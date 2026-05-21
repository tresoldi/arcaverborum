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
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd
import yaml

from arcaverborum.aggregate import FORMS_OUT_FIELDS, _form_quality_score, _load_parameter_index
from arcaverborum.catalog import Variety
from arcaverborum.concepts import load_concept_maps
from arcaverborum.phonology import load_profile, normalize_segments

logger = logging.getLogger(__name__)


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
    with vd.config_path.open("w", encoding="utf-8") as f:
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
    that ``build_one`` consumes.
    """
    if concept_map.empty or forms.empty:
        return forms
    cmap = {
        str(row["Parameter_ID"]).strip(): (
            str(row.get("Concepticon_ID", "")).strip(),
            str(row.get("Concepticon_Gloss", "")).strip(),
            str(row.get("concept_id", "")).strip(),
        )
        for _, row in concept_map.iterrows()
        if str(row.get("Parameter_ID", "")).strip()
    }
    if not cmap:
        return forms

    forms = forms.copy()
    if "_concept_id_override" not in forms.columns:
        forms["_concept_id_override"] = ""

    def _fix_row(row: pd.Series) -> pd.Series:
        pid = str(row.get("Parameter_ID", "")).strip()
        if pid in cmap:
            cid, gloss, concept_id = cmap[pid]
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
            "quality_score": f"{_form_quality_score(row.to_dict(), forms_score):.4f}",
            "tier": tier,
        }
        rows.append(out_row)
    return rows


def build_one(
    av_id: str,
    varieties_root: Path,
    intake_forms: Path | pd.DataFrame,
    catalog: dict[str, Variety],
    parameters_path: Path | None = None,
    param_index: dict[str, tuple[str, str]] | None = None,
    concept_index: dict[str, tuple[str, str]] | None = None,
    concept_labels: dict[str, str] | None = None,
) -> int:
    """Build varieties/<av_id>/generated/forms.csv. Returns row count.

    `intake_forms` may be a Path (load fresh, useful for one-off builds)
    or a pre-loaded DataFrame (when batching many varieties — caller
    loads once and passes here repeatedly). `param_index` (Parameter_ID
    → Concepticon) and the concept lookups (`concept_index` mapping a
    Concepticon id to our `(concept_id, label)`; `concept_labels` mapping
    a concept_id to its label) can all be pre-built and reused.
    """
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
    forms_score = float(config.get("scoring", {}).get("forms_score", 0.0))
    tier = config.get("scoring", {}).get("tier", "copper")
    gc = (variety.glottocode or av_id).lower()

    if param_index is None:
        param_index = _load_parameter_index(parameters_path) if parameters_path else {}
    if concept_index is None or concept_labels is None:
        concept_index, concept_labels = load_concept_maps()

    if isinstance(intake_forms, pd.DataFrame):
        df = intake_forms
        if "_glottocode_lc" in df.columns:
            df = df[(df["_glottocode_lc"] == gc) & (df["Dataset"] == transcription_source)].copy()
        else:
            df = df[(df["Glottocode"].astype(str).str.strip().str.lower() == gc)
                    & (df["Dataset"] == transcription_source)].copy()
    else:
        df = pd.read_csv(intake_forms, dtype=str, keep_default_na=False)
        df["Glottocode"] = df["Glottocode"].astype(str).str.strip().str.lower()
        df = df[(df["Glottocode"] == gc) & (df["Dataset"] == transcription_source)].copy()

    # When several source languages share a Glottocode (e.g. IECOR's Old
    # Czech vs Czech), restrict to the one this variety represents.
    if source_language_id and not df.empty:
        df = df[df["Language_ID"].astype(str).str.strip() == source_language_id].copy()

    if df.empty and not vd.custom_path("forms.csv").exists():
        vd.generated_forms.write_text(",".join(FORMS_OUT_FIELDS) + "\n", encoding="utf-8")
        return 0

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

    out_rows = []
    for _, row in df.iterrows():
        param_id = row.get("Parameter_ID", "")
        looked_cid, _looked_gloss = param_index.get(param_id, ("", ""))
        concepticon_id = row.get("Concepticon_ID", "") or looked_cid
        # Resolve to our concept catalog: explicit override (concept_map)
        # wins, else the Concepticon-id mapping.
        override = str(row.get("_concept_id_override", "") or "").strip()
        if override:
            concept_id = override
            concept_label = concept_labels.get(override, "")
        else:
            concept_id, concept_label = concept_index.get(concepticon_id, ("", ""))
        src_segments = row.get("Segments", "") or ""
        src_form = row.get("Form", "") or row.get("Value", "") or ""
        segments, seg_source = normalize_segments(src_segments, src_form, profile)
        out_row = {
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
            "quality_score": f"{_form_quality_score(row.to_dict(), forms_score):.4f}",
            "tier": tier,
        }
        out_rows.append(out_row)

    custom_forms_df = _read_custom(vd.custom_path("forms.csv"))
    out_rows.extend(_additive_custom_rows(
        custom_forms_df, av_id, variety, forms_score, tier,
        concept_index, concept_labels, profile,
    ))

    vd.generated_forms.parent.mkdir(parents=True, exist_ok=True)
    out_df = pd.DataFrame(out_rows, columns=list(FORMS_OUT_FIELDS))
    out_df.to_csv(vd.generated_forms, index=False)
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
    with vd.config_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, sort_keys=False, allow_unicode=True)
