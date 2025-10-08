#!/usr/bin/env python3
"""
Update documentation files with DOI information from Zenodo state.

This script reads DOI and file size information from .zenodo_state.json
and updates README.md and docs/index.html with the correct values.

Usage:
    python update_docs_doi.py [--dry-run]
"""
import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, Any


STATE_FILE = Path(".zenodo_state.json")
README_FILE = Path("README.md")
WEBSITE_FILE = Path("docs/index.html")


def format_bytes(size: int) -> str:
    """
    Format byte size as human-readable string.

    @param size: Size in bytes
    @type size: int
    @return: Formatted size string (e.g., "84 MB")
    @rtype: str
    """
    size_float = float(size)
    for unit in ["B", "KB", "MB", "GB"]:
        if size_float < 1024.0:
            return f"{int(size_float)} {unit}"
        size_float = size_float / 1024.0
    return f"{size_float:.1f} TB"


def load_state() -> Dict[str, Any]:
    """
    Load state from .zenodo_state.json.

    @return: State dictionary
    @rtype: Dict[str, Any]
    @raises FileNotFoundError: If state file doesn't exist
    """
    if not STATE_FILE.exists():
        raise FileNotFoundError(
            f"State file {STATE_FILE} not found. "
            f"Please publish to Zenodo first using zenodo_publish.py"
        )

    print(f"[load_state] Reading {STATE_FILE}")
    state = json.loads(STATE_FILE.read_text(encoding="utf-8"))

    # Validate required fields
    if "conceptdoi" not in state:
        raise ValueError("State file missing 'conceptdoi' field")
    if "deposition_id" not in state:
        raise ValueError("State file missing 'deposition_id' field")
    if "last_version" not in state:
        raise ValueError("State file missing 'last_version' field")

    return state


