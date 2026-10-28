"""Compile the frozen African dictionary reviews after staging and intake append.

Writes written-only admissions and delegates derived readings to the finite-profile
compiler. Promotion to a primary remains a separate, preservation-reviewed choice.
"""

from __future__ import annotations

import argparse
import json

from compile_african_profiles import ROOT, compile_profiles, read, write_csv
from compile_supplements import merge_reviews

from arcaverborum.supplements import evidence_hash


def compile_lexica(*, root=ROOT, write=False):
    profiles = []
    written = {}
    for spec in json.loads((root / "src/arcaverborum/data/african_lexical_sources.json").read_text()):
        source = spec["dataset"]
        stage = root / "raw/curation" / ("stage-" + source) / "lexibank"
        forms = {r["ID"]: r for r in read(stage / "forms.csv")}
        params = {r["ID"]: r for r in read(stage / "parameters_raw.csv")}
        for r in read(root / spec["review"]):
            if r["decision"] != "admit":
                continue
            row = forms[source + "_" + r["source_form_id"]]
            param = params[row["Parameter_ID"]]
            if row["Form"] != r["Form"] or param["Name"] != r["source_sense"] or row["Glottocode"] != r["glottocode"]:
                raise ValueError("Staged African evidence differs from review")
            native = json.loads(row["Comment"])
            if native["native_sha256"] != r["native_sha256"] or native["source_member"] != r["member"]:
                raise ValueError("Staged African record/member differs from review")
            record = dict(
                source=source,
                source_form_id=row["ID"],
                source_language_id=row["Language_ID"],
                source_glottocode=row["Glottocode"],
                evidence_sha256=evidence_hash(row),
                expected_source_concepticon_id=param["Concepticon_ID"],
                concept_id=r["concept_id"],
                decision="admit",
                rationale=" ".join(filter(None, [r["rationale"], r.get("reading_notes", "")])),
            )
            if r.get("segments"):
                profiles.append(
                    dict(
                        record, av_id=r["av_id"], Form=r["Form"], source_sense=r["source_sense"], segments=r["segments"]
                    )
                )
            else:
                record["transcription_policy"] = "orthographic_only"
                written.setdefault(r["av_id"], []).append(record)
    for aid, records in written.items():
        custom = root / "varieties" / aid / "custom"
        # New-language primaries are explicitly bounded written-only slices.
        path = custom / ("primary.csv" if aid in {"atl-wamey", "atl-kam"} else "supplements.csv")
        old = read(path) if path.exists() else []
        merged = merge_reviews(old, records)
        if write:
            write_csv(path, merged)
        elif [{k: v for k, v in r.items() if v} for r in merged] != [{k: v for k, v in r.items() if v} for r in old]:
            raise ValueError("African written ledger differs from review")
    path = root / "raw/curation/africa-profile-admissions.csv"
    write_csv(path, profiles)
    compile_profiles(path, root=root, write=write)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--write", action="store_true")
    compile_lexica(write=p.parse_args().write)
