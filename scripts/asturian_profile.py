"""Conservative standard-Asturian broad phonemic profile (ALLA 2001).

Excludes loans/foreign letters, dialect signs, ambiguous x/y, vowel sequences,
and non-intervocalic noninitial r. No surface allophones or stress are inferred.
Source-supplied IPA always takes precedence over this incomplete profile.
"""
from __future__ import annotations

import argparse
import csv
import sqlite3
import unicodedata
from pathlib import Path

from arcaverborum.phonology import segments_are_valid

ROOT = Path(__file__).resolve().parents[1]
SIMPLE = dict(zip('abdefgilmnñopstuvz',
                  ['a', 'b', 'd', 'e', 'f', 'g', 'i', 'l', 'm', 'n', 'ɲ', 'o', 'p', 's', 't', 'u', 'b', 'θ']))


def reading(form):
    word = unicodedata.normalize('NFC', form.lower())
    word = word.translate(str.maketrans('áéíóú', 'aeiou'))
    if not word or any(c not in SIMPLE and c not in 'chqr' for c in word):
        return ''
    out = []
    i = 0
    while i < len(word):
        c = word[i]
        rest = word[i:]
        next_c = word[i+1:i+2]
        if rest.startswith('ch'):
            out.append('tʃ')
            i += 2
            continue
        if rest.startswith('ll'):
            out.append('ʎ')
            i += 2
            continue
        if rest.startswith('rr'):
            if i == 0 or i+2 >= len(word) or word[i-1] not in 'aeiou' or word[i+2] not in 'aeiou':
                return ''
            out.append('r')
            i += 2
            continue
        if c in 'gq' and next_c == 'u' and word[i+2:i+3] in {'e', 'i'}:
            out.append('g' if c == 'g' else 'k')
            i += 2
            continue
        if c == 'q' or c == 'g' and next_c in {'e', 'i'}:
            return ''
        if c == 'h':
            i += 1
            continue
        if c == 'c':
            out.append('θ' if next_c in {'e', 'i'} else 'k')
        elif c == 'r':
            if i == 0:
                out.append('r')
            elif word[i-1] in 'aeiou' and next_c in 'aeiou':
                out.append('ɾ')
            else:
                return ''
        else:
            out.append(SIMPLE[c])
        i += 1
    if any(a in 'aeiou' and b in 'aeiou' for a, b in zip(out, out[1:])):
        return ''
    result = ' '.join(out)
    return result if result and segments_are_valid(result) else ''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    path = ROOT / 'varieties/ine-asturian-leonese-cantabrian/custom'
    path.mkdir(exist_ok=True)
    with sqlite3.connect((ROOT / 'intake/intake.sqlite').as_uri() + '?mode=ro', uri=True) as db:
        rows = db.execute("SELECT ID,Form FROM forms WHERE Dataset='wiktionary' "
                          "AND Language_ID='wikt_ast' ORDER BY seq")
        review = [dict(source_form_id=fid, Form=form, segments=reading(form)) for fid, form in rows]
    review_path = path / 'profile_review.csv'
    if review_path.exists():
        with review_path.open() as f:
            old = {r['source_form_id']: r['Form'] for r in csv.DictReader(f)}
        if old != {r['source_form_id']: r['Form'] for r in review}:
            raise ValueError('Reviewed source changed; inspect before rewriting')
    profile = {r['Form']: r['segments'] for r in review if r['segments']}
    if args.write:
        with (path / 'profile.tsv').open('w') as f:
            f.write('Grapheme\tIPA\tnotes\n')
            for form, segments in sorted(profile.items()):
                f.write(f'^{form}$\t{segments}\tALLA 2001 pp.15–16,23–24,36–48; broad phonemic subset\n')
        with (path / 'profile_review.csv').open('w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(review[0]), lineterminator='\n')
            w.writeheader()
            w.writerows(review)
    print(len(profile), 'spellings;', sum(bool(r['segments']) for r in review), 'supported rows')


if __name__ == '__main__':
    main()
