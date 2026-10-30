"""Append staged, newly ingested Lexibank datasets without replacing existing intake.

Stage with ingest_lexibank(raw_root, temporary_intake_root, datasets=[...]).
Pass its lexibank directory with --staged; default is a read-only validation.
--write preserves every original byte, appends new rows, then replaces files.
This is for new source names only, not an upstream refresh of an existing name.
"""

from __future__ import annotations

import argparse
import csv
import os
import shutil
import sys
import tempfile
from pathlib import Path

csv.field_size_limit(sys.maxsize)

ROOT = Path(__file__).resolve().parents[1]
TABLES = ('forms.csv', 'languages.csv', 'parameters_raw.csv', 'metadata.csv')


def append_intake(staged: Path, target: Path, *, write: bool = False) -> set[str]:
    def datasets(path: Path) -> set[str]:
        with path.open() as f:
            return {r['Dataset'] for r in csv.DictReader(f)}

    added = datasets(staged / 'metadata.csv')
    if not added or added & datasets(target / 'metadata.csv'):
        raise ValueError('Stage must contain only new, nonempty dataset names')
    for name in TABLES:
        with (staged / name).open() as f, (target / name).open() as old:
            reader = csv.DictReader(f)
            if reader.fieldnames != csv.DictReader(old).fieldnames:
                raise ValueError('Intake schema mismatch: ' + name)
            seen = set()
            for row in reader:
                seen.add(row['Dataset'])
                if row['Dataset'] not in added:
                    raise ValueError('Unregistered staged dataset: ' + row['Dataset'])
            if seen != added:
                raise ValueError('Dataset missing from staged table: ' + name)
    if not (staged / 'sources.bib').exists():
        raise ValueError('Staged bibliography missing')
    if not write:
        return added
    names = (*TABLES, 'sources.bib')
    # Prepare all complete outputs first. Original hard links support rollback
    # if a replacement fails; they disappear with this temporary directory.
    with tempfile.TemporaryDirectory(prefix='.append-', dir=target.parent) as temporary:
        work = Path(temporary)
        for name in names:
            os.link(target / name, work / ('old-' + name))
            shutil.copyfile(target / name, work / name)
            with (work / name).open('ab') as out, (staged / name).open('rb') as source:
                if name != 'sources.bib':
                    source.readline()
                out.write(b'\n')
                shutil.copyfileobj(source, out)
        committed = []
        try:
            for name in names:
                os.replace(work / name, target / name)
                committed.append(name)
        except BaseException:
            for name in committed:
                os.replace(work / ('old-' + name), target / name)
            raise
    return added


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--staged', type=Path, required=True)
    parser.add_argument('--target', type=Path, default=ROOT / 'intake/lexibank')
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    added = append_intake(args.staged, args.target, write=args.write)
    print(('Appended: ' if args.write else 'Validated, no writes: ') + ', '.join(sorted(added)))


if __name__ == '__main__':
    main()
