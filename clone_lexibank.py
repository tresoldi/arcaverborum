#!/usr/bin/env python3
"""
Clone and update Lexibank repositories from datasets.csv.

This script reads a CSV file containing repository information and clones
or updates repositories in a local lexibank/ directory.
"""

import argparse
import csv
import logging
import subprocess
import sys
from pathlib import Path
from typing import Tuple


def setup_logging(verbose: bool = False) -> None:
    """
    Configure logging for the script.

    @param verbose: If True, set logging level to DEBUG
    @type verbose: bool
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def clone_repository(name: str, url: str, target_dir: Path) -> bool:
    """
    Clone a repository with shallow clone.

    @param name: Repository name
    @type name: str
    @param url: Repository URL
    @type url: str
    @param target_dir: Target directory for clone
    @type target_dir: Path
    @return: True if successful, False otherwise
    @rtype: bool
    """
    try:
        logging.info(f"Cloning {name} from {url}")
        result = subprocess.run(
            ['git', 'clone', '--depth', '1', url, str(target_dir)],
            capture_output=True,
            text=True,
            check=True
        )
        logging.debug(f"Clone output: {result.stdout}")
        logging.info(f"Successfully cloned {name}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to clone {name}: {e.stderr}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error cloning {name}: {e}")
        return False


def update_repository(name: str, repo_dir: Path) -> bool:
    """
    Update an existing repository with git pull.

    @param name: Repository name
    @type name: str
    @param repo_dir: Repository directory
    @type repo_dir: Path
    @return: True if successful, False otherwise
    @rtype: bool
    """
    try:
        logging.info(f"Updating {name}")
        result = subprocess.run(
            ['git', '-C', str(repo_dir), 'pull'],
            capture_output=True,
            text=True,
            check=True
        )
        logging.debug(f"Pull output: {result.stdout}")
        logging.info(f"Successfully updated {name}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to update {name}: {e.stderr}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error updating {name}: {e}")
        return False


def process_repository(name: str, url: str, lexibank_dir: Path) -> Tuple[bool, str]:
    """
    Clone or update a repository.

    @param name: Repository name
    @type name: str
    @param url: Repository URL
    @type url: str
    @param lexibank_dir: Lexibank directory
    @type lexibank_dir: Path
    @return: Tuple of (success, action) where action is 'cloned', 'updated', or 'failed'
    @rtype: Tuple[bool, str]
    """
    repo_dir = lexibank_dir / name

    if repo_dir.exists():
        success = update_repository(name, repo_dir)
        return (success, 'updated' if success else 'failed')
    else:
        success = clone_repository(name, url, repo_dir)
        return (success, 'cloned' if success else 'failed')


def read_datasets(csv_path: Path, core_only: bool = False, corecog_only: bool = False) -> list:
    """
    Read repository information from CSV file.

    @param csv_path: Path to datasets.csv
    @type csv_path: Path
    @param core_only: If True, only return core datasets
    @type core_only: bool
    @param corecog_only: If True, only return corecog datasets
    @type corecog_only: bool
    @return: List of repository dictionaries
    @rtype: list
    """
    repositories = []

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get('NAME', '').strip()
                url = row.get('URL', '').strip()
                is_core = row.get('CORE', '').strip() == 'TRUE'
                is_corecog = row.get('CORECOG', '').strip() == 'TRUE'

                # Filter by collection if requested
                if core_only and not is_core:
                    continue
                if corecog_only and not is_corecog:
                    continue

                if name and url:
                    repositories.append({
                        'name': name,
                        'url': url,
                        'is_core': is_core,
                        'is_corecog': is_corecog
                    })

        if core_only:
            logging.info(f"Found {len(repositories)} core repositories in {csv_path}")
        elif corecog_only:
            logging.info(f"Found {len(repositories)} corecog repositories in {csv_path}")
        else:
            logging.info(f"Found {len(repositories)} repositories in {csv_path}")
        return repositories

    except FileNotFoundError:
        logging.error(f"CSV file not found: {csv_path}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error reading CSV file: {e}")
        sys.exit(1)


def main() -> None:
    """
    Main entry point for the script.
    """
    parser = argparse.ArgumentParser(
        description='Clone and update Lexibank repositories from datasets.csv'
    )
    parser.add_argument(
        '--csv',
        type=Path,
        default=Path('datasets.csv'),
        help='Path to datasets.csv file (default: datasets.csv)'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('lexibank'),
        help='Output directory for repositories (default: lexibank)'
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without actually cloning/updating'
    )
    parser.add_argument(
        '--core-only',
        action='store_true',
        help='Clone only core datasets (13 datasets for pedagogical use)'
    )
    parser.add_argument(
        '--corecog-only',
        action='store_true',
        help='Clone only corecog datasets (58 datasets with expert cognate judgments)'
    )

    args = parser.parse_args()

    setup_logging(args.verbose)

    if args.core_only:
        logging.info("Starting Lexibank core repository synchronization (core-only mode)")
    elif args.corecog_only:
        logging.info("Starting Lexibank corecog repository synchronization (corecog-only mode)")
    else:
        logging.info("Starting Lexibank repository synchronization")

    # Read repositories from CSV
    repositories = read_datasets(args.csv, core_only=args.core_only, corecog_only=args.corecog_only)

    if args.dry_run:
        logging.info("DRY RUN MODE - No actual changes will be made")
        for repo in repositories:
            repo_dir = args.output_dir / repo['name']
            action = "update" if repo_dir.exists() else "clone"
            logging.info(f"Would {action}: {repo['name']} from {repo['url']}")
        return

    # Create lexibank directory if it doesn't exist
    args.output_dir.mkdir(exist_ok=True)
    logging.info(f"Using output directory: {args.output_dir}")

    # Process each repository
    stats = {'cloned': 0, 'updated': 0, 'failed': 0}

    for repo in repositories:
        success, action = process_repository(
            repo['name'],
            repo['url'],
            args.output_dir
        )
        stats[action] += 1

    # Print summary
    logging.info("=" * 60)
    logging.info("SUMMARY")
    logging.info("=" * 60)
    logging.info(f"Total repositories: {len(repositories)}")
    logging.info(f"Cloned: {stats['cloned']}")
    logging.info(f"Updated: {stats['updated']}")
    logging.info(f"Failed: {stats['failed']}")

    if stats['failed'] > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()
