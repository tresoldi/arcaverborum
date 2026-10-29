"""Inventory exact source codes absent from accepted output; never equate leads with languages."""

from __future__ import annotations

import argparse
import collections
import csv
import gzip
import json
import sqlite3
from pathlib import Path

R = Path(__file__).resolve().parents[1]


def rd(path):
    with (R / path).open() as handle:
        return list(csv.DictReader(handle))


def wr(path, rows):
    path.parent.mkdir(exist_ok=True, parents=True)
    with path.open("w") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=R / "output/report/missing_languages.csv")
    args = parser.parse_args()

    c = json.load(gzip.open(R / "web/data/catalog.json.gz"))
    accepted = {r["Glottocode"] for r in c["languages"]}
    registry = rd("src/arcaverborum/data/varieties.csv")
    bygc = collections.defaultdict(list)
    for r in registry:
        bygc[r["glottocode"]].append(r)
    glos = {r["Glottocode"]: r for r in rd("raw/glottolog/languages.csv")}
    langs = {r["ID"]: r for p in (R / "intake").glob("*/languages.csv") for r in rd(p)}
    db = sqlite3.connect((R / "intake/intake.sqlite").as_uri() + "?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    out = []
    for x in db.execute(
        'select Dataset,Language_ID,Glottocode,count(*) as rows,'
        'sum(case when Segments!="" then 1 else 0 end) as segmented '
        'from forms group by Dataset,Language_ID,Glottocode'
    ):
        x = dict(x)
        gc = x["Glottocode"]
        if not gc or gc in accepted:
            continue
        language = langs.get(x["Language_ID"], {})
        g = glos.get(gc, {})
        level = g.get("Level", "")
        decision = "review_language" if level == "language" else "exclude_from_new_language_count"
        if language.get("Name", "").lower() in {r["Name"].lower() for r in c["languages"]}:
            decision = "review_existing_name_identity"
        out.append(
            dict(
                glottolog_level=level,
                canonical_parent_language=g.get("Language_ID", ""),
                source=x["Dataset"],
                source_language_id=x["Language_ID"],
                glottocode=gc,
                name=language.get("Name", ""),
                macroarea=language.get("Macroarea", "") or g.get("Macroarea", ""),
                rows=x["rows"],
                raw_segmented=x["segmented"],
                registered_ids=";".join(r["av_id"] for r in bygc[gc]),
                glottolog_metadata_present=bool(g),
                decision=decision,
                rationale=("Absent exact Glottocode from accepted catalog; language level, ancestry, aliases, "
                    "original evidence and terms still require review. Segmented input is not quality certification."),
            )
        )
    out.sort(key=lambda r: (r["macroarea"] != "South America", -r["raw_segmented"], -r["rows"], r["name"]))
    wr(args.output, out)
    print(len(out), "missing exact-code members")
    print(collections.Counter(r["glottolog_level"] for r in out))


if __name__ == "__main__":
    main()
