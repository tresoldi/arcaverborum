"""Reproduce complete registered original-source namespaces without changing intake."""
import argparse
import csv
import hashlib
import json
import sqlite3
import sys

from arcaverborum.ingest import ingest_lexibank
from arcaverborum.sources.original_lexica import MANIFEST, ROOT, materialize
from arcaverborum.supplements import evidence_hash

csv.field_size_limit(sys.maxsize)


def table_hashes(path, datasets):
    """Compare ordered complete records without loading unrelated bulk editions."""
    states = {ds: [0, hashlib.sha256()] for ds in datasets}
    with path.open(newline='') as handle:
        for row in csv.DictReader(handle):
            if row['Dataset'] not in states:
                continue
            state = states[row['Dataset']]
            state[0] += 1
            state[1].update(json.dumps(row, sort_keys=True, ensure_ascii=False).encode() + b'\n')
    return {ds: (count, digest.hexdigest()) for ds, (count, digest) in states.items()}

def read(path):
    with path.open(newline='') as handle:
        return list(csv.DictReader(handle))


def verify():
    registered = {r['NAME'] for r in read(ROOT / 'datasets.csv')}
    specs = [s for s in json.loads(MANIFEST.read_text()) if s['dataset'] in registered]
    datasets = {s['dataset'] for s in specs}
    tables = ['parameters_raw.csv', 'languages.csv', 'metadata.csv']
    accepted_tables = {name: table_hashes(ROOT / 'intake/lexibank' / name, datasets) for name in tables}
    results = {}
    with sqlite3.connect((ROOT / 'intake/intake.sqlite').as_uri() + '?mode=ro', uri=True) as db:
        db.row_factory = sqlite3.Row
        for spec in specs:
            ds = spec['dataset']
            if ds not in registered:
                continue
            result = materialize(ROOT / 'raw', dataset=ds)
            stage = ROOT / 'raw/curation/s-reproduction' / ds
            ingest_lexibank(ROOT / 'raw', stage, datasets=[ds])
            with (stage / 'lexibank/forms.csv').open(newline='') as handle:
                expected = {r['ID']: evidence_hash(r) for r in csv.DictReader(handle)}
            assert len(expected) == result['forms']
            count = 0
            codes = sorted({m['Glottocode'].strip().lower() for m in spec['members']})
            placeholders = ','.join('?' for _ in codes)
            query = f'select * from forms where gc_lc in ({placeholders}) and Dataset=?'
            for row in db.execute(query, (*codes, ds)):
                assert evidence_hash(dict(row)) == expected.pop(row['ID']), (ds, row['ID'])
                count += 1
            assert not expected and count == result['forms']
            for name in tables:
                assert table_hashes(stage / 'lexibank' / name, {ds})[ds] == accepted_tables[name][ds], (ds, name)
            # Bibliographic keys are prefixed during ingestion; complete references must survive.
            bibliography = (stage / 'lexibank/sources.bib').read_text()
            assert bibliography in (ROOT / 'intake/lexibank/sources.bib').read_text()
            results[ds] = result | dict(resource_hashes=len(spec['resources']),
                                       bibliography_sha256=hashlib.sha256(bibliography.encode()).hexdigest())
            print(ds, count, flush=True)
    return dict(namespaces=results, complete_native_rows=sum(r['forms'] for r in results.values()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    proof = verify()
    (ROOT / args.output).write_text(json.dumps(proof, indent=2) + '\n')
    print(json.dumps(proof))
