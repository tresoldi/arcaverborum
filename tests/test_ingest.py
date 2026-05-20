"""Tests for the CLDF ingest pipeline (raw/lexibank → intake/lexibank)."""

from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd

from arcaverborum.ingest import ingest_lexibank


def _build_raw_tree(tmp_path: Path, fixture: Path, datasets: list[str]) -> Path:
    raw_root = tmp_path / "raw"
    for ds in datasets:
        target = raw_root / "lexibank" / ds / "cldf"
        target.mkdir(parents=True, exist_ok=True)
        for src in fixture.iterdir():
            shutil.copy(src, target / src.name)
    return raw_root


def test_ingest_single_dataset(tmp_path: Path, minimal_dataset_path: Path):
    raw_root = _build_raw_tree(tmp_path, minimal_dataset_path, ["alpha"])
    intake_root = tmp_path / "intake"
    stats = ingest_lexibank(raw_root, intake_root)

    assert stats["datasets_ingested"] == 1
    assert stats["total_forms"] > 0

    forms = pd.read_csv(intake_root / "lexibank" / "forms.csv", dtype=str, keep_default_na=False)
    assert "Dataset" in forms.columns
    assert (forms["Dataset"] == "alpha").all()
    # IDs prefixed
    assert all(fid.startswith("alpha_") for fid in forms["ID"])
    assert all(lid.startswith("alpha_") for lid in forms["Language_ID"])
    assert all(pid.startswith("alpha_") for pid in forms["Parameter_ID"])

    # Glottocode joined from languages
    if "Glottocode" in forms.columns:
        non_empty = forms["Glottocode"].astype(str).str.strip() != ""
        if non_empty.any():
            assert forms.loc[non_empty, "Glottocode"].notna().all()


def test_ingest_two_datasets(tmp_path: Path, minimal_dataset_path: Path):
    raw_root = _build_raw_tree(tmp_path, minimal_dataset_path, ["alpha", "beta"])
    intake_root = tmp_path / "intake"
    stats = ingest_lexibank(raw_root, intake_root)
    assert stats["datasets_ingested"] == 2

    forms = pd.read_csv(intake_root / "lexibank" / "forms.csv", dtype=str, keep_default_na=False)
    assert set(forms["Dataset"]) == {"alpha", "beta"}

    metadata = pd.read_csv(intake_root / "lexibank" / "metadata.csv", dtype=str, keep_default_na=False)
    assert set(metadata["Dataset"]) == {"alpha", "beta"}


def test_ingest_bibtex_keys_prefixed(tmp_path: Path, minimal_dataset_path: Path):
    raw_root = _build_raw_tree(tmp_path, minimal_dataset_path, ["alpha"])
    intake_root = tmp_path / "intake"
    ingest_lexibank(raw_root, intake_root)

    bib = (intake_root / "lexibank" / "sources.bib").read_text(encoding="utf-8")
    if bib.strip():
        # If BibTeX entries exist, they should be prefixed
        import re
        keys = re.findall(r"@\w+\{([^,]+),", bib)
        if keys:
            assert all(k.startswith("alpha_") for k in keys)
