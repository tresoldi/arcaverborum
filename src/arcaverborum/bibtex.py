from __future__ import annotations

import logging
import re
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def prefix_bibtex_keys(source_str: str, dataset: str) -> str:
    if pd.isna(source_str) or source_str == "":
        return source_str
    keys = [k.strip() for k in str(source_str).split(";")]
    return ";".join(f"{dataset}_{k}" for k in keys if k)


def prefix_bibtex_file(bibtex_content: str, dataset: str) -> str:
    return re.sub(
        r"@(\w+)\{([^,]+),",
        lambda m: f"@{m.group(1)}{{{dataset}_{m.group(2)},",
        bibtex_content,
    )


def load_bibtex(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        logger.warning("Failed to load BibTeX from %s: %s", path, e)
        return ""
