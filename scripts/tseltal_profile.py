"""Compile an authored Tseltal subset using Polian2020's documented orthography.

Consonant-initial single stems only. No inferred initial glottals, compound
hyphens, loan spelling, stress, pre-laryngealization or dialect homogenization.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import sqlite3
import unicodedata
from pathlib import Path

from arcaverborum.phonology import canonicalize
from arcaverborum.supplements import evidence_hash

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "https://github.com/dictionaria/tseltal#the-orthography-used-in-the-dictionary"
SIMPLE = dict(zip("aiueobptkmnsxlrwyjh", "aiueobptkmnsʃlɾwjxh", strict=True))
DIGRAPHS = {"ts": "t͡s", "ch": "t͡ʃ", "p'": "pʼ", "t'": "tʼ", "k'": "kʼ", "ts'": "t͡sʼ", "ch'": "t͡ʃʼ"}


def reading(word):
    if not word or word[0] in "aiueo'" or any(c not in SIMPLE and c != "'" for c in word):
        return ""
    out = []
    while word:
        key = next((k for k in sorted(DIGRAPHS, key=len, reverse=True) if word.startswith(k)), word[0])
        out.append(DIGRAPHS.get(key, SIMPLE.get(key, "ʔ" if key == "'" else "")))
        word = word[len(key):]
    tokens, valid = canonicalize(out)
    return unicodedata.normalize("NFC", " ".join(tokens)) if valid else ""


def read(path):
    with path.open() as f:
        return list(csv.DictReader(f))


def compile_profile(root, write=False):
    reviews = read(root / "docs/north_america_na04_review_2026-10-28.csv")
    selected = [r for r in reviews if r["decision"] == "admit"]
    text = "Grapheme\tIPA\tnotes\n" + "".join(
        f"^{word}$\t{ipa}\tPolian2020 documented broad orthography; dialect context retained.\n"
        for word, ipa in sorted({(r["Form"], reading(r["Form"])) for r in selected})
    )
    digest = hashlib.sha256(text.encode()).hexdigest()
    params = {r["ID"]: r for r in read(root / "intake/lexibank/parameters_raw.csv")}
    ledger = []
    with sqlite3.connect(root / "intake/intake.sqlite") as db:
        db.row_factory = sqlite3.Row
        for r in selected:
            f = db.execute("select * from forms where gc_lc=? and Dataset=? and ID=?",
                           ("tzel1254", "dicttseltal", r["source_form_id"])).fetchall()
            if len(f) != 1 or not reading(r["Form"]):
                raise ValueError("Missing or unreviewed Tseltal reading")
            f = dict(f[0])
            if f["Form"] != r["Form"] or f["Segments"] or evidence_hash(f) != r["evidence_sha256"]:
                raise ValueError("Tseltal source evidence changed")
            ledger.append(dict(source="dicttseltal", source_form_id=f["ID"], source_language_id=f["Language_ID"],
                               source_glottocode="tzel1254", evidence_sha256=evidence_hash(f),
                               expected_source_concepticon_id=params[f["Parameter_ID"]]["Concepticon_ID"],
                               concept_id=r["concept_id"], decision="admit", rationale=r["rationale"] + " " + SOURCE,
                               profile_file="dicttseltal.tsv", profile_sha256=digest))
    custom = root / "varieties/may-tzeltal/custom"
    if write:
        (custom / "supplement_profiles").mkdir(parents=True, exist_ok=True)
        (custom / "supplement_profiles/dicttseltal.tsv").write_text(text)
        with (custom / "primary.csv").open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(ledger[0]), lineterminator="\n")
            w.writeheader()
            w.writerows(ledger)
    elif read(custom / "primary.csv") != ledger or (custom / "supplement_profiles/dicttseltal.tsv").read_text() != text:
        raise ValueError("Compiled Tseltal profile/ledger differs from authored review")
    print(len(ledger), "guarded Tseltal profile forms", len({r['concept_id'] for r in selected}), "concepts")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--write", action="store_true")
    compile_profile(ROOT, p.parse_args().write)
