"""Repair detached U+0306 vowel breves in the accepted Vakh–Vasyugan slice.

--write compiles reviewed transcription overrides. Without it, validate the
source snapshot and built output. The repair changes whitespace only; comma
alternatives with no source segments remain unresolved.
"""

from __future__ import annotations

import argparse
import csv
import sqlite3
import unicodedata
from pathlib import Path

from arcaverborum.phonology import segments_are_valid

ROOT = Path(__file__).resolve().parents[1]
VARIETY = 'urj-vach-vasjugan'
VOWELS = {'ɑ', 'o', 'ø'}


def attach_breves(segments: str) -> str:
    output = []
    for token in segments.split():
        if token == '\u0306':
            if not output or output[-1] not in VOWELS:
                raise ValueError('Detached breve has no reviewed vowel base')
            output[-1] += token
        else:
            output.append(token)
    result = ' '.join(output)
    if unicodedata.normalize('NFD', result.replace(' ', '')) != unicodedata.normalize(
            'NFD', segments.replace(' ', '')):
        raise ValueError('Repair changed segment characters')
    if result and not segments_are_valid(result):
        raise ValueError('Repaired source still contains invalid segments')
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    root = args.root.resolve()
    custom = root / 'varieties' / VARIETY / 'custom'
    custom.mkdir(exist_ok=True)
    with sqlite3.connect((root / 'intake/intake.sqlite').as_uri() + '?mode=ro', uri=True) as db:
        db.row_factory = sqlite3.Row
        source = {r['ID']: dict(r) for r in db.execute(
            'SELECT * FROM forms WHERE gc_lc=? AND Dataset=? AND Language_ID=? ORDER BY seq',
            ('fare1244', 'uralex', 'uralex_khanty_vakh_vasyugan'))}
    review_path = custom / 'transcription_review.csv'
    if review_path.exists():
        with review_path.open() as f:
            for review in csv.DictReader(f):
                row = source.get(review['source_form_id'])
                if row is None or (row['Form'], row['Segments']) != (review['Form'], review['original_segments']):
                    raise ValueError('Reviewed source changed: ' + review['source_form_id'])
    reviews = []
    for fid, row in source.items():
        if '\u0306' not in row['Segments'].split():
            continue
        repaired = attach_breves(row['Segments'])
        reviews.append(dict(source_form_id=fid, Form=row['Form'], original_segments=row['Segments'],
                            corrected_segments=repaired,
                            reason='Attach detached breve to its original vowel; preserve every segment character. '
                                   'UraLex IPA_NOTES.md: Short vowel breve; reviewed 2026-10-27.'))
    if args.write:
        if not reviews:
            raise ValueError('No detached source breves; review obsolete overrides before rewriting')
        output = custom / 'transcriptions.csv'
        if output.exists():
            with output.open() as f:
                old = {r['source_form_id'] for r in csv.DictReader(f)}
            if not old <= {r['source_form_id'] for r in reviews}:
                raise ValueError('Refusing to discard unrelated transcription overrides')
        with review_path.open('w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(reviews[0]), lineterminator='\n')
            writer.writeheader()
            writer.writerows(reviews)
        with output.open('w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['Concepticon_ID', 'source_form_id', 'Value', 'Form',
                                                  'Segments', 'Comment', 'notes'], lineterminator='\n')
            writer.writeheader()
            for review in reviews:
                writer.writerow(dict(Concepticon_ID='', source_form_id=review['source_form_id'], Value='', Form='',
                                     Segments=review['corrected_segments'], Comment='', notes=review['reason']))
        print(f'Wrote {len(reviews)} whitespace-only repairs')
    else:
        with (custom.parent / 'generated/forms.csv').open() as f:
            built = {r['source_form_id']: r for r in csv.DictReader(f)}
        for review in reviews:
            row = built[review['source_form_id']]
            if row['Segments_Source'] != 'source' or unicodedata.normalize(
                    'NFD', row['Segments'].replace(' ', '')) != unicodedata.normalize(
                        'NFD', review['corrected_segments'].replace(' ', '')):
                raise ValueError('Build does not contain reviewed repair: ' + review['source_form_id'])
        print(f'{len(reviews)} repaired forms verified; source characters preserved')


if __name__ == '__main__':
    main()
