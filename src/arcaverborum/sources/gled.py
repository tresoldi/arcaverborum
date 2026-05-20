"""GLED (Global Lexical Database) source.

GLED is distributed as a TSV. We convert it into a CLDF Wordlist under
`raw/lexibank/gled/cldf/` so it behaves like any other Lexibank entry.

The actual git clone is handled by `arcaverborum.sources.lexibank.fetch`
(GLED is one of the entries in datasets.csv). This module only owns the
TSV→CLDF conversion.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

SOURCES_BIB = """\
@misc{Tresoldi2022gled,
  year      = {2022},
  author    = {Tiago Tresoldi},
  title     = {A Global Lexical Database (GLED) with cognate annotation and phonological alignments},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.5911132}
}
"""


def find_latest_release(repo_dir: Path) -> Path:
    releases_dir = repo_dir / "releases"
    if not releases_dir.exists():
        print(f"ERROR: No releases/ directory in {repo_dir}", file=sys.stderr)
        sys.exit(1)

    release_dirs = sorted(
        [d for d in releases_dir.iterdir() if d.is_dir()],
        key=lambda d: d.name,
        reverse=True,
    )
    if not release_dirs:
        print(f"ERROR: No release directories in {releases_dir}", file=sys.stderr)
        sys.exit(1)

    tsv_path = release_dirs[0] / "gled.tsv"
    if not tsv_path.exists():
        print(f"ERROR: {tsv_path} not found", file=sys.stderr)
        sys.exit(1)

    return tsv_path


def build_cldf_metadata(
    form_count: int, language_count: int, parameter_count: int, release_tag: str
) -> dict:
    return {
        "dc:conformsTo": "http://cldf.clld.org/v1.0/terms.rdf#Wordlist",
        "dc:title": "Global Lexical Database (GLED)",
        "dc:bibliographicCitation": (
            "Tresoldi, Tiago (2022): A Global Lexical Database (GLED) "
            "with cognate annotation and phonological alignments. Zenodo. "
            "https://doi.org/10.5281/zenodo.5911132"
        ),
        "dc:license": "CC-BY-4.0",
        "dcat:accessURL": "https://github.com/tresoldi/gled",
        "prov:wasDerivedFrom": [
            {"dc:title": "Repository", "dc:created": release_tag},
        ],
        "prov:wasGeneratedBy": [
            {
                "dc:title": "python",
                "dc:description": "convert_gled.py (arcaverborum)",
            }
        ],
        "tables": [
            {
                "dc:conformsTo": "http://cldf.clld.org/v1.0/terms.rdf#FormTable",
                "dc:extent": form_count,
                "url": "forms.csv",
            },
            {
                "dc:conformsTo": "http://cldf.clld.org/v1.0/terms.rdf#LanguageTable",
                "dc:extent": language_count,
                "url": "languages.csv",
            },
            {
                "dc:conformsTo": "http://cldf.clld.org/v1.0/terms.rdf#ParameterTable",
                "dc:extent": parameter_count,
                "url": "parameters.csv",
            },
        ],
    }


def convert(repo_dir: Path) -> None:
    tsv_path = find_latest_release(repo_dir)
    release_tag = tsv_path.parent.name
    print(f"Reading {tsv_path} (release {release_tag})")

    df = pd.read_csv(tsv_path, sep="\t", dtype=str, keep_default_na=False)
    print(f"  {len(df)} rows, {df['DOCULECT'].nunique()} languages, {df['CONCEPT'].nunique()} concepts")

    # --- forms.csv ---
    forms = pd.DataFrame({
        "ID": df["ID"],
        "Language_ID": df["DOCULECT"],
        "Parameter_ID": df["CONCEPT"],
        "Value": df["ASJP_FORM"],
        "Form": df["FORM"],
        "Segments": df["IPA"],
        "Cognacy": df["COGSET"],
        "Alignment": df["ALIGNMENT"],
        "Source": "Tresoldi2022gled",
    })

    # --- languages.csv ---
    lang_cols = ["DOCULECT", "LANGUAGE_NAME", "GLOTTOCODE", "GLOTTOLOG_NAME", "FAMILY"]
    langs_raw = df[lang_cols].drop_duplicates(subset=["DOCULECT"])
    languages = pd.DataFrame({
        "ID": langs_raw["DOCULECT"].values,
        "Name": langs_raw["LANGUAGE_NAME"].values,
        "Glottocode": langs_raw["GLOTTOCODE"].values,
        "Glottolog_Name": langs_raw["GLOTTOLOG_NAME"].values,
        "ISO639P3code": "",
        "Macroarea": "",
        "Latitude": "",
        "Longitude": "",
        "Family": langs_raw["FAMILY"].values,
    })

    # --- parameters.csv ---
    param_cols = ["CONCEPT", "CONCEPTICON_ID"]
    params_raw = df[param_cols].drop_duplicates(subset=["CONCEPT"])
    parameters = pd.DataFrame({
        "ID": params_raw["CONCEPT"].values,
        "Name": params_raw["CONCEPT"].values,
        "Concepticon_ID": params_raw["CONCEPTICON_ID"].values,
        "Concepticon_Gloss": params_raw["CONCEPT"].str.upper().values,
    })

    # --- write output ---
    cldf_dir = repo_dir / "cldf"
    cldf_dir.mkdir(parents=True, exist_ok=True)

    forms.to_csv(cldf_dir / "forms.csv", index=False, encoding="utf-8")
    languages.to_csv(cldf_dir / "languages.csv", index=False, encoding="utf-8")
    parameters.to_csv(cldf_dir / "parameters.csv", index=False, encoding="utf-8")

    metadata = build_cldf_metadata(len(forms), len(languages), len(parameters), release_tag)
    (cldf_dir / "cldf-metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    (cldf_dir / "sources.bib").write_text(SOURCES_BIB, encoding="utf-8")

    print(f"  Wrote CLDF to {cldf_dir}/")
    print(f"    forms:      {len(forms):>8,}")
    print(f"    languages:  {len(languages):>8,}")
    print(f"    parameters: {len(parameters):>8,}")


def fetch(raw_root: Path, **kwargs) -> None:
    """Ensure GLED is fetched (via lexibank) and converted."""
    from arcaverborum.sources import lexibank
    lexibank.fetch(raw_root, **kwargs)


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert GLED TSV to CLDF Wordlist")
    parser.add_argument(
        "--repo-dir",
        type=Path,
        default=Path("raw/lexibank/gled"),
        help="Path to cloned GLED repository (default: raw/lexibank/gled)",
    )
    args = parser.parse_args()

    if not args.repo_dir.exists():
        print(f"ERROR: {args.repo_dir} does not exist. Clone it first.", file=sys.stderr)
        sys.exit(1)

    convert(args.repo_dir)


if __name__ == "__main__":
    main()
