"""Reproduce Q finite readings and scoped IPA from the frozen source cache."""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sqlite3
from collections import defaultdict
from pathlib import Path

from iquito_profile import reading
from qualified_pronunciations import scoped_readings

from arcaverborum.sources.wiktionary.parameters import parse_parameter_name
from arcaverborum.sources.wiktionary.pronunciations import decide, ipa_segments, key
from arcaverborum.supplements import evidence_hash

ROOT = Path(__file__).resolve().parents[1]


def rows(path):
    with (ROOT / path).open() as handle:
        return list(csv.DictReader(handle))


checks = 0
with sqlite3.connect((ROOT / 'intake/intake.sqlite').as_uri() + '?mode=ro', uri=True) as db:
    db.row_factory = sqlite3.Row
    for name in ['worldwide_q03_profiles', 'worldwide_q04_profiles']:
        for review in rows('docs/' + name + '_2026-10-29.csv'):
            raw = dict(db.execute('select * from forms where gc_lc=? and Dataset=? and ID=?',
                                 (review['source_glottocode'], review['source'],
                                  review['source_form_id'])).fetchone())
            assert evidence_hash(raw) == review['evidence_sha256']
            if review['source'] == 'dictiquito':
                segments = reading(raw['Form'])
            else:
                assert review['raw_reading'] in raw['Comment']
                segments = (ipa_segments(review['raw_reading']) if review['source'] == 'dictwersing'
                            else ' '.join(re.findall(r'ᵐb|ⁿd|ᶮɟ|ᵑg|mʷ|pʷ|[^ ]', review['raw_reading'])))
            assert segments == review['segments']
            checks += 1
assert checks == 45
frozen = {}
by_key = defaultdict(list)
for line in (ROOT / 'raw/curation/q/frozen-entries.jsonl').open():
    payload = json.loads(line)
    entry = payload['entry']
    frozen[str(payload['line'])] = entry
    by_key[key(entry['lang_code'], entry['word'], entry['pos'])].append((payload['line'], entry))
strict = 0
for name in ['worldwide_q01_review', 'worldwide_q05_review']:
    for review in rows('docs/' + name + '_2026-10-29.csv'):
        if review['decision'] != 'admit':
            continue
        pos = parse_parameter_name(review['source_sense'])[1]
        entries = by_key[key(review['source_language_id'][5:], review['Form'], pos)]
        assert decide([entry for _, entry in entries]) == ('accept', review['raw_ipa'], review['segments'])
        assert review['reciprocal_glosses']
        strict += 1
assert strict == 185
qualified = rows('varieties/ine-northern-frisian/custom/primary.csv')
reviewed = {r['source_form_id']: r for r in rows('docs/worldwide_q05_mooring_review_2026-10-29.csv')}
for decision in qualified:
    review = reviewed[decision['source_form_id']]
    pos = parse_parameter_name(review['source_sense'])[1]
    status, variants = scoped_readings(by_key[key('frr', review['Form'], pos)], ['Mooring'])
    assert status == 'accept_alternatives'
    assert set(variants) == {r['raw_ipa'] for r in qualified
                             if r['source_form_id'] == decision['source_form_id']}
    for line in decision['pronunciation_lines'].split(';'):
        entry = frozen[line]
        assert entry['lang_code'] == 'frr'
        assert any(sound.get('ipa') == decision['raw_ipa'] and sound.get('tags') == ['Mooring']
                   for sound in entry['sounds'])
    assert decision['pronunciation_tags'] == '["Mooring"]'
assert len(qualified) == 33
pins = 0
specs = json.loads((ROOT / 'src/arcaverborum/data/ancient_lexical_sources.json').read_text())
spec = next(s for s in specs if s['dataset'] == 'copticsahidic')
for resource in spec['resources']:
    payload = (ROOT / 'raw/lexibank/copticsahidic' / resource['filename']).read_bytes()
    assert hashlib.sha256(payload).hexdigest() == resource['sha256']
    pins += 1
print(json.dumps(dict(finite_readings=checks, qualified_readings=len(qualified),
                      strict_pronunciations=strict, full_frozen_entries=len(frozen), coptic_resource_pins=pins)))

namespaces = {}
with sqlite3.connect((ROOT / 'intake/intake.sqlite').as_uri() + '?mode=ro', uri=True) as db:
    db.row_factory = sqlite3.Row
    for dataset, stage in [('reflexqdict', 'stage-reflexqdict'), ('ruruulioriginal', 'stage-ruruulioriginal'),
                           ('copticsahidic', 'q-stage-coptic')]:
        expected = rows('raw/curation/' + stage + '/lexibank/forms.csv')
        actual = {r['ID']: dict(r) for r in db.execute('select * from forms where Dataset=?', (dataset,))}
        assert set(actual) == {r['ID'] for r in expected}
        assert all(evidence_hash(actual[r['ID']]) == evidence_hash(r) for r in expected)
        for name in ['parameters_raw.csv', 'languages.csv', 'metadata.csv']:
            want = [r for r in rows('raw/curation/' + stage + '/lexibank/' + name) if r['Dataset'] == dataset]
            current = [r for r in rows('intake/lexibank/' + name) if r['Dataset'] == dataset]
            assert want == current, (dataset, name)
        namespaces[dataset] = len(expected)
assert namespaces == dict(reflexqdict=48, ruruulioriginal=116, copticsahidic=74)
print('Complete namespace reproduction:', namespaces)
