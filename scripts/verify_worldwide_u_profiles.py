"""Recheck U finite profiles against actual native supplied readings and Beja PDF context."""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sqlite3
import unicodedata
from pathlib import Path

import pymupdf

from arcaverborum.phonology import resegment, segments_are_valid
from arcaverborum.sources.original_lexica import plain_tex
from arcaverborum.supplements import evidence_hash

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    with path.open(newline='') as handle:
        return list(csv.DictReader(handle))


def main():
    pdf = ROOT / 'raw/curation/after-r-planning/beja2026.pdf'
    text = ROOT / 'raw/curation/u/beja-pdf-layout.txt'
    pdf_hash = hashlib.file_digest(pdf.open('rb'), 'sha256').hexdigest()
    assert pdf_hash == 'f173826ab756fa35ab2ed3a043c13b38df13da72828106bffc65520a23fed111'
    with pymupdf.open(pdf) as document:
        extracted = '\n'.join(page.get_text() for page in document)
    text.parent.mkdir(parents=True, exist_ok=True)
    text.write_text(extracted)
    published = unicodedata.normalize('NFC', extracted)
    cohorts = [('chakalioriginal', 'atl-chakali', 'u09'),
               ('dagaareoriginal', 'atl-central-dagaare', 'u09'),
               ('bejaoriginal', 'afa-beja', 'u09'),
               ('wiktionaryfr202610', 'sit-lepcha', 'u06')]
    reports = []
    with sqlite3.connect((ROOT / 'intake/intake.sqlite').as_uri() + '?mode=ro', uri=True) as db:
        db.row_factory = sqlite3.Row
        for source, aid, track in cohorts:
            custom = ROOT / 'varieties' / aid / 'custom'
            filename = track + '-' + source + '.tsv'
            decisions = [r for r in read(custom / 'supplements.csv') if r.get('profile_file') == filename]
            emitted = {r['source_form_id']: r for r in
                       read(ROOT / 'varieties' / aid / 'generated/forms.csv')
                       if r['transcription_source'] == source}
            codes = {r['source_glottocode'] for r in decisions}
            assert len(codes) == 1
            native = {r['ID']: dict(r) for r in db.execute(
                'select * from forms where gc_lc=? and Dataset=?', (next(iter(codes)), source))}
            profile = custom / 'supplement_profiles' / filename
            sha = hashlib.sha256(profile.read_bytes()).hexdigest()
            with profile.open() as handle:
                rules = {r['Grapheme']: r['IPA'] for r in csv.DictReader(handle, delimiter='\t')}
            for decision in decisions:
                row = native[decision['source_form_id']]
                assert evidence_hash(row) == decision['evidence_sha256']
                assert sha == decision['profile_sha256']
                original = json.loads(row['Comment'])['original']
                if source != 'wiktionaryfr202610':
                    assert len(original['headwords']) == 1
                    pos = original['POS'][0]
                    if source == 'chakalioriginal':
                        assert pos in {'n', 'n. phr'}
                    elif source == 'dagaareoriginal':
                        assert pos == 'n.'
                    else:
                        assert pos == 'n' or pos.startswith(('n.', 'nom'))
                else:
                    assert original['pos'] != 'name'
                    if original['pos'] in {'prefix', 'suffix'}:
                        assert decision['entry_kind'] == 'affix'
                if source == 'wiktionaryfr202610':
                    readings = {s['ipa'].strip('\\/[] ') for s in original.get('sounds', [])
                                if s.get('ipa') and not s.get('tags') and not s.get('raw_tags')}
                    assert len(readings) == 1
                    ipa = next(iter(readings))
                elif source == 'bejaoriginal':
                    ipa = row['Form']
                    assert 'ɛ' not in ipa
                    sense = original['senses'][0]
                    hits = re.finditer(r'(?m)^' + re.escape(unicodedata.normalize('NFC', ipa)) + r'(?=\s)', published)
                    assert any(re.search(r'\bn\.', published[h.end():h.end() + 180])
                               and re.search(r'\b' + re.escape(sense) + r'\b', published[h.end():h.end() + 200])
                               for h in hits), row['ID']
                else:
                    assert len(original['phonetic']) == 1
                    ipa = plain_tex(original['phonetic'][0])
                segments, okay = resegment(ipa.replace('-', '+'))
                assert okay and segments_are_valid(segments)
                assert rules['^' + row['Form'] + '$'] == segments
                accepted = emitted[row['ID']]
                assert accepted['Segments'] == segments and accepted['Segments_Source'] == 'profile'
                assert accepted['concept_id'] == ''
            reports.append(dict(dataset=source, av_id=aid, source_readings=len(decisions),
                                profile_sha256=sha, native_evidence_and_reading_checks='passed',
                                basis='Supplied phonetic field or explicitly IPA Beja head; no spelling inference'))
    proof = dict(cohorts=reports, finite_source_readings=sum(r['source_readings'] for r in reports),
                 beja_pdf_sha256=pdf_hash,
                 beja_text_sha256=hashlib.file_digest(text.open('rb'), 'sha256').hexdigest(),
                 beja_text_method='PyMuPDF get_text, pages joined by newline, from pinned published PDF',
                 limit='Finite source-notation fidelity; not independent confirmation or restored unwritten contrasts.')
    (ROOT / 'docs/worldwide_u_profile_verification_2026-10-30.json').write_text(json.dumps(proof, indent=2) + '\n')
    print([(r['dataset'], r['source_readings']) for r in reports])


if __name__ == '__main__':
    main()
