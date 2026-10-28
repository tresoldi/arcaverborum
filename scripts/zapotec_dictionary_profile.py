"""Bounded PDLMA readings for reviewed Isthmus Zapotec dictionary entries.

Pérez Báez & Kaufman2018, dictionary phonology/orthography: unmarked low,
* rising,! high,7 checked nucleus. Rearticulated vowels and morpheme/clitic
boundaries remain outside this subset. Profiles are exact source forms only.
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
SIMPLE = {c: c for c in "aiueobdgkptmnslwz"} | {"y": "j", "j": "h", "x": "ʃ"}
DIGRAPHS = {"ch": "t͡ʃ", "dx": "d͡ʒ", "zh": "ʒ", "ny": "ɲ"}
SOURCE = "https://github.com/dictionaria/diidxaza#typology-phonology-and-orthography"


def reading(word):
    if not word or any(c not in SIMPLE and c not in "7*!h" for c in word):
        return ""
    if any(c * 2 in word for c in "aiueobdgkptmnslwz") or "kw" in word or "nd" in word:
        return ""
    if "7" in word and sum(c in "aiueo" for c in word) != 1:
        return ""  # Do not invent laryngealization spreading in longer roots.
    out = []
    i = 0
    while i < len(word):
        c = word[i]
        if c in "aiueo":
            mark = word[i + 1:i + 2]
            out.append(c + {"*": "̌", "!": "́"}.get(mark, "̀"))
            i += 1 + (mark in {"*", "!"})
        elif c == "7" and out and out[-1][0] in "aiueo":
            out.append("ʔ")
            i += 1
        elif word[i:i + 2] in DIGRAPHS:
            out.append(DIGRAPHS[word[i:i + 2]])
            i += 2
        elif c in SIMPLE:
            out.append(SIMPLE[c])
            i += 1
        else:
            return ""
    tokens, valid = canonicalize(out)
    return " ".join(tokens) if valid else ""


def read(path):
    with path.open() as f:
        return list(csv.DictReader(f))


def compile_profile(root, write=False):
    selected = [r for r in read(root / "docs/north_america_na05_review_2026-10-28.csv") if r["decision"] == "admit"]
    custom = root / "varieties/oto-isthmus-zapotec/custom"
    params = {r["ID"]: r for r in read(root / "intake/lexibank/parameters_raw.csv")}
    ledger = []
    with sqlite3.connect(root / "intake/intake.sqlite") as db:
        db.row_factory = sqlite3.Row
        for ds in sorted({r['source'] for r in selected}):
            rows = [r for r in selected if r['source'] == ds]
            text = "Grapheme\tIPA\tnotes\n" + "".join(
                f"^{word}$\t{ipa}\tPDLMA documented tone/nucleus subset; exact source form.\n"
                for word, ipa in sorted({(r['Form'], reading(r['pdlma'])) for r in rows})
            )
            digest = hashlib.sha256(text.encode()).hexdigest()
            path = custom / "supplement_profiles" / (ds + ".tsv")
            if write:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text)
            elif path.read_text() != text:
                raise ValueError("Compiled Zapotec profile changed")
            for r in rows:
                fs = db.execute('select * from forms where gc_lc=? and Dataset=? and ID=?',
                                ('isth1244', ds, r['source_form_id'])).fetchall()
                if len(fs) != 1 or not reading(r['pdlma']):
                    raise ValueError('Missing or unreviewed Zapotec record')
                f = dict(fs[0])
                if evidence_hash(f) != r['evidence_sha256'] or f['Segments'] or f['Form'] != r['Form']:
                    raise ValueError('Zapotec evidence changed')
                ledger.append(dict(source=ds, source_form_id=f['ID'], source_language_id=f['Language_ID'],
                                   source_glottocode='isth1244', evidence_sha256=evidence_hash(f),
                                   expected_source_concepticon_id=params[f['Parameter_ID']]['Concepticon_ID'],
                                   concept_id=r['concept_id'], decision='admit',
                                   rationale=r['rationale'] + ' ' + SOURCE,
                                   profile_file=ds + '.tsv', profile_sha256=digest))
    path = custom / 'supplements.csv'
    if write:
        with path.open('w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(ledger[0]), lineterminator='\n')
            w.writeheader()
            w.writerows(ledger)
    elif read(path) != ledger:
        raise ValueError('Compiled Zapotec ledger changed')
    print(len(ledger), 'Zapotec profile forms', len({r['concept_id'] for r in ledger}), 'concepts')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--write', action='store_true')
    compile_profile(ROOT, p.parse_args().write)
