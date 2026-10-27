"""Review a versioned ABVD snapshot against accepted source membership.

Default writes a ledger; --apply pins candidates passing identity, overlay,
concept-retention and source-segmentation gates. Old intake remains available.
Run after appending the abvd2026 intake namespace. No cognate IDs are transferred.
"""

from __future__ import annotations

import argparse
import csv
import subprocess
from collections import defaultdict
from pathlib import Path

import pandas as pd
import yaml

from arcaverborum.concepts import load_concept_maps
from arcaverborum.score import compute_signals_for_group, load_weights, score_cognates_block, score_forms_block

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    expected = {
        "abvd": "2af9f4ef6fff6250e0a31f383f249c3c9cf42e55",
        "abvd2026": "81748db0c5fcf3bf1d8c8372b86df75c375e1f22",
    }
    for dataset, commit in expected.items():
        repository = ROOT / "raw/lexibank" / dataset
        actual = subprocess.check_output(["git", "-C", str(repository), "rev-parse", "HEAD"], text=True).strip()
        if actual != commit:
            raise ValueError("Unreviewed ABVD snapshot: " + dataset)
        subprocess.run(["git", "-C", str(repository), "diff", "--quiet", "HEAD", "--", "cldf"], check=True)
    glottolog = {r["ID"]: r for r in read(ROOT / "raw/glottolog/languages.csv")}
    index, _ = load_concept_maps()
    core = {r["concept_id"] for r in read(ROOT / "src/arcaverborum/data/concept_core.csv")}
    snapshots = {}
    for dataset in ("abvd", "abvd2026"):
        cldf = ROOT / "raw/lexibank" / dataset / "cldf"
        langs = {r["ID"]: r for r in read(cldf / "languages.csv")}
        forms = defaultdict(list)
        for row in read(cldf / "forms.csv"):
            forms[row["Language_ID"]].append(row)
        params = {r["ID"]: index.get(r["Concepticon_ID"], ("", ""))[0] for r in read(cldf / "parameters.csv")}
        snapshots[dataset] = langs, forms, params
    old_langs, old_forms, old_params = snapshots["abvd"]
    new_langs, new_forms, new_params = snapshots["abvd2026"]
    ledger = []
    selected = []
    for path in sorted((ROOT / "varieties").glob("*/config.yaml")):
        if not (path.parent / "generated/forms.csv").exists():
            continue
        cfg = yaml.safe_load(path.read_text())
        source = cfg["sources"]
        if source["transcription"] not in ("abvd", "abvd2026"):
            continue
        gc = source.get("source_glottocode") or cfg["glottocode"]
        lid = source.get("source_language_id", "").removeprefix("abvd_")
        previous = sorted(k for k, r in old_langs.items() if r["Glottocode"] == gc and (not lid or k == lid))
        # A canonical language can explicitly include its named dialect samples;
        # dialect varieties themselves receive exact-code samples only.
        candidates = sorted(
            k
            for k, r in new_langs.items()
            if (not lid or k == lid)
            and (
                r["Glottocode"] == gc
                or (
                    glottolog.get(gc, {}).get("Level") == "language"
                    and glottolog.get(r["Glottocode"], {}).get("Language_ID") == gc
                )
            )
        )
        before = [r for k in previous for r in old_forms[k]]
        after = [r for k in candidates for r in new_forms[k]]
        old_concepts = {old_params.get(r["Parameter_ID"], "") for r in before} - {""}
        new_concepts = {new_params.get(r["Parameter_ID"], "") for r in after} - {""}
        old_clean = {old_params.get(r["Parameter_ID"], "") for r in before if r["Segments"].strip()} - {""}
        new_clean = {new_params.get(r["Parameter_ID"], "") for r in after if r["Segments"].strip()} - {""}
        reasons = []
        if not after:
            reasons.append("no identity-compatible refreshed member")
        for name in ("forms.csv", "transcriptions.csv", "concept_map.csv", "cognates.csv"):
            custom = path.parent / "custom" / name
            if custom.exists() and read(custom):
                reasons.append("source-specific authored overlay: " + name)
        if old_concepts - new_concepts:
            reasons.append("mapped concept loss")
        if old_clean - new_clean:
            reasons.append("source-segmented concept loss")
        decision = "hold" if reasons else "promote"
        row = dict(
            av_id=cfg["av_id"],
            glottocode=gc,
            decision=decision,
            reason="; ".join(reasons) or "explicit members; canonical identity and concept coverage retained",
            old_members=";".join(previous),
            new_members=";".join(candidates),
            old_forms=len(before),
            new_forms=len(after),
            old_core=len(old_concepts & core),
            new_core=len(new_concepts & core),
            lost_concepts=";".join(sorted(old_concepts - new_concepts)),
            member_selection_changed=previous != candidates,
        )
        ledger.append(row)
        if decision == "promote" and args.apply and source["transcription"] == "abvd":
            source["transcription"] = "abvd2026"
            source["cognates"] = "abvd2026"
            source.pop("source_language_id", None)
            source["source_glottocodes"] = sorted({new_langs[k]["Glottocode"] for k in candidates})
            source["source_language_ids"] = ["abvd2026_" + k for k in candidates]
            cfg["pinned"] = True
            cfg["notes"] = (
                "Reviewed ABVD snapshot 81748db (2026-10-27); explicit canonical-language "
                "membership, including named dialect samples where applicable. Source cognates "
                "remain in abvd2026 namespace; previous ABVD judgments are not transferred. "
                "See docs/abvd_promotion_2026-10-27.csv."
            )
            path.write_text(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True))
            selected.append(
                dict(
                    av_id=cfg["av_id"],
                    transcription_source="abvd2026",
                    cognate_source="abvd2026",
                    locked_at="2026-10-27",
                    notes=cfg["notes"],
                )
            )
    report = ROOT / "docs/abvd_promotion_2026-10-27.csv"
    with report.open("w") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(ledger[0]))
        writer.writeheader()
        writer.writerows(ledger)
    write_identity_review(ledger)
    if selected:
        selection = ROOT / "src/arcaverborum/data/selection.csv"
        with selection.open("a") as handle:
            csv.DictWriter(handle, fieldnames=list(selected[0])).writerows(selected)
    if args.apply:
        rescore_promoted()
    print(
        "Reviewed",
        len(ledger),
        "promote",
        sum(r["decision"] == "promote" for r in ledger),
        "hold",
        sum(r["decision"] == "hold" for r in ledger),
        "applied",
        len(selected),
    )


