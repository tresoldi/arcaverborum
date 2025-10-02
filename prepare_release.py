#!/usr/bin/env python3

"""
Prepare Release for Arca Verborum

Automates the creation of Zenodo release archives:
- Generates documentation from templates
- Creates ZIP archive with all output files
- Computes checksums
- Updates zenodo.metadata.yml
- Optionally creates git tag

Usage:
    python prepare_release.py                    # Uses today's date as version
    python prepare_release.py --version 20251001 # Explicit version
    python prepare_release.py --force            # Override version check
    python prepare_release.py --git-tag          # Create and push git tag
"""

import argparse
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

try:
    import jinja2
    import yaml
except ImportError:
    print("Error: Missing dependencies. Run: pip install jinja2 pyyaml", file=sys.stderr)
    sys.exit(1)

# === CONFIGURATION ===
OUTPUT_DIR = Path("output")
OUTPUT_DIR_FULL = OUTPUT_DIR / "full"
OUTPUT_DIR_CORE = OUTPUT_DIR / "core"
RELEASES_DIR = Path("releases")
TEMPLATES_DIR = Path("templates")
STATE_FILE = Path(".zenodo_state.json")
METADATA_FILE = Path("zenodo.metadata.yml")

# Files to include in release archive
RELEASE_FILES = [
    "forms.csv",
    "languages.csv",
    "parameters.csv",
    "metadata.csv",
    "sources.bib",
    "validation_report.json"
]


# === HELPER FUNCTIONS ===

def die(msg, code=1):
    """Print error and exit."""
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def sha256sum(path: Path) -> str:
    """
    Compute SHA256 checksum of a file.

    @param path: Path to file
    @return: Hex digest of SHA256 hash
    """
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def format_bytes(size: int) -> str:
    """
    Format byte size as human-readable string.

    @param size: Size in bytes
    @return: Formatted string (e.g., "527 MB")
    """
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024.0:
            return f"{size:.0f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


def format_number(n: int) -> str:
    """
    Format integer with thousands separators.

    @param n: Number to format
    @return: Formatted string (e.g., "2,915,515")
    """
    return f"{n:,}"


def load_state() -> dict:
    """Load release state from JSON file."""
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"releases": {}}


def save_state(state: dict):
    """Save release state to JSON file."""
    STATE_FILE.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def load_validation_report(output_dir: Path) -> dict:
    """
    Load validation report from output directory.

    @param output_dir: Output directory path
    @return: Parsed validation report
    """
    report_path = output_dir / "validation_report.json"
    if not report_path.exists():
        die(f"Validation report not found: {report_path}")
    return json.loads(report_path.read_text(encoding="utf-8"))


def extract_statistics(validation_report: dict, output_dir: Path) -> dict:
    """
    Extract statistics from validation report for templates.

    @param validation_report: Parsed validation_report.json
    @param output_dir: Output directory path
    @return: Dictionary of statistics
    """
    summary = validation_report.get("summary", {})
    quality = validation_report.get("data_quality", {})
    integrity = validation_report.get("referential_integrity", {})
    versions = validation_report.get("version_distribution", {})

    # Count sources.bib entries
    sources_path = output_dir / "sources.bib"
    sources_count = 0
    if sources_path.exists():
        content = sources_path.read_text(encoding="utf-8")
        sources_count = content.count("@")

    return {
        "datasets_count": summary.get("total_datasets", 0),
        "forms_count": summary.get("total_forms", 0),
        "languages_count": summary.get("total_languages", 0),
        "parameters_count": summary.get("total_parameters", 0),
        "cognates_datasets": summary.get("datasets_with_cognates", 0),
        "sources_entries": sources_count,

        # Coverage metrics
        "glottolog_coverage": quality.get("glottocode_coverage_percent", 0),
        "concepticon_coverage": quality.get("concepticon_coverage_percent", 0),
        "cognate_coverage": quality.get("forms_with_cognate_data_percent", 0),
        "segments_coverage": quality.get("forms_with_segments_percent", 0),
        "alignment_coverage": quality.get("forms_with_alignment_percent", 0),

        # Integrity
        "orphan_languages": integrity.get("orphan_language_ids", 0),
        "orphan_parameters": integrity.get("orphan_parameter_ids", 0),

        # Version distributions
        "glottolog_version_dist": versions.get("glottolog", {}),
        "concepticon_version_dist": versions.get("concepticon", {}),
        "clts_version_dist": versions.get("clts", {}),
    }


