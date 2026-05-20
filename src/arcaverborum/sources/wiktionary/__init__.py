"""Wiktionary source: download kaikki dump + processing pipeline.

`fetch(raw_root)` downloads (if missing) the kaikki.org JSONL dump to
`raw/wiktionary/raw.jsonl.gz`. Processing the dump into intake CSVs is
handled by `_cli.py` (kept for parity with the previous pipeline).
"""

from __future__ import annotations

import logging
import urllib.request
from pathlib import Path

logger = logging.getLogger(__name__)

KAIKKI_URL = "https://kaikki.org/dictionary/raw-wiktextract-data.jsonl.gz"


def fetch(raw_root: Path, url: str = KAIKKI_URL, force: bool = False) -> Path:
    target_dir = raw_root / "wiktionary"
    target_dir.mkdir(parents=True, exist_ok=True)
    out = target_dir / "raw.jsonl.gz"
    if out.exists() and not force:
        logger.info("Wiktionary dump already cached at %s (%d bytes)",
                    out, out.stat().st_size)
        return out
    logger.info("Downloading %s → %s", url, out)
    urllib.request.urlretrieve(url, out)
    logger.info("Done. %d bytes", out.stat().st_size)
    return out


def ingest(raw_root: Path, intake_root: Path, threshold: int = 10) -> dict:
    """raw/wiktionary/raw.jsonl.gz → intake/wiktionary/ with Glottocodes."""
    from arcaverborum.sources.wiktionary._cli import run_pipeline

    dump = raw_root / "wiktionary" / "raw.jsonl.gz"
    out_dir = intake_root / "wiktionary"
    return run_pipeline(
        input_path=dump,
        output_dir=out_dir,
        threshold=threshold,
        enrich_glottocodes=True,
    )