def write_identity_review(ledger):
    promoted = {r["av_id"]: r for r in ledger}
    earlier = ROOT / "docs/source_refresh_2026-10-27/abvd/accepted_varieties.csv"
    rows = []
    for previous in read(earlier):
        if previous["member_selection_changed"] != "True":
            continue
        current = promoted.get(previous["av_id"])
        rows.append(
            dict(
                av_id=previous["av_id"],
                previous_exact_members=previous["old_members"],
                refreshed_exact_members=previous["new_members"],
                reviewed_members=current["new_members"] if current else "",
                decision=current["decision"] if current else "retain current transcription",
                rationale=(
                    "Reviewed canonical language/dialect membership; versioned transcription selection promoted."
                    if current
                    else "ABVD is not the current transcription source; no lexical or cognate block was transferred."
                ),
            )
        )
    path = ROOT / "docs/abvd_identity_review_2026-10-27.csv"
    with path.open("w") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def rescore_promoted():
    frames = []
    for part in pd.read_csv(ROOT / "intake/lexibank/forms.csv", dtype=str, keep_default_na=False, chunksize=200000):
        selected = part[part.Dataset == "abvd2026"]
        if not selected.empty:
            frames.append(selected)
    forms = pd.concat(frames, ignore_index=True)
    assert len(forms) == 349424
    assert forms.Comment.str.contains("Upstream contribution evidence:", regex=False).all()
    assert forms.Source.ne("").all()
    weights = load_weights()
    groups = {k: g for k, g in forms.groupby("Language_ID", sort=False)}
    count = 0
    for path in sorted((ROOT / "varieties").glob("*/config.yaml")):
        cfg = yaml.safe_load(path.read_text())
        if cfg["sources"]["transcription"] != "abvd2026":
            continue
        group = pd.concat([groups[k] for k in cfg["sources"]["source_language_ids"]], ignore_index=True)
        sig = compute_signals_for_group(group)
        cfg["scoring"]["forms_score"] = float(round(score_forms_block(sig, weights), 4))
        cfg["scoring"]["cognates_score"] = float(round(score_cognates_block(sig, weights), 4))
        # Membership review does not certify transcription or yield a gold tier.
        cfg["scoring"]["tier"] = "bronze"
        path.write_text(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True))
        count += 1
    print("Verified ABVD contribution provenance, rescored", count, "selections", flush=True)
    # Record the source commit rather than the upstream metadata's stale version string.
    p = ROOT / "intake/lexibank/metadata.csv"
    with p.open() as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        rows = list(reader)
    for row in rows:
        if row["Dataset"] == "abvd2026":
            row["Repository_Version"] = "81748db0c5fcf3bf1d8c8372b86df75c375e1f22"
    work = p.with_suffix(".staged.csv")
    with work.open("w") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    work.replace(p)


if __name__ == "__main__":
    main()
