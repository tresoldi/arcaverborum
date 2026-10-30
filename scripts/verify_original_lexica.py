"""Reproduce complete registered original-source namespaces without changing intake."""
import argparse
import csv
import hashlib
import json
import sqlite3

from arcaverborum.ingest import ingest_lexibank
from arcaverborum.sources.original_lexica import MANIFEST, ROOT, materialize
from arcaverborum.supplements import evidence_hash


def read(path):
    with path.open() as handle:
        return list(csv.DictReader(handle))


def verify():
    registered = {r['NAME'] for r in read(ROOT / 'datasets.csv')}
    results = {}
    with sqlite3.connect((ROOT / 'intake/intake.sqlite').as_uri() + '?mode=ro', uri=True) as db:
        db.row_factory = sqlite3.Row
        for spec in json.loads(MANIFEST.read_text()):
            ds = spec['dataset']
            if ds not in registered:
                continue
            result = materialize(ROOT / 'raw', dataset=ds)
            stage = ROOT / 'raw/curation/s-reproduction' / ds
            ingest_lexibank(ROOT / 'raw', stage, datasets=[ds])
            with (stage / 'lexibank/forms.csv').open() as handle:
                expected = {r['ID']: evidence_hash(r) for r in csv.DictReader(handle)}
            assert len(expected) == result['forms']
            count = 0
            for row in db.execute('select * from forms where Dataset=?', (ds,)):
                assert evidence_hash(dict(row)) == expected.pop(row['ID']), (ds, row['ID'])
                count += 1
            assert not expected and count == result['forms']
            for name in ['parameters_raw.csv', 'languages.csv', 'metadata.csv']:
                assert read(stage / 'lexibank' / name) == [
                    r for r in read(ROOT / 'intake/lexibank' / name) if r['Dataset'] == ds
                ], (ds, name)
            # Bibliographic keys are prefixed during ingestion; complete references must survive.
            bibliography = (stage / 'lexibank/sources.bib').read_text()
            assert bibliography in (ROOT / 'intake/lexibank/sources.bib').read_text()
            results[ds] = result | dict(resource_hashes=len(spec['resources']),
                                       bibliography_sha256=hashlib.sha256(bibliography.encode()).hexdigest())
            print(ds, count, flush=True)
    return dict(namespaces=results, complete_native_rows=sum(r['forms'] for r in results.values()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='docs/worldwide_s_source_verification_2026-10-30.json')
    args = parser.parse_args()
    proof = verify()
    (ROOT / args.output).write_text(json.dumps(proof, indent=2) + '\n')
    print(json.dumps(proof))
