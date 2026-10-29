"""Verify immutable source bytes for the GW01–GW10 batch, without touching intake.

--fetch acquires the pinned repositories/PDFs under raw/. Existing dirty research
checkouts are never reset. African, RVID and ancient derivative reproduction use
those sources' dedicated staging commands; this verifies the underlying inputs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/worldwide_execution_sources_2026-10-29.json"


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def verify(*, fetch=False):
    resources = 0
    for name, spec in json.loads(MANIFEST.read_text()).items():
        if "resource_sha256" in spec:
            root = ROOT / "raw/lexibank" / name
            if fetch:
                created = not root.exists()
                if not root.exists():
                    subprocess.run(["git", "clone", "--no-checkout", spec["repo"], str(root)], check=True)
                if not created and git(root, "status", "--porcelain"):
                    raise ValueError("Pinned source has local research edits: " + name)
                subprocess.run(["git", "-C", str(root), "fetch", "origin", spec["commit"]], check=True)
                subprocess.run(["git", "-C", str(root), "checkout", "--detach", spec["commit"]], check=True)
            if git(root, "rev-parse", "HEAD") != spec["commit"]:
                raise ValueError("Source commit differs: " + name)
            for relative, expected in spec["resource_sha256"].items():
                if hashlib.sha256((root / relative).read_bytes()).hexdigest() != expected:
                    raise ValueError("Source bytes differ: " + name + "/" + relative)
                resources += 1
        elif spec.get("cache_path"):
            path = ROOT / spec["cache_path"]
            if fetch:
                response = requests.get(spec["url"], timeout=60)
                response.raise_for_status()
                if hashlib.sha256(response.content).hexdigest() != spec["sha256"]:
                    raise ValueError("Acquired PDF differs: " + name)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(response.content)
            if hashlib.sha256(path.read_bytes()).hexdigest() != spec["sha256"]:
                raise ValueError("Acquisition bytes differ: " + name)
            resources += 1
    return resources


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true")
    args = parser.parse_args()
    print("Verified", verify(fetch=args.fetch), "pinned source resources; active intake unchanged")
