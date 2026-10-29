"""List accepted constructions with guarded alternatives to their configured primary.

This inventories authored admissions, not raw dictionaries or independent attestations.
It does not validate source drift, certify quality, or choose a primary. Rebuild and
review exact identity, senses, provenance and readings before changing a recipe.
"""
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def audit(root=ROOT):
    result = []
    for directory in sorted((root / 'varieties').iterdir()):
        if not (directory / 'generated/forms.csv').exists():
            continue
        config = yaml.safe_load((directory / 'config.yaml').read_text())
        primary = config['sources']['transcription']
        ledger = directory / 'custom/supplements.csv'
        if not ledger.exists():
            continue
        groups = defaultdict(list)
        with ledger.open() as handle:
            for row in csv.DictReader(handle):
                if row['decision'] == 'admit' and row['source'] != primary:
                    groups[row['source']].append(row)
        for source, rows in groups.items():
            result.append(dict(
                av_id=directory.name, primary=primary, alternative=source,
                reviewed_records=len(rows),
                concepts=len({row['concept_id'] for row in rows}),
                profile_records=sum(bool(row.get('profile_file')) for row in rows),
                scoped_records=sum(bool(row.get('pronunciation_scope')) for row in rows),
                profile_groups=len({row.get('profile_file', '') for row in rows}),
                next_gate=('Review original readings, exact member/stage, senses and residual coverage; '
                           'counts do not certify quality.'),
            ))
    return sorted(result, key=lambda row: (
        row['primary'] != 'gled', row['alternative'] != 'wiktionary',
        -row['concepts'], row['av_id'], row['alternative']))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    rows = audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('w') as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            'av_id', 'primary', 'alternative', 'reviewed_records', 'concepts',
            'profile_records', 'scoped_records', 'profile_groups', 'next_gate',
        ], lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    print(f'{len(rows)} reviewed source alternatives: {args.output}')


if __name__ == '__main__':
    main()