def format_version_range(version_dist: dict) -> str:
    """
    Format version distribution as a range string.

    @param version_dist: Dictionary of version -> count
    @return: Formatted string (e.g., "v4.7-v5.0")
    """
    if not version_dist:
        return "unknown"
    versions = sorted(version_dist.keys())
    if len(versions) == 1:
        return versions[0]
    return f"{versions[0]}-{versions[-1]}"


def compute_checksums(files: list[Path]) -> dict:
    """
    Compute SHA256 checksums for all files.

    @param files: List of file paths
    @return: Dictionary mapping filenames to checksums
    """
    checksums = {}
    for path in files:
        if path.exists():
            checksum = sha256sum(path)
            # Use safe key names (replace . with _)
            key = path.name.replace(".", "_")
            checksums[key] = checksum
        else:
            print(f"Warning: File not found for checksum: {path}", file=sys.stderr)
    return checksums


def get_file_sizes(files: list[Path]) -> dict:
    """
    Get human-readable file sizes.

    @param files: List of file paths
    @return: Dictionary mapping filenames to formatted sizes
    """
    sizes = {}
    for path in files:
        if path.exists():
            size = path.stat().st_size
            key = path.name.replace(".", "_")
            sizes[key] = format_bytes(size)
        else:
            sizes[path.name.replace(".", "_")] = "N/A"
    return sizes


def render_template(template_path: Path, context: dict) -> str:
    """
    Render a Jinja2 template with given context.

    @param template_path: Path to template file
    @param context: Context dictionary for template
    @return: Rendered template as string
    """
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(TEMPLATES_DIR),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True
    )

    # Custom filters
    env.filters["format_number"] = format_number

    template = env.get_template(template_path.name)
    return template.render(**context)


def create_archive(version: str, output_files: list[Path], doc_files: dict[str, str],
                   collection_suffix: str = "") -> Path:
    """
    Create ZIP archive with all release files.

    @param version: Release version string
    @param output_files: List of paths to output files
    @param doc_files: Dictionary of filename -> content for generated docs
    @param collection_suffix: Suffix for archive name (e.g., "_core" or empty for full)
    @return: Path to created ZIP file
    """
    archive_name = f"arcaverborum{collection_suffix}_{version}.zip"
    archive_path = RELEASES_DIR / archive_name
    base_dir = f"arcaverborum{collection_suffix}_{version}"

    print(f"Creating archive: {archive_path}")

    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # Add output files
        for file_path in output_files:
            if file_path.exists():
                arcname = f"{base_dir}/{file_path.name}"
                zf.write(file_path, arcname)
                print(f"  Added: {file_path.name}")
            else:
                print(f"  Warning: Skipping missing file: {file_path.name}", file=sys.stderr)

        # Add generated documentation
        for filename, content in doc_files.items():
            arcname = f"{base_dir}/{filename}"
            zf.writestr(arcname, content.encode("utf-8"))
            print(f"  Added: {filename}")

    return archive_path


