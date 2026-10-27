"""Reviewed additive source forms, with exact evidence and concept guards."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pandas as pd

from arcaverborum.intake_db import IntakeDB
from arcaverborum.phonology import normalize_segments
from arcaverborum.sources.wiktionary.pronunciations import ipa_segments

EVIDENCE_FIELDS = (
    "ID",
    "Dataset",
    "Language_ID",
    "Glottocode",
    "Parameter_ID",
    "Value",
    "Form",
    "Segments",
    "Cognacy",
    "Cognate_Detection_Method",
    "Cognate_Source",
    "Source",
    "Comment",
    "Loan",
    "Doubt",
    "Alignment",
    "Morpheme_Index",
    "Segment_Slice",
)


def evidence_hash(row):
    payload = {key: str(row.get(key, "") or "") for key in EVIDENCE_FIELDS}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def ledger(custom_dir):
    path = custom_dir / "supplements.csv"
    if not path.exists():
        return []
    with path.open() as handle:
        return list(csv.DictReader(handle))


def input_keys(custom_dir):
    return {(r["source_glottocode"].strip().lower(), r["source"]) for r in ledger(custom_dir)}


def scope_rule(decision, target):
    path = Path(__file__).parent / "data/pronunciation_scopes.csv"
    with path.open() as handle:
        rules = {r["scope"]: r for r in csv.DictReader(handle)}
    rule = rules.get(decision.get("pronunciation_scope"))
    if (
        not rule
        or rule["source_glottocode"] != decision["source_glottocode"]
        or rule["target_glottocode"] != target
        or rule["source_language_id"] != decision["source_language_id"]
        or json.loads(rule["tags"]) != json.loads(decision.get("pronunciation_tags") or "[]")
    ):
        raise ValueError("Pronunciation scope does not establish source identity")
    return rule


def reviewed_frames(custom_dir, intake, glottocode, param_index, concept_index):
    """Yield source-separated frames; fail closed on drift or uncertified segments.

    Ordinary admission requires canonical Glottocode equality. A pronunciation
    alternative can use only an explicitly registered source/target/tag scope.
    """
    decisions = ledger(custom_dir)
    keys = [(r["source"], r["source_form_id"], r.get("source_pronunciation_id", "")) for r in decisions]
    if len(set(keys)) != len(keys):
        raise ValueError("Duplicate supplemental source-form decision")
    if not decisions:
        return
    if isinstance(intake, Path):
        intake = pd.read_csv(intake, dtype=str, keep_default_na=False)
    for gc, source in sorted(input_keys(custom_dir)):
        if gc != glottocode.strip().lower():
            for decision in [r for r in decisions if r["source_glottocode"].strip().lower() == gc]:
                if not decision.get("pronunciation_scope"):
                    raise ValueError("Supplement source identity requires exact canonical Glottocode")
                scope_rule(decision, glottocode.strip().lower())
        if isinstance(intake, IntakeDB):
            frame = intake.slice(gc, source)
        else:
            mask = intake["Glottocode"].str.strip().str.lower().eq(gc) & intake["Dataset"].eq(source)
            frame = intake[mask].copy()
        chosen = []
        for decision in [r for r in decisions if (r["source_glottocode"].strip().lower(), r["source"]) == (gc, source)]:
            matches = frame[frame["ID"].eq(decision["source_form_id"])]
            if len(matches) != 1:
                raise ValueError("Supplement source form missing or duplicated: " + decision["source_form_id"])
            row = matches.iloc[0].to_dict()
            if (
                row["Language_ID"] != decision["source_language_id"]
                or evidence_hash(row) != decision["evidence_sha256"]
            ):
                raise ValueError("Supplement evidence changed: " + decision["source_form_id"])
            raw_cid = row.get("Concepticon_ID") or param_index.get(row["Parameter_ID"], ("", ""))[0]
            if raw_cid != decision["expected_source_concepticon_id"]:
                raise ValueError("Supplement source concept changed: " + row["Parameter_ID"])
            cid = decision["concept_id"]
            if cid not in concept_index or decision["decision"] != "admit" or not decision["rationale"]:
                raise ValueError("Supplement lacks a valid explicit sense decision")
            if decision.get("raw_ipa"):
                scope_rule(decision, glottocode.strip().lower())
                segments = ipa_segments(decision["raw_ipa"])
                if (
                    not segments
                    or not decision.get("pronunciation_lines")
                    or len(decision.get("dump_sha256", "")) != 64
                ):
                    raise ValueError("Pronunciation alternative lacks supplied evidence")
                row["Segments"] = segments
                for name in ("raw_ipa", "pronunciation_tags", "source_pronunciation_id"):
                    row["_" + name] = decision[name]
                row["Comment"] = "; ".join(
                    filter(
                        None,
                        [
                            row.get("Comment", ""),
                            "Scoped source pronunciation: "
                            + decision["raw_ipa"]
                            + "; tags "
                            + decision["pronunciation_tags"]
                            + "; lines "
                            + decision["pronunciation_lines"]
                            + "; dump "
                            + decision["dump_sha256"],
                        ],
                    )
                )
            _, status = normalize_segments(row["Segments"], row["Form"])
            if status != "source":
                raise ValueError("Supplement requires validated supplied segments")
            row["_concept_id_override"] = cid
            row["Concepticon_ID"] = concept_index[cid]
            row["Comment"] = "; ".join(
                filter(None, [row.get("Comment", ""), "Reviewed supplement: " + decision["rationale"]])
            )
            chosen.append(row)
        yield source, pd.DataFrame(chosen).fillna("")
