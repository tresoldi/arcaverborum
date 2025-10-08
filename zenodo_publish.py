#!/usr/bin/env python3
import argparse
import json
import os
import sys
import time
import hashlib
from pathlib import Path

import requests

try:
    import yaml
except Exception:
    print("Please `pip install pyyaml requests`", file=sys.stderr)
    sys.exit(1)

STATE_FILE = Path(".zenodo_state.json")
META_FILE = Path("zenodo.metadata.yml")

PROD_API = "https://zenodo.org/api"
SANDBOX_API = "https://sandbox.zenodo.org/api"

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {}

def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")

def sha256sum(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def die(msg, code=1):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)

def zenodo_headers(token):
    return {"Authorization": f"Bearer {token}"}

def ensure_token(sandbox: bool):
    env = "ZENODO_SANDBOX_TOKEN" if sandbox else "ZENODO_TOKEN"
    token = os.getenv(env)
    if not token:
        die(f"Missing {env} environment variable.")
    return token

def read_metadata():
    if not META_FILE.exists():
        die(f"Metadata file {META_FILE} not found.")
    meta = yaml.safe_load(META_FILE.read_text(encoding="utf-8"))
    required = ["title", "version", "description", "files"]
    for k in required:
        if k not in meta:
            die(f"Missing required field `{k}` in {META_FILE}")
    if not isinstance(meta["files"], list) or len(meta["files"]) == 0:
        die("`files` must be a non-empty list.")
    return meta

def get_api_base(sandbox: bool):
    return SANDBOX_API if sandbox else PROD_API

def list_depositions(api, token, size=200):
    r = requests.get(f"{api}/deposit/depositions", headers=zenodo_headers(token), params={"size": size})
    r.raise_for_status()
    return r.json()

def find_deposition_by_conceptdoi(api, token, conceptdoi):
    # Search among your depositions (auth required), match conceptdoi
    for dep in list_depositions(api, token, size=200):
        conceptdoi_dep = (dep.get("conceptdoi") or dep.get("concept_doi"))
        if conceptdoi_dep and conceptdoi_dep == conceptdoi:
            return dep
    return None

def create_new_deposition(api, token, metadata):
    r = requests.post(f"{api}/deposit/depositions",
                      headers={**zenodo_headers(token), "Content-Type": "application/json"},
                      data=json.dumps({"metadata": metadata}))
    r.raise_for_status()
    return r.json()

def new_version_from_deposition(api, token, dep_id):
    # POST /deposit/depositions/{id}/actions/newversion -> returns links.latest_draft
    r = requests.post(f"{api}/deposit/depositions/{dep_id}/actions/newversion", headers=zenodo_headers(token))
    r.raise_for_status()
    latest_draft_url = r.json()["links"]["latest_draft"]
    # Follow the draft link to get the new draft deposition JSON
    r2 = requests.get(latest_draft_url, headers=zenodo_headers(token))
    r2.raise_for_status()
    return r2.json()

def update_metadata(api, token, dep_id, metadata):
    r = requests.put(f"{api}/deposit/depositions/{dep_id}",
                     headers={**zenodo_headers(token), "Content-Type": "application/json"},
                     data=json.dumps({"metadata": metadata}))
    r.raise_for_status()
    return r.json()

def upload_file_to_bucket(bucket_url, token, local_path: Path, target_name: str, retries=3):
    for attempt in range(1, retries+1):
        with local_path.open("rb") as f:
            r = requests.put(f"{bucket_url}/{target_name}",
                             headers=zenodo_headers(token),
                             data=f)
        if r.status_code in (200, 201):
            return True
        # retry on transient errors
        time.sleep(2 * attempt)
    r.raise_for_status()  # if we got here, raise last error
    return False

def publish_deposition(api, token, dep_id):
    r = requests.post(f"{api}/deposit/depositions/{dep_id}/actions/publish", headers=zenodo_headers(token))
    r.raise_for_status()
    return r.json()

def build_metadata_payload(meta):
    md = {
        "title": meta["title"],
        "upload_type": meta.get("upload_type", "dataset"),
        "description": meta["description"],
        "version": meta["version"],
    }
    if meta.get("creators"):
        md["creators"] = meta["creators"]
    if meta.get("keywords"):
        md["keywords"] = meta["keywords"]
    if meta.get("license"):
        md["license"] = meta["license"]
    if meta.get("communities"):
        md["communities"] = [{"identifier": c["name"] if isinstance(c, dict) and "name" in c else c} for c in meta["communities"]]
    if meta.get("publication_date"):
        md["publication_date"] = meta["publication_date"]
    if meta.get("related_identifiers"):
        md["related_identifiers"] = meta["related_identifiers"]
    return md

