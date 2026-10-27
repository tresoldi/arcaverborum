"""Compile a conservative broad phonemic Pannonian Rusyn spelling profile.

Ramač (2002), phonetics §§7–14 and transcription §21: five vowels,
consonant distinctions, and contextual palatalization. Outputs are inferred
phonemic sequences, not narrow surface IPA or stress annotations. Multiword,
foreign-script, punctuation and unsupported palatal spellings are excluded.
"""

from __future__ import annotations

import argparse
import csv
import sqlite3
import unicodedata
from pathlib import Path

from arcaverborum.phonology import segments_are_valid

ROOT = Path(__file__).resolve().parents[1]
SINGLE = dict(zip('абвгґдежзийклмнопрстуфхцчш',
                  ['a', 'b', 'v', 'ɦ', 'g', 'd', 'e', 'ʒ', 'z', 'i', 'j', 'k',
                   'l', 'm', 'n', 'o', 'p', 'r', 's', 't', 'u', 'f', 'h', 'ts', 'tʃ', 'ʃ']))
IOTATED = {'я': 'a', 'є': 'e', 'ї': 'i', 'ю': 'u'}
SOFT = {'д': 'dʲ', 'т': 'tʲ', 'л': 'lʲ', 'н': 'nʲ'}


def reading(form: str) -> tuple[str, str]:
    text = unicodedata.normalize('NFC', form.lower())
    if not text or any(c not in SINGLE and c not in IOTATED and c not in 'ьщ' for c in text):
        return '', 'unsupported script, accent, punctuation or word boundary'
    if 'дз' in text or 'дж' in text:
        return '', 'affricate versus morpheme-boundary cluster requires lexical review'
    output = []
    i = 0
    while i < len(text):
        char = text[i]
        following = text[i+1] if i+1 < len(text) else ''
        if char in SOFT and following and following in 'ьяєїю':
            output.append(SOFT[char])
            if following != 'ь':
                output.append(IOTATED[following])
            i += 2
            continue
        if char == 'ь':
            return '', 'soft sign outside reviewed d/t/l/n context'
        if char in IOTATED:
            output.extend(['j', IOTATED[char]])
        elif char == 'щ':
            output.extend(['ʃ', 'tʃ'])
        else:
            output.append(SINGLE[char])
        i += 1
    result = ' '.join(output)
    if not segments_are_valid(result):
        raise ValueError('Invalid phonemic output for ' + form)
    return result, 'broad phonemic reading; stress and surface assimilation not inferred'


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    root = args.root.resolve()
    custom = root / 'varieties/ine-pannonian-ruthenian/custom'
    with sqlite3.connect((root / 'intake/intake.sqlite').as_uri() + '?mode=ro', uri=True) as db:
        db.row_factory = sqlite3.Row
        source = list(db.execute('SELECT * FROM forms WHERE gc_lc=? AND Dataset=? ORDER BY seq',
                                 ('pann1240', 'wiktionary')))
    path = custom / 'profile_review.csv'
    if path.exists():
        with path.open() as f:
            previous = {r['source_form_id']: r for r in csv.DictReader(f)}
        current = {r['ID']: r for r in source}
        if set(previous) != set(current) or any(previous[k]['Form'] != current[k]['Form'] for k in previous):
            raise ValueError('Reviewed source changed; inspect before regenerating profile')
    records, profile = [], {}
    for row in source:
        segments, reason = reading(row['Form'])
        if segments:
            profile[row['Form']] = segments
        records.append(dict(source_form_id=row['ID'], Form=row['Form'], proposed_segments=segments,
                            decision='broad_phonemic' if segments else 'defer', rationale=reason))
    profile_text = 'Grapheme\tIPA\tnotes\n' + ''.join(
        f'^{word}$\t{segments}\tInferred broad phonemic sequence; Ramač 2002 §§7–14,21\n'
        for word, segments in sorted(profile.items()))
    if args.write:
        custom.mkdir(exist_ok=True)
        with path.open('w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(records[0]), lineterminator='\n')
            writer.writeheader()
            writer.writerows(records)
        (custom / 'profile.tsv').write_text(profile_text)
    else:
        if (custom / 'profile.tsv').read_text() != profile_text:
            raise ValueError('Active profile differs from compiler output')
        if not path.exists():
            raise ValueError('Compile the reviewed profile with --write first')
        with path.open() as f:
            if list(csv.DictReader(f)) != records:
                raise ValueError('Profile review differs from reproducible compiler output')
    print(f'{len(profile)} spellings; {sum(bool(r["proposed_segments"]) for r in records)}/{len(records)} rows; '
          'surface phonetics and stress remain unspecified')


if __name__ == '__main__':
    main()
