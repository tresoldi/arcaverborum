"""Materialize and stage frozen African lexical sources outside active intake."""

import argparse
from pathlib import Path

from arcaverborum.ingest import ingest_lexibank
from arcaverborum.sources.african_lexica import materialize

ROOT = Path(__file__).resolve().parents[1]
if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dataset", required=True)
    p.add_argument("--fetch", action="store_true")
    a = p.parse_args()
    stats = materialize(ROOT / "raw", dataset=a.dataset, download=a.fetch)
    result = ingest_lexibank(ROOT / "raw", ROOT / "raw/curation" / ("stage-" + a.dataset), datasets=[a.dataset])
    if result["datasets_ingested"] != 1 or result["total_forms"] != stats["forms"]:
        raise ValueError("African source staging incomplete")
    print(stats)
