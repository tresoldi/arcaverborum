"""Build an advisory, core-only Chickasaw profile and dictionary comparison.

No accepted source choice is changed. Only spellings with positive modern
orthography diagnostics are proposed; native dictionary spelling equality is
recorded as lexical evidence, not treated as observed IPA. --fetch populates
bounded public dictionary queries; default operation uses local caches.
"""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

import requests

from arcaverborum.concepts import load_concept_maps
from arcaverborum.phonology import segments_are_valid
from arcaverborum.sources.wiktionary.parameters import parse_parameter_name

ROOT = Path(__file__).resolve().parents[1]
API = 'https://es.achickasawdictionary.com/humes2_english/_search'
SINGLE = dict(zip('abfhiklmnpstwy', ['a', 'b', 'f', 'h', 'i', 'k', 'l', 'm', 'n', 'p', 's', 't', 'w', 'j']))
SINGLE['o'] = 'o'
DIGRAPHS = {'chch': 'tʃː', 'lhlh': 'ɬː', 'shsh': 'ʃː', 'ch': 'tʃ', 'lh': 'ɬ', 'sh': 'ʃ'}
APOSTROPHES = "'ʼꞌ’"


def modern_reading(form: str) -> str:
    """Broad Munro–Willmond reading; reject unsupported/legacy spellings."""
    text = unicodedata.normalize('NFD', form.lower())
    output = []
    i = 0
    while i < len(text):
        char = text[i]
        if char.isspace():
            output.append('_')
            i += 1
            continue
        if char in APOSTROPHES:
            output.append('ʔ')
            i += 1
            continue
        digraph = next((key for key in DIGRAPHS if text.startswith(key, i)), None)
        if digraph:
            output.append(DIGRAPHS[digraph])
            i += len(digraph)
            continue
        if char in 'aio':
            marks = ''
            i += 1
            while i < len(text) and unicodedata.combining(text[i]):
                marks += text[i]
                i += 1
            long = i < len(text) and text[i] == char
            if long:
                i += 1
                while i < len(text) and unicodedata.combining(text[i]):
                    marks += text[i]
                    i += 1
            if any(mark not in '\u0301\u0331\u0320' for mark in marks):
                return ''
            vowel = char + ('̃' if any(mark in marks for mark in '\u0331\u0320') else '')
            output.append(unicodedata.normalize('NFC', vowel) + ('ː' if long else ''))
            if '\u0301' in marks:
                output.append('⁵')
            continue
        if char not in SINGLE:
            return ''
        long = i + 1 < len(text) and text[i+1] == char
        output.append(SINGLE[char] + ('ː' if long else ''))
        i += 2 if long else 1
    result = ' '.join(output)
    return result if result and segments_are_valid(result) else ''


