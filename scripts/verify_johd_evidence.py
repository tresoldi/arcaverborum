"""Reproduce guarded JOHD/HGN stages and compare every native intake row."""
import csv
import hashlib
import json
import sqlite3

from arcaverborum.ingest import ingest_lexibank
from arcaverborum.sources.american_evidence import ROOT, materialize
from arcaverborum.supplements import evidence_hash


def read(path):
    with path.open() as handle:
        return list(csv.DictReader(handle))


specs = json.loads((ROOT / 'src/arcaverborum/data/american_evidence_sources.json').read_text())
checks, counts = 0, {}
with sqlite3.connect((ROOT / 'intake/intake.sqlite').as_uri() + '?mode=ro', uri=True) as db:
    db.row_factory = sqlite3.Row
    for spec in specs:
        ds = spec['dataset']
        for resource in spec['resources']:
            p = ROOT / 'raw/lexibank' / ds / resource['filename']
            assert hashlib.sha256(p.read_bytes()).hexdigest() == resource['sha256']
            checks += 1
        result = materialize(ROOT / 'raw', dataset=ds)
        stage = ROOT / 'raw/curation/j-reproduction' / ds
        ingest_lexibank(ROOT / 'raw', stage, datasets=[ds])
        forms = read(stage / 'lexibank/forms.csv')
        actual = {r['ID']: dict(r) for r in db.execute('select * from forms where Dataset=?', (ds,))}
        assert set(actual) == {r['ID'] for r in forms}
        assert all(evidence_hash(actual[r['ID']]) == evidence_hash(r) for r in forms)
        for filename in ['parameters_raw.csv', 'languages.csv', 'metadata.csv']:
            want = [r for r in read(stage / 'lexibank' / filename) if r['Dataset'] == ds]
            current = [r for r in read(ROOT / 'intake/lexibank' / filename) if r['Dataset'] == ds]
            # Additive intake migration preserves earlier row order; a complete
            # native re-extraction can interleave the newly reviewed citations.
            key = 'Dataset' if filename == 'metadata.csv' else 'ID'
            assert len({r[key] for r in want}) == len(want)
            assert len({r[key] for r in current}) == len(current)
            assert sorted(want, key=lambda r: r[key]) == sorted(current, key=lambda r: r[key]), (ds, filename)
        counts[ds] = result['forms']
assert counts == dict(hgnphonemic=109, hgnphonemicdepth=20, johdproto=60)
print(json.dumps(dict(resource_hashes=checks, complete_namespaces=counts, native_rows=sum(counts.values()))))
