#!/usr/bin/env python3
"""
Publish Arca Verborum dataset to Zenodo using zenodo-client library.

This script reads metadata from zenodo.metadata.yml and uploads the dataset
to Zenodo (or sandbox), handling versioning automatically.
"""
import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml
from zenodo_client import ensure_zenodo

STATE_FILE = Path(".zenodo_state.json")
META_FILE = Path("zenodo.metadata.yml")


def format_bytes(size: int) -> str:
    """
    Format byte size as human-readable string.

    @param size: Size in bytes
    @type size: int
    @return: Formatted size string
    @rtype: str
    """
    size_float = float(size)
    for unit in ["B", "KB", "MB", "GB"]:
        if size_float < 1024.0:
            return f"{size_float:.1f} {unit}"
        size_float = size_float / 1024.0
    return f"{size_float:.1f} TB"


def print_section(title: str) -> None:
    """
    Print a section header.

    @param title: Section title
    @type title: str
    """
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def load_state() -> Dict[str, Any]:
    """
    Load state from .zenodo_state.json.

    @return: State dictionary
    @rtype: Dict[str, Any]
    """
    if STATE_FILE.exists():
        print(f"[load_state] Loading state from {STATE_FILE}")
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        print(f"[load_state] Found existing state: {json.dumps(state, indent=2)}")
        return state
    print(f"[load_state] No state file found at {STATE_FILE}")
    return {}


def save_state(state: Dict[str, Any]) -> None:
    """
    Save state to .zenodo_state.json.

    @param state: State dictionary to save
    @type state: Dict[str, Any]
    """
    print(f"[save_state] Saving state to {STATE_FILE}")
    print(f"[save_state] State contents: {json.dumps(state, indent=2)}")
    STATE_FILE.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
    print("[save_state] State saved successfully")


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
    print(f"[read_metadata] Reading metadata from {META_FILE}")
    if not META_FILE.exists():
        die(f"Metadata file {META_FILE} not found.")

    meta = yaml.safe_load(META_FILE.read_text(encoding="utf-8"))
    print("[read_metadata] Successfully loaded YAML")

    # Validate required fields
    required = ["title", "version", "description", "files"]
    print(f"[read_metadata] Validating required fields: {', '.join(required)}")
    for k in required:
        if k not in meta:
            die(f"Missing required field `{k}` in {META_FILE}")

    if not isinstance(meta["files"], list) or len(meta["files"]) == 0:
        die("`files` must be a non-empty list.")

    print("[read_metadata] Metadata validation successful")
    print(f"[read_metadata]   Title: {meta['title']}")
    print(f"[read_metadata]   Version: {meta['version']}")
    print(f"[read_metadata]   Files: {len(meta['files'])} file(s)")
    print(f"[read_metadata]   Creators: {len(meta.get('creators', []))} creator(s)")
    if "keywords" in meta:
        print(f"[read_metadata]   Keywords: {', '.join(meta['keywords'])}")
    if "related_identifiers" in meta:
        print(f"[read_metadata]   Related identifiers: {len(meta['related_identifiers'])}")

    return meta


