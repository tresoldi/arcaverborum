"""Reproduce the bounded Sidaama reading witnesses from frozen original SFM bytes."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import merkmal
import requests

from arcaverborum.phonology import canonicalize_token, segments_are_valid
from arcaverborum.sources.sidaama_readings import phonemic_witnesses

ROOT = Path(__file__).resolve().parents[1]


def verify(*, fetch=False):
    directory = ROOT / "raw/curation/ax04-sidaama"
    directory.mkdir(parents=True, exist_ok=True)
    for spec in json.loads((ROOT / "docs/africa_ax04_sidaama_sources_2026-10-29.json").read_text()):
        path = directory / spec["path"].replace("/", "-")
        if fetch:
            response = requests.get(spec["url"], timeout=60)
            response.raise_for_status()
            if hashlib.sha256(response.content).hexdigest() != spec["sha256"]:
                raise ValueError("Original Sidaama source bytes changed")
            path.write_bytes(response.content)
        if hashlib.sha256(path.read_bytes()).hexdigest() != spec["sha256"]:
            raise ValueError("Original Sidaama source bytes changed")
    payload = (directory / "raw-db.sfm").read_bytes()
    with (ROOT / "docs/africa_ax04_sidaama_witnesses_2026-10-29.csv").open() as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        if hashlib.sha256(payload).hexdigest() != row["original_sfm_sha256"]:
            raise ValueError("Original Sidaama source hash drift")
        witnesses = phonemic_witnesses(payload, row["Form"])
        if witnesses != json.loads(row["witnesses"]):
            raise ValueError("Original Sidaama phonemic witnesses changed")
        tokens = [canonicalize_token(t) for t in merkmal.segment_ipa(row["Form"])]
        out = []
        i = 0
        while i < len(tokens):
            token = tokens[i]
            i += 1
            if i < len(tokens) and token == tokens[i]:
                token += "ː"
                i += 1
            out.append(token)
        segments = " ".join(out)
        if segments != row["segments"] or not segments_are_valid(segments):
            raise ValueError("Sidaama finite reading changed")
    print(f"Verified {len(rows)} explicit source-phonemic witnesses and quantity readings")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true")
    verify(fetch=parser.parse_args().fetch)