def update_metadata_file(version: str, archive_paths: list[Path]):
    """
    Update zenodo.metadata.yml with new version and file paths.

    @param version: Release version
    @param archive_paths: List of paths to release archives (full and core)
    """
    if not METADATA_FILE.exists():
        die(f"Metadata file not found: {METADATA_FILE}")

    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        metadata = yaml.safe_load(f)

    # Update version
    metadata["version"] = version

    # Update files section with both archives
    metadata["files"] = [
        {
            "path": str(path),
            "name": path.name
        }
        for path in archive_paths
    ]

    # Write back
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        yaml.dump(metadata, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    print(f"Updated {METADATA_FILE}")


def create_git_tag(version: str):
    """
    Create and push git tag for release.

    @param version: Release version
    """
    tag_name = f"v{version}"

    print(f"\nCreating git tag: {tag_name}")

    # Check if tag already exists
    result = subprocess.run(
        ["git", "tag", "-l", tag_name],
        capture_output=True,
        text=True
    )

    if result.stdout.strip():
        print(f"  Warning: Tag {tag_name} already exists", file=sys.stderr)
        return

    # Create annotated tag
    subprocess.run(
        ["git", "tag", "-a", tag_name, "-m", f"Release version {version}"],
        check=True
    )
    print(f"  Created tag: {tag_name}")

    # Ask to push
    response = input(f"Push tag {tag_name} to origin? [y/N]: ").strip().lower()
    if response == "y":
        subprocess.run(["git", "push", "origin", tag_name], check=True)
        print(f"  Pushed tag: {tag_name}")
    else:
        print(f"  Tag not pushed. Push manually with: git push origin {tag_name}")


# === MAIN ===

def main():
    """Main entry point - creates both full and core archives."""
    parser = argparse.ArgumentParser(
        description="Prepare Arca Verborum release for Zenodo (creates both full and core archives)",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--version",
        type=str,
        help="Release version (default: today's date as YYYYMMDD)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Override version existence check"
    )
    parser.add_argument(
        "--git-tag",
        action="store_true",
        help="Create git tag for this release"
    )
    parser.add_argument(
        "--changes",
        type=str,
        help="Changes description for non-initial releases"
    )
    parser.add_argument(
        "--known-issues",
        type=str,
        help="Known issues for this release"
    )

    args = parser.parse_args()

    # Determine version
    if args.version:
        version = args.version
    else:
        version = datetime.datetime.now().strftime("%Y%m%d")

    print(f"Preparing release version: {version}")
    print("Building both full and core archives...\n")

    # Check if both output directories exist
    if not OUTPUT_DIR_FULL.exists():
        die(f"Full collection directory not found: {OUTPUT_DIR_FULL}. Run merge_cldf_datasets.py first.")
    if not OUTPUT_DIR_CORE.exists():
        die(f"Core collection directory not found: {OUTPUT_DIR_CORE}. Run merge_cldf_datasets.py first.")

    # Verify all required files exist in both directories
    for output_dir, name in [(OUTPUT_DIR_FULL, "full"), (OUTPUT_DIR_CORE, "core")]:
        missing_files = []
        for filename in RELEASE_FILES:
            if not (output_dir / filename).exists():
                missing_files.append(filename)
        if missing_files:
            die(f"Missing required files in {name} collection: {', '.join(missing_files)}")

    # Load state and check version
    state = load_state()
    if version in state.get("releases", {}) and not args.force:
        die(f"Version {version} already released. Use --force to override.")

    # Create releases directory
    RELEASES_DIR.mkdir(exist_ok=True)

    # Prepare common template context
    today = datetime.datetime.now()
    processing_date = today.strftime("%Y-%m-%d")
    is_first_release = len(state.get("releases", {})) == 0

    # === PROCESS FULL COLLECTION ===
    print("=" * 70)
    print("FULL COLLECTION")
    print("=" * 70)

    # Load validation report and extract statistics
    print("Loading validation report...")
    validation_report_full = load_validation_report(OUTPUT_DIR_FULL)
    stats_full = extract_statistics(validation_report_full, OUTPUT_DIR_FULL)

    # Compute checksums and file sizes
    output_files_full = [OUTPUT_DIR_FULL / f for f in RELEASE_FILES]
    checksums_full = compute_checksums(output_files_full)
    file_sizes_full = get_file_sizes(output_files_full)

    context_full = {
        "version": version,
        "collection": "full",
        "collection_name": "Full Collection",
        "release_date": processing_date,
        "processing_date": processing_date,
        "year": today.year,
        "doi": "10.5281/zenodo.XXXXXXX",  # Placeholder, filled by Zenodo
        "is_first_release": is_first_release,
        "changes": args.changes or "",
        "known_issues": args.known_issues or "",
        "checksums": checksums_full,
        "file_sizes": file_sizes_full,
        "next_release": None,

        # Format version ranges
        "glottolog_versions": format_version_range(stats_full["glottolog_version_dist"]),
        "concepticon_versions": format_version_range(stats_full["concepticon_version_dist"]),
        "clts_versions": format_version_range(stats_full["clts_version_dist"]),

        **stats_full
    }

    # Render documentation for full collection
    print("Generating documentation...")
    dataset_desc_full = render_template(
        TEMPLATES_DIR / "DATASET_DESCRIPTION.md.j2",
        context_full
    )
    release_notes_full = render_template(
        TEMPLATES_DIR / "RELEASE_NOTES.md.j2",
        context_full
    )

    # Create full archive
    print("Creating release archive...")
    doc_files_full = {
        "DATASET_DESCRIPTION.md": dataset_desc_full,
        "RELEASE_NOTES.md": release_notes_full
    }
    archive_path_full = create_archive(version, output_files_full, doc_files_full, "")

    # Compute archive checksum
    archive_checksum_full = sha256sum(archive_path_full)
    archive_size_full = format_bytes(archive_path_full.stat().st_size)

    print(f"\nFull archive created: {archive_path_full}")
    print(f"  Size: {archive_size_full}")
    print(f"  SHA256: {archive_checksum_full}")

    # === PROCESS CORE COLLECTION ===
    print("\n" + "=" * 70)
    print("CORE COLLECTION")
    print("=" * 70)

    # Load validation report and extract statistics
    print("Loading validation report...")
    validation_report_core = load_validation_report(OUTPUT_DIR_CORE)
    stats_core = extract_statistics(validation_report_core, OUTPUT_DIR_CORE)

    # Compute checksums and file sizes
    output_files_core = [OUTPUT_DIR_CORE / f for f in RELEASE_FILES]
    checksums_core = compute_checksums(output_files_core)
    file_sizes_core = get_file_sizes(output_files_core)

    context_core = {
        "version": version,
        "collection": "core",
        "collection_name": "Core Collection",
        "release_date": processing_date,
        "processing_date": processing_date,
        "year": today.year,
        "doi": "10.5281/zenodo.XXXXXXX",  # Placeholder, filled by Zenodo
        "is_first_release": is_first_release,
        "changes": args.changes or "",
        "known_issues": args.known_issues or "",
        "checksums": checksums_core,
        "file_sizes": file_sizes_core,
        "next_release": None,

        # Format version ranges
        "glottolog_versions": format_version_range(stats_core["glottolog_version_dist"]),
        "concepticon_versions": format_version_range(stats_core["concepticon_version_dist"]),
        "clts_versions": format_version_range(stats_core["clts_version_dist"]),

        **stats_core
    }

    # Render documentation for core collection
    print("Generating documentation...")
    dataset_desc_core = render_template(
        TEMPLATES_DIR / "DATASET_DESCRIPTION.md.j2",
        context_core
    )
    release_notes_core = render_template(
        TEMPLATES_DIR / "RELEASE_NOTES.md.j2",
        context_core
    )

    # Create core archive
    print("Creating release archive...")
    doc_files_core = {
        "DATASET_DESCRIPTION.md": dataset_desc_core,
        "RELEASE_NOTES.md": release_notes_core
    }
    archive_path_core = create_archive(version, output_files_core, doc_files_core, "_core")

    # Compute archive checksum
    archive_checksum_core = sha256sum(archive_path_core)
    archive_size_core = format_bytes(archive_path_core.stat().st_size)

    print(f"\nCore archive created: {archive_path_core}")
    print(f"  Size: {archive_size_core}")
    print(f"  SHA256: {archive_checksum_core}")

    # Update metadata file with both archives
    print("\n" + "=" * 70)
    update_metadata_file(version, [archive_path_full, archive_path_core])

    # Update state
    if "releases" not in state:
        state["releases"] = {}

    state["last_version"] = version
    state["releases"][version] = {
        "date": processing_date,
        "archives": {
            "full": {
                "path": str(archive_path_full),
                "sha256": archive_checksum_full,
                "size": archive_path_full.stat().st_size
            },
            "core": {
                "path": str(archive_path_core),
                "sha256": archive_checksum_core,
                "size": archive_path_core.stat().st_size
            }
        }
    }
    save_state(state)

    print(f"Updated {STATE_FILE}")

    # Create git tag if requested
    if args.git_tag:
        create_git_tag(version)

    # Print next steps
    print("\n" + "=" * 70)
    print("SUCCESS! Both archives prepared.")
    print("=" * 70)
    print("\nArchives:")
    print(f"  Full:  {archive_path_full} ({archive_size_full})")
    print(f"  Core:  {archive_path_core} ({archive_size_core})")
    print("\nNext steps:")
    print(f"  1. Review the archives:")
    print(f"       unzip -l {archive_path_full}")
    print(f"       unzip -l {archive_path_core}")
    print(f"  2. Preview Zenodo metadata: python zenodo_publish.py --show")
    print(f"  3. Test on sandbox: python zenodo_publish.py --sandbox")
    print(f"  4. Publish to Zenodo: python zenodo_publish.py")
    if not args.git_tag:
        print(f"  5. (Optional) Create git tag: python prepare_release.py --version {version} --git-tag")
    print()


if __name__ == "__main__":
    main()
