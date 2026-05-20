"""Concepticon source: cache concepticon.tsv from concepticon-data.

`fetch(raw_root)` writes `raw/concepticon/concepticon.tsv`.
"""

from __future__ import annotations

import logging
import urllib.request
from pathlib import Path

logger = logging.getLogger(__name__)

CONCEPTICON_URL = (
    "https://raw.githubusercontent.com/concepticon/concepticon-data/"
    "master/concepticondata/concepticon.tsv"
)


def fetch(raw_root: Path, url: str = CONCEPTICON_URL, force: bool = False) -> Path:
    target_dir = raw_root / "concepticon"
    target_dir.mkdir(parents=True, exist_ok=True)
    out = target_dir / "concepticon.tsv"
    if out.exists() and not force:
        logger.info("Concepticon cache present: %s (%d bytes)", out, out.stat().st_size)
        return out
    logger.info("Downloading %s → %s", url, out)
    urllib.request.urlretrieve(url, out)
    logger.info("Done. %d bytes", out.stat().st_size)
    return out
