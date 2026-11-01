"""SQLite-backed broader inference, with separately fitted sampling panels.

Recorded identity is the target. Source/publication and error diagnostics do not
constitute linguistic gold labels, empirical error rates or calibrated polysemy.
"""

from __future__ import annotations

import csv
import json
import math
import sqlite3
from collections import Counter
from pathlib import Path

from arcaverborum.colexification import digest, sha, verify_database
from arcaverborum.colexification_inference import (
    bayesian,
    contexts,
    incidence_null,
    rank,
    ridge_predict,
    scores,
)


class SqlRows:
    """Reiterable bounded query; never caches observations."""

    def __init__(self, db, query, args=()):
        self.db, self.query, self.args = db, query, args

    def __iter__(self):
        cursor = self.db.execute(self.query, self.args)
        names = [col[0] for col in cursor.description]
        for row in cursor:
            yield dict(zip(names, row))

    def __len__(self):
        return self.db.execute("SELECT COUNT(*) FROM (" + self.query + ")", self.args).fetchone()[0]


def fold(group, task, seed):
    return int(rank(seed + "/" + task + "/" + group)[:12], 16) % 5 if group else None


def error_sensitivity(rows, rates):
    n = 0
    losses = [0.0, 0.0]
    squares = [0.0, 0.0]
    for row in rows:
        p = min(1 - 1e-6, max(1e-6, row["probability"]))
        for i, y in enumerate([row["y"], 1 - row["y"]]):
            losses[i] -= y * math.log2(p) + (1 - y) * math.log2(1 - p)
            squares[i] += (p - y) ** 2
        n += 1
    return dict(
        interpretation=(
            "Expected score under hypothetical symmetric held-out label flips; no refitting or estimated error rate"
        ),
        n=n,
        rates=[
            dict(
                flip_rate=e,
                log_loss_bits=((1 - e) * losses[0] + e * losses[1]) / n if n else None,
                brier=((1 - e) * squares[0] + e * squares[1]) / n if n else None,
            )
            for e in rates
        ],
    )


def evaluate(db, protocol):
    results = {}
    count = len(protocol["pairs"])
    panels = sorted({p["role"] for p in protocol["pairs"]})
    for panel in panels:
        results[panel] = {}
        for task, column in [
            ("resource_block", "fold_block"),
            ("family", "fold_family"),
            ("questionnaire_lineage_sensitivity", "fold_questionnaire"),
        ]:
            base = "SELECT * FROM contexts WHERE role=? AND y IS NOT NULL AND " + column + " IS NOT NULL"
            details = []
            for held in range(5):
                train = SqlRows(db, base + " AND " + column + "<>? ORDER BY seq", (panel, held))
                test = SqlRows(db, base + " AND " + column + "=? ORDER BY seq", (panel, held))
                ntrain, ntest = len(train), len(test)
                if not ntrain or not ntest:
                    continue
                pos = sum(r["y"] for r in train)
                pooled = (pos + 1) / (ntrain + 2)
                totals, positives = Counter(), Counter()
                for r in train:
                    totals[r["pair"]] += 1
                    positives[r["pair"]] += r["y"]
                ridge = iter(ridge_predict(train, test, count, streaming=True))
                with db:
                    for row in test:
                        pair = row["pair"]
                        predictions = dict(
                            pooled_laplace=pooled,
                            pair_laplace=(positives[pair] + 1) / (totals[pair] + 2),
                            pair_shrinkage_10=(positives[pair] + 10 * pooled) / (totals[pair] + 10),
                            ridge_pair_coverage=next(ridge),
                        )
                        for model, probability in predictions.items():
                            db.execute(
                                "INSERT INTO predictions VALUES(?,?,?,?,?,?,?,?)",
                                (task, panel, held, row["seq"], pair, model, probability, ntrain),
                            )
                details.append(dict(fold=held, train=ntrain, test=ntest))
            task_result = dict(folds=details, models={}, per_pair={}, per_area={}, error_sensitivity={})
            for model in protocol["evaluation"]["models"]:
                query = """SELECT c.*,p.probability FROM predictions p JOIN contexts c ON c.seq=p.seq
                           WHERE p.task=? AND p.panel=? AND p.model=?"""
                params = (task, panel, model)
                sample = SqlRows(db, query + " ORDER BY p.fold,c.seq", params)
                task_result["models"][model] = scores(sample, (r["probability"] for r in sample))
                task_result["error_sensitivity"][model] = error_sensitivity(sample, protocol["diagnostic_error_rates"])
                for area in ["North America", "South America"]:
                    selected = SqlRows(
                        db, query + " AND c.area LIKE ? ORDER BY p.fold,c.seq", params + ("%" + area + "%",)
                    )
                    task_result["per_area"].setdefault(area, {})[model] = scores(
                        selected, (r["probability"] for r in selected)
                    )
                for i, pair in enumerate(protocol["pairs"]):
                    if pair["role"] != panel:
                        continue
                    selected = SqlRows(db, query + " AND p.pair=? ORDER BY p.fold,c.seq", params + (i,))
                    task_result["per_pair"].setdefault(pair["a"] + "|" + pair["b"], {})[model] = scores(
                        selected, (r["probability"] for r in selected)
                    )
            pooled_loss = task_result["models"]["pooled_laplace"]["log_loss_bits"]
            for value in task_result["models"].values():
                value["gain_bits_vs_pooled"] = pooled_loss - value["log_loss_bits"] if value["n"] else None
            results[panel][task] = task_result
            print("Validation completed:", panel, task, flush=True)
    return results


