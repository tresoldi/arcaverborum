"""Reproduce registered pinned CLDF conversions and compare complete intake evidence."""
import csv
import json
import sqlite3

from arcaverborum.ingest import ingest_lexibank
from arcaverborum.sources.reviewed_cldf import MANIFEST, ROOT, materialize
from arcaverborum.supplements import evidence_hash


def read(path):
    with path.open() as handle:
        return list(csv.DictReader(handle))


registered = {r['NAME'] for r in read(ROOT / 'datasets.csv')}
results = {}
with sqlite3.connect((ROOT / 'intake/intake.sqlite').as_uri() + '?mode=ro', uri=True) as db:
    db.row_factory = sqlite3.Row
    for spec in json.loads(MANIFEST.read_text()):
        ds = spec['dataset']
        if ds not in registered:
            continue
        result = materialize(ROOT / 'raw', dataset=ds)
        stage = ROOT / 'raw/curation/r-reproduction' / ds
        ingest_lexibank(ROOT / 'raw', stage, datasets=[ds])
        expected = read(stage / 'lexibank/forms.csv')
        actual = {r['ID']: dict(r) for r in db.execute('select * from forms where Dataset=?', (ds,))}
        assert len(actual) == result['forms']
        assert set(actual) == {r['ID'] for r in expected}
        assert all(evidence_hash(actual[r['ID']]) == evidence_hash(r) for r in expected)
        for name in ['parameters_raw.csv', 'languages.csv', 'metadata.csv']:
            assert read(stage / 'lexibank' / name) == [
                r for r in read(ROOT / 'intake/lexibank' / name) if r['Dataset'] == ds
            ], (ds, name)
        results[ds] = len(expected)
print(json.dumps(dict(complete_namespaces=results, native_rows=sum(results.values()))))
