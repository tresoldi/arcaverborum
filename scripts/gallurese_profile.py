"""Compile a finite Gallurese neutral spelling subset; no dialect-wide rules.

Convention section6 (unionegallura.it, 3564_6cunveniuoltugraficu.pdf).
No inferred stress, surface vowel length, lenition or syllabic allophones.
"""

from __future__ import annotations

import argparse
import csv
import sqlite3
from pathlib import Path

from arcaverborum.phonology import segments_are_valid
from arcaverborum.supplements import evidence_hash

ROOT = Path(__file__).resolve().parents[1]


def compile_profile(root=ROOT, *, write=False):
    with (root / "docs/romance_r02_review_2026-10-28.csv").open() as f:
        rows = list(csv.DictReader(f))
    entries = {}
    with sqlite3.connect(root / "intake/intake.sqlite") as db:
        db.row_factory = sqlite3.Row
        for r in rows:
            found = db.execute(
                "select * from forms where gc_lc='gall1276' and Dataset='wiktionary' "
                "and Language_ID='wikt_sdn' and ID=?",
                (r["source_form_id"],),
            ).fetchall()
            if len(found) != 1 or evidence_hash(dict(found[0])) != r["evidence_sha256"]:
                raise ValueError("Reviewed Gallurese source changed")
            if r["decision"] != "admit":
                continue
            if not segments_are_valid(r["segments"]):
                raise ValueError("Invalid reviewed Gallurese reading")
            if r["Form"] in entries and entries[r["Form"]] != r["segments"]:
                raise ValueError("Ambiguous Gallurese exact form")
            entries[r["Form"]] = r["segments"]
    text = "Grapheme\tIPA\tnotes\n" + "".join(
        f"^{word}$\t{ipa}\tFinite neutral Gallurese subset; convention section6; no stress/surface inference.\n"
        for word, ipa in sorted(entries.items())
    )
    path = root / "varieties/ine-gallurese-sardinian/custom/profile.tsv"
    if write:
        path.write_text(text)
    elif path.read_text() != text:
        raise ValueError("Compiled Gallurese profile differs from review")
    print(len(entries), "exact Gallurese profile spellings")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--write", action="store_true")
    compile_profile(write=p.parse_args().write)