def main():
    parser = argparse.ArgumentParser(description="Publish dataset to Zenodo (manual, simple).")
    parser.add_argument("--sandbox", action="store_true", help="Use Zenodo sandbox.")
    parser.add_argument("--dry-run", action="store_true", help="Do everything except upload/publish.")
    parser.add_argument("--force", action="store_true", help="Bypass version check.")
    parser.add_argument("--show", action="store_true", help="Print resolved metadata and exit.")
    args = parser.parse_args()

    meta = read_metadata()
    state = load_state()
    token = ensure_token(args.sandbox)
    api = get_api_base(args.sandbox)

    # Resolve files and compute checksums
    resolved_files = []
    for f in meta["files"]:
        lp = Path(f["path"]).expanduser().resolve()
        if not lp.exists():
            die(f"File not found: {lp}")
        resolved_files.append({
            "local": lp,
            "name": f.get("name", lp.name),
            "sha256": sha256sum(lp),
            "size": lp.stat().st_size
        })

    if args.show:
        # Convert resolved_files to JSON-serializable format
        files_info = [{
            "local": str(f["local"]),
            "name": f["name"],
            "sha256": f["sha256"],
            "size": f["size"]
        } for f in resolved_files]

        print(json.dumps({
            "api": api,
            "metadata": build_metadata_payload(meta),
            "files": files_info
        }, indent=2))
        return

    last_version = state.get("last_version")
    if last_version == meta["version"] and not args.force:
        die(f"Version {meta['version']} was already published (state says last_version={last_version}). Use --force if intentional.")

    conceptdoi = meta.get("conceptdoi") or state.get("conceptdoi")
    deposition_json = None

    if conceptdoi:
        existing = find_deposition_by_conceptdoi(api, token, conceptdoi)
        if not existing:
            print(f"Note: concept DOI {conceptdoi} not found among your depositions. Will create a NEW concept.", file=sys.stderr)
            deposition_json = None
        else:
            print(f"Found existing concept DOI {conceptdoi}; creating a new version…")
            if args.dry_run:
                print("[dry-run] Would POST newversion and get latest draft.")
                # fake deposition-like structure for preview
                deposition_json = {"id": existing["id"], "links": {"bucket": "(dry-run)"}}
            else:
                draft = new_version_from_deposition(api, token, existing["id"])
                deposition_json = draft
    if deposition_json is None:
        # Create fresh deposition with metadata
        md_payload = build_metadata_payload(meta)
        if args.dry_run:
            print("[dry-run] Would create new deposition with metadata:")
            print(json.dumps(md_payload, indent=2))
            deposition_json = {"id": 0, "links": {"bucket": "(dry-run)"}}
        else:
            deposition_json = create_new_deposition(api, token, md_payload)

    dep_id = deposition_json["id"]
    print(f"Working deposition id: {dep_id}")

    # Upload files
    bucket_url = deposition_json["links"].get("bucket")
    if not bucket_url:
        if args.dry_run:
            bucket_url = "(dry-run)"
        else:
            die("Bucket link not found on deposition.")

    for f in resolved_files:
        print(f"Uploading {f['local'].name} ({f['size']} bytes) as {f['name']} …")
        if args.dry_run:
            print(f"[dry-run] Would PUT to {bucket_url}/{f['name']}")
        else:
            upload_file_to_bucket(bucket_url, token, f["local"], f["name"])
            print(f"  ✓ uploaded; sha256={f['sha256']}")

    # Ensure metadata (e.g., if we created newversion first, we still set/refresh metadata)
    md_payload = build_metadata_payload(meta)
    if args.dry_run:
        print("[dry-run] Would PUT metadata:")
        print(json.dumps(md_payload, indent=2))
    else:
        update_metadata(api, token, dep_id, md_payload)
        print("  ✓ metadata updated")

    # Publish
    if args.dry_run:
        print("[dry-run] Would publish now.")
        publish_json = {"conceptdoi": "(dry-run)"}
    else:
        publish_json = publish_deposition(api, token, dep_id)
        print("  ✓ published")

    # Update local state
    # After publishing, Zenodo responds with concept DOI; store it for next runs.
    new_conceptdoi = publish_json.get("conceptdoi") or publish_json.get("concept_doi") or conceptdoi
    state["last_version"] = meta["version"]
    if new_conceptdoi:
        state["conceptdoi"] = new_conceptdoi
    save_state(state)

    print("\nDone.")
    if new_conceptdoi:
        print(f"Concept DOI: {new_conceptdoi}")
    if not args.dry_run:
        record_url = publish_json["links"].get("record_html") or publish_json["links"].get("html")
        if record_url:
            print(f"Record: {record_url}")

if __name__ == "__main__":
    main()

