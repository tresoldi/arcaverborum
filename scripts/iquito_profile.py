"""Compile a conservative, source-scoped Iquito dictionary profile and supplements.

Michael & Beier (2021), Dictionaria 14, tables 1–4 and tone-marking section.
Only individually reviewed senses enter the supplement ledger. High tone is
retained on short vowels; mixed-tone long vowels, hiatus/glide ambiguity,
clitics and unreviewed foreign characters are withheld. Low/null tone is not
inferred. The source itself marks high tone only; this is a partial tonal
representation, not a surface phonetic transcription.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import sqlite3
import unicodedata
from pathlib import Path

from arcaverborum.phonology import canonicalize, segments_are_valid
from arcaverborum.supplements import evidence_hash

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "https://dictionaria.clld.org/contributions/iquito"
SIMPLE = dict(zip("jkmnprstwy", ["h", "k", "m", "n", "p", "ɾ", "s", "t", "w", "j"], strict=True))
VOWELS = "aiɨu"


def read(path):
    with path.open() as handle:
        return list(csv.DictReader(handle))


def reading(form):
    """Return a documented subset reading; refuse incomplete tonal contrasts."""
    text = unicodedata.normalize("NFD", form.lower())
    units = []
    for c in text:
        if c == "\u0301":
            if not units or units[-1] not in VOWELS:
                return ""
            units[-1] += c
        elif c in VOWELS or c in SIMPLE:
            units.append(c)
        else:
            return ""
    out = []
    i = 0
    while i < len(units):
        c = units[i]
        base = c[0]
        nxt = units[i + 1] if i + 1 < len(units) else ""
        after = units[i + 2] if i + 2 < len(units) else ""
        if base in VOWELS:
            if nxt and nxt[0] == base:
                if c != nxt:  # Do not collapse the position of high tone on a long vowel.
                    return ""
                out.append(c + "ː")
                i += 2
            else:
                out.append(c)
                i += 1
            if i < len(units) and units[i][0] in VOWELS:
                return ""  # The conservative subset excludes remaining hiatus/glide sequences.
            continue
        if c == "k" and nxt == "w":
            if not after or after[0] != "a":
                return ""
            out.append("kʷ")
            i += 2
            continue
        if c in "kns" and nxt == "i" and after and after[0] in VOWELS and after[0] != "i":
            if c == "k" and after[0] != "a":
                return ""
            out.append({"k": "kʲ", "n": "ɲ", "s": "ʃ"}[c])
            i += 2
            continue
        if c in "ns" and nxt and nxt[0] == "i":
            return ""  # Do not resolve /Ci/ versus palatalized readings here.
        out.append(SIMPLE[c])
        i += 1
    tokens, valid = canonicalize(out)
    return " ".join(tokens) if valid else ""


def compile_profile(root, write=False):
    custom = root / "varieties/zap-iquito/custom"
    decisions = [r for r in read(root / "src/arcaverborum/data/dictionary_senses.csv") if r["dataset"] == "dictiquito"]
    entries = {r["ID"]: r for r in read(root / "raw/lexibank/dictiquito/cldf/entries.csv")}
    senses = {r["ID"]: r for r in read(root / "raw/lexibank/dictiquito/cldf/senses.csv")}
    eligible, held = [], []
    for review in decisions:
        sense = senses[review["sense_id"]]
        entry = entries[sense["Entry_ID"]]
        if (entry["Headword"], sense["Description"], entry["Part_Of_Speech"]) != (
            review["expected_headword"],
            review["expected_description"],
            review["expected_pos"],
        ):
            raise ValueError("Iquito source spelling/sense changed: " + review["sense_id"])
        ipa = reading(entry["Headword"])
        item = dict(
            sense_id=review["sense_id"],
            headword=entry["Headword"],
            concept_id=review["concept_id"],
            segments=ipa,
            decision="admit" if ipa else "hold",
            rationale="Source tables 1–4; explicit short-vowel high tone retained, low/null unspecified."
            if ipa
            else "Outside conservative subset: tonal length, palatalization, hiatus or character ambiguity.",
        )
        (eligible if ipa else held).append(item)
    profile_text = "Grapheme\tIPA\tnotes\n" + "".join(
        f"^{word}$\t{ipa}\tMichael & Beier 2021 tables 1–4; source-specific partial-tone profile. {SOURCE}\n"
        for word, ipa in sorted({(r["headword"], r["segments"]) for r in eligible})
    )
    digest = hashlib.sha256(profile_text.encode()).hexdigest()
    ledger = []
    with sqlite3.connect((root / "intake/intake.sqlite").as_uri() + "?mode=ro", uri=True) as db:
        db.row_factory = sqlite3.Row
        params = {r["ID"]: r for r in read(root / "intake/lexibank/parameters_raw.csv") if r["Dataset"] == "dictiquito"}
        for decision in eligible:
            sid = "dictiquito_" + decision["sense_id"]
            matches = db.execute(
                "SELECT * FROM forms WHERE gc_lc=? AND Dataset=? AND ID=?", ("iqui1243", "dictiquito", sid)
            ).fetchall()
            if len(matches) != 1:
                raise ValueError("Missing/duplicate Iquito intake record: " + sid)
            row = dict(matches[0])
            if row["Form"] != decision["headword"] or row["Segments"]:
                raise ValueError("Iquito representation changed; review before profile conversion")
            if not segments_are_valid(decision["segments"]):
                raise ValueError("Invalid compiled profile reading")
            ledger.append(
                dict(
                    source="dictiquito",
                    source_form_id=sid,
                    source_language_id=row["Language_ID"],
                    source_glottocode="iqui1243",
                    evidence_sha256=evidence_hash(row),
                    expected_source_concepticon_id=params[row["Parameter_ID"]]["Concepticon_ID"],
                    concept_id=decision["concept_id"],
                    decision="admit",
                    mapping_decision="reviewed_override",
                    rationale=decision["rationale"] + " " + SOURCE,
                    profile_file="dictiquito.tsv",
                    profile_sha256=digest,
                )
            )
    path = custom / "supplements.csv"
    existing = read(path) if path.exists() else []
    old = {r["source_form_id"]: r for r in existing}
    for row in ledger:
        if row["source_form_id"] in old and (
            row["evidence_sha256"] != old[row["source_form_id"]]["evidence_sha256"]
            or row["expected_source_concepticon_id"] != old[row["source_form_id"]]["expected_source_concepticon_id"]
        ):
            raise ValueError("Previously reviewed Iquito evidence changed")
    # Preserve other source admissions; intentional removals from this profile are explicit in its report.
    combined = [r for r in existing if r["source"] != "dictiquito"] + ledger
    if write:
        directory = custom / "supplement_profiles"
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "dictiquito.tsv").write_text(profile_text)
        for output, rows in [(path, combined), (root / "docs/iquito_profile_review_2026-10-27.csv", eligible + held)]:
            with output.open("w", newline="") as handle:
                fields = list(dict.fromkeys(k for r in rows for k in r))
                writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
                writer.writeheader()
                writer.writerows(rows)
    print(len(eligible), "Iquito profile supplements;", len(held), "held; primary source retained")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    compile_profile(ROOT, args.write)


if __name__ == "__main__":
    main()
