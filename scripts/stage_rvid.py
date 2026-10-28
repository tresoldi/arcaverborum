"""Reproduce the pinned RVID infinitive derivative outside active intake."""

from __future__ import annotations

import argparse
from pathlib import Path

from arcaverborum.ingest import ingest_lexibank
from arcaverborum.sources.rvid import materialize

ROOT = Path(__file__).resolve().parents[1]
if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fetch", action="store_true")
    p.add_argument("--source-root", type=Path)
    p.add_argument("--output", type=Path, default=ROOT / "raw/curation/rvid-stage")
    a = p.parse_args()
    if a.output.resolve() == ROOT / "intake" or ROOT / "intake" in a.output.resolve().parents:
        raise ValueError("Stage outside active intake")
    print(materialize(ROOT / "raw", download=a.fetch, source_root=a.source_root))
    result = ingest_lexibank(ROOT / "raw", a.output, datasets=["rvidinfinitives"])
    if result["datasets_ingested"] != 1 or result["total_forms"] != 33:
        raise ValueError("Reviewed RVID slice did not stage completely")
    print(result)
