"""Independent SQL/count/score checks for a sealed exploratory inference pilot."""

import argparse
import csv
import json
import math
import resource
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

from arcaverborum.colexification import sha, verify_database


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--build", type=Path, required=True)
    p.add_argument("--pilot", type=Path, required=True)
    p.add_argument("--baseline", type=Path)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    resource.setrlimit(resource.RLIMIT_AS, (256 * 1024**2, 256 * 1024**2))
    seal = verify_database(a.build)
    complete = json.loads((a.pilot / "complete.json").read_text())
    for name, digest in complete["files"].items():
        if sha(a.pilot / name) != digest:
            raise ValueError("Pilot artifact hash mismatch: " + name)
    result = json.loads((a.pilot / "results.json").read_text())
    if (
        result["signature"] != complete["signature"]
        or result["signature"]["database_sha256"] != seal["database_sha256"]
    ):
        raise ValueError("Pilot/core binding differs")
    db = sqlite3.connect(f"file:{a.build / 'index.sqlite'}?mode=ro", uri=True)
    db.execute("PRAGMA cache_size=-16000")
    db.execute("PRAGMA temp_store=FILE")
    expected_pos = set()
    expected_available = set()
    for i, pair in enumerate(result["protocol"]["pairs"]):
        args = (pair["a"], pair["b"])
        for (sid,) in db.execute(
            """SELECT DISTINCT w.sid FROM witnesses w
          JOIN readings ra ON ra.id=w.ra JOIN readings rb ON rb.id=w.rb
          WHERE w.layer='segmented' AND w.kind='observed' AND w.a=? AND w.b=?
          AND ra.semantic<>'unreviewed_dictionary_sense' AND rb.semantic<>'unreviewed_dictionary_sense' """,
            args,
        ):
            expected_pos.add((sid, i))
        for (sid,) in db.execute(
            """SELECT DISTINCT ra.sid FROM valid ra JOIN valid rb ON rb.sid=ra.sid
          WHERE ra.layer='segmented' AND rb.layer='segmented' AND ra.cid=? AND rb.cid=?
          AND ra.semantic<>'unreviewed_dictionary_sense' AND rb.semantic<>'unreviewed_dictionary_sense'
          AND ra.fid<>rb.fid AND ra.param<>rb.param""",
            args,
        ):
            expected_available.add((sid, i))
    observed_pos = set()
    available = {}
    count = 0
    fold_totals = defaultdict(Counter)
    with (a.pilot / "contexts.csv").open() as h:
        for r in csv.DictReader(h):
            count += 1
            key = int(r["sid"]), int(r["pair"])
            if r["y"] == "":
                continue
            y = int(r["y"])
            available[key] = (y, r["family"], r["block"])
            if y:
                observed_pos.add(key)
            for task, field in [("family", "family"), ("resource_block", "block")]:
                if not r[field]:
                    continue
                fold = result["evaluation"][task]["group_assignments"][r[field]]
                fold_totals[task]["n"] += 1
                fold_totals[task]["p"] += y
                fold_totals[task]["n", fold] += 1
                fold_totals[task]["p", fold] += y
    if observed_pos != expected_pos or set(available) != expected_available:
        raise AssertionError("Independent SQL labels/comparability disagree")
    sums = defaultdict(lambda: [0, 0.0, 0.0])
    fold_scores = defaultdict(lambda: [0, 0.0, 0.0])
    seen = set()
    with (a.pilot / "predictions.csv").open() as h:
        for r in csv.DictReader(h):
            key = int(r["sid"]), int(r["pair"])
            y, family, block = available[key]
            task = r["task"]
            group = family if task == "family" else block
            fold = int(r["fold"])
            if y != int(r["y"]) or group != r["heldout_group"]:
                raise AssertionError("Prediction target/group changed")
            if result["evaluation"][task]["group_assignments"][group] != fold:
                raise AssertionError("Test group leakage")
            unique = task, r["model"], *key
            if unique in seen:
                raise AssertionError("Duplicate test prediction")
            seen.add(unique)
            totals = fold_totals[task]
            n = totals["n"] - totals["n", fold]
            positive = totals["p"] - totals["p", fold]
            if n != int(r["train_n"]) or positive != int(r["train_positive"]):
                raise AssertionError("Training counts include test fold")
            pred = float(r["probability"])
            if r["model"] == "pooled_laplace" and abs(pred - (positive + 1) / (n + 2)) > 1e-12:
                raise AssertionError("Baseline uses held-out labels")
            pred = min(1 - 1e-6, max(1e-6, pred))
            s = sums[task, r["model"]]
            s[0] += 1
            s[1] -= y * math.log2(pred) + (1 - y) * math.log2(1 - pred)
            s[2] += (y - pred) ** 2
            f = fold_scores[task, fold, r["model"]]
            f[0] += 1
            f[1] -= y * math.log2(pred) + (1 - y) * math.log2(1 - pred)
            f[2] += (y - pred) ** 2
    for (task, name), (n, ll, brier) in sums.items():
        published = result["evaluation"][task]["models"][name]
        if (
            n != published["n"]
            or abs(ll / n - published["log_loss_bits"]) > 1e-10
            or abs(brier / n - published["brier"]) > 1e-10
        ):
            raise AssertionError("Independent predictive scores differ")
    audit = list(csv.DictReader((a.pilot / "audit_packet.csv").open()))
    if any(r["reviewer"] or r["decision"] or r["review_status"] != "pending_independent_review" for r in audit):
        raise AssertionError("Generated packet pretends independent adjudication")
    pair_index = {(p["a"], p["b"]): i for i, p in enumerate(result["protocol"]["pairs"])}
    for p in result["incidence_null"]["pairs"]:
        i = pair_index[p["a"], p["b"]]
        if not p["comparable_families"] and p["empirical_upper_tail"] is not None:
            raise AssertionError("Unknown comparison given a null tail")
        if p["comparable_families"]:
            tail = (1 + sum(v >= p["observed_families"] for v in p["null_counts"])) / (1 + len(p["null_counts"]))
            if abs(tail - p["empirical_upper_tail"]) > 1e-12:
                raise AssertionError("Permutation tail arithmetic differs")
        if not result["incidence_null"]["exclusions"]["concepts_with_shared_native_ids"]:
            families = {r[1] for (sid, pi), r in available.items() if pi == i and r[1]}
            positives = {r[1] for (sid, pi), r in available.items() if pi == i and r[1] and r[0]}
            if len(families) != p["comparable_families"] or len(positives) != p["observed_families"]:
                raise AssertionError("Null population differs from declared admissible contexts")
    for p in result["bayesian_sensitivity"]["results"]:
        i = pair_index[p["a"], p["b"]]
        chosen = [available[sid, i] for sid in p["selected_scope_ids"]]
        if len(chosen) != p["known_families"] or len({r[1] for r in chosen}) != len(chosen):
            raise AssertionError("Repeated families enter Bayesian sensitivity")
        if sum(r[0] for r in chosen) != p["positive"]:
            raise AssertionError("Bayesian selected outcome differs")
        if not chosen and p["evidence_status"] != "prior_only_no_comparable_families":
            raise AssertionError("Prior-only output not labelled")
        if not 0 <= p["next_independent_trial_information_bits"] <= p["predictive_entropy_bits"] + 1e-9:
            raise AssertionError("Information decomposition outside entropy bound")
    comparison = {}
    if a.baseline:
        verify_database(a.baseline)
        db.execute("ATTACH DATABASE ? AS previous", (str(a.baseline / "index.sqlite"),))
        comparison["new_reported_pairs"] = db.execute("""SELECT COUNT(*) FROM
          (SELECT layer,kind,a,b FROM edges EXCEPT SELECT layer,kind,a,b FROM previous.edges)""").fetchone()[0]
        comparison["removed_reported_pairs"] = db.execute("""SELECT COUNT(*) FROM
          (SELECT layer,kind,a,b FROM previous.edges EXCEPT SELECT layer,kind,a,b FROM edges)""").fetchone()[0]
        old = json.loads((a.baseline / "public/manifest.json").read_text())
        new = json.loads((a.build / "public/manifest.json").read_text())
        comparison["lexical_aggregate_unchanged"] = (
            old["inputs"]["output/aggregate/forms.csv"] == new["inputs"]["output/aggregate/forms.csv"]
        )
        if not comparison["lexical_aggregate_unchanged"] or comparison["new_reported_pairs"]:
            raise AssertionError("Unexpected lexical changes or added identities")
    checks = dict(
        core=seal["build_id"],
        signature=result["signature"],
        contexts=count,
        available=len(available),
        positive=len(expected_pos),
        predictions=len(seen),
        audit_rows=len(audit),
        independent_sql_labels=True,
        independent_scores=True,
        train_test_counts=True,
        null_frame_and_arithmetic=True,
        bayesian_context_counts=True,
        fold_scores={
            "|".join(map(str, k)): dict(n=v[0], log_loss_bits=v[1] / v[0], brier=v[2] / v[0])
            for k, v in fold_scores.items()
        },
        independent_linguistic_adjudication=False,
        comparison=comparison,
        peak_rss_mb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
    )
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(checks, indent=2) + "\n")
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()
