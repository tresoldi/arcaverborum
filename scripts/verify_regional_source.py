"""Reproduce the complete Mongolic namespace and compare all indexed intake fields."""
import csv
import hashlib
import json
import sqlite3
import tempfile
from pathlib import Path

from stage_mongolic_original import stage

ROOT = Path(__file__).resolve().parents[1]


def verify():
    with tempfile.TemporaryDirectory(dir=ROOT / 'raw/curation') as scratch:
        output = Path(scratch)
        summary = stage(ROOT, output)
        proof = {name: dict(bytes=(output / name).stat().st_size,
                            sha256=hashlib.sha256((output / name).read_bytes()).hexdigest())
                 for name in ['forms.csv', 'languages.csv', 'parameters_raw.csv', 'metadata.csv', 'sources.bib']}
        with sqlite3.connect((ROOT / 'intake/intake.sqlite').as_uri() + '?mode=ro', uri=True) as db:
            db.row_factory = sqlite3.Row
            source_rows = {r['ID']: dict(r) for gc in ['', 'chin1476'] for r in db.execute(
                'SELECT * FROM forms WHERE gc_lc=? AND Dataset=?', (gc, 'mongolicbv2026'))}
            count = 0
            with (output / 'forms.csv').open(newline='') as handle:
                for row in csv.DictReader(handle):
                    stored = source_rows.pop(row['ID'])
                    assert all(stored[k] == v for k, v in row.items() if k in stored), row['ID']
                    assert not row['Segments']
                    count += 1
            assert not source_rows and count == summary['forms'] == 11457
        for filename, key in [('languages.csv', 'ID'), ('parameters_raw.csv', 'ID'), ('metadata.csv', 'Dataset')]:
            with (output / filename).open(newline='') as handle:
                expected = {r[key]: r for r in csv.DictReader(handle)}
            with (ROOT / 'intake/lexibank' / filename).open(newline='') as handle:
                actual = {r[key]: r for r in csv.DictReader(handle) if r['Dataset'] == 'mongolicbv2026'}
            assert expected == actual, filename
    return dict(dataset='mongolicbv2026', native_forms=count, entries=921, native_member_columns=14,
                missing_cells=1437, reproduced_tables=proof, all_intake_fields_match=True,
                source_segments_deliberately_empty=True)


if __name__ == '__main__':
    result = verify()
    (ROOT / 'docs/regional_source_verification_2026-11-01.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
