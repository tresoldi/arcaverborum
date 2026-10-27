"""Build the complete research explorer: small catalog plus family-sized shards.

Reads accepted aggregate output only. Keeps raw source identifiers, uncertainty,
license metadata and multiple cognate assignments; never changes acceptance.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import sqlite3
import tempfile
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    with path.open(encoding='utf-8') as handle:
        return list(csv.DictReader(handle))


def write_json(path, value):
    raw = json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode()
    path.write_bytes(gzip.compress(raw, compresslevel=6, mtime=0))
    return dict(bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def assignments(row):
    """Preserve set membership and namespace; do not equate composite strings."""
    value = row.get('canonical_cognate_id') or row.get('Cognacy', '')
    return sorted(set(part.strip() for part in value.split(';') if part.strip()))


def build(root=ROOT, output=None):
    output = output or root / 'web/data'
    output.mkdir(parents=True, exist_ok=True)
    aggregate = root / 'output/aggregate'
    registry = {r['av_id']: r for r in read(root / 'src/arcaverborum/data/varieties.csv')}
    core = {r['concept_id'] for r in read(root / 'src/arcaverborum/data/concept_core.csv')}
    sources = {r['Dataset']: r for r in read(aggregate / 'metadata.csv')}
    if 'wiktionary' not in sources:
        fallback = dict.fromkeys(next(iter(sources.values()), {}).keys(), '')
        fallback.update(Dataset='wiktionary', Title='English Wiktionary via Kaikki extraction',
                        Citation='English Wiktionary contributors; local Kaikki extraction. '
                                 'Exact dump date and original citation metadata were not recorded.',
                        URL='https://kaikki.org/dictionary/rawdata.html', License='', Repository_Version='')
        sources['wiktionary'] = fallback
    core_sources = {r['NAME'] for r in read(root / 'datasets.csv') if r['CORE'].strip().upper() == 'TRUE'}
    concepts = read(aggregate / 'parameters.csv')
    for row in concepts:
        row['is_core'] = row['concept_id'] in core
    glottolog_path = root / 'raw/glottolog/languages.csv'
    glottolog = {r['ID']: r for r in read(glottolog_path)} if glottolog_path.exists() else {}
    language_labels = {}
    for path in (root / 'intake').glob('*/languages.csv'):
        for row in read(path):
            language_labels[row['ID']] = [row.get('Name', ''), row.get('Glottolog_Name', '')]
    aliases = defaultdict(set)
    parameters = {}
    for path in (root / 'intake').glob('*/parameters_raw.csv'):
        for row in read(path):
            parameters[row['ID']] = row.get('Name', '')
    reviews = {}
    for custom in (root / 'varieties').glob('*/custom'):
        av = custom.parent.name
        for filename in ['concept_map.csv', 'core_review.csv', 'form_review.csv']:
            path = custom / filename
            if not path.exists():
                continue
            for record in read(path):
                key = record.get('source_form_id') or record.get('Parameter_ID')
                if key:
                    reviews[av, key] = (record.get('decision') or record.get('action') or 'mapping override',
                                        record.get('rationale') or record.get('notes', ''),
                                        record.get('expected_form') or record.get('source_form', ''))
    shared_path = root / 'src/arcaverborum/data/wiktionary_sense_overrides.csv'
    shared_reviews = {r['Parameter_ID']: r for r in read(shared_path)} if shared_path.exists() else {}
    languages = read(aggregate / 'varieties.csv')
    by_id = {r['av_id']: r for r in languages}
    for row in languages:
        entry = registry.get(row['av_id'], {})
        row.update({k: entry.get(k, '') for k in ['parent_av_id', 'iso639p3', 'latitude', 'longitude', 'notes']})
        g = glottolog.get(entry.get('glottocode', ''), {})
        row.update(countries=g.get('Countries', ''), glottolog_family_id=g.get('Family_ID', ''),
                   identity_level=g.get('Level', 'not recorded'),
                   first_documented=g.get('First_Year_Of_Documentation', ''),
                   last_documented=g.get('Last_Year_Of_Documentation', ''))
        row.update(core_collection=row['transcription_source'] in core_sources,
                   mapped_concepts=0, core_concepts=0, supported_core=0, forms=0, statuses={})
    seen, counts, statuses = defaultdict(set), Counter(), defaultdict(Counter)
    core_seen, supported = defaultdict(set), defaultdict(set)
    fields = []
    families = sorted({r['Family'] or 'Unclassified' for r in languages})
    family_keys = {family: hashlib.sha256(family.encode()).hexdigest()[:16] for family in families}
    with tempfile.TemporaryDirectory() as temp:
        db = sqlite3.connect(Path(temp) / 'rows.sqlite')
        db.execute('CREATE TABLE rows(family TEXT, payload TEXT)')
        batch = []
        with (aggregate / 'forms.csv').open() as handle:
            for index, row in enumerate(csv.DictReader(handle)):
                if not fields:
                    fields = ['ID', *('cognate_evidence_source' if k == 'Cognate_Source' else k for k in row),
                              'is_core_concept', 'License', 'source_gloss', 'cognate_sets',
                              'mapping_review', 'mapping_note']
                row['cognate_evidence_source'] = row.pop('Cognate_Source', '')
                row['ID'] = f"{row['av_id']}:{row['source_form_id']}:{index}"
                row['is_core_concept'] = 'true' if row['concept_id'] in core else 'false'
                meta = sources.get(row['transcription_source'], {})
                row['License'] = meta.get('License', '') or 'Not recorded; consult upstream source terms'
                row['source_gloss'] = parameters.get(row['source_parameter_id'], '')
                row['cognate_sets'] = json.dumps(assignments(row), ensure_ascii=False)
                review = reviews.get((row['av_id'], row['source_form_id'])) or reviews.get(
                    (row['av_id'], row['source_parameter_id']))
                row['mapping_review'], row['mapping_note'] = 'source mapping; no local review recorded', ''
                shared = (shared_reviews.get(row['source_parameter_id'])
                          if row['transcription_source'] == 'wiktionary' else None)
                if shared:
                    row['mapping_review'] = 'shared ' + shared['action']
                    row['mapping_note'] = shared['notes'] + ' Reviewed in: ' + shared['reviewed_languages']
                if review:
                    decision, rationale, expected = review
                    row['mapping_review'] = decision if not expected or expected == row['Form'] else 'snapshot differs'
                    row['mapping_note'] = rationale
                av = row['av_id']
                aliases[av].update(label for label in language_labels.get(row.get('source_language_id', ''), [])
                                   if label)
                counts[av] += 1
                statuses[av][row['Segments_Source']] += 1
                if row['concept_id']:
                    seen[av].add(row['concept_id'])
                if row['concept_id'] in core:
                    core_seen[av].add(row['concept_id'])
                    if row['Segments_Source'] in {'source', 'profile'}:
                        supported[av].add(row['concept_id'])
                family = by_id[av]['Family'] or 'Unclassified'
                batch.append((family, json.dumps([row.get(k, '') for k in fields], ensure_ascii=False)))
                if len(batch) >= 5000:
                    db.executemany('INSERT INTO rows VALUES(?,?)', batch)
                    batch.clear()
        db.executemany('INSERT INTO rows VALUES(?,?)', batch)
        db.execute('CREATE INDEX family_rows ON rows(family)')
        db.commit()
        shards = {}
        for family in families:
            filename = family_keys[family] + '.json.gz'
            path = output / filename
            with path.open('wb') as raw, gzip.GzipFile(fileobj=raw, mode='wb', compresslevel=6, mtime=0) as handle:
                handle.write(b'[')
                first = True
                n = 0
                for (payload,) in db.execute('SELECT payload FROM rows WHERE family=? ORDER BY rowid', (family,)):
                    if not first:
                        handle.write(b',')
                    handle.write(payload.encode())
                    first = False
                    n += 1
                handle.write(b']')
            shards[family] = dict(url='data/' + filename, forms=n, bytes=path.stat().st_size,
                                  sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        db.close()
    for row in languages:
        av = row['av_id']
        row.update(forms=counts[av], mapped_concepts=len(seen[av]), core_concepts=len(core_seen[av]),
                   supported_core=len(supported[av]), statuses=dict(statuses[av]))
        row['aliases'] = sorted(aliases[av])
        row['concept_ids'] = sorted(seen[av])
        row['core_ids'] = sorted(core_seen[av])
        row['supported_ids'] = sorted(supported[av])
        row['packet_url'] = ('https://github.com/tresoldi/arcaverborum/blob/master/varieties/' + av + '/PACKET.md'
                             if (root / 'varieties' / av / 'PACKET.md').exists() else '')
    catalog = dict(languages=languages, concepts=concepts, sources=list(sources.values()), core=sorted(core))
    catalog_meta = write_json(output / 'catalog.json.gz', catalog)
    bib = aggregate / 'sources.bib'
    if bib.exists():
        (output / 'sources.bib').write_text('\n'.join(line.rstrip() for line in bib.read_text().splitlines()) + '\n')
    manifest = dict(schema=1, build_date=date.today().isoformat(), counts=dict(forms=sum(counts.values()),
                    varieties=len(languages), concepts=len(concepts)), fields=fields, shards=shards,
                    catalog=dict(url='data/catalog.json.gz', **catalog_meta),
                    core_count=len(core), source_files={name: hashlib.file_digest((aggregate / name).open('rb'),
                                                                               'sha256').hexdigest()
                                                      for name in ['forms.csv', 'varieties.csv', 'parameters.csv']})
    # Remove obsolete generated shards only; keep bibliography and manifest.
    active = {r['url'].split('/')[-1] for r in shards.values()} | {'catalog.json.gz'}
    for path in output.glob('*.json.gz'):
        if path.name not in active:
            path.unlink()
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(dict(counts=manifest['counts'], families=len(shards),
                         compressed_mb=round(sum(r['bytes'] for r in shards.values()) / 1e6, 1)), indent=2))
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    build(args.root, args.output)


if __name__ == '__main__':
    main()