def diagnostic(form: str) -> bool:
    text = unicodedata.normalize('NFD', form.lower())
    return any(marker in text for marker in [*APOSTROPHES, '\u0301', '\u0331', '\u0320',
                                            'aa', 'ii', 'oo', 'chch', 'lhlh', 'shsh', 'ff', 'tt', 'kk', 'mm', 'nn'])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--fetch', action='store_true')
    args = parser.parse_args()
    root = args.root.resolve()
    proposal = root / 'varieties/mus-chickasaw/proposals'
    proposal.mkdir(exist_ok=True)
    cache = root / 'raw/curation/chickasaw/queries'
    cache.mkdir(parents=True, exist_ok=True)
    parameters = {r['ID']: r for r in csv.DictReader((root / 'intake/wiktionary/parameters_raw.csv').open())}
    index, _ = load_concept_maps(root / 'src/arcaverborum/data/concepts.csv')
    core = {r['concept_id'] for r in csv.DictReader((root / 'src/arcaverborum/data/concept_core.csv').open())}
    with sqlite3.connect((root / 'intake/intake.sqlite').as_uri() + '?mode=ro', uri=True) as db:
        db.row_factory = sqlite3.Row
        forms = db.execute('SELECT * FROM forms WHERE gc_lc=? AND Dataset=? ORDER BY seq',
                           ('chic1270', 'wiktionary')).fetchall()
    selected = [r for r in forms if index.get(parameters[r['Parameter_ID']]['Concepticon_ID'], ('', ''))[0] in core]
    words = sorted({parse_parameter_name(parameters[r['Parameter_ID']]['Name'])[0].lower() for r in selected})
    dictionary = {}
    for word in words:
        path = cache / (word.replace(' ', '_') + '.json')
        params = {'size': '100', 'q': 'raw_word:"' + word + '"'}
        url = API + '?' + urlencode(params)
        if path.exists():
            cached = json.loads(path.read_text())
            if 'result' not in cached:
                cached = dict(query_url=url, checked_at=datetime.fromtimestamp(
                    path.stat().st_mtime, timezone.utc).date().isoformat(), result=cached)
                path.write_text(json.dumps(cached, ensure_ascii=False) + '\n')
            result = cached['result']
        elif args.fetch:
            response = requests.get(API, params=params, timeout=30)
            response.raise_for_status()
            result = response.json()
            cached = dict(query_url=url, checked_at=datetime.now(timezone.utc).date().isoformat(), result=result)
            path.write_text(json.dumps(cached, ensure_ascii=False) + '\n')
            time.sleep(0.2)
        else:
            raise FileNotFoundError('Missing query cache for ' + word + '; run --fetch')
        hits = result.get('hits', {})
        total = hits.get('total', 0)
        if isinstance(total, dict):
            total = total['value']
        if total > 100:
            raise ValueError('Query truncated for ' + word)
        dictionary[word] = (cached['query_url'], cached['checked_at'], [hit['_source'] for hit in hits.get('hits', [])
                                if hit['_source'].get('raw_word', '').lower() == word])
    records = []
    profile = {}
    for row in selected:
        parameter = parameters[row['Parameter_ID']]
        word = parse_parameter_name(parameter['Name'])[0].lower()
        url, checked_at, hits = dictionary[word]
        native = [hit for hit in hits if unicodedata.normalize('NFC', hit.get('chickasaw_word', '')).lower()
                  == unicodedata.normalize('NFC', row['Form']).lower()]
        segments = modern_reading(row['Form'])
        eligible = bool(segments and diagnostic(row['Form']))
        if eligible:
            profile[row['Form']] = segments
        records.append(dict(source_form_id=row['ID'], Form=row['Form'], Parameter_ID=row['Parameter_ID'],
                            source_name=parameter['Name'], concept_id=index[parameter['Concepticon_ID']][0],
                            proposed_segments=segments if eligible else '',
                            decision='advisory_modern_diagnostic' if eligible else 'orthography_unresolved',
                            dictionary_query=url, checked_at=checked_at,
                            exact_dictionary_entry_ids=';'.join(str(h['id']) for h in native),
                            notes='Dictionary lexical match is not an orthography or IPA certification. '
                                  'Proposed readings require native/specialist review; source senses also need audit.'))
    with (proposal / 'core_evidence.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(records)
    with (proposal / 'profile.tsv').open('w') as f:
        f.write('Grapheme\tIPA\tnotes\n')
        for form, segments in sorted(profile.items()):
            f.write(f'^{form}$\t{segments}\tAdvisory only; mixed source orthographies require review\n')
    covered = {r['concept_id'] for r in records if r['proposed_segments']}
    (proposal / 'summary.json').write_text(json.dumps(dict(
        source_rows=len(selected), core_concepts=len({r['concept_id'] for r in records}),
        proposed_spellings=len(profile), proposed_core_concepts=len(covered),
        exact_dictionary_matches=sum(bool(r['exact_dictionary_entry_ids']) for r in records),
        accepted=False, reason='Mixed spelling systems; dictionary respelling is not IPA. No source switch.'),
        indent=2) + '\n')
    print(f'{len(profile)} advisory spellings; {len(covered)} core concepts; accepted source unchanged')


if __name__ == '__main__':
    main()
