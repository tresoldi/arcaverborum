"""Glottolog source: cache the languages.csv from glottolog-cldf.

`fetch(raw_root)` downloads (if missing) into `raw/glottolog/languages.csv`.
The catalog module reads from this cache by preference, falling back to
the URL.
"""

from __future__ import annotations

import logging
import urllib.request
from pathlib import Path

logger = logging.getLogger(__name__)

GLOTTOLOG_CSV_URL = (
    "https://raw.githubusercontent.com/glottolog/glottolog-cldf/master/cldf/languages.csv"
)


def fetch(raw_root: Path, url: str = GLOTTOLOG_CSV_URL, force: bool = False) -> Path:
    target_dir = raw_root / "glottolog"
    target_dir.mkdir(parents=True, exist_ok=True)
    out = target_dir / "languages.csv"
    if out.exists() and not force:
        logger.info("Glottolog cache present: %s (%d bytes)", out, out.stat().st_size)
        return out
    logger.info("Downloading %s → %s", url, out)
    urllib.request.urlretrieve(url, out)
    logger.info("Done. %d bytes", out.stat().st_size)
    return out
