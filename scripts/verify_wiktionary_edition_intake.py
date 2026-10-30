"""Verify complete staged edition tables survive as unchanged contiguous append blocks."""
from __future__ import annotations

import argparse
import hashlib
import json
import mmap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def range_digest(handle, count):
    digest = hashlib.sha256()
    while count:
        block = handle.read(min(count, 2**20))
        if not block:
            raise ValueError('Truncated complete edition block')
        digest.update(block)
        count -= len(block)
    return digest.hexdigest()


def verify(edition):
    source = 'wiktionary' + edition + '202610'
    stage = ROOT / 'raw/curation' / ('stage-' + source) / 'lexibank'
    tables = {}
    for name in ['forms.csv', 'parameters_raw.csv', 'languages.csv', 'metadata.csv', 'sources.bib']:
        path = stage / name
        with path.open('rb') as expected:
            if name != 'sources.bib':
                expected.readline()
            start = expected.tell()
            length = path.stat().st_size - start
            prefix = expected.read(min(96, length))
            expected.seek(start)
            expected_hash = range_digest(expected, length)
        target = ROOT / 'intake/lexibank' / name
        with target.open('rb') as actual:
            with mmap.mmap(actual.fileno(), 0, access=mmap.ACCESS_READ) as view:
                offset = view.find(b'\n' + prefix)
                if offset < 0:
                    raise ValueError('Complete edition append not found: ' + name)
                offset += 1
            actual.seek(offset)
            actual_hash = range_digest(actual, length)
        assert expected_hash == actual_hash, (source, name)
        tables[name] = dict(complete_body_bytes=length, sha256=expected_hash, matches_intake=True)
    return dict(dataset=source, measured=json.loads((stage / 'stage-proof.json').read_text()), tables=tables,
                note='Exact full staged table bodies preserved in intake; native archive/version pins are separate. '
                     'Counts are native entry blocks and senses, not accepted lexemes or independent witnesses.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    proof = [verify(edition) for edition in ['pt', 'fr']]
    args.output.write_text(json.dumps(proof, indent=2) + '\n')
    print([(r['dataset'], r['measured']['lexical_entries']) for r in proof], flush=True)
