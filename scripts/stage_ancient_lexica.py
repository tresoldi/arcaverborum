"""Reproduce frozen historical lexical slices outside active intake."""

from __future__ import annotations

import argparse
from pathlib import Path

from arcaverborum.ingest import ingest_lexibank
from arcaverborum.sources.ancient_lexica import materialize

ROOT = Path(__file__).resolve().parents[1]
if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dataset", required=True)
    p.add_argument("--fetch", action="store_true")
    p.add_argument("--output", type=Path)
    a = p.parse_args()
    out = (a.output or ROOT / "raw/curation" / ("stage-" + a.dataset)).resolve()
    if out == ROOT / "intake" or ROOT / "intake" in out.parents:
        raise ValueError("Stage outside active intake")
    expected = materialize(ROOT / "raw", dataset=a.dataset, download=a.fetch)
    print(expected)
    result = ingest_lexibank(ROOT / "raw", out, datasets=[a.dataset])
    if result["datasets_ingested"] != 1 or result["total_forms"] != expected["forms"]:
        raise ValueError("Historical slice incomplete")
    print(result)
