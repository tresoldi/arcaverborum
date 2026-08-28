"""Content-based build tracking for per-variety regeneration.

A variety's `generated/forms.csv` is a pure function of four inputs:

  config    output-relevant fields of config.yaml (source picks, scoring,
            identity) — *not* the extensions flags, which `build_one`
            rewrites after every build.
  custom    the four custom/*.csv override files (raw bytes).
  slice     the variety's own intake rows (Glottocode × transcription
            source), with Concepticon resolution folded in so a change to
            parameters_raw.csv that touches this variety's concepts also
            shows up here.
  recipe    the transform code (variety.py, phonology.py, aggregate.py),
            score weights, and the merkmal version.

Each input has a short component digest; their combination is the
variety's *fingerprint*, stored in `generated/build_manifest.json`. On
`update`, a variety is rebuilt only when its current fingerprint differs
from the stored one (or `--force` is given). The manifest lives under the
gitignored `generated/`, so a fresh checkout has no manifests and rebuilds
everything — which is correct, since it has no output either.
"""

from __future__ import annotations

import hashlib
import json
import logging
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

MANIFEST_NAME = "build_manifest.json"

_PKG_DIR = Path(__file__).resolve().parent
_RECIPE_FILES = (
    "variety.py", "phonology.py", "aggregate.py", "forms_schema.py", "concepts.py",
    "data/score_weights.yaml",
    # The frozen concept catalog: re-curating a label/field/id rebuilds the
    # forms that resolve through it.
    "data/concepts.csv", "data/semantic_field_codes.csv",
)

_CUSTOM_FILES = ("transcriptions.csv", "forms.csv", "cognates.csv", "concept_map.csv", "profile.tsv")

# Columns of the intake forms table that build_one actually consumes
# (Concepticon resolution is added separately via the parameter index).
_SLICE_CONTENT_COLS = (
    "Value", "Form", "Segments", "Cognacy", "Alignment", "Morpheme_Index",
    "Segment_Slice", "Doubt", "Cognate_Detection_Method", "Cognate_Source",
    "Loan", "Comment", "ID", "Language_ID", "Source", "Parameter_ID",
)


