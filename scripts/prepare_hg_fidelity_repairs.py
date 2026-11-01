"""Prepare guarded, source-column-backed repairs for three reviewed HG members.

Writes a review packet, never edits intake or varieties. Ambiguous notation and
alternative strings stay held. Database phonemicization is retained as supplied,
not certified as original field phonetics or a resolution of phonological theory.
"""

import argparse
import csv
import json
import sqlite3
import unicodedata
from collections import Counter
from pathlib import Path

from arcaverborum.colexification import digest, sha
from arcaverborum.sources.wiktionary.pronunciations import ipa_segments
from arcaverborum.supplements import evidence_hash
from arcaverborum.variety import CUSTOM_TRANSCRIPTION_FIELDS

MEMBERS = [("sab-piaroa", "piar1243", "130"), ("tuc-wa-ikhana", "pira1254", "137"), ("ara-yucuna", "yucu1253", "65")]


def write(path, rows, fields):
    with path.open("w") as h:
        writer = csv.DictWriter(h, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise ValueError("Use a new repair packet directory")
    a.output.mkdir(parents=True)
    native = a.root / "raw/lexibank/huntergatherer"
    cldf = native / "cldf/forms.csv"
    forms = {r["ID"]: r for r in csv.DictReader(cldf.open()) if r["Language_ID"] in {m[2] for m in MEMBERS}}
    parameters = {r["ID"]: r for r in csv.DictReader((native / "cldf/parameters.csv").open())}
    db = sqlite3.connect(f"file:{a.root / 'intake/intake.sqlite'}?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    decisions, holds = [], []
    sources = {str(cldf.relative_to(a.root)): sha(cldf)}
    for av, gc, member in MEMBERS:
        original = native / f"raw/{member}.json"
        sources[str(original.relative_to(a.root))] = sha(original)
        tables = json.loads(original.read_text())["tables"]
        native_rows = [
            dict(zip(t["header"], row))
            for name, t in tables.items()
            if name in {"basic", "flora", "cult"}
            for row in t["rows"]
        ]
        output = []
        for row in db.execute("SELECT * FROM forms WHERE gc_lc=? AND Dataset=?", (gc, "huntergatherer")):
            row = dict(row)
            if row["Language_ID"] != "huntergatherer_" + member:
                continue
            if not row["Form"] or not row["Value"].startswith(row["Form"] + "'"):
                continue
            supplied = forms[row["ID"].removeprefix("huntergatherer_")]
            param = parameters[supplied["Parameter_ID"]]
            candidates = [
                r
                for r in native_rows
                if r["English"][0].rsplit("/", 1)[-1] == param["Database_ID"]
                and r["Orthographic Form"].strip() == row["Value"]
            ]
            reason = ""
            if len(candidates) != 1:
                reason = "Native feature and spelling do not identify exactly one row"
            elif candidates[0]["Phonemicized Form"].strip() != supplied["Phonemic"].strip():
                reason = "Native phonemic column and CLDF disagree"
            elif any(c in row["Value"] for c in "()[]{},;:/\n"):
                reason = "Alternatives, annotations or unresolved separator"
            elif any(unicodedata.category(c)[0] not in "LM" and c not in "' -ʔɁ" for c in row["Value"]):
                reason = "Unreviewed spelling symbol"
            if reason:
                holds.append(
                    dict(
                        av_id=av,
                        source_form_id=row["ID"],
                        reason=reason,
                        Value=row["Value"],
                        Phonemic=supplied["Phonemic"],
                    )
                )
                continue
            raw = supplied["Phonemic"].strip()
            segments = ""
            if member != "137" and raw and not any(c in raw for c in "'0123456789\uf7f3-:=?"):
                segments = ipa_segments(raw)
            policy = "supplied_phonemic" if segments else "orthographic_only"
            note = (
                f"CINF-02: full native spelling restored; policy {policy}; database phonemicization "
                f"{raw!r}, not independently field-verified; native feature {param['Database_ID']}; "
                f"raw/{member}.json SHA256 {sha(original)}; superseded parser Form {row['Form']!r}, "
                f"Segments {row['Segments']!r}. Original spelling, source IDs and cognacy retained."
            )
            decision = dict.fromkeys(CUSTOM_TRANSCRIPTION_FIELDS, "")
            decision.update(
                source_form_id=row["ID"],
                Form=row["Value"],
                Segments=segments,
                raw_ipa=raw if segments else "",
                transcription_policy=policy,
                Comment="; ".join(s for s in [row.get("Comment", ""), note] if s),
                expected_evidence_sha256=evidence_hash(row),
                notes=f"Native CLDF record SHA256 {digest(supplied)}; source URL "
                f"https://huntergatherer.la.utexas.edu/languages/language/{member}",
            )
            output.append(decision)
            decisions.append(
                dict(
                    av_id=av,
                    source_form_id=row["ID"],
                    policy=policy,
                    native_row_sha256=digest(candidates[0]),
                    phonemic=raw,
                )
            )
        write(a.output / f"{av}.csv", output, CUSTOM_TRANSCRIPTION_FIELDS)
    write(a.output / "holds.csv", holds, ["av_id", "source_form_id", "reason", "Value", "Phonemic"])
    summary = dict(
        sources=sources,
        decisions=decisions,
        holds=len(holds),
        by_variety={av: dict(Counter(d["policy"] for d in decisions if d["av_id"] == av)) for av, _, _ in MEMBERS},
        files={p.name: sha(p) for p in a.output.glob("*.csv")},
    )
    (a.output / "manifest.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "decisions"}, indent=2))


if __name__ == "__main__":
    main()
