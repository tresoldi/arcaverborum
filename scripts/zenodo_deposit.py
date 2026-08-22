#!/usr/bin/env python3
"""Prepare / upload the Arca Verborum Core release to Zenodo as a NEW VERSION
of the existing concept DOI.

Safe by design:
* With no token (or --dry-run), it only builds and writes the Zenodo metadata
  JSON next to the release and prints the manual-upload steps. No network.
* With a token, it creates a new-version DRAFT and uploads the zip, but does
  NOT publish unless you pass --publish. Review the draft in the Zenodo UI first.
* --sandbox targets sandbox.zenodo.org (recommended for a first dry run).

Token: pass --token, or set ZENODO_TOKEN (ZENODO_SANDBOX_TOKEN for --sandbox).

Usage:
  python scripts/zenodo_deposit.py --dry-run            # write metadata only
  ZENODO_SANDBOX_TOKEN=... python scripts/zenodo_deposit.py --sandbox
  ZENODO_TOKEN=... python scripts/zenodo_deposit.py            # real, draft only
  ZENODO_TOKEN=... python scripts/zenodo_deposit.py --publish  # real + publish
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONCEPT_DOI = "10.5281/zenodo.17294927"
LEXIBANK_DOI = "10.1038/s41597-022-01432-0"


def _load_citation_authors(cff_path: Path) -> list[dict]:
    """Best-effort parse of CITATION.cff authors (uses yaml if available)."""
    try:
        import yaml
        cff = yaml.safe_load(cff_path.read_text(encoding="utf-8"))
    except Exception:
        return [{"name": "Tresoldi, Tiago",
                 "orcid": "https://orcid.org/0000-0002-2863-1467",
                 "affiliation": "Uppsala University"}]
    out = []
    for a in cff.get("authors", []):
        entry = {"name": f"{a.get('family-names', '')}, {a.get('given-names', '')}".strip(", ")}
        if a.get("orcid"):
            entry["orcid"] = a["orcid"].replace("https://orcid.org/", "")
        if a.get("affiliation"):
            entry["affiliation"] = a["affiliation"]
        out.append(entry)
    return out or [{"name": "Tresoldi, Tiago"}]


def build_metadata(release_dir: Path) -> dict:
    manifest = json.loads((release_dir / "MANIFEST.json").read_text(encoding="utf-8"))
    authors = _load_citation_authors(PROJECT_ROOT / "CITATION.cff")
    c = manifest["counts"]

    src_rows = "".join(
        f"<li>{s['dataset']} — {s['forms']:,} forms — {s['license']}</li>"
        for s in manifest["sources"]
    )
    description = (
        "<p><strong>Arca Verborum Core</strong> is a basic-vocabulary lexical dataset for "
        "computational historical linguistics. For each language variety it provides one "
        "accepted construction from a single curated source, with per-form provenance and "
        "quality scoring, across 13 curated CORE families (one source per family).</p>"
        f"<p>This version contains <strong>{c['forms']:,} forms</strong> across "
        f"<strong>{c['languages']} varieties</strong> and <strong>{c['parameters']} concepts</strong>, "
        f"with {c['cognate_rows']:,} cognate-coded forms in {c['cognatesets']:,} cognate sets. "
        "A frozen basic-vocabulary core is marked with the <code>is_core_concept</code> flag. "
        "The dataset is a CLDF-compatible Wordlist that is also plain CSV.</p>"
        "<p><strong>Licensing (mixed, per source).</strong> Each source retains its own license, "
        "recorded per row in the <code>License</code> column and summarised below. Attribution is "
        "required. Most sources are CC-BY-4.0; <em>grollemundbantu</em> (Bantu) is "
        "<strong>CC-BY-NC-4.0</strong>, so commercial reuse must exclude those rows (filter "
        "<code>License</code>). See README.md in the archive for full attribution and citations.</p>"
        f"<ul>{src_rows}</ul>"
        f"<p>Built with merkmal {manifest['merkmal_version']}; per-source repository versions are "
        "recorded in MANIFEST.json.</p>"
    )

    related = [{"identifier": LEXIBANK_DOI, "relation": "references", "scheme": "doi"}]
    for s in manifest["sources"]:
        if s.get("url"):
            related.append({"identifier": s["url"], "relation": "isDerivedFrom", "scheme": "url"})

    return {
        "metadata": {
            "title": "Arca Verborum Core",
            "upload_type": "dataset",
            "description": description,
            "creators": authors,
            "version": manifest["version"],
            # Mixed licensing: Zenodo record-level set to Other (Open); the authoritative
            # per-source terms live in the License column + README. REVIEW in the UI.
            "license": "other-open",
            "access_right": "open",
            "keywords": ["computational historical linguistics", "lexical database",
                         "wordlist", "cognates", "CLDF", "basic vocabulary", "Lexibank"],
            "related_identifiers": related,
            "notes": "Contains one CC-BY-NC-4.0 source (grollemundbantu); the aggregate is "
                     "therefore not uniformly CC-BY. See per-row License column and README.md.",
        }
    }


def _api(base: str, path: str, token: str, method: str = "GET", **kw):
    import requests
    url = f"{base}/api{path}"
    params = kw.pop("params", {})
    params["access_token"] = token
    r = requests.request(method, url, params=params, timeout=60, **kw)
    if r.status_code >= 400:
        raise SystemExit(f"Zenodo API {method} {path} failed [{r.status_code}]: {r.text[:500]}")
    return r.json() if r.text else {}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--release-dir",
                    default=str(PROJECT_ROOT / "output" / "release" / "arca-verborum-core-0.1.0"))
    ap.add_argument("--zip", default=None, help="Zip to upload (default: <release-dir>.zip)")
    ap.add_argument("--concept-doi", default=CONCEPT_DOI)
    ap.add_argument("--sandbox", action="store_true")
    ap.add_argument("--publish", action="store_true", help="Publish the draft (irreversible!)")
    ap.add_argument("--dry-run", action="store_true", help="Write metadata JSON only; no network")
    ap.add_argument("--token", default=None)
    args = ap.parse_args(argv)

    release_dir = Path(args.release_dir)
    # Note: release_dir name contains dots (e.g. 0.1.0), so with_suffix would mangle it.
    zip_path = Path(args.zip) if args.zip else release_dir.parent / (release_dir.name + ".zip")
    metadata = build_metadata(release_dir)

    meta_path = release_dir.parent / f"zenodo-deposit-{metadata['metadata']['version']}.json"
    meta_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote deposit metadata -> {meta_path}")

    base = "https://sandbox.zenodo.org" if args.sandbox else "https://zenodo.org"
    token = args.token or os.environ.get(
        "ZENODO_SANDBOX_TOKEN" if args.sandbox else "ZENODO_TOKEN")

    if args.dry_run or not token:
        print("\nNo upload performed (dry-run or no token).")
        print("Manual route: create a new version of "
              f"{args.concept_doi} in the Zenodo UI, upload\n  {zip_path}\n"
              f"and apply the metadata from {meta_path}.")
        print("Automated route: set ZENODO_TOKEN (or ZENODO_SANDBOX_TOKEN with --sandbox) "
              "and re-run; add --publish only when the draft looks right.")
        return 0

    if not zip_path.exists():
        raise SystemExit(f"Zip not found: {zip_path}")

    concept_recid = args.concept_doi.split("zenodo.")[-1]
    print(f"Resolving concept {args.concept_doi} on {base} …")
    versions = _api(base, "/deposit/depositions", token,
                    params={"q": f"conceptrecid:{concept_recid}", "size": 100, "all_versions": 1})
    if not versions:
        raise SystemExit(f"No owned depositions found for conceptrecid {concept_recid}. "
                         "Check the token owns this record, or deposit as a new record instead.")
    latest = sorted(versions, key=lambda d: d.get("created", ""))[-1]
    print(f"Latest owned version: id={latest['id']} state={latest.get('state')}")

    draft = _api(base, f"/deposit/depositions/{latest['id']}/actions/newversion", token, method="POST")
    draft = _api(base, f"/deposit/depositions/{draft['links']['latest_draft'].split('/')[-1]}", token)
    dep_id = draft["id"]
    print(f"New-version draft: id={dep_id}")

    for f in draft.get("files", []):
        _api(base, f"/deposit/depositions/{dep_id}/files/{f['id']}", token, method="DELETE")
    print("Cleared copied files.")

    import requests
    bucket = draft["links"]["bucket"]
    with zip_path.open("rb") as fh:
        r = requests.put(f"{bucket}/{zip_path.name}", data=fh,
                         params={"access_token": token}, timeout=1800)
    if r.status_code >= 400:
        raise SystemExit(f"Upload failed [{r.status_code}]: {r.text[:500]}")
    print(f"Uploaded {zip_path.name}")

    _api(base, f"/deposit/depositions/{dep_id}", token, method="PUT", json=metadata)
    print("Metadata applied.")

    if args.publish:
        rec = _api(base, f"/deposit/depositions/{dep_id}/actions/publish", token, method="POST")
        print(f"PUBLISHED: {rec['links'].get('record_html', rec['links'])}  DOI: {rec.get('doi')}")
    else:
        print(f"\nDRAFT ready (NOT published). Review: {draft['links'].get('html')}")
        print("Re-run with --publish to publish, or publish from the Zenodo UI.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
