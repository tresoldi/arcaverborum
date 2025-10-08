#!/usr/bin/env python3
"""
Publish Arca Verborum dataset to Zenodo using zenodo-client library.

This script reads metadata from zenodo.metadata.yml and uploads the dataset
to Zenodo (or sandbox), handling versioning automatically.
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml
from zenodo_client import ensure_zenodo

STATE_FILE = Path(".zenodo_state.json")
META_FILE = Path("zenodo.metadata.yml")


def load_state() -> Dict[str, Any]:
    """
    Load state from .zenodo_state.json.

    @return: State dictionary
    @rtype: Dict[str, Any]
    """
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {}


def save_state(state: Dict[str, Any]) -> None:
    """
    Save state to .zenodo_state.json.

    @param state: State dictionary to save
    @type state: Dict[str, Any]
    """
    STATE_FILE.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def die(msg: str, code: int = 1) -> None:
    """
    Print error message and exit.

    @param msg: Error message
    @type msg: str
    @param code: Exit code
    @type code: int
    """
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def read_metadata() -> Dict[str, Any]:
    """
    Read and validate metadata from zenodo.metadata.yml.

    @return: Metadata dictionary
    @rtype: Dict[str, Any]
    """
    if not META_FILE.exists():
        die(f"Metadata file {META_FILE} not found.")

    meta = yaml.safe_load(META_FILE.read_text(encoding="utf-8"))

    # Validate required fields
    required = ["title", "version", "description", "files"]
    for k in required:
        if k not in meta:
            die(f"Missing required field `{k}` in {META_FILE}")

    if not isinstance(meta["files"], list) or len(meta["files"]) == 0:
        die("`files` must be a non-empty list.")

    return meta


def resolve_file_paths(meta: Dict[str, Any]) -> List[Path]:
    """
    Resolve and validate file paths from metadata.

    @param meta: Metadata dictionary
    @type meta: Dict[str, Any]
    @return: List of resolved file paths
    @rtype: List[Path]
    """
    resolved_paths = []
    for f in meta["files"]:
        path = Path(f["path"]).expanduser().resolve()
        if not path.exists():
            die(f"File not found: {path}")
        resolved_paths.append(path)

    return resolved_paths


def build_metadata_dict(meta: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build metadata dictionary for Zenodo API from our metadata format.

    Uses dict format instead of Metadata class to support related_identifiers.

    @param meta: Our metadata from zenodo.metadata.yml
    @type meta: Dict[str, Any]
    @return: Metadata dict for Zenodo API
    @rtype: Dict[str, Any]
    """
    # Build creators list
    creators_list = []
    for c in meta.get("creators", []):
        creator_dict = {"name": c["name"]}
        if "affiliation" in c:
            creator_dict["affiliation"] = c["affiliation"]
        if "orcid" in c:
            creator_dict["orcid"] = c["orcid"]
        creators_list.append(creator_dict)

    # Build metadata dict
    metadata = {
        "title": meta["title"],
        "upload_type": meta.get("upload_type", "dataset"),
        "description": meta["description"],
        "version": meta["version"],
        "creators": creators_list,
        "keywords": meta.get("keywords", []),
        "license": meta.get("license", "CC-BY-4.0"),
    }

    # Add optional fields
    if "communities" in meta:
        # Convert communities to expected format
        communities = []
        for c in meta["communities"]:
            if isinstance(c, dict):
                communities.append({"identifier": c.get("identifier", c.get("name", ""))})
            else:
                communities.append({"identifier": str(c)})
        metadata["communities"] = communities

    if "related_identifiers" in meta:
        metadata["related_identifiers"] = meta["related_identifiers"]

    if "publication_date" in meta:
        metadata["publication_date"] = meta["publication_date"]

    return metadata