def get_file_sizes(state: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract file sizes for the latest version from state.

    @param state: State dictionary
    @type state: Dict[str, Any]
    @return: Dictionary with formatted file sizes
    @rtype: Dict[str, str]
    """
    version = state["last_version"]
    print(f"[get_file_sizes] Extracting sizes for version {version}")

    if "releases" not in state or version not in state["releases"]:
        raise ValueError(f"No release information for version {version}")

    release = state["releases"][version]

    if "archives" not in release:
        raise ValueError(f"No archive information for version {version}")

    sizes = {}
    for collection in ["full", "core", "corecog"]:
        if collection not in release["archives"]:
            raise ValueError(f"Missing {collection} archive in release {version}")

        size_bytes = release["archives"][collection]["size"]
        sizes[collection] = format_bytes(size_bytes)
        print(f"[get_file_sizes]   {collection}: {sizes[collection]}")

    return sizes


def update_readme(
    state: Dict[str, Any],
    sizes: Dict[str, str],
    dry_run: bool = False
) -> None:
    """
    Update README.md with DOI and file size information.

    @param state: State dictionary with DOI info
    @type state: Dict[str, Any]
    @param sizes: File sizes for each collection
    @type sizes: Dict[str, str]
    @param dry_run: If True, only show changes without writing
    @type dry_run: bool
    """
    print(f"\n[update_readme] Updating {README_FILE}")

    if not README_FILE.exists():
        raise FileNotFoundError(f"{README_FILE} not found")

    content = README_FILE.read_text(encoding="utf-8")
    original = content

    concept_doi = state["conceptdoi"]
    print(f"[update_readme] Concept DOI: {concept_doi}")

    # Update DOI badge (line 3)
    content = re.sub(
        r'\[\!\[DOI\]\(https://zenodo\.org/badge/DOI/[^)]+\.svg\)\]\(https://doi\.org/[^)]+\)',
        f'[![DOI](https://zenodo.org/badge/DOI/{concept_doi}.svg)](https://doi.org/{concept_doi})',
        content
    )
    print("[update_readme]   Updated DOI badge")

    # Update download links with concept DOI and file sizes
    # Full Collection
    content = re.sub(
        r'\*\*\[Full Collection\]\(https://doi\.org/[^)]+\)\*\* - All 149 datasets \([^)]+\)',
        f'**[Full Collection](https://doi.org/{concept_doi})** - All 149 datasets (~{sizes["full"]})',
        content
    )
    print("[update_readme]   Updated Full Collection link and size")

    # Core Collection
    content = re.sub(
        r'\*\*\[Core Collection\]\(https://doi\.org/[^)]+\)\*\* - 13 curated datasets for teaching \([^)]+\)',
        f'**[Core Collection](https://doi.org/{concept_doi})** - 13 curated datasets for teaching (~{sizes["core"]})',
        content
    )
    print("[update_readme]   Updated Core Collection link and size")

    # CoreCog Collection
    content = re.sub(
        r'\*\*\[CoreCog Collection\]\(https://doi\.org/[^)]+\)\*\* - 58 datasets with expert cognate data \([^)]+\)',
        f'**[CoreCog Collection](https://doi.org/{concept_doi})** - 58 datasets with expert cognate data (~{sizes["corecog"]})',
        content
    )
    print("[update_readme]   Updated CoreCog Collection link and size")

    # Update BibTeX citation
    content = re.sub(
        r'doi\s*=\s*{10\.5281/zenodo\.[^}]+}',
        f'doi          = {{10.5281/zenodo.{concept_doi.split("/")[-1]}}}',
        content
    )
    content = re.sub(
        r'url\s*=\s*{https://doi\.org/10\.5281/zenodo\.[^}]+}',
        f'url          = {{https://doi.org/{concept_doi}}}',
        content
    )
    print("[update_readme]   Updated BibTeX citation DOI")

    if content == original:
        print("[update_readme]   No changes needed")
        return

    if dry_run:
        print(f"[update_readme]   DRY RUN: Would update {README_FILE}")
    else:
        README_FILE.write_text(content, encoding="utf-8")
        print(f"[update_readme]   ✓ Updated {README_FILE}")


def update_website(
    state: Dict[str, Any],
    dry_run: bool = False
) -> None:
    """
    Update docs/index.html with DOI and download link information.

    @param state: State dictionary with DOI info
    @type state: Dict[str, Any]
    @param dry_run: If True, only show changes without writing
    @type dry_run: bool
    """
    print(f"\n[update_website] Updating {WEBSITE_FILE}")

    if not WEBSITE_FILE.exists():
        raise FileNotFoundError(f"{WEBSITE_FILE} not found")

    content = WEBSITE_FILE.read_text(encoding="utf-8")
    original = content

    concept_doi = state["conceptdoi"]
    record_id = state["deposition_id"]
    version = state["last_version"]

    print(f"[update_website] Concept DOI: {concept_doi}")
    print(f"[update_website] Record ID: {record_id}")
    print(f"[update_website] Version: {version}")

    # Update download button URLs with record ID
    # Full
    content = re.sub(
        r'<a href="https://zenodo\.org/records/\d+/files/arcaverborum\.A\.full\.\d+\.zip\?download=1"',
        f'<a href="https://zenodo.org/records/{record_id}/files/arcaverborum.A.full.{version.replace("A.", "")}.zip?download=1"',
        content
    )
    print("[update_website]   Updated Full download link")

    # Core
    content = re.sub(
        r'<a href="https://zenodo\.org/records/\d+/files/arcaverborum\.A\.core\.\d+\.zip\?download=1"',
        f'<a href="https://zenodo.org/records/{record_id}/files/arcaverborum.A.core.{version.replace("A.", "")}.zip?download=1"',
        content
    )
    print("[update_website]   Updated Core download link")

    # CoreCog
    content = re.sub(
        r'<a href="https://zenodo\.org/records/\d+/files/arcaverborum\.A\.corecog\.\d+\.zip\?download=1"',
        f'<a href="https://zenodo.org/records/{record_id}/files/arcaverborum.A.corecog.{version.replace("A.", "")}.zip?download=1"',
        content
    )
    print("[update_website]   Updated CoreCog download link")

    # Update concept DOI link (after download buttons)
    content = re.sub(
        r'All collections share a single DOI: <a href="https://doi\.org/10\.5281/zenodo\.[^"]+">https://doi\.org/10\.5281/zenodo\.[^<]+</a>',
        f'All collections share a single DOI: <a href="https://doi.org/{concept_doi}">https://doi.org/{concept_doi}</a>',
        content
    )
    print("[update_website]   Updated concept DOI link")

    # Update DOI badge in citation section
    content = re.sub(
        r'<img src="https://zenodo\.org/badge/DOI/10\.5281/zenodo\.[^"]+" alt="DOI">',
        f'<img src="https://zenodo.org/badge/DOI/{concept_doi}.svg" alt="DOI">',
        content
    )
    content = re.sub(
        r'<a href="https://doi\.org/10\.5281/zenodo\.[^"]+">(\s*<img src="https://zenodo\.org/badge/DOI/[^"]+\.svg")',
        f'<a href="https://doi.org/{concept_doi}">\\1',
        content
    )
    print("[update_website]   Updated DOI badge")

    # Update BibTeX citation DOI in website
    content = re.sub(
        r'doi = {10\.5281/zenodo\.[^}]+}',
        f'doi = {{10.5281/zenodo.{concept_doi.split("/")[-1]}}}',
        content
    )
    content = re.sub(
        r'url = {https://doi\.org/10\.5281/zenodo\.[^}]+}',
        f'url = {{https://doi.org/{concept_doi}}}',
        content
    )
    print("[update_website]   Updated BibTeX citation DOI")

    if content == original:
        print("[update_website]   No changes needed")
        return

    if dry_run:
        print(f"[update_website]   DRY RUN: Would update {WEBSITE_FILE}")
    else:
        WEBSITE_FILE.write_text(content, encoding="utf-8")
        print(f"[update_website]   ✓ Updated {WEBSITE_FILE}")


def main() -> None:
    """
    Main entry point.
    """
    parser = argparse.ArgumentParser(
        description="Update documentation files with DOI information from Zenodo state"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without actually modifying files"
    )

    args = parser.parse_args()

    print("="*70)
    print("  Arca Verborum DOI Documentation Updater")
    print("="*70)

    try:
        # Load state
        state = load_state()

        print("\n[main] State information:")
        print(f"[main]   Concept DOI: {state['conceptdoi']}")
        print(f"[main]   Deposition ID: {state['deposition_id']}")
        print(f"[main]   Last version: {state['last_version']}")

        # Get file sizes
        sizes = get_file_sizes(state)

        # Update files
        update_readme(state, sizes, dry_run=args.dry_run)
        update_website(state, dry_run=args.dry_run)

        print("\n" + "="*70)
        if args.dry_run:
            print("  DRY RUN COMPLETE - No files were modified")
        else:
            print("  ✓ Documentation updated successfully")
        print("="*70)

    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
