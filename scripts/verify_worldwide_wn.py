"""Verify WN finite reading derivations and original dictionary resource pins."""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sqlite3
from pathlib import Path

from iquito_profile import reading

from arcaverborum.ingest import ingest_lexibank
from arcaverborum.sources.ancient_lexica import materialize
from arcaverborum.sources.wiktionary.pronunciations import ipa_segments
from arcaverborum.supplements import evidence_hash

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    with (ROOT / path).open() as handle:
        return list(csv.DictReader(handle))


manifest = json.loads((ROOT / 'docs/worldwide_wn_sources_2026-10-29.json').read_text())
checks = 0
for dataset, spec in manifest.items():
    for name, digest in spec['resource_sha256'].items():
        assert hashlib.sha256((ROOT / 'raw/lexibank' / dataset / name).read_bytes()).hexdigest() == digest
        checks += 1
with sqlite3.connect((ROOT / 'intake/intake.sqlite').as_uri() + '?mode=ro', uri=True) as db:
    db.row_factory = sqlite3.Row
    for review in read('docs/worldwide_wn06_profiles_2026-10-29.csv'):
        raw = dict(db.execute('select * from forms where gc_lc=? and Dataset=? and ID=?',
                             (review['source_glottocode'], review['source'], review['source_form_id'])).fetchone())
        assert evidence_hash(raw) == review['evidence_sha256']
        assert review['raw_reading'] in raw['Comment']
        if review['source'] == 'dictteanu':
            segments = ' '.join(re.findall(r'ᵐb|ⁿd|ᶮɟ|ᵑg|mʷ|pʷ|[^ ]', review['raw_reading']))
        else:
            segments = ipa_segments(review['raw_reading'])
        assert segments == review['segments']
        checks += 1
    for review in read('docs/worldwide_wn02_review_2026-10-29.csv'):
        if review['source'] != 'dictiquito':
            continue
        raw = dict(db.execute("select * from forms where gc_lc='iqui1243' and Dataset=? and ID=?",
                              ('dictiquito', review['source_form_id'])).fetchone())
        assert evidence_hash(raw) == review['evidence_sha256']
        assert reading(raw['Form']) == review['segments']
        checks += 1
print(f'{checks} original-resource and finite-reading reproduction checks passed')

# Complete staged namespaces must reproduce active lexical/parameter/terms payloads.

stage = ROOT / 'raw/curation/wn-reproduction'
materialize(ROOT / 'raw', dataset='copticsahidic', download=False)
ingest_lexibank(ROOT / 'raw', stage, datasets=['dictwersing', 'copticsahidic'])
with (ROOT / 'intake/lexibank/forms.csv').open() as handle:
    staged_actual = {r['ID']: r for r in csv.DictReader(handle)
                     if r['Dataset'] in {'dictwersing', 'copticsahidic'}}
with sqlite3.connect((ROOT / 'intake/intake.sqlite').as_uri() + '?mode=ro', uri=True) as db:
    db.row_factory = sqlite3.Row
    counts = {}
    for dataset, gc in [('dictwersing', 'wers1238'), ('copticsahidic', 'copt1239')]:
        expected = [r for r in read(stage / 'lexibank/forms.csv') if r['Dataset'] == dataset]
        actual = {key: row for key, row in staged_actual.items() if row['Dataset'] == dataset}
        assert set(actual) == {r['ID'] for r in expected}
        assert all(all(actual[row['ID']][k] == v for k, v in row.items()) for row in expected)
        for name in ['parameters_raw.csv', 'languages.csv', 'metadata.csv']:
            want = [r for r in read(stage / 'lexibank' / name) if r['Dataset'] == dataset]
            current = [r for r in read(ROOT / 'intake/lexibank' / name) if r['Dataset'] == dataset]
            assert want == current, (dataset, name)
        counts[dataset] = len(expected)
    print('Complete staged namespace reproduction passed:', counts)