def show_metadata_preview(meta: Dict[str, Any], sandbox: bool) -> None:
    """
    Print metadata preview and exit.

    @param meta: Metadata dictionary
    @type meta: Dict[str, Any]
    @param sandbox: Whether using sandbox environment
    @type sandbox: bool
    """
    metadata_dict = build_metadata_dict(meta)
    paths = resolve_file_paths(meta)

    preview = {
        "environment": "sandbox" if sandbox else "production",
        "metadata": metadata_dict,
        "files": [str(p) for p in paths],
    }

    print(json.dumps(preview, indent=2))


def publish_to_zenodo(
    meta: Dict[str, Any],
    sandbox: bool = False,
    dry_run: bool = False,
    force: bool = False,
) -> None:
    """
    Publish dataset to Zenodo using zenodo-client library.

    @param meta: Metadata dictionary
    @type meta: Dict[str, Any]
    @param sandbox: Use Zenodo sandbox environment
    @type sandbox: bool
    @param dry_run: Dry run mode (not implemented in zenodo-client)
    @type dry_run: bool
    @param force: Force publication even if version exists
    @type force: bool
    """
    # Check version against state
    state = load_state()
    last_version = state.get("last_version")

    if not force and last_version == meta["version"]:
        die(
            f"Version {meta['version']} was already published "
            f"(state says last_version={last_version}). Use --force if intentional."
        )

    # Resolve file paths
    paths = resolve_file_paths(meta)

    # Build metadata dictionary
    metadata_dict = build_metadata_dict(meta)

    # Dry run warning
    if dry_run:
        print("WARNING: --dry-run not fully supported with zenodo-client.", file=sys.stderr)
        print("         Showing what would be uploaded:", file=sys.stderr)
        print(f"\nMetadata:\n{json.dumps(metadata_dict, indent=2)}")
        print(f"\nFiles: {[str(p) for p in paths]}")
        print("\nTo actually publish, run without --dry-run")
        return

    print(f"Publishing to {'sandbox' if sandbox else 'production'} Zenodo...")
    print(f"Version: {meta['version']}")
    print(f"Files: {len(paths)}")

    try:
        # Use ensure_zenodo for automatic versioning
        # The 'key' parameter is used to store/retrieve deposition ID
        key = "arcaverborum_sandbox" if sandbox else "arcaverborum"

        response = ensure_zenodo(
            key=key,
            data={"metadata": metadata_dict},
            paths=paths,
            sandbox=sandbox,
        )

        # Extract information from response
        response_data = response.json()

        # Update state
        new_state = {
            "last_version": meta["version"],
            "last_publication_date": response_data.get("created"),
        }

        # Try to get concept DOI if available
        if "conceptdoi" in response_data:
            new_state["conceptdoi"] = response_data["conceptdoi"]
        elif "concept_doi" in response_data:
            new_state["conceptdoi"] = response_data["concept_doi"]

        # Merge with existing state
        state.update(new_state)
        save_state(state)

        print("\n✓ Successfully published to Zenodo!")
        print(f"  Concept DOI: {new_state.get('conceptdoi', 'N/A')}")

        # Print record URL if available
        if "links" in response_data:
            record_url = response_data["links"].get("record_html") or response_data["links"].get("html")
            if record_url:
                print(f"  Record URL: {record_url}")

        print(f"\nState saved to {STATE_FILE}")

    except Exception as e:
        die(f"Failed to publish to Zenodo: {e}")


def main() -> None:
    """
    Main entry point for the script.
    """
    parser = argparse.ArgumentParser(
        description="Publish Arca Verborum dataset to Zenodo using zenodo-client."
    )
    parser.add_argument(
        "--sandbox",
        action="store_true",
        help="Use Zenodo sandbox environment (requires ZENODO_SANDBOX_TOKEN)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be uploaded without actually publishing"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force publication even if version was already published"
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Show metadata preview and exit"
    )

    args = parser.parse_args()

    # Read metadata
    meta = read_metadata()

    # Show preview and exit if requested
    if args.show:
        show_metadata_preview(meta, args.sandbox)
        return

    # Publish to Zenodo
    publish_to_zenodo(
        meta=meta,
        sandbox=args.sandbox,
        dry_run=args.dry_run,
        force=args.force,
    )


if __name__ == "__main__":
    main()
