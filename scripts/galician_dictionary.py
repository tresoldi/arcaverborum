"""Fetch and reconcile ILG pronunciations for Galician Wiktionary core forms.

Caches individual lookups under raw/curation/galician-ilg. Only exact headwords
are considered. A pronunciation is accepted automatically only when it is
shared by every returned homograph. No vowel quality is inferred from spelling.
Run with --fetch to populate missing cache entries; otherwise network-free.
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import re
import sqlite3
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path
from urllib.parse import urlencode

import pandas as pd
import requests

from arcaverborum.concepts import load_concept_maps
from arcaverborum.forms_schema import load_parameter_index
from arcaverborum.phonology import resegment
from arcaverborum.variety import VarietyDir, apply_overlays

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = 'https://ilg.usc.gal/pronuncia/'


def parse_results(document: str, form: str) -> list[dict]:
    """Extract exact-headword result facts, excluding superscript sense numbers."""
    entries = []
    pattern = r'<td class="palabra">(.*?)<td class="audio">'
    for block in re.findall(pattern, document, re.S):
        anchor = re.search(r'href="\?l=2&amp;ficha=(\d+)"[^>]*>(.*?)</a>', block, re.S)
        if anchor is None:
            anchor = re.search(r'href="\?l=2&ficha=(\d+)"[^>]*>(.*?)</a>', block, re.S)
        pronunciation = re.search(r'<div class="ipa">(.*?)</div>', block, re.S)
        if anchor is None or pronunciation is None:
            continue
        headword = re.sub(r'<sup>.*?</sup>', '', anchor[2], flags=re.S)
        headword = html.unescape(re.sub('<[^>]*>', '', headword)).strip()
        if headword != form:
            continue
        ipa = html.unescape(re.sub('<[^>]*>', '', pronunciation[1])).strip()
        entries.append({'entry_id': anchor[1], 'headword': headword, 'ipa': ipa})
    return entries


def resolve(entries: list[dict]) -> tuple[str, str]:
    """Require a validated pronunciation common to all homographs."""
    by_entry = defaultdict(list)
    for entry in entries:
        ipa = entry['ipa'].strip('() ')
        # Arca's segment tier omits stress. Remove it before tokenization:
        # an internal stress mark can otherwise bind to the preceding vowel.
        segments, valid = resegment(ipa.replace('ˈ', '').replace('ˌ', ''))
        # Parentheses around an entire alternative mark a secondary reading;
        # internal annotations or unparsed separators remain unsupported.
        if valid and segments:
            by_entry[entry['entry_id']].append(segments)
        else:
            by_entry[entry['entry_id']]  # retain an unresolved homograph
    if not by_entry:
        return '', 'not_found'
    common = set.intersection(*(set(values) for values in by_entry.values()))
    if not common:
        return '', 'ambiguous_or_invalid'
    for values in by_entry.values():
        for segments in values:
            if segments in common:
                return segments, 'dictionary'
    raise AssertionError('nonempty pronunciation intersection')


def core_forms(root: Path) -> list[dict]:
    parameters = {}
    for path in sorted((root / 'intake').glob('*/parameters_raw.csv')):
        parameters.update(load_parameter_index(path))
    concepts, _ = load_concept_maps(root / 'src/arcaverborum/data/concepts.csv')
    with (root / 'src/arcaverborum/data/concept_core.csv').open() as f:
        core = {row['concept_id'] for row in csv.DictReader(f)}
    with sqlite3.connect((root / 'intake/intake.sqlite').as_uri() + '?mode=ro', uri=True) as db:
        db.row_factory = sqlite3.Row
        rows = db.execute('SELECT * FROM forms WHERE gc_lc=? AND Dataset=? ORDER BY seq',
                          ('gali1258', 'wiktionary')).fetchall()
    variety = root / 'varieties/ine-galician'
    frame, _ = apply_overlays(pd.DataFrame([dict(row) for row in rows]),
                              VarietyDir('ine-galician', variety))
    selected = []
    for row in frame.to_dict('records'):
        if row.get('_concept_mapping_blocked', False):
            continue
        external = row.get('Concepticon_ID', '') or parameters.get(row['Parameter_ID'], ('', ''))[0]
        concept = row.get('_concept_id_override', '') or concepts.get(external, ('', ''))[0]
        if concept in core:
            selected.append(row)
    return selected


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--fetch', action='store_true')
    args = parser.parse_args()
    root = args.root.resolve()
    rows = core_forms(root)
    cache = root / 'raw/curation/galician-ilg'
    cache.mkdir(parents=True, exist_ok=True)
    custom = root / 'varieties/ine-galician/custom'
    evidence_path = custom / 'pronunciation_evidence.csv'
    tracked = {}
    if evidence_path.exists():
        with evidence_path.open() as f:
            tracked = {row['Form']: row for row in csv.DictReader(f)}
    # Keep attested pronunciations when a sense is corrected out of the core;
    # lookup facts remain useful for non-core senses with the same spelling.
    forms = sorted({row['Form'] for row in rows} | tracked.keys())

    def lookup(form: str) -> dict:
        import hashlib
        path = cache / (hashlib.sha256(form.encode()).hexdigest() + '.json')
        if path.exists():
            return json.loads(path.read_text())
        if form in tracked:
            row = tracked[form]
            return {'form': form, 'query_url': row['query_url'], 'checked_at': row['checked_at'],
                    'entries': json.loads(row['dictionary_entries'])}
        query_url = BASE_URL + '?' + urlencode({'l': 1, 'q': form})
        if not args.fetch:
            raise FileNotFoundError(f'Missing cached lookup: {form}; rerun with --fetch')
        response = requests.get(query_url, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        if 'Resultados atopados' not in response.text and 'Non se atoparon' not in response.text:
            # No-result wording can vary; require the actual dictionary shell.
            if 'Dicionario de pronuncia' not in response.text:
                raise ValueError(f'Unexpected response for {form}')
        result = {'form': form, 'query_url': query_url, 'checked_at': str(date.today()),
                  'entries': parse_results(response.text, form)}
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
        time.sleep(0.25)  # two bounded workers; at most eight requests/second
        return result

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = []
        for i, result in enumerate(pool.map(lookup, forms), 1):
            results.append(result)
            if i % 50 == 0:
                print(f'{i}/{len(forms)} dictionary lookups', flush=True)
    custom.mkdir(parents=True, exist_ok=True)
    evidence = []
    resolved = {}
    for result in results:
        segments, status = resolve(result['entries'])
        resolved[result['form']] = (segments, result['query_url'])
        evidence.append(dict(Form=result['form'], query_url=result['query_url'],
                             checked_at=result['checked_at'], status=status,
                             dictionary_entries=json.dumps(result['entries'], ensure_ascii=False),
                             Segments=segments))
    with (custom / 'pronunciation_evidence.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(evidence[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(evidence)
    supported = {form: value for form, value in resolved.items() if value[0]}
    with (custom / 'profile.tsv').open('w') as f:
        f.write('Grapheme\tIPA\tnotes\n')
        for form, (segments, url) in sorted(supported.items()):
            f.write(f'^{form}$\t{segments}\tILG dictionary; {url}; see pronunciation_evidence.csv\n')
    print(f'{len(supported)} exact-form mappings from {len(evidence)} headword lookups')


if __name__ == '__main__':
    main()
