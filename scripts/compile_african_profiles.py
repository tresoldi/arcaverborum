"""Compile guarded finite source-specific African reading profiles."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sqlite3
from pathlib import Path

from arcaverborum.phonology import segments_are_valid
from arcaverborum.supplements import evidence_hash

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    with path.open() as f:
        return list(csv.DictReader(f))


def write_csv(path, rows):
    path.parent.mkdir(exist_ok=True, parents=True)
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(dict.fromkeys(k for r in rows for k in r)), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def reject_dictionary_pos_conflict(comment, target_pos):
    """Reject explicit noun/verb contradictions; unknown labels remain unclassified."""
    prefix = "Original dictionary evidence: "
    if not comment.startswith(prefix):
        return
    original = json.loads(comment[len(prefix):])
    pos = original.get("entry", {}).get("Part_Of_Speech", "").lower().strip()
    noun = pos.startswith("n") or pos.endswith("noun")
    verb = not noun and (pos.startswith("v") or re.search(r"\bverb\b", pos))
    if (noun and target_pos == "v") or (verb and target_pos == "n"):
        raise ValueError("Dictionary source/target POS mismatch")


def compile_profiles(review, *, root=ROOT, write=False):
    concept_rows = read(root / "src/arcaverborum/data/concepts.csv")
    concepts = {r["concept_id"]: r["concepticon_id"] for r in concept_rows}
    positions = {r["concept_id"]: r["pos"] for r in concept_rows}
    params = {r["ID"]: r for p in (root / "intake").glob("*/parameters_raw.csv") for r in read(p)}
    groups = {}
    with sqlite3.connect((root / "intake/intake.sqlite").as_uri() + "?mode=ro", uri=True) as db:
        db.row_factory = sqlite3.Row
        for r in read(review):
            if r["decision"] != "admit":
                continue
            found = db.execute(
                "select * from forms where gc_lc=? and Dataset=? and ID=?",
                (r["source_glottocode"], r["source"], r["source_form_id"]),
            ).fetchall()
            if len(found) != 1:
                raise ValueError("African profile source identity missing or duplicated")
            row = dict(found[0])
            p = params[row["Parameter_ID"]]
            if (
                evidence_hash(row) != r["evidence_sha256"]
                or row["Segments"]
                or row["Form"] != r["Form"]
                or p["Name"] != r["source_sense"]
                or not segments_are_valid(r["segments"])
            ):
                raise ValueError("African profile evidence or reading changed")
            reject_dictionary_pos_conflict(row["Comment"], positions[r["concept_id"]])
            groups.setdefault((r["av_id"], r["source"]), []).append((r, row, p))
    for (aid, source), entries in groups.items():
        words = {}
        for r, row, p in entries:
            if r["Form"] in words and words[r["Form"]] != r["segments"]:
                raise ValueError("Ambiguous African whole-form profile")
            words[r["Form"]] = r["segments"]
        text = "Grapheme\tIPA\tnotes\n" + "".join(
            f"^{word}$\t{reading}\tFinite reviewed source-specific broad reading; see authored evidence.\n"
            for word, reading in sorted(words.items())
        )
        filename = source + ".tsv"
        digest = hashlib.sha256(text.encode()).hexdigest()
        custom = root / "varieties" / aid / "custom"
        profile = custom / "supplement_profiles" / filename
        primary = custom / "primary.csv"
        ledger = (
            primary
            if primary.exists() and {r["source"] for r in read(primary)} == {source}
            else custom / "supplements.csv"
        )
        old = read(ledger) if ledger.exists() else []
        records = []
        for r, row, p in entries:
            records.append(
                dict(
                    source=source,
                    source_form_id=row["ID"],
                    source_language_id=row["Language_ID"],
                    source_glottocode=row["Glottocode"],
                    evidence_sha256=r["evidence_sha256"],
                    expected_source_concepticon_id=p["Concepticon_ID"],
                    concept_id=r["concept_id"],
                    decision="admit",
                    mapping_decision="map" if concepts[r["concept_id"]] != p["Concepticon_ID"] else "retain",
                    rationale=r["rationale"],
                    profile_file=filename,
                    profile_sha256=digest,
                )
            )
        # Exact source/target identity scopes must survive profile reproduction.
        for record, (reviewed, _, _) in zip(records, entries, strict=True):
            for field in ("pronunciation_scope", "pronunciation_tags", "pronunciation_note"):
                if reviewed.get(field):
                    record[field] = reviewed[field]
        keys = {(r["source"], r["source_form_id"]) for r in records}
        for r in old:
            key = (r["source"], r["source_form_id"])
            if key in keys and r["evidence_sha256"] != next(
                x["evidence_sha256"] for x in records if (x["source"], x["source_form_id"]) == key
            ):
                raise ValueError("Previously reviewed African evidence changed")
        merged = [r for r in old if (r["source"], r["source_form_id"]) not in keys] + records
        if write:
            profile.parent.mkdir(parents=True, exist_ok=True)
            profile.write_text(text)
            write_csv(ledger, merged)
        elif profile.read_text() != text or [{k: v for k, v in r.items() if v} for r in old] != [
            {k: v for k, v in r.items() if v} for r in merged
        ]:
            raise ValueError("African profile ledger differs from reviewed evidence")
        print(aid, source, len(records), "guarded finite-profile readings")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--review", type=Path, required=True)
    p.add_argument("--write", action="store_true")
    a = p.parse_args()
    compile_profiles(a.review, write=a.write)
