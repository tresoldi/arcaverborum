"""Conservative pronunciation matches from a reviewed Wiktextract index."""
from __future__ import annotations

import csv
import json
import sqlite3
import unicodedata
from urllib.parse import quote

from arcaverborum.phonology import resegment

POLICY = "exact language/NFC spelling/POS; all matching entries unqualified and identical raw IPA"


def key(lang, word, pos):
    return lang, unicodedata.normalize('NFC', word), pos


def ipa_segments(ipa):
    text = unicodedata.normalize('NFC', ipa.strip())
    if len(text) > 2 and (text[0], text[-1]) in {('/', '/'), ('[', ']')}:
        text = text[1:-1]
    # Alternatives/optional segments and unreviewed multiword transcriptions
    # cannot be collapsed into one reading. Stress/syllable marks are retained
    # in raw IPA; canonical segment output follows the normal Arca policy.
    if not text or any(c in text for c in '(){}[]/,;') or any(c.isspace() for c in text):
        return ''
    segments, valid = resegment(text.replace('.', '').replace('ˈ', '').replace('ˌ', ''))
    return segments if valid else ''


def decide(entries):
    if not entries:
        return 'no_entry', '', ''
    readings, raw = set(), set()
    for entry in entries:
        sounds = [s for s in entry.get('sounds', []) if s.get('ipa')]
        if not sounds:
            return 'incomplete_homograph', '', ''
        for sound in sounds:
            if any(sound.get(k) for k in ['tags', 'raw_tags', 'note', 'form']):
                return 'qualified_pronunciation', '', ''
            segments = ipa_segments(sound['ipa'])
            if not segments:
                return 'unsupported_ipa', '', ''
            readings.add(segments)
            raw.add(sound['ipa'])
    # Never erase a stress/length/allophony contrast merely because the
    # downstream segment canonicalizer collapses it.
    normalized_raw = {value.strip().removeprefix('/').removesuffix('/').removeprefix('[').removesuffix(']')
                      for value in raw}
    if len(readings) != 1 or len(normalized_raw) != 1:
        return 'ambiguous_pronunciation', '', ''
    return 'accept', sorted(raw)[0], next(iter(readings))



def annotation(word, ipa, metadata):
    url = 'https://en.wiktionary.org/wiki/' + quote(word, safe='')
    return (f'Pronunciation IPA {ipa}; {url}; exact language/POS match; '
            f'dump {metadata["dump_sha256"][:16]}')


def load_index(path, dump):
    with sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True) as db:
        metadata = json.loads(db.execute('SELECT payload FROM metadata').fetchone()[0])
        if (dump.stat().st_size, dump.stat().st_mtime_ns) != (metadata['dump_bytes'], metadata['dump_mtime_ns']):
            raise ValueError('Pronunciation index belongs to another dump; rebuild/review it before ingestion')
        if metadata.get('policy') != POLICY:
            raise ValueError('Pronunciation index needs a current decision-policy review')
        matches = {row[:3]: row[3:] for row in db.execute(
            "SELECT lang,word,pos,ipa,segments,source_lines FROM decisions WHERE decision='accept'")}
    return matches, metadata


def write_ledger(forms, parameters, matches, metadata, path):
    from .parameters import parse_parameter_name
    positions = {row.ID: parse_parameter_name(row.Name)[1] for row in parameters.itertuples(index=False)}
    with path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['source_form_id', 'language', 'Form', 'pos', 'raw_ipa',
                                'segments', 'entry_url', 'source_lines', 'dump_sha256'], lineterminator='\n')
        writer.writeheader()
        for row in forms.itertuples(index=False):
            lang = row.Language_ID.removeprefix('wikt_')
            pos = positions[row.Parameter_ID]
            match = matches.get(key(lang, row.Form, pos))
            if not match:
                continue
            ipa, segments, lines = match
            writer.writerow(dict(source_form_id=row.ID, language=lang, Form=row.Form, pos=pos, raw_ipa=ipa,
                                 segments=segments, source_lines=lines, dump_sha256=metadata['dump_sha256'],
                                 entry_url='https://en.wiktionary.org/wiki/' + quote(row.Form, safe='')))