def run(root, built, protocol_path, destination):
    root, built, protocol_path, destination = map(Path, [root, built, protocol_path, destination])
    if destination.exists():
        raise ValueError("Refuse to overwrite broader research outcomes")
    protocol = json.loads(protocol_path.read_text())
    if not 60 <= len(protocol["pairs"]) <= 100 or not protocol["fit_panels_separately"]:
        raise ValueError("Unexpected frozen broader protocol")
    concepts = {r["concept_id"]: r for r in csv.DictReader((root / "src/arcaverborum/data/concepts.csv").open())}
    for p in protocol["pairs"]:
        if digest(concepts[p["a"]]) != p["concept_a_sha256"] or digest(concepts[p["b"]]) != p["concept_b_sha256"]:
            raise ValueError("Frozen concept definition changed")
    seal = verify_database(built)
    manifest = json.loads((built / "public/manifest.json").read_text())
    aggregate_hash = sha(root / "output/aggregate/forms.csv")
    if aggregate_hash != manifest["inputs"]["output/aggregate/forms.csv"]:
        raise ValueError("Aggregate differs from analytical input")
    destination.mkdir(parents=True)
    db = sqlite3.connect(destination / "contexts.sqlite")
    db.execute("PRAGMA cache_size=-8000")
    db.execute("PRAGMA temp_store=FILE")
    db.execute("PRAGMA mmap_size=0")
    db.execute("PRAGMA max_page_count=" + str(protocol["max_context_database_mb"] * 1024**2 // 4096))
    core = sqlite3.connect(f"file:{built / 'index.sqlite'}?mode=ro", uri=True)
    core.execute("PRAGMA cache_size=-8000")
    core.execute("PRAGMA temp_store=FILE")
    core.execute("PRAGMA mmap_size=0")
    try:
        columns = None
        with db:
            for seq, row in enumerate(contexts(core, protocol, publication=True)):
                if seq >= protocol["scope_cap"] * len(protocol["pairs"]):
                    raise ValueError("Context budget exceeded")
                lineage = "ids_wold" if row["block"] in {"ids", "wold"} else row["block"]
                row = dict(
                    seq=seq,
                    **row,
                    fold_block=fold(row["block"], "resource_block", protocol["evaluation"]["hash_seed"]),
                    fold_family=fold(row["family"], "family", protocol["evaluation"]["hash_seed"]),
                    fold_questionnaire=fold(lineage, "resource_block", protocol["evaluation"]["hash_seed"]),
                )
                if columns is None:
                    columns = list(row)
                    integer = {
                        "seq",
                        "sid",
                        "pair",
                        "y",
                        "coverage",
                        "publication_y",
                        "comparable_publications",
                        "conflicting_publications",
                        "fold_block",
                        "fold_family",
                        "fold_questionnaire",
                    }
                    real = {"length_a", "length_b"}
                    db.execute(
                        "CREATE TABLE contexts ("
                        + ",".join(
                            '"' + k + '" ' + ("INTEGER" if k in integer else "REAL" if k in real else "TEXT")
                            for k in columns
                        )
                        + ")"
                    )
                db.execute("INSERT INTO contexts VALUES(" + ",".join("?" for _ in columns) + ")", tuple(row.values()))
        db.execute("CREATE UNIQUE INDEX scope_pair ON contexts(sid,pair)")
        db.execute("CREATE UNIQUE INDEX context_seq ON contexts(seq)")
        db.execute("CREATE INDEX panel_outcome ON contexts(role,y)")
        db.execute(
            "CREATE TABLE predictions(task TEXT,panel TEXT,fold INTEGER,seq INTEGER,pair INTEGER,"
            "model TEXT,probability REAL,train_n INTEGER,UNIQUE(task,seq,model))"
        )
        db.execute("CREATE INDEX prediction_scores ON predictions(task,panel,model,pair)")
        db.commit()
        print("Validation contexts streamed:", len(SqlRows(db, "SELECT * FROM contexts")), flush=True)
        results = evaluate(db, protocol)
        bayes = bayesian(SqlRows(db, "SELECT * FROM contexts ORDER BY seq"), protocol)
        null = incidence_null(core, protocol, concepts)
        summary = dict(
            signature=dict(
                core=seal["build_id"],
                database_sha256=seal["database_sha256"],
                aggregate_sha256=aggregate_hash,
                protocol_sha256=sha(protocol_path),
                pipeline_sha256=sha(Path(__file__)),
                cli_sha256=sha(root / "scripts/validate_colexification_inference.py"),
                inference_library_sha256=sha(root / "src/arcaverborum/colexification_inference.py"),
            ),
            target=protocol["target"],
            sampling=protocol["sampling"],
            evaluation=results,
            context_counts=[
                dict(panel=panel, y=y, n=n)
                for panel, y, n in db.execute("SELECT role,y,COUNT(*) FROM contexts GROUP BY role,y ORDER BY role,y")
            ],
            publication_sensitivity=[
                dict(panel=panel, y=y, publication_y=pub, n=n)
                for panel, y, pub, n in db.execute(
                    "SELECT role,y,publication_y,COUNT(*) FROM contexts GROUP BY role,y,publication_y"
                )
            ],
            bayesian_sensitivity=bayes,
            null_sensitivity=null,
            independent_expert_adjudications=0,
            production_graph_weights_changed=False,
        )
        (destination / "results.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
        for name, query in [
            ("contexts", "SELECT * FROM contexts ORDER BY seq"),
            ("predictions", "SELECT * FROM predictions ORDER BY task,panel,fold,seq,model"),
        ]:
            cursor = db.execute(query)
            with (destination / (name + ".csv")).open("w") as h:
                writer = csv.writer(h)
                writer.writerow([c[0] for c in cursor.description])
                writer.writerows(cursor)
        db.commit()
    finally:
        db.close()
        core.close()
    complete = dict(signature=summary["signature"], files={p.name: sha(p) for p in destination.iterdir()})
    (destination / "complete.json").write_text(json.dumps(complete, indent=2) + "\n")
    return summary