def resolve_file_paths(meta: Dict[str, Any]) -> List[Path]:
    """
    Resolve and validate file paths from metadata.

    @param meta: Metadata dictionary
    @type meta: Dict[str, Any]
    @return: List of resolved file paths
    @rtype: List[Path]
    """
    print(f"[resolve_file_paths] Resolving {len(meta['files'])} file path(s)")
    resolved_paths = []
    total_size = 0

    for i, f in enumerate(meta["files"], 1):
        path = Path(f["path"]).expanduser().resolve()
        print(f"[resolve_file_paths] File {i}/{len(meta['files'])}: {f['path']}")
        print(f"[resolve_file_paths]   Resolved to: {path}")

        if not path.exists():
            die(f"File not found: {path}")

        file_size = path.stat().st_size
        total_size += file_size
        print(f"[resolve_file_paths]   Size: {format_bytes(file_size)}")
        print("[resolve_file_paths]   Exists: ✓")
        resolved_paths.append(path)

    print("[resolve_file_paths] All files validated")
    print(f"[resolve_file_paths] Total upload size: {format_bytes(total_size)}")

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
    print("[build_metadata_dict] Building Zenodo API metadata")

    # Build creators list
    print(f"[build_metadata_dict] Processing {len(meta.get('creators', []))} creator(s)")
    creators_list = []
    for i, c in enumerate(meta.get("creators", []), 1):
        creator_dict = {"name": c["name"]}
        if "affiliation" in c:
            creator_dict["affiliation"] = c["affiliation"]
        if "orcid" in c:
            creator_dict["orcid"] = c["orcid"]
        creators_list.append(creator_dict)
        print(f"[build_metadata_dict]   Creator {i}: {c['name']}")

    # Build metadata dict
    print("[build_metadata_dict] Building core metadata fields")
    metadata = {
        "title": meta["title"],
        "upload_type": meta.get("upload_type", "dataset"),
        "description": meta["description"],
        "version": meta["version"],
        "creators": creators_list,
        "keywords": meta.get("keywords", []),
        "license": meta.get("license", "CC-BY-4.0"),
    }
    print(f"[build_metadata_dict]   Upload type: {metadata['upload_type']}")
    print(f"[build_metadata_dict]   License: {metadata['license']}")
    print(f"[build_metadata_dict]   Keywords: {len(metadata['keywords'])}")
    print(f"[build_metadata_dict]   Description length: {len(metadata['description'])} chars")

    # Add optional fields
    if "communities" in meta:
        # Convert communities to expected format
        print("[build_metadata_dict] Processing communities")
        communities = []
        for c in meta["communities"]:
            if isinstance(c, dict):
                communities.append({"identifier": c.get("identifier", c.get("name", ""))})
            else:
                communities.append({"identifier": str(c)})
        metadata["communities"] = communities
        print(f"[build_metadata_dict]   Communities: {[c['identifier'] for c in communities]}")

    if "related_identifiers" in meta:
        print(f"[build_metadata_dict] Adding {len(meta['related_identifiers'])} related identifier(s)")
        for rel in meta["related_identifiers"]:
            print(f"[build_metadata_dict]   {rel.get('relation', 'N/A')}: {rel.get('identifier', 'N/A')}")
        metadata["related_identifiers"] = meta["related_identifiers"]

    if "publication_date" in meta:
        print(f"[build_metadata_dict] Publication date: {meta['publication_date']}")
        metadata["publication_date"] = meta["publication_date"]

    print("[build_metadata_dict] Metadata dict built successfully")
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
    print_section("ZENODO PUBLICATION")
    print(f"[publish_to_zenodo] Environment: {'SANDBOX' if sandbox else 'PRODUCTION'}")
    print(f"[publish_to_zenodo] Dry run: {dry_run}")
    print(f"[publish_to_zenodo] Force: {force}")

    # Check environment variable
    token_var = "ZENODO_SANDBOX_API_TOKEN" if sandbox else "ZENODO_API_TOKEN"
    token_set = token_var in os.environ
    print(f"[publish_to_zenodo] Environment variable {token_var}: {'SET' if token_set else 'NOT SET'}")
    if not token_set:
        print(f"[publish_to_zenodo] WARNING: {token_var} not found in environment")
        print("[publish_to_zenodo] zenodo-client will try to read from ~/.config/zenodo.ini")

    # Check version against state
    print("\n[publish_to_zenodo] Checking version constraints")
    state = load_state()
    last_version = state.get("last_version")
    print(f"[publish_to_zenodo] Current version: {meta['version']}")
    print(f"[publish_to_zenodo] Last published version: {last_version or 'None'}")

    if not force and last_version == meta["version"]:
        die(
            f"Version {meta['version']} was already published "
            f"(state says last_version={last_version}). Use --force if intentional."
        )

    if force and last_version == meta["version"]:
        print(f"[publish_to_zenodo] WARNING: Force flag set, republishing same version {meta['version']}")

    # Resolve file paths
    print()
    paths = resolve_file_paths(meta)

    # Build metadata dictionary
    print()
    metadata_dict = build_metadata_dict(meta)

    # Dry run warning
    if dry_run:
        print("\n" + "="*70)
        print("WARNING: --dry-run not fully supported with zenodo-client.", file=sys.stderr)
        print("         Showing what would be uploaded:", file=sys.stderr)
        print("="*70)
        print(f"\nMetadata:\n{json.dumps(metadata_dict, indent=2)}")
        print(f"\nFiles: {[str(p) for p in paths]}")
        print("\nTo actually publish, run without --dry-run")
        return

    print_section("UPLOADING TO ZENODO")
    print(f"[publish_to_zenodo] Target: {'https://sandbox.zenodo.org' if sandbox else 'https://zenodo.org'}")
    print(f"[publish_to_zenodo] Version: {meta['version']}")
    print(f"[publish_to_zenodo] Files to upload: {len(paths)}")

    # Enable verbose logging from zenodo-client
    print("\n[publish_to_zenodo] Enabling DEBUG logging for zenodo-client")
    zenodo_logger = logging.getLogger("zenodo_client")
    zenodo_logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('[zenodo-client] %(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    zenodo_logger.addHandler(handler)

    try:
        # Use ensure_zenodo for automatic versioning
        # The 'key' parameter is used to store/retrieve deposition ID
        key = "arcaverborum_sandbox" if sandbox else "arcaverborum"
        print(f"\n[publish_to_zenodo] Using key '{key}' for deposition tracking")
        print("[publish_to_zenodo] Calling ensure_zenodo()...")
        print("[publish_to_zenodo] This will create a new deposition or update existing one")
        print(f"[publish_to_zenodo] Metadata structure: {{'metadata': {{...{len(metadata_dict)} fields...}}}}")
        print()

        response = ensure_zenodo(
            key=key,
            data={"metadata": metadata_dict},
            paths=paths,
            sandbox=sandbox,
        )

        print("\n[publish_to_zenodo] ensure_zenodo() completed successfully")
        print(f"[publish_to_zenodo] Response status code: {response.status_code}")

        # Extract information from response
        response_data = response.json()
        print("[publish_to_zenodo] Response data received, parsing...")
        print(f"[publish_to_zenodo] Response keys: {list(response_data.keys())}")

        # Update state
        print("\n[publish_to_zenodo] Updating local state")
        new_state = {
            "last_version": meta["version"],
            "last_publication_date": response_data.get("created"),
        }

        # Try to get concept DOI if available
        if "conceptdoi" in response_data:
            new_state["conceptdoi"] = response_data["conceptdoi"]
            print(f"[publish_to_zenodo] Found conceptdoi: {response_data['conceptdoi']}")
        elif "concept_doi" in response_data:
            new_state["conceptdoi"] = response_data["concept_doi"]
            print(f"[publish_to_zenodo] Found concept_doi: {response_data['concept_doi']}")

        if "doi" in response_data:
            new_state["doi"] = response_data["doi"]
            print(f"[publish_to_zenodo] Found DOI: {response_data['doi']}")

        if "id" in response_data:
            new_state["deposition_id"] = response_data["id"]
            print(f"[publish_to_zenodo] Deposition ID: {response_data['id']}")

        # Merge with existing state
        state.update(new_state)
        print()
        save_state(state)

        print_section("SUCCESS")
        print("✓ Successfully published to Zenodo!")
        print(f"\n  Version: {meta['version']}")
        print(f"  Concept DOI: {new_state.get('conceptdoi', 'N/A')}")
        if "doi" in new_state:
            print(f"  Version DOI: {new_state['doi']}")
        if "deposition_id" in new_state:
            print(f"  Deposition ID: {new_state['deposition_id']}")

        # Print record URL if available
        if "links" in response_data:
            print("\n  Available links:")
            for link_name, link_url in response_data["links"].items():
                print(f"    {link_name}: {link_url}")

            record_url = response_data["links"].get("record_html") or response_data["links"].get("html")
            if record_url:
                print(f"\n  🔗 View record at: {record_url}")

        print(f"\n  State file: {STATE_FILE}")
        print("="*70)

    except Exception as e:
        print("\n[publish_to_zenodo] ERROR occurred during publication", file=sys.stderr)
        print(f"[publish_to_zenodo] Exception type: {type(e).__name__}", file=sys.stderr)
        print(f"[publish_to_zenodo] Exception details: {e}", file=sys.stderr)
        import traceback
        print("\n[publish_to_zenodo] Full traceback:", file=sys.stderr)
        traceback.print_exc()
        die(f"Failed to publish to Zenodo: {e}")


def main() -> None:
    """
    Main entry point for the script.
    """
    print_section("ARCA VERBORUM ZENODO PUBLISHER")
    print("Script: zenodo_publish.py")
    print(f"Working directory: {Path.cwd()}")
    print()

    parser = argparse.ArgumentParser(
        description="Publish Arca Verborum dataset to Zenodo using zenodo-client."
    )
    parser.add_argument(
        "--sandbox",
        action="store_true",
        help="Use Zenodo sandbox environment (requires ZENODO_SANDBOX_API_TOKEN)"
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
    print("[main] Parsed arguments:")
    print(f"[main]   sandbox: {args.sandbox}")
    print(f"[main]   dry_run: {args.dry_run}")
    print(f"[main]   force: {args.force}")
    print(f"[main]   show: {args.show}")

    # Read metadata
    print()
    meta = read_metadata()

    # Show preview and exit if requested
    if args.show:
        print()
        print_section("METADATA PREVIEW")
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
