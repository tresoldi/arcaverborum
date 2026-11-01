"""Independently recover broader labels, folds, baselines and exported scores."""

import argparse
import csv
import hashlib
import json
import math
import resource
import sqlite3
from collections import defaultdict
from pathlib import Path

from arcaverborum.colexification import sha, verify_database


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--build", type=Path, required=True)
    p.add_argument("--validation", type=Path, required=True)
    p.add_argument("--protocol", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    resource.setrlimit(resource.RLIMIT_AS, (256 * 1024**2, 256 * 1024**2))
    seal = verify_database(a.build)
    complete = json.loads((a.validation / "complete.json").read_text())
    for name, expected in complete["files"].items():
        assert sha(a.validation / name) == expected, name
    result = json.loads((a.validation / "results.json").read_text())
    protocol = json.loads(a.protocol.read_text())
    assert result["signature"] == complete["signature"]
    assert result["signature"]["database_sha256"] == seal["database_sha256"]
    assert result["signature"]["protocol_sha256"] == sha(a.protocol)
    db = sqlite3.connect(f"file:{a.validation / 'contexts.sqlite'}?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA cache_size=-8000")
    db.execute("PRAGMA temp_store=FILE")
    db.execute("PRAGMA mmap_size=0")
    assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    db.execute("CREATE TEMP TABLE expected_available(sid INTEGER,pair INTEGER,PRIMARY KEY(sid,pair))")
    db.execute("CREATE TEMP TABLE expected_positive(sid INTEGER,pair INTEGER,PRIMARY KEY(sid,pair))")
    core = sqlite3.connect(f"file:{a.build / 'index.sqlite'}?mode=ro", uri=True)
    core.execute("PRAGMA cache_size=-8000")
    core.execute("PRAGMA temp_store=FILE")
    for i, pair in enumerate(protocol["pairs"]):
        args = (pair["a"], pair["b"])
        available = core.execute(
            """SELECT DISTINCT ra.sid FROM valid ra JOIN valid rb ON rb.sid=ra.sid
            WHERE ra.layer='segmented' AND rb.layer='segmented' AND ra.cid=? AND rb.cid=?
            AND ra.semantic<>'unreviewed_dictionary_sense' AND rb.semantic<>'unreviewed_dictionary_sense'
            AND ra.fid<>rb.fid AND ra.param<>rb.param""",
            args,
        )
        db.executemany("INSERT INTO expected_available VALUES(?,?)", ((r[0], i) for r in available))
        positive = core.execute(
            """SELECT DISTINCT w.sid FROM witnesses w
            JOIN readings ra ON ra.id=w.ra JOIN readings rb ON rb.id=w.rb
            WHERE w.layer='segmented' AND w.kind='observed' AND w.a=? AND w.b=?
            AND ra.semantic<>'unreviewed_dictionary_sense' AND rb.semantic<>'unreviewed_dictionary_sense'""",
            args,
        )
        db.executemany("INSERT INTO expected_positive VALUES(?,?)", ((r[0], i) for r in positive))
    for table, condition in [("expected_available", "y IS NOT NULL"), ("expected_positive", "y=1")]:
        query = "SELECT sid,pair FROM contexts WHERE " + condition
        assert not db.execute("SELECT * FROM (" + query + " EXCEPT SELECT * FROM " + table + ") LIMIT 1").fetchall()
        assert not db.execute("SELECT * FROM (SELECT * FROM " + table + " EXCEPT " + query + ") LIMIT 1").fetchall()
    totals = {}
    pair_totals = {}
    tasks = [
        ("resource_block", "block", "fold_block"),
        ("family", "family", "fold_family"),
        ("questionnaire_lineage_sensitivity", "block", "fold_questionnaire"),
    ]
    seed = protocol["evaluation"]["hash_seed"]
    for row in db.execute("SELECT * FROM contexts ORDER BY seq"):
        for task, field, column in tasks:
            group = row[field]
            if task == "questionnaire_lineage_sensitivity" and group in {"ids", "wold"}:
                group = "ids_wold"
            prefix = "resource_block" if task == "questionnaire_lineage_sensitivity" else task
            expected = (
                int(hashlib.sha256((seed + "/" + prefix + "/" + group).encode()).hexdigest()[:12], 16) % 5
                if group
                else None
            )
            assert row[column] == expected
    for task, _, column in tasks:
        totals[task] = {
            (r[0], r[1]): (r[2], r[3])
            for r in db.execute(
                "SELECT role,"
                + column
                + ",COUNT(*),SUM(y) FROM contexts WHERE y IS NOT NULL AND "
                + column
                + " IS NOT NULL GROUP BY role,"
                + column
            )
        }
        pair_totals[task] = {
            (r[0], r[1]): (r[2], r[3])
            for r in db.execute(
                "SELECT pair,"
                + column
                + ",COUNT(*),SUM(y) FROM contexts WHERE y IS NOT NULL AND "
                + column
                + " IS NOT NULL GROUP BY pair,"
                + column
            )
        }
    sums = defaultdict(lambda: [0, 0.0, 0.0])
    prediction_count = 0
    last_seq, context = None, None
    export_cursor = iter(db.execute("SELECT * FROM predictions ORDER BY task,panel,fold,seq,model"))
    with (a.validation / "predictions.csv").open() as h:
        for row in csv.DictReader(h):
            persisted = next(export_cursor)
            assert list(row.values()) == ["" if x is None else str(x) for x in persisted]
            seq = int(row["seq"])
            if seq != last_seq:
                context = db.execute("SELECT * FROM contexts WHERE seq=?", (seq,)).fetchone()
                last_seq = seq
            task, panel, held, model = row["task"], row["panel"], int(row["fold"]), row["model"]
            column = next(t[2] for t in tasks if t[0] == task)
            assert context["y"] is not None and context[column] == held and context["role"] == panel
            assert int(row["pair"]) == context["pair"]
            n = sum(v[0] for (p, f), v in totals[task].items() if p == panel and f != held)
            k = sum(v[1] for (p, f), v in totals[task].items() if p == panel and f != held)
            assert int(row["train_n"]) == n
            probability = float(row["probability"])
            assert math.isfinite(probability) and 0 <= probability <= 1
            pooled = (k + 1) / (n + 2)
            tn = sum(v[0] for (p, f), v in pair_totals[task].items() if p == context["pair"] and f != held)
            tk = sum(v[1] for (p, f), v in pair_totals[task].items() if p == context["pair"] and f != held)
            expected = dict(
                pooled_laplace=pooled,
                pair_laplace=(tk + 1) / (tn + 2),
                pair_shrinkage_10=(tk + 10 * pooled) / (tn + 10),
            ).get(model)
            if expected is not None:
                assert abs(probability - expected) < 1e-12
            prob = min(1 - 1e-6, max(1e-6, probability))
            y = context["y"]
            value = sums[panel, task, model]
            value[0] += 1
            value[1] -= y * math.log2(prob) + (1 - y) * math.log2(1 - prob)
            value[2] += (prob - y) ** 2
            prediction_count += 1
    assert prediction_count == db.execute("SELECT COUNT(*) FROM predictions").fetchone()[0]
    for (panel, task, model), (n, ll, brier) in sums.items():
        logged = result["evaluation"][panel][task]["models"][model]
        assert logged["n"] == n and abs(logged["log_loss_bits"] - ll / n) < 1e-10
        assert abs(logged["brier"] - brier / n) < 1e-10
    checks = dict(
        contexts=db.execute("SELECT COUNT(*) FROM contexts").fetchone()[0],
        comparable=db.execute("SELECT COUNT(*) FROM expected_available").fetchone()[0],
        positive=db.execute("SELECT COUNT(*) FROM expected_positive").fetchone()[0],
        predictions=prediction_count,
        score_groups=len(sums),
        independent_sql_labels=True,
        folds_recovered=True,
        three_baselines_recovered=True,
        scores_recovered=True,
        expert_gold=False,
        signature=result["signature"],
        sqlite_integrity="ok",
        memory_limit_mb=256,
    )
    a.output.write_text(json.dumps(checks, indent=2) + "\n")
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()
