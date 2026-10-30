"""Disk-backed, provenance-scoped whole-form colexification.

No dataframe, all-pairs language matrix or complete in-memory graph is built.
Derived concept splits and reduced/written representations remain separate.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import io
import itertools
import json
import os
import shutil
import sqlite3
import sys
import time
import unicodedata
from collections import Counter, defaultdict
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path

DATA = Path(__file__).parent / 'data'
LAYERS = ('segmented', 'written', 'reduced')
KINDS = ('observed', 'inferred')
SCHEMA = '''
CREATE TABLE varieties(av TEXT PRIMARY KEY, name TEXT, language TEXT, family TEXT, area TEXT);
CREATE TABLE scopes(id INTEGER PRIMARY KEY,av TEXT,source TEXT,member TEXT,tags TEXT,basis TEXT,
 UNIQUE(av,source,member,tags,basis));
CREATE TABLE readings(id INTEGER PRIMARY KEY,sid INTEGER,layer TEXT,key TEXT,cid TEXT,
 fid TEXT,param TEXT,word TEXT,status TEXT,loan TEXT,bib TEXT,web_id TEXT,
 UNIQUE(sid,layer,key,cid,fid,param));
CREATE TABLE witnesses(id INTEGER PRIMARY KEY,sid INTEGER,layer TEXT,kind TEXT,
 a TEXT,b TEXT,key TEXT,ra INTEGER,rb INTEGER,original_concept TEXT,
 UNIQUE(sid,layer,kind,a,b,key));
CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT);
'''


@dataclass(frozen=True)
class Limits:
    cache_mb: int = 24
    batch_rows: int = 1000
    identity_concepts: int = 64
    text_bytes: int = 4096
    key_bytes: int = 1024
    max_witnesses: int = 5_000_000
    database_mb: int = 3072
    page_edges: int = 40
    payload_bytes: int = 1_048_576
    min_free_mb: int = 256
    csv_shard_rows: int = 50000
    public_file_bytes: int = 90 * 1024 * 1024

    def validate(self):
        if any(value <= 0 for value in asdict(self).values()):
            raise ValueError('Colexification limits must be positive')
        if self.identity_concepts > 256 or self.page_edges > 100:
            raise ValueError('Identity/page limits exceed supported bounded working sets')


def read_csv(path):
    with Path(path).open(encoding='utf-8', newline='') as handle:
        yield from csv.DictReader(handle)


def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def identity(value):
    return ' '.join(unicodedata.normalize('NFC', value).split())


def usable(value, limit):
    return bool(value and len(value.encode()) <= limit and any(unicodedata.category(c).startswith('L') for c in value))


def input_files(root):
    files = ['output/aggregate/forms.csv', 'output/aggregate/varieties.csv',
             'output/aggregate/metadata.csv', 'output/aggregate/parameters.csv',
             'src/arcaverborum/data/concepts.csv',
             'src/arcaverborum/data/colexification/policy.json',
             'src/arcaverborum/data/colexification/expansions.csv']
    for optional in ['raw/glottolog/languages.csv', 'src/arcaverborum/data/construction_kinds.csv']:
        if (root / optional).exists():
            files.append(optional)
    return {name: sha(root / name) for name in files}


def connect(path, limits=Limits()):
    db = sqlite3.connect(path)
    db.execute('PRAGMA temp_store=FILE')
    db.execute(f'PRAGMA cache_size=-{limits.cache_mb * 1024}')
    db.execute('PRAGMA mmap_size=0')
    db.execute('PRAGMA threads=1')
    db.execute('PRAGMA synchronous=NORMAL')
    db.execute('PRAGMA busy_timeout=60000')
    page = db.execute('PRAGMA page_size').fetchone()[0]
    db.execute(f'PRAGMA max_page_count={limits.database_mb * 1024 * 1024 // page}')
    return db


def expansions(root, concepts):
    result = defaultdict(list)
    for row in read_csv(root / 'src/arcaverborum/data/colexification/expansions.csv'):
        ids = [row['source_concept_id'], row['target_a'], row['target_b']]
        for cid, guard in zip(ids, ['source_sha256', 'target_a_sha256', 'target_b_sha256']):
            if cid not in concepts or concepts[cid]['status'] != 'active' or digest(concepts[cid]) != row[guard]:
                raise ValueError(f'Stale colexification concept expansion: {cid}')
        if len(set(ids)) != 3 or not row['rationale'].strip():
            raise ValueError('Invalid concept-scope expansion')
        result[ids[0]].append(tuple(sorted(ids[1:])))
    return result


def load_varieties(db, root):
    # Retain only needed classification fields, never a full Glottolog dataframe.
    varieties = list(read_csv(root / 'output/aggregate/varieties.csv'))
    needed = {r['Glottocode'] for r in varieties if r.get('Glottocode')}
    classification = {}
    path = root / 'raw/glottolog/languages.csv'
    if path.exists():
        for row in read_csv(path):
            if row['ID'] not in needed:
                continue
            language = row.get('Language_ID') or (row['ID'] if row.get('Level') == 'language' else '')
            family = row.get('Family_ID', '')
            if not family and row.get('Is_Isolate', '').lower() in {'true', '1'}:
                family = 'isolate:' + row['ID']
            classification[row['ID']] = (language, family)
    for row in varieties:
        language, family = classification.get(row.get('Glottocode'), ('', ''))
        db.execute('INSERT INTO varieties VALUES(?,?,?,?,?)',
                   (row['av_id'], row.get('Name', ''), language, family, row.get('Macroarea', '')))
    db.commit()


def ingest(db, root, concepts, policy, limits, work):
    splits = expansions(root, concepts)
    reconstructed = {r['av_id'] for r in read_csv(root / 'src/arcaverborum/data/construction_kinds.csv')
                     if r['construction_kind'] == 'reconstruction'} if (
                         root / 'src/arcaverborum/data/construction_kinds.csv').exists() else set()
    known = {r[0] for r in db.execute('SELECT av FROM varieties')}
    counters = Counter()

    @lru_cache(maxsize=4096)
    def scope(av, source, member, tags, basis):
        values = (av, source, member, tags, basis)
        db.execute('INSERT OR IGNORE INTO scopes(av,source,member,tags,basis) VALUES(?,?,?,?,?)', values)
        return db.execute('SELECT id FROM scopes WHERE av=? AND source=? AND member=? AND tags=? AND basis=?',
                          values).fetchone()[0]

    # The CSV parser itself is bounded, including unused Comment fields.
    previous_limit = csv.field_size_limit(8 * 1024 * 1024)
    try:
        for ordinal, row in enumerate(read_csv(root / 'output/aggregate/forms.csv')):
            counters['input_records'] += 1
            if ordinal % limits.batch_rows == 0:
                db.commit()
                if shutil.disk_usage(work).free < limits.min_free_mb * 1024 * 1024:
                    raise RuntimeError('Insufficient scratch space; existing publication was not replaced')
            av, cid = row['av_id'], row['concept_id']
            if av not in known:
                raise ValueError(f'Unknown accepted variety: {av}')
            if not cid:
                counters['excluded_unmapped'] += 1
                continue
            if cid not in concepts:
                raise ValueError(f'Unknown frozen concept: {cid}')
            if concepts[cid]['status'] != 'active':
                counters['excluded_merged'] += 1
                continue
            if av in reconstructed or row.get('Value', '').lstrip().startswith('*'):
                counters['excluded_reconstruction'] += 1
                continue
            if row.get('Doubt', '').strip().lower() not in {'', '0', 'false', 'no'}:
                counters['excluded_doubtful'] += 1
                continue
            source, member = row['transcription_source'], row['source_language_id']
            fid, param = row['source_form_id'], row['source_parameter_id']
            if not all([source, member, fid, param]):
                counters['excluded_missing_provenance'] += 1
                continue
            tags = identity(row.get('pronunciation_tags', ''))
            if any(len(v.encode()) > limits.text_bytes for v in (av, source, member, fid, param, tags)):
                counters['excluded_oversize_provenance'] += 1
                continue
            word = identity(row['Form'])
            choices = []
            if (source not in policy['reduced_sources'] and usable(word, limits.key_bytes)
                    and not any(c in word for c in ',;/|{}[]?~')):
                choices.append(('written', word, 'citation_form'))
            else:
                counters['excluded_written_identity'] += 1
            segments = identity(row['Segments'])
            if row['Segments_Source'] in {'source', 'profile'} and usable(segments, limits.key_bytes):
                if source in policy['reduced_sources']:
                    choices.append(('reduced', segments, 'reduced_asjp'))
                else:
                    raw = identity(row.get('raw_ipa', '')) if row['Segments_Source'] == 'source' else ''
                    stressed = next((identity(value) for value in (row.get('Value', ''), row['Form'])
                                     if any(mark in value for mark in 'ˈˌ')), '')
                    key, basis = ((raw, 'supplied_ipa') if raw else (stressed, 'explicit_stress_citation')
                                  if stressed else (segments, 'normalized_segments'))
                    if basis != 'normalized_segments':
                        # Original notation guards lost prosody, but must never
                        # override a correction in the accepted construction.
                        key = json.dumps([key, segments], ensure_ascii=False, separators=(',', ':'))
                    if usable(key, limits.key_bytes):
                        choices.append(('segmented', key, basis))
                    else:
                        counters['excluded_original_reading_identity'] += 1
            else:
                counters['excluded_segment_identity'] += 1
            for layer, key, basis in choices:
                sid = scope(av, source, member, tags, basis)
                web_id = f"{av}:{fid}:{row.get('source_pronunciation_id') or ordinal}"
                values = (sid, layer, key, cid, fid, param, word, row['Segments_Source'],
                          row.get('Loan', ''), row.get('bibtex_key', ''), web_id)
                if any(len(str(v).encode()) > limits.text_bytes for v in values):
                    counters['excluded_oversize_record'] += 1
                    continue
                cursor = db.execute('INSERT OR IGNORE INTO readings'
                                    '(sid,layer,key,cid,fid,param,word,status,loan,bib,web_id) '
                                    'VALUES(?,?,?,?,?,?,?,?,?,?,?)', values)
                if cursor.rowcount:
                    counters['readings_' + layer] += 1
                    rid = cursor.lastrowid
                    for a, b in splits.get(cid, []):
                        added = db.execute(
                            'INSERT OR IGNORE INTO witnesses(sid,layer,kind,a,b,key,ra,rb,original_concept) '
                            'VALUES(?,?,?,?,?,?,?,?,?)', (sid, layer, 'inferred', a, b, key, rid, rid, cid))
                        counters['inferred_witnesses'] += added.rowcount
                        if counters['inferred_witnesses'] > limits.max_witnesses:
                            raise RuntimeError('Colexification witness budget exceeded during concept expansion')
                else:
                    counters['duplicate_readings'] += 1
            if (ordinal + 1) % 250000 == 0:
                print(f'Colexification: streamed {ordinal + 1:,} accepted records', flush=True)
        db.commit()
    finally:
        csv.field_size_limit(previous_limit)
    return counters


def representatives(db, sid, layer, key, cid):
    """At most five (form ID, parameter ID) points preserve pair existence.

    Every test point compatible with any native reading is compatible with one
    of these representatives. This prevents quadratic joins in duplicated senses.
    """
    if key is None:
        base = 'SELECT id,fid,param FROM valid WHERE sid=? AND layer=? AND cid=?'
        args = (sid, layer, cid)
    else:
        base = 'SELECT id,fid,param FROM readings WHERE sid=? AND layer=? AND key=? AND cid=?'
        args = (sid, layer, key, cid)

    def first(condition='', values=()):
        return db.execute(base + condition + ' ORDER BY fid,param LIMIT 1', args + values).fetchone()

    initial = first()
    result = {initial}
    different_parameter = first(' AND param<>?', (initial[2],))
    if different_parameter:
        result.add(different_parameter)
        result.add(first(' AND param<>? AND fid<>?', (initial[2], different_parameter[1])))
    different_form = first(' AND fid<>?', (initial[1],))
    if different_form:
        result.add(different_form)
        result.add(first(' AND fid<>? AND param<>?', (initial[1], different_form[2])))
    return sorted((r for r in result if r is not None), key=lambda r: (r[1], r[2], r[0]))


def infer(db, limits):
    db.executescript('''
      CREATE INDEX reading_concept ON readings(cid,sid,layer);
      CREATE TABLE cells AS SELECT DISTINCT sid,layer,key,cid FROM readings;
      CREATE UNIQUE INDEX cells_identity ON cells(sid,layer,key,cid);
      CREATE TABLE groups AS SELECT sid,layer,key,COUNT(*) AS concepts FROM cells GROUP BY sid,layer,key;
      CREATE UNIQUE INDEX group_identity ON groups(sid,layer,key);
    ''')
    db.execute('CREATE TABLE quarantine AS SELECT * FROM groups WHERE concepts>?', (limits.identity_concepts,))
    db.execute('CREATE UNIQUE INDEX quarantine_identity ON quarantine(sid,layer,key)')
    db.executescript('''
      CREATE VIEW valid AS SELECT r.* FROM readings r WHERE NOT EXISTS
       (SELECT 1 FROM quarantine q WHERE q.sid=r.sid AND q.layer=r.layer AND q.key=r.key);
      CREATE TABLE coverage AS SELECT sid,layer,cid,MIN(param) AS pmin,MAX(param) AS pmax,
       MIN(fid) AS fmin,MAX(fid) AS fmax FROM valid GROUP BY sid,layer,cid;
      CREATE UNIQUE INDEX coverage_concept ON coverage(cid,layer,sid);
    ''')
    # A quarantined pathological identity cannot leak into the derived layer either.
    db.execute('DELETE FROM witnesses WHERE EXISTS (SELECT 1 FROM quarantine q '
               'WHERE q.sid=witnesses.sid AND q.layer=witnesses.layer AND q.key=witnesses.key)')
    count = db.execute('SELECT COUNT(*) FROM witnesses').fetchone()[0]
    groups = db.execute('SELECT sid,layer,key FROM groups WHERE concepts BETWEEN 2 AND ? '
                        'ORDER BY sid,layer,key', (limits.identity_concepts,))
    for sid, layer, key in groups:
        cids = [r[0] for r in db.execute('SELECT cid FROM cells WHERE sid=? AND layer=? AND key=? ORDER BY cid',
                                      (sid, layer, key))]
        candidates = {cid: representatives(db, sid, layer, key, cid) for cid in cids}
        for a, b in itertools.combinations(cids, 2):
            pair = next(((ra[0], rb[0]) for ra in candidates[a] for rb in candidates[b]
                         if ra[1] != rb[1] and ra[2] != rb[2]), None)
            if pair is None:
                continue  # one native questionnaire item mapped twice is not independent attestation
            count += 1
            if count > limits.max_witnesses:
                raise RuntimeError('Colexification witness budget exceeded; publication was not replaced')
            db.execute('INSERT OR IGNORE INTO witnesses(sid,layer,kind,a,b,key,ra,rb,original_concept) '
                       'VALUES(?,?,?,?,?,?,?,?,?)', (sid, layer, 'observed', a, b, key, *pair, ''))
        if count % limits.batch_rows == 0:
            db.commit()
    db.executescript('''
      CREATE INDEX witness_edge ON witnesses(layer,kind,a,b,sid);
      CREATE INDEX witness_scope ON witnesses(sid,layer,kind,a,b);
      CREATE TABLE edges AS
       SELECT w.layer,w.kind,w.a,w.b,COUNT(*) AS witnesses,
        COUNT(DISTINCT s.av) AS varieties,
        COUNT(DISTINCT NULLIF(v.language,'')) AS languages,
        COUNT(DISTINCT NULLIF(v.family,'')) AS families
       FROM witnesses w JOIN scopes s ON s.id=w.sid JOIN varieties v ON v.av=s.av
       GROUP BY w.layer,w.kind,w.a,w.b;
      CREATE UNIQUE INDEX edge_pair ON edges(layer,kind,a,b);
      CREATE INDEX edge_neighbor ON edges(layer,kind,b,a);
    ''')
    db.commit()


def pair_status(db, a, b, layer='segmented'):
    """Three-way status for a requested pair; never materialize a dense matrix."""
    a, b = sorted((a, b))
    sql = '''SELECT ca.sid,s.av,v.language,v.family,
      EXISTS(SELECT 1 FROM witnesses w WHERE w.sid=ca.sid AND w.layer=ca.layer
       AND w.kind='observed' AND w.a=? AND w.b=?) AS colexified,
      ca.pmin,ca.pmax,ca.fmin,ca.fmax,cb.pmin,cb.pmax,cb.fmin,cb.fmax
      FROM coverage ca JOIN coverage cb ON cb.sid=ca.sid AND cb.layer=ca.layer
      JOIN scopes s ON s.id=ca.sid JOIN varieties v ON v.av=s.av
      WHERE ca.cid=? AND cb.cid=? AND ca.layer=? ORDER BY ca.sid'''
    for row in db.execute(sql, (a, b, a, b, layer)):
        ap, aq, af, ag, bp, bq, bf, bg = row[5:]
        if ap == aq == bp == bq or af == ag == bf == bg:
            continue
        if aq < bp or bq < ap or ag < bf or bg < af:
            yield row[:5]
            continue
        left = representatives(db, row[0], layer, None, a)
        right = representatives(db, row[0], layer, None, b)
        if any(x[1] != y[1] and x[2] != y[2] for x in left for y in right):
            yield row[:5]


def opportunities(db, a, b, layer):
    # Sets contain at most the accepted variety/language catalog, not lexical rows.
    comparable, languages, families = set(), set(), set()
    observed = set()
    for _, av, language, family, positive in pair_status(db, a, b, layer):
        comparable.add(av)
        if language:
            languages.add(language)
        if family:
            families.add(family)
        if positive:
            observed.add(av)
    return dict(comparable_varieties=len(comparable), comparable_languages=len(languages),
                comparable_families=len(families),
                no_shared_form_observed=len(comparable - observed),
                observed_fraction=round(len(observed) / len(comparable), 6) if comparable else None)


def write_json(path, value, limits):
    raw = (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n').encode()
    if len(raw) > limits.payload_bytes:
        raise RuntimeError(f'Bounded JSON payload exceeded: {path.name}')
    path.write_bytes(raw)
    return dict(url=path.name, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


@contextmanager
def gzip_text(path):
    with path.open('wb') as raw:
        with gzip.GzipFile(filename='', fileobj=raw, mode='wb', mtime=0, compresslevel=6) as compressed:
            with io.TextIOWrapper(compressed, encoding='utf-8', newline='') as text:
                yield text


def csv_shards(public, prefix, fields, rows, limits):
    """Deterministic gzip shards, bounded by rows and checked after compression."""
    iterator, number, finished = iter(rows), 0, False
    while not finished:
        first = next(iterator, None)
        if first is None:
            break
        path = public / f'{prefix}.{number:04d}.csv.gz'
        with gzip_text(path) as handle:
            writer = csv.writer(handle, lineterminator='\n')
            writer.writerow(fields)
            writer.writerow(first)
            for _ in range(limits.csv_shard_rows - 1):
                row = next(iterator, None)
                if row is None:
                    finished = True
                    break
                writer.writerow(row)
        if path.stat().st_size > limits.public_file_bytes:
            raise RuntimeError('Compressed evidence shard exceeded the public file limit')
        number += 1


def sample(db, layer, kind, a, b):
    row = db.execute('''SELECT s.av,s.source,s.member,s.tags,s.basis,w.key,ra.word,rb.word,
     ra.fid,rb.fid,ra.param,rb.param,ra.web_id,rb.web_id,ra.status,rb.status,ra.loan,rb.loan,
     ra.bib,rb.bib,w.original_concept
     FROM witnesses w JOIN scopes s ON s.id=w.sid JOIN readings ra ON ra.id=w.ra
     JOIN readings rb ON rb.id=w.rb WHERE w.layer=? AND w.kind=? AND w.a=? AND w.b=?
     ORDER BY s.av,s.source,s.member,s.tags,w.key LIMIT 1''', (layer, kind, a, b)).fetchone()
    keys = ['av_id', 'source', 'source_language_id', 'pronunciation_tags', 'comparison_basis',
            'identity', 'form_a', 'form_b',
            'source_form_a', 'source_form_b', 'parameter_a', 'parameter_b', 'record_a', 'record_b',
            'segments_source_a', 'segments_source_b', 'loan_a', 'loan_b', 'bibtex_a', 'bibtex_b', 'original_concept']
    result = dict(zip(keys, row))
    if result['comparison_basis'] in {'supplied_ipa', 'explicit_stress_citation'}:
        original, accepted = json.loads(result['identity'])
        result.update(identity_display=original, accepted_segments=accepted)
    return result


def export(db, public, root, concepts, policy, inputs, fingerprint, counters, limits):
    public.mkdir()
    metadata = {r['Dataset']: r for r in read_csv(root / 'output/aggregate/metadata.csv')}
    db.execute('ALTER TABLE edges ADD COLUMN opportunities TEXT')
    for number, (layer, a, b) in enumerate(db.execute("SELECT layer,a,b FROM edges WHERE kind='observed'"), 1):
        value = json.dumps(opportunities(db, a, b, layer), sort_keys=True)
        db.execute('UPDATE edges SET opportunities=? WHERE layer=? AND kind=? AND a=? AND b=?',
                   (value, layer, 'observed', a, b))
        if number % 5000 == 0:
            db.commit()
            print(f'Colexification: comparison coverage for {number:,} edges', flush=True)
    db.commit()
    edge_fields = ['layer', 'kind', 'concept_a', 'concept_b', 'witnesses', 'varieties', 'languages', 'families',
                   'comparable_varieties', 'comparable_languages', 'comparable_families',
                   'no_shared_form_observed', 'observed_fraction']
    with (public / 'edges.csv').open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=edge_fields, lineterminator='\n')
        writer.writeheader()
        for layer, kind, a, b, n, av, lang, fam, opp in db.execute('SELECT * FROM edges ORDER BY layer,kind,a,b'):
            writer.writerow(dict(layer=layer, kind=kind, concept_a=a, concept_b=b, witnesses=n,
                                 varieties=av, languages=lang, families=fam, **(json.loads(opp) if opp else {})))
    # Complete witnesses stream independently of the bounded examples in node pages.
    witness_fields = ['layer', 'kind', 'concept_a', 'concept_b', 'av_id', 'source', 'source_language_id',
                         'pronunciation_tags', 'comparison_basis', 'identity', 'source_form_a', 'source_form_b',
                         'parameter_a', 'parameter_b',
                         'form_a', 'form_b', 'segments_source_a', 'segments_source_b', 'loan_a', 'loan_b',
                         'bibtex_a', 'bibtex_b', 'record_a', 'record_b', 'original_concept',
                         'license', 'source_version']
    rows = db.execute('''SELECT w.layer,w.kind,w.a,w.b,s.av,s.source,s.member,s.tags,s.basis,w.key,
         a.fid,b.fid,a.param,b.param,a.word,b.word,a.status,b.status,a.loan,b.loan,a.bib,b.bib,
         a.web_id,b.web_id,w.original_concept FROM witnesses w JOIN scopes s ON s.id=w.sid
         JOIN readings a ON a.id=w.ra JOIN readings b ON b.id=w.rb
         ORDER BY w.layer,w.kind,w.a,w.b,s.av,s.source,w.key''')
    def witness_rows():
        for row in rows:
            source = metadata.get(row[5], {})
            yield [*row, source.get('License', ''), source.get('Repository_Version', '')]
    csv_shards(public, 'witnesses', witness_fields, witness_rows(), limits)
    for layer in LAYERS:
        rows = db.execute('''SELECT DISTINCT s.av,s.source,s.member,s.tags,s.basis,r.layer,r.cid,r.fid,r.param,
          v.language,v.family FROM valid r JOIN scopes s ON s.id=r.sid JOIN varieties v ON v.av=s.av
          WHERE r.layer=? ORDER BY s.av,s.source,s.member,s.tags,r.cid,r.fid,r.param''', (layer,))
        fields = ['av_id', 'source', 'source_language_id', 'pronunciation_tags',
                  'comparison_basis', 'layer', 'concept_id',
                  'source_form_id', 'source_parameter_id', 'glottolog_language', 'family_lineage']
        csv_shards(public, 'coverage.' + layer, fields, rows, limits)
    shutil.copyfile(root / 'output/aggregate/metadata.csv', public / 'sources.csv')
    with (public / 'quarantines.csv').open('w', newline='') as handle:
        writer = csv.writer(handle, lineterminator='\n')
        writer.writerow(['av_id', 'source', 'source_language_id', 'pronunciation_tags',
                         'layer', 'identity', 'concepts'])
        writer.writerows(db.execute('SELECT s.av,s.source,s.member,s.tags,q.layer,q.key,q.concepts '
                                    'FROM quarantine q JOIN scopes s ON s.id=q.sid ORDER BY q.sid,q.layer,q.key'))
    nodes = {}
    for cid, concept in sorted(concepts.items()):
        node = dict(concept_id=cid, catalog_status=concept['status'], layers={})
        for layer in LAYERS:
            represented = db.execute('SELECT COUNT(DISTINCT s.av) FROM coverage c JOIN scopes s ON s.id=c.sid '
                                     'WHERE c.cid=? AND c.layer=?', (cid, layer)).fetchone()[0]
            kinds = {}
            for kind in KINDS:
                pages, batch, degree, recurrent = [], [], 0, 0
                query = '''SELECT a,b,witnesses,varieties,languages,families,opportunities FROM edges
                  WHERE layer=? AND kind=? AND a=? UNION ALL
                  SELECT a,b,witnesses,varieties,languages,families,opportunities FROM edges
                  WHERE layer=? AND kind=? AND b=? ORDER BY families DESC,languages DESC,varieties DESC,a,b'''
                for a, b, n, av, lang, fam, opp in db.execute(query, (layer, kind, cid, layer, kind, cid)):
                    degree += 1
                    recurrent += fam >= policy['recurrence_families']
                    batch.append(dict(concept_id=b if cid == a else a, witnesses=n, varieties=av, languages=lang,
                                      families=fam, **(json.loads(opp) if opp else {}),
                                      example=sample(db, layer, kind, a, b)))
                    if len(batch) == limits.page_edges:
                        name = f'{cid}.{layer}.{kind}.{len(pages)}.json'
                        pages.append(write_json(public / name, dict(edges=batch), limits))
                        batch = []
                if batch:
                    name = f'{cid}.{layer}.{kind}.{len(pages)}.json'
                    pages.append(write_json(public / name, dict(edges=batch), limits))
                kinds[kind] = dict(neighbors=degree, recurrent_neighbors=recurrent, pages=pages)
            node['layers'][layer] = dict(usable_varieties=represented, **kinds)
        primary = node['layers']['segmented']
        node['status'] = ('merged' if concept['status'] != 'active' else 'observed' if
                          primary['observed']['neighbors'] else 'no_shared_form_observed' if
                          primary['usable_varieties'] else 'no_comparable_segmented_data')
        nodes[cid] = write_json(public / (cid + '.json'), node, limits)
    filenames = ['edges.csv', 'quarantines.csv', 'sources.csv'] + sorted(p.name for p in public.glob('*.csv.gz'))
    files = {name: dict(url=name, bytes=(public / name).stat().st_size, sha256=sha(public / name))
             for name in filenames}
    if any(spec['bytes'] > limits.public_file_bytes for spec in files.values()):
        raise RuntimeError('Public colexification file exceeded its size budget')
    stats = dict(counters, witnesses=db.execute('SELECT COUNT(*) FROM witnesses').fetchone()[0],
                 edges=db.execute('SELECT COUNT(*) FROM edges').fetchone()[0],
                 quarantined_identities=db.execute('SELECT COUNT(*) FROM quarantine').fetchone()[0],
                 concepts=len(concepts), active_concepts=sum(c['status'] == 'active' for c in concepts.values()))
    stats['networks'] = [dict(layer=layer, kind=kind, edges=n) for layer, kind, n in db.execute(
        'SELECT layer,kind,COUNT(*) FROM edges GROUP BY layer,kind ORDER BY layer,kind')]
    split_map = expansions(root, concepts)
    manifest = dict(schema=1, build_id=fingerprint, inputs=inputs, policy=policy, limits=asdict(limits),
                    nodes=nodes, files=files, stats=stats, runtime=runtime(),
                    concept_expansions={cid: [dict(a=a, b=b) for a, b in pairs] for cid, pairs in split_map.items()})
    # The catalog index is bounded separately from small per-concept payloads.
    write_json(public / 'manifest.json', manifest, Limits(payload_bytes=4 * 1024 * 1024))
    return manifest


def verify_public(public, manifest=None):
    """Check every bounded node/page and complete CSV before publishing a build."""
    public = Path(public)
    manifest = manifest or json.loads((public / 'manifest.json').read_text())

    def check(spec):
        if Path(spec['url']).name != spec['url']:
            raise ValueError('Invalid colexification asset path')
        path = public / spec['url']
        if path.stat().st_size != spec['bytes'] or sha(path) != spec['sha256']:
            raise ValueError(f'Corrupt colexification asset: {spec["url"]}')
        return path

    for spec in manifest['files'].values():
        check(spec)
    for spec in manifest['nodes'].values():
        node = json.loads(check(spec).read_text())
        for layer in node['layers'].values():
            for kind in KINDS:
                for page in layer[kind]['pages']:
                    check(page)
    return manifest


def runtime():
    return dict(python=sys.version, sqlite=sqlite3.sqlite_version, unicode=unicodedata.unidata_version)


def build(root, output=None, limits=Limits()):
    root = Path(root)
    limits.validate()
    inputs = input_files(root)
    inputs['pipeline'] = sha(Path(__file__))
    inputs['runtime'] = digest(runtime())
    fingerprint = digest(dict(inputs=inputs, limits=asdict(limits)))[:24]
    output = Path(output or root / 'output/colexification')
    output.mkdir(parents=True, exist_ok=True)
    destination = output / fingerprint
    if (destination / 'complete.json').exists():
        verify_public(destination / 'public')
        return destination
    stage = output / ('.' + fingerprint + '.building')
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir()
    os.environ['SQLITE_TMPDIR'] = str(stage.resolve())
    started = time.monotonic()
    try:
        concepts = {r['concept_id']: r for r in read_csv(root / 'src/arcaverborum/data/concepts.csv')}
        policy = json.loads((root / 'src/arcaverborum/data/colexification/policy.json').read_text())
        db = connect(stage / 'index.sqlite', limits)
        try:
            db.executescript(SCHEMA)
            load_varieties(db, root)
            counters = ingest(db, root, concepts, policy, limits, stage)
            print('Colexification: inferring source-scoped whole-form matches', flush=True)
            infer(db, limits)
            print('Colexification: computing comparison opportunities and bounded node pages', flush=True)
            manifest = export(db, stage / 'public', root, concepts, policy, inputs, fingerprint, counters, limits)
            current = input_files(root)
            if any(current[name] != value for name, value in inputs.items() if name not in {'pipeline', 'runtime'}):
                raise ValueError('Colexification inputs changed during build')
            db.execute('INSERT INTO meta VALUES(?,?)', ('manifest', json.dumps(manifest)))
            db.commit()
            if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise ValueError('Colexification database integrity failed')
        finally:
            db.close()
        (stage / 'complete.json').write_text(
            json.dumps(dict(build_id=fingerprint, stats=manifest['stats']), indent=2)+'\n')
        (stage / 'run.json').write_text(json.dumps(dict(seconds=round(time.monotonic()-started, 2)), indent=2)+'\n')
        if destination.exists():
            raise ValueError('Refusing to replace an incomplete existing build')
        stage.rename(destination)
        return destination
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise


def publish(root, built):
    """Publish immutable assets, then switch the tiny web manifest last."""
    root, built = Path(root), Path(built)
    public = built / 'public'
    colex = json.loads((public / 'manifest.json').read_text())
    verify_public(public, colex)
    if colex['inputs']['pipeline'] != sha(Path(__file__)) or colex['inputs']['runtime'] != digest(runtime()):
        raise ValueError('Stale colexification pipeline; rebuild before publication')
    current = input_files(root)
    if any(current[name] != value for name, value in colex['inputs'].items() if name not in {'pipeline', 'runtime'}):
        raise ValueError('Stale colexification build cannot be published')
    manifest_path = root / 'web/data/manifest.json'
    web = json.loads(manifest_path.read_text())
    for name in ('forms.csv', 'varieties.csv', 'parameters.csv'):
        expected = colex['inputs'].get('output/aggregate/' + name)
        if expected and web['source_files'][name] != expected:
            raise ValueError('Web/aggregate snapshot mismatch; rebuild research web first')
    destination = root / 'web/data/colexification' / colex['build_id']
    destination.parent.mkdir(exist_ok=True)
    if not destination.exists():
        staging = destination.with_name('.' + destination.name + '.publishing')
        if staging.exists():
            shutil.rmtree(staging)
        shutil.copytree(public, staging)
        staging.rename(destination)
    else:
        verify_public(destination)
        if sha(destination / 'manifest.json') != sha(public / 'manifest.json'):
            raise ValueError('Conflicting immutable colexification build')
    spec = dict(url=f'data/colexification/{colex["build_id"]}/manifest.json',
                sha256=sha(public / 'manifest.json'), bytes=(public / 'manifest.json').stat().st_size,
                schema=1, build_id=colex['build_id'])
    web['colexification'] = spec
    temporary = manifest_path.with_suffix('.pending')
    temporary.write_text(json.dumps(web, ensure_ascii=False, indent=2)+'\n')
    temporary.replace(manifest_path)
    return spec
