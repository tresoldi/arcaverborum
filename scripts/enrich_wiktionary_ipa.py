"""Recover exact-lemma/POS IPA from the cached multilingual Wiktextract dump.

Index once (--index), inspect decisions/report, then --apply. No spelling is
interpreted as IPA. Ambiguous, qualified, unsupported and incomplete homograph
matches are deferred. Raw IPA and headword provenance remain in a sidecar.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import os
import sqlite3
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import quote

from arcaverborum.sources.wiktionary.extract import stream_entries
from arcaverborum.sources.wiktionary.parameters import parse_parameter_name
from arcaverborum.sources.wiktionary.pronunciations import POLICY, decide, key

ROOT = Path(__file__).resolve().parents[1]


def load_parameters(root):
    with (root / 'intake/wiktionary/parameters_raw.csv').open() as f:
        return {r['ID']: parse_parameter_name(r['Name'])[1] for r in csv.DictReader(f)}


def index(root, cache):
    dump = root / 'raw/wiktionary/raw.jsonl.gz'
    parameters = load_parameters(root)
    targets = set()
    with (root / 'intake/wiktionary/forms.csv').open() as f:
        for row in csv.DictReader(f):
            targets.add(key(row['Language_ID'].removeprefix('wikt_'), row['Form'], parameters[row['Parameter_ID']]))
    langs = {k[0] for k in targets}
    cache.parent.mkdir(parents=True, exist_ok=True)
    work = cache.with_suffix('.building.sqlite')
    if work.exists():
        work.unlink()
    db = sqlite3.connect(work)
    db.execute('CREATE TABLE entries(lang,word,pos,line,payload)')
    batch = []
    n = 0
    for n, entry in enumerate(stream_entries(dump), 1):
        lang = entry.get('lang_code', '')
        if lang in langs:
            k = key(lang, entry.get('word', ''), entry.get('pos', ''))
            if k in targets:
                data = dict(sounds=entry.get('sounds', []), etymology_number=entry.get('etymology_number'))
                batch.append((*k, n, json.dumps(data, ensure_ascii=False)))
        if len(batch) >= 5000:
            db.executemany('INSERT INTO entries VALUES(?,?,?,?,?)', batch)
            batch.clear()
        if n % 1000000 == 0:
            print(f'{n:,} source entries scanned', flush=True)
    db.executemany('INSERT INTO entries VALUES(?,?,?,?,?)', batch)
    db.execute('CREATE INDEX entry_key ON entries(lang,word,pos)')
    db.execute('CREATE TABLE decisions(lang,word,pos,decision,ipa,segments,source_lines)')
    groups = itertools.groupby(db.execute('SELECT * FROM entries ORDER BY lang,word,pos,line'), lambda r: r[:3])
    records = []
    for k, group in groups:
        rows = list(group)
        decision, ipa, segments = decide([json.loads(r[4]) for r in rows])
        records.append((*k, decision, ipa, segments, ';'.join(str(r[3]) for r in rows)))
    db.executemany('INSERT INTO decisions VALUES(?,?,?,?,?,?,?)', records)
    db.execute('CREATE UNIQUE INDEX decision_key ON decisions(lang,word,pos)')
    db.execute('CREATE TABLE metadata(payload)')
    with dump.open('rb') as f:
        digest = hashlib.file_digest(f, 'sha256').hexdigest()
    metadata = dict(dump_sha256=digest, dump_bytes=dump.stat().st_size, dump_mtime_ns=dump.stat().st_mtime_ns,
                    scanned_entries=n, target_lexemes=len(targets), matching_lexemes=len(records),
                    decisions=dict(Counter(r[3] for r in records)))
    db.execute('INSERT INTO metadata VALUES(?)', (json.dumps(metadata),))
    db.commit()
    db.close()
    os.replace(work, cache)
    print(json.dumps(metadata, indent=2), flush=True)


def refresh_decisions(cache):
    db = sqlite3.connect(cache)
    records = []
    groups = itertools.groupby(db.execute('SELECT * FROM entries ORDER BY lang,word,pos,line'), lambda r: r[:3])
    for k, group in groups:
        rows = list(group)
        decision, ipa, segments = decide([json.loads(r[4]) for r in rows])
        records.append((*k, decision, ipa, segments, ';'.join(str(r[3]) for r in rows)))
    db.execute('DELETE FROM decisions')
    db.executemany('INSERT INTO decisions VALUES(?,?,?,?,?,?,?)', records)
    meta = json.loads(db.execute('SELECT payload FROM metadata').fetchone()[0])
    meta['decisions'] = dict(Counter(r[3] for r in records))
    meta['policy'] = POLICY
    db.execute('UPDATE metadata SET payload=?', (json.dumps(meta),))
    db.commit()
    db.close()


def apply(root, cache, write=False):
    db = sqlite3.connect(cache.as_uri() + '?mode=ro', uri=True)
    meta = json.loads(db.execute('SELECT payload FROM metadata').fetchone()[0])
    dump = root / 'raw/wiktionary/raw.jsonl.gz'
    if (dump.stat().st_size, dump.stat().st_mtime_ns) != (meta['dump_bytes'], meta['dump_mtime_ns']):
        raise ValueError('Dump snapshot changed; rebuild the pronunciation index')
    decisions = {r[:3]: r[3:] for r in db.execute('SELECT * FROM decisions')}
    parameters = load_parameters(root)
    path = root / 'intake/wiktionary/forms.csv'
    work = path.with_suffix('.ipa-staged.csv')
    provenance = root / 'intake/wiktionary/pronunciations.csv'
    review = provenance.with_suffix('.staged.csv')
    counts = defaultdict(Counter)
    with path.open() as f, work.open('w', newline='') as out, review.open('w', newline='') as evidence:
        reader = csv.DictReader(f)
        writer = csv.DictWriter(out, fieldnames=reader.fieldnames, lineterminator='\n')
        writer.writeheader()
        ledger = csv.DictWriter(evidence, fieldnames=['source_form_id', 'language', 'Form', 'pos', 'raw_ipa',
                               'segments', 'entry_url', 'source_lines', 'dump_sha256'], lineterminator='\n')
        ledger.writeheader()
        for row in reader:
            lang = row['Language_ID'].removeprefix('wikt_')
            pos = parameters[row['Parameter_ID']]
            decision, ipa, segments, lines = decisions.get(key(lang, row['Form'], pos), ('no_entry', '', '', ''))
            if decision == 'accept':
                if row['Segments'] and row['Segments'] != segments:
                    decision = 'existing_segments_preserved'
                else:
                    url = 'https://en.wiktionary.org/wiki/' + quote(row['Form'], safe='')
                    annotation = (f'Pronunciation IPA {ipa}; {url}; exact language/POS match; '
                                  f'dump {meta["dump_sha256"][:16]}')
                    row['Segments'] = segments
                    if annotation not in row['Comment']:
                        row['Comment'] = '; '.join(filter(None, [row['Comment'], annotation]))
                    ledger.writerow(dict(source_form_id=row['ID'], language=lang, Form=row['Form'], pos=pos,
                                         raw_ipa=ipa, segments=segments, entry_url=url, source_lines=lines,
                                         dump_sha256=meta['dump_sha256']))
            counts[lang][decision] += 1
            writer.writerow(row)
    report = root / 'docs/wiktionary_ipa_2026-10-27.csv'
    with report.open('w', newline='') as f:
        statuses = sorted({status for c in counts.values() for status in c})
        writer = csv.DictWriter(f, fieldnames=['language', *statuses], lineterminator='\n')
        writer.writeheader()
        for lang, count in sorted(counts.items()):
            writer.writerow(dict(language=lang, **count))
    (root / 'docs/wiktionary_ipa_snapshot_2026-10-27.json').write_text(json.dumps(meta, indent=2) + '\n')
    if write:
        original = path.with_suffix('.before-ipa.csv')
        if not original.exists():
            os.link(path, original)
        with tempfile.TemporaryDirectory(prefix='.ipa-rollback-', dir=path.parent) as temp:
            backup = Path(temp)
            os.link(path, backup / 'forms.csv')
            if provenance.exists():
                os.link(provenance, backup / 'pronunciations.csv')
            try:
                os.replace(work, path)
                os.replace(review, provenance)
            except BaseException:
                os.replace(backup / 'forms.csv', path)
                if (backup / 'pronunciations.csv').exists():
                    os.replace(backup / 'pronunciations.csv', provenance)
                raise
        from arcaverborum.sources.wiktionary.provenance import write_provenance
        with (path.parent / 'languages.csv').open() as handle:
            n_languages = sum(1 for _ in csv.DictReader(handle))
        write_provenance(path.parent, dump,
                         dict(forms=sum(sum(c.values()) for c in counts.values()),
                              languages=n_languages, parameters=len(parameters)), meta)
    else:
        work.unlink()
        review.unlink()
    print(json.dumps(dict(applied=write, forms=dict(sum(counts.values(), Counter()))), indent=2), flush=True)
    db.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--index', action='store_true')
    parser.add_argument('--refresh-decisions', action='store_true')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    root = args.root.resolve()
    cache = root / 'raw/curation/wiktionary-pronunciations.sqlite'
    if args.index:
        index(root, cache)
    if args.refresh_decisions:
        refresh_decisions(cache)
    apply(root, cache, args.apply)


if __name__ == '__main__':
    main()