def _sha16(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def recipe_hash() -> str:
    """Digest of the build recipe: transform modules, score weights, merkmal.

    Cheap; compute once per `update` run and reuse for every variety.
    """
    h = hashlib.sha256()
    for rel in _RECIPE_FILES:
        p = _PKG_DIR / rel
        h.update(rel.encode("utf-8"))
        h.update(p.read_bytes() if p.exists() else b"")
    try:
        import merkmal

        h.update(str(getattr(merkmal, "__version__", "?")).encode("utf-8"))
    except Exception:
        h.update(b"merkmal-missing")
    return h.hexdigest()[:16]


def config_component(config: dict) -> str:
    """Digest of the output-relevant config fields (excludes extensions,
    notes, registered_on, pinned, macroarea, cognates_score)."""
    sources = config.get("sources") or {}
    scoring = config.get("scoring") or {}
    subset = {
        "glottocode": str(config.get("glottocode", "")),
        "name": str(config.get("name", "")),
        "transcription": str(sources.get("transcription", "")),
        "cognates": str(sources.get("cognates", "") or sources.get("transcription", "")),
        "source_language_id": str(sources.get("source_language_id", "")),
        "source_glottocode": str(sources.get("source_glottocode", "")),
        "forms_score": round(float(scoring.get("forms_score", 0.0) or 0.0), 4),
        "tier": str(scoring.get("tier", "")),
    }
    return _sha16(json.dumps(subset, sort_keys=True))


def custom_component(custom_dir: Path) -> str:
    """Digest of the four custom override files (raw bytes; "" if absent)."""
    digests = {}
    for name in _CUSTOM_FILES:
        p = custom_dir / name
        digests[name] = hashlib.sha1(p.read_bytes()).hexdigest() if p.exists() else ""
    return _sha16(json.dumps(digests, sort_keys=True))


def compute_intake_slice_hashes(
    intake_df: pd.DataFrame,
    param_index: dict[str, tuple[str, str]],
) -> dict[tuple[str, str], str]:
    """One pass over the full intake → {(glottocode_lc, Dataset): slice_hash}.

    The slice hash is order-independent of intake row order (rows are
    sorted by ID before hashing) and folds in the resolved Concepticon
    ID/Gloss, mirroring exactly the inputs `build_one` reads for a
    variety's (Glottocode, transcription-source) slice.
    """
    df = intake_df
    empty = pd.Series([""] * len(df), index=df.index)

    pid = df.get("Parameter_ID", empty).astype(str)
    cid_map = {p: v[0] for p, v in param_index.items()}
    gloss_map = {p: v[1] for p, v in param_index.items()}
    eff_cid = df.get("Concepticon_ID", empty).astype(str)
    eff_cid = eff_cid.where(eff_cid.str.strip() != "", pid.map(cid_map).fillna(""))
    eff_gloss = df.get("Concepticon_Gloss", empty).astype(str)
    eff_gloss = eff_gloss.where(eff_gloss.str.strip() != "", pid.map(gloss_map).fillna(""))

    content = {"cid": eff_cid, "gloss": eff_gloss}
    for col in _SLICE_CONTENT_COLS:
        content[col] = df.get(col, empty).astype(str)
    row_h = pd.util.hash_pandas_object(pd.DataFrame(content), index=False).to_numpy()

    gc = df.get("_glottocode_lc")
    if gc is None:
        gc = df.get("Glottocode", empty).astype(str).str.strip().str.lower()

    keyer = pd.DataFrame({
        "gc": gc.to_numpy(),
        "ds": df.get("Dataset", empty).to_numpy(),
        "id": df.get("ID", empty).astype(str).to_numpy(),
        "h": row_h,
    })
    keyer.sort_values(["gc", "ds", "id"], kind="stable", inplace=True)

    out: dict[tuple[str, str], str] = {}
    for (gcode, dataset), grp in keyer.groupby(["gc", "ds"], sort=False):
        digest = hashlib.sha1(grp["h"].to_numpy().tobytes()).hexdigest()[:16]
        out[(str(gcode), str(dataset))] = f"{digest}:{len(grp)}"
    return out


def _hash_chunk(
    chunk: pd.DataFrame,
    cid_map: dict[str, str],
    gloss_map: dict[str, str],
) -> pd.DataFrame:
    """Compute per-row hashes for a chunk, return (gc, ds, h) keyer."""
    n = len(chunk)
    empty = pd.Series([""] * n, index=chunk.index)

    pid = chunk.get("Parameter_ID", empty).astype(str)
    eff_cid = chunk.get("Concepticon_ID", empty).astype(str)
    eff_cid = eff_cid.where(eff_cid.str.strip() != "", pid.map(cid_map).fillna(""))
    eff_gloss = chunk.get("Concepticon_Gloss", empty).astype(str)
    eff_gloss = eff_gloss.where(eff_gloss.str.strip() != "", pid.map(gloss_map).fillna(""))

    content = {"cid": eff_cid, "gloss": eff_gloss}
    for col in _SLICE_CONTENT_COLS:
        content[col] = chunk.get(col, empty).astype(str)
    row_h = pd.util.hash_pandas_object(pd.DataFrame(content), index=False).to_numpy()

    gc = chunk.get("Glottocode", empty).astype(str).str.strip().str.lower()
    return pd.DataFrame({
        "gc": gc.to_numpy(),
        "ds": chunk.get("Dataset", empty).to_numpy(),
        "h": row_h,
    })


def compute_slice_hashes_from_files(
    paths: list[Path],
    param_index: dict[str, tuple[str, str]],
    chunksize: int = 200_000,
) -> dict[tuple[str, str], str]:
    """Streaming version of compute_intake_slice_hashes.

    Reads CSVs in chunks so peak memory stays bounded (~200 MB for
    the chunk + ~54 MB for accumulated hashes), instead of the ~15 GB
    the in-memory version needs on the full intake.
    """
    cid_map = {p: v[0] for p, v in param_index.items()}
    gloss_map = {p: v[1] for p, v in param_index.items()}

    buckets: dict[tuple[str, str], list[np.ndarray]] = defaultdict(list)

    for path in paths:
        if not path.exists():
            continue
        reader = pd.read_csv(
            path, dtype=str, keep_default_na=False, chunksize=chunksize,
        )
        for chunk in reader:
            chunk = chunk.fillna("")
            keyer = _hash_chunk(chunk, cid_map, gloss_map)
            for (gcode, dataset), grp in keyer.groupby(["gc", "ds"], sort=False):
                buckets[(str(gcode), str(dataset))].append(grp["h"].to_numpy())

    out: dict[tuple[str, str], str] = {}
    for key, arrays in buckets.items():
        all_h = np.concatenate(arrays)
        all_h.sort()
        digest = hashlib.sha1(all_h.tobytes()).hexdigest()[:16]
        out[key] = f"{digest}:{len(all_h)}"
    return out


def fingerprint(
    config_comp: str,
    custom_comp: str,
    slice_comp: str,
    recipe_comp: str,
) -> tuple[str, dict[str, str]]:
    """Combine the four component digests into a variety fingerprint.

    Returns (fingerprint, components) — components are stored in the
    manifest so `status` can later attribute *why* a variety is stale.
    """
    components = {
        "config": config_comp,
        "custom": custom_comp,
        "slice": slice_comp,
        "recipe": recipe_comp,
    }
    digest = hashlib.sha256(
        json.dumps(components, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return digest, components


def manifest_path(generated_dir: Path) -> Path:
    return generated_dir / MANIFEST_NAME


def load_manifest(generated_dir: Path) -> dict:
    p = manifest_path(generated_dir)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_manifest(
    generated_dir: Path,
    digest: str,
    components: dict[str, str],
    n_forms: int,
) -> None:
    generated_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "fingerprint": digest,
        "n_forms": n_forms,
        "built_on": datetime.now().isoformat(timespec="seconds"),
        "components": components,
    }
    manifest_path(generated_dir).write_text(
        json.dumps(data, indent=2), encoding="utf-8"
    )


def is_fresh(generated_dir: Path, digest: str, forms_path: Path) -> bool:
    """True when the output exists and its stored fingerprint matches."""
    if not forms_path.exists():
        return False
    manifest = load_manifest(generated_dir)
    return bool(manifest) and manifest.get("fingerprint") == digest
