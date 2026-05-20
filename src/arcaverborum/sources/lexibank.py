"""Lexibank: clone/update CLDF wordlist datasets from datasets.csv.

`fetch(raw_root)` clones into `raw_root/lexibank/<dataset>/` (170 repos).
Datasets needing conversion (e.g. GLED) are post-processed via
`arcaverborum.sources.gled.convert`.
"""

from __future__ import annotations

import csv
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

DATASETS_CSV_DEFAULT = Path("datasets.csv")
DATASETS_NEEDING_CONVERSION = {"gled"}


def _clone(name: str, url: str, target_dir: Path) -> bool:
    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", url, str(target_dir)],
            capture_output=True, text=True, check=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        logger.error("clone %s: %s", name, e.stderr.strip())
        return False


def _update(name: str, repo_dir: Path) -> bool:
    try:
        subprocess.run(
            ["git", "-C", str(repo_dir), "pull"],
            capture_output=True, text=True, check=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        logger.error("pull %s: %s", name, e.stderr.strip())
        return False


def _read_datasets(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open(encoding="utf-8") as f:
        return [dict(r) for r in csv.DictReader(f) if r.get("NAME") and r.get("URL")]


def fetch(
    raw_root: Path,
    datasets_csv: Path = DATASETS_CSV_DEFAULT,
    curated_only: bool = False,
    expert_cognates_only: bool = False,
    dry_run: bool = False,
) -> dict[str, int]:
    target_dir = raw_root / "lexibank"
    target_dir.mkdir(parents=True, exist_ok=True)

    repos = _read_datasets(datasets_csv)
    if curated_only:
        repos = [r for r in repos if r.get("CORE", "").strip().upper() == "TRUE"]
    elif expert_cognates_only:
        repos = [r for r in repos if r.get("ExpertCognates", "").strip().upper() == "TRUE"]

    logger.info("Fetch lexibank: %d repos", len(repos))
    stats = {"cloned": 0, "updated": 0, "failed": 0}

    for repo in repos:
        name = repo["NAME"].strip()
        url = repo["URL"].strip()
        repo_dir = target_dir / name

        if dry_run:
            action = "update" if repo_dir.exists() else "clone"
            logger.info("[dry-run] %s %s", action, name)
            continue

        if repo_dir.exists():
            ok = _update(name, repo_dir)
            stats["updated" if ok else "failed"] += 1
        else:
            ok = _clone(name, url, repo_dir)
            stats["cloned" if ok else "failed"] += 1

        if ok and name in DATASETS_NEEDING_CONVERSION:
            from arcaverborum.sources import gled
            gled.convert(repo_dir)

    logger.info("Lexibank fetch summary: %s", stats)
    return stats


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    fetch(Path("raw"))
