"""Compile exact reviewed Kodiak-correlated Wiktionary spellings only.

Alutiiq Museum alphabet, consonants, doubled-vowel and numbers lessons.
Subset excludes apostrophe conventions, e, c, Russian rhotics, g/r/gw,
complex nasal alternations and mixed vowels. No surface allophones/stress inferred.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import sqlite3
from pathlib import Path

from arcaverborum.phonology import canonicalize
from arcaverborum.supplements import evidence_hash

ROOT = Path(__file__).resolve().parents[1]
SIMPLE = dict(zip("aiupktmnslqy", "aiupktmnslqj", strict=True))


def reading(word):
    if not word or any(c not in SIMPLE and c != "g" for c in word):
        return ""
    out = []
    i = 0
    while i < len(word):
        pair = word[i:i + 2]
        if pair in {"ng", "ll", "aa", "ii", "uu"}:
            out.append({"ng": "ŋ", "ll": "ɬ", "aa": "aː", "ii": "iː", "uu": "uː"}[pair])
            i += 2
        elif word[i] == "g":
            return ""
        elif word[i] in "aiu" and i + 1 < len(word) and word[i + 1] in "aiu":
            return ""
        else:
            out.append(SIMPLE[word[i]])
            i += 1
    tokens, valid = canonicalize(out)
    return " ".join(tokens) if valid else ""


def compile_profile(root, write=False):
    with (root / "docs/north_america_na06_review_2026-10-28.csv").open() as f:
        rows = [r for r in csv.DictReader(f) if r["decision"] == "admit"]
    entries = {}
    with sqlite3.connect(root / "intake/intake.sqlite") as db:
        db.row_factory = sqlite3.Row
        for r in rows:
            fs = db.execute("select * from forms where gc_lc=? and Dataset=? and ID=?",
                            ("paci1278", "wiktionary", r['source_form_id'])).fetchall()
            if len(fs) != 1 or evidence_hash(dict(fs[0])) != r['evidence_sha256'] or not reading(r['Form']):
                raise ValueError('Alutiiq exact source evidence/reading changed')
            entries[r['Form']] = reading(r['Form'])
    text = "Grapheme\tIPA\tnotes\n" + "".join(
        f"^{word}$\t{ipa}\tExact Kodiak-correlated subset; broad reading, no surface/stress inference.\n"
        for word, ipa in sorted(entries.items())
    )
    path = root / 'varieties/esk-pacific-gulf-yupik/custom/profile.tsv'
    if write:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    elif path.read_text() != text:
        raise ValueError('Alutiiq compiled profile differs from authored review')
    print(len(entries), 'Alutiiq exact profile spellings; SHA256', hashlib.sha256(text.encode()).hexdigest())


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--write', action='store_true')
    compile_profile(ROOT, p.parse_args().write)
