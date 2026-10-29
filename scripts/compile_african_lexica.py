"""Compile the frozen African dictionary reviews after staging and intake append.

Writes written-only admissions and delegates derived readings to the finite-profile
compiler. Promotion to a primary remains a separate, preservation-reviewed choice.
"""

from __future__ import annotations

import argparse
import json
import re

import yaml
from compile_african_profiles import ROOT, compile_profiles, read, write_csv
from compile_supplements import merge_reviews

from arcaverborum.supplements import evidence_hash


def compile_lexica(*, root=ROOT, write=False):
    concepts = {r["concept_id"]: r for r in read(root / "src/arcaverborum/data/concepts.csv")}
    unmaps = {}
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
            accepted_cid = r.get("accepted_concept_id") or r["concept_id"]
            original = native["original"]
            if source == "fweoriginal":
                source_pos = original["native"].split("\\relax")[1].strip()
            elif "pos" in original:
                source_pos = original["pos"].strip()
            elif "entry" in original:
                source_pos = original["entry"].get("Part_Of_Speech", "")
            elif "record" in original:
                source_pos = original["record"].get("CGR", "")
            else:
                source_pos = "|".join(re.findall(r"\\fmtPOS\{([^}]+)\}", original.get("native", "")))
            source_pos = source_pos.lower()
            target_pos = concepts[accepted_cid]["pos"]
            if r.get("accepted_action") != "unmap" and (
                (source_pos.startswith("v") and target_pos == "n") or (source_pos.startswith("n") and target_pos == "v")
            ):
                raise ValueError("Dictionary source/target POS mismatch: " + row["ID"])
            source_cid = original.get("sense", {}).get("Concepticon_ID", "")
            if (
                source_cid
                and source_cid != concepts[accepted_cid]["concepticon_id"]
                and r.get("accepted_action") not in {"map", "unmap"}
            ):
                raise ValueError("Original dictionary comparison meaning needs explicit review: " + row["ID"])
            if r.get("accepted_action") == "unmap":
                unmaps.setdefault(r["av_id"], []).append(
                    dict(
                        source_form_id=row["ID"],
                        Parameter_ID=row["Parameter_ID"],
                        expected_form=row["Form"],
                        Concepticon_ID="",
                        Concepticon_Gloss="",
                        concept_id="",
                        action="unmap",
                        notes=r["accepted_mapping_notes"],
                    )
                )
            record = dict(
                source=source,
                source_form_id=row["ID"],
                source_language_id=row["Language_ID"],
                source_glottocode=row["Glottocode"],
                evidence_sha256=evidence_hash(row),
                expected_source_concepticon_id=param["Concepticon_ID"],
                concept_id=accepted_cid,
                decision="admit",
                rationale=" ".join(
                    filter(None, [r["rationale"], r.get("reading_notes", ""), r.get("accepted_mapping_notes", "")])
                ),
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
    for aid, rows in unmaps.items():
        path = root / "varieties" / aid / "custom/concept_map.csv"
        old = read(path) if path.exists() else []
        ids = {r["source_form_id"] for r in rows}
        merged = [r for r in old if r.get("source_form_id") not in ids] + rows
        if write:
            write_csv(path, merged)
        elif merged != old:
            raise ValueError("African unmapping overlay differs from review")
    for aid, records in written.items():
        custom = root / "varieties" / aid / "custom"
        config = yaml.safe_load((custom.parent / "config.yaml").read_text())
        is_primary = config["sources"]["transcription"] == records[0]["source"]
        has_profiles = any(r["av_id"] == aid and r["source"] == records[0]["source"] for r in profiles)
        path = custom / ("primary.csv" if is_primary and not has_profiles else "supplements.csv")
        old = read(path) if path.exists() else []
        merged = merge_reviews(old, records)
        if write:
            write_csv(path, merged)
        elif [{k: v for k, v in r.items() if v} for r in merged] != [{k: v for k, v in r.items() if v} for r in old]:
            raise ValueError("African written ledger differs from review")
    path = root / "raw/curation/africa-profile-admissions.csv"
    write_csv(path, profiles)
    compile_profiles(path, root=root, write=write)
    # A recovered reading enriches the same lexical identity; do not retain a
    # duplicate written copy when it moves into a guarded profile primary.
    for aid in {r["av_id"] for r in profiles}:
        custom = root / "varieties" / aid / "custom"
        primary = custom / "primary.csv"
        if not primary.exists():
            continue
        old_primary = read(primary)
        source = {r["source"] for r in old_primary}
        if len(source) != 1:
            raise ValueError("Primary source scope ambiguous")
        written_keys = {(r["source"], r["source_form_id"]) for r in written.get(aid, [])}
        new_primary = [r for r in old_primary if (r["source"], r["source_form_id"]) not in written_keys]
        profiled = {(r["source"], r["source_form_id"]): r for r in new_primary if r.get("profile_file")}
        supplement = custom / "supplements.csv"
        old_supp = read(supplement) if supplement.exists() else []
        new_supp = []
        for r in old_supp:
            key = r["source"], r["source_form_id"]
            if key in profiled and not r.get("source_pronunciation_id"):
                if (
                    r.get("transcription_policy") != "orthographic_only"
                    or r["evidence_sha256"] != profiled[key]["evidence_sha256"]
                ):
                    raise ValueError("Primary recovery would erase distinct supplemental evidence")
            else:
                new_supp.append(r)
        if write:
            if new_primary != old_primary:
                write_csv(primary, new_primary)
            if new_supp != old_supp:
                write_csv(supplement, new_supp)
        elif new_primary != old_primary or new_supp != old_supp:
            raise ValueError("Recovered primary still duplicates written evidence")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--write", action="store_true")
    compile_lexica(write=p.parse_args().write)
