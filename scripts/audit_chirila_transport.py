"""Privately stage the pinned historical CHIRILA export without public admission.

No spellings, upstream phonemicizations, reconstructed forms or glosses are
rewritten. Row ordinals preserve duplicates. The SQLite output is research-only;
this tool never writes active intake, recipes or website data.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
from pathlib import Path

PINNED_SHA256 = '9df03930ef869415a99842ce447fd15a3e1cc19f5c1325ff43b11e558f4b74e5'


def stage(source: Path, destination: Path, expected_sha256: str):
    actual = hashlib.sha256(source.read_bytes()).hexdigest()
    if actual != expected_sha256:
        raise ValueError('Historical CHIRILA payload changed')
    if destination.exists():
        raise ValueError('Use a new private staging path')
    connection = sqlite3.connect(destination)
    try:
        connection.execute('CREATE TABLE native (ordinal INTEGER PRIMARY KEY, member TEXT, '
                           'native_json TEXT NOT NULL, native_sha256 TEXT NOT NULL, malformed INTEGER)')
        malformed, count = [], 0
        with source.open(encoding='utf-8-sig', newline='') as handle:
            reader = csv.DictReader(handle)
            for count, row in enumerate(reader, 1):
                bad = None in row or any(v is None for v in row.values())
                if bad:
                    malformed.append(count)
                # JSON includes all original column names/values, including nulls.
                native = json.dumps(row, ensure_ascii=False, sort_keys=True)
                connection.execute('INSERT INTO native VALUES (?,?,?,?,?)',
                                   (count, row.get('StdLangID', ''), native,
                                    hashlib.sha256(native.encode()).hexdigest(), int(bad)))
        connection.commit()
        return dict(source_sha256=actual, rows=count, malformed_ordinals=malformed,
                    columns=reader.fieldnames, public_admission=False,
                    reading_basis='Upstream PhonemicisedIPA remains distinct from OriginalForm',
                    terms_status='Historical BY-NC-ND/custom conditions unresolved for adapted public export',
                    source_edition_status='No edition shortcode column; author alone is insufficient')
    finally:
        connection.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--expected-sha256', default=PINNED_SHA256)
    parser.add_argument('--summary', type=Path, required=True)
    args = parser.parse_args()
    report = stage(args.input, args.output, args.expected_sha256)
    args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
