"""Streamed fitting preserves the small reference method and conditional targets."""

import sqlite3

import pytest

from arcaverborum.colexification_inference import evaluate as retained_evaluate
from arcaverborum.colexification_validation import SqlRows, error_sensitivity, evaluate, fold


def test_sql_rows_are_reiterable_and_label_flip_zero_recovers_score():
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE example(y INTEGER,probability REAL)")
    db.executemany("INSERT INTO example VALUES(?,?)", [(1, 0.8), (0, 0.3)])
    rows = SqlRows(db, "SELECT * FROM example ORDER BY rowid")
    assert len(rows) == 2 and list(rows) == list(rows)
    result = error_sensitivity(rows, [0, 0.1])
    assert result["rates"][0]["brier"] == pytest.approx((0.2**2 + 0.3**2) / 2)
    assert result["rates"][1]["brier"] > result["rates"][0]["brier"]


def test_streamed_panel_fits_match_legacy_without_group_leakage():
    seed = "test-streamed-panels"
    protocol = dict(
        pairs=[dict(a="a", b="b", role="sampled_common"), dict(a="c", b="d", role="sampled_common")],
        diagnostic_error_rates=[0, 0.05, 0.1],
        evaluation=dict(
            hash_seed=seed,
            split_units=["resource_block", "family"],
            models=["pooled_laplace", "pair_laplace", "pair_shrinkage_10", "ridge_pair_coverage"],
        ),
    )
    rows = [
        dict(
            seq=i,
            sid=i,
            pair=i % 2,
            role="sampled_common",
            y=int(i % 5 == 0),
            coverage=20 + i,
            length_a=2 + i % 3,
            length_b=3 + i % 2,
            family="fam" + str(i % 7),
            block="block" + str(i % 8),
            area="South America",
        )
        for i in range(45)
    ]
    reference = retained_evaluate(rows, protocol)
    db = sqlite3.connect(":memory:")
    db.execute(
        "CREATE TABLE contexts(seq INTEGER,sid INTEGER,pair INTEGER,role TEXT,y INTEGER,"
        "coverage INTEGER,length_a REAL,length_b REAL,family TEXT,block TEXT,area TEXT,"
        "fold_block INTEGER,fold_family INTEGER,fold_questionnaire INTEGER)"
    )
    for row in rows:
        db.execute(
            "INSERT INTO contexts VALUES(" + ",".join("?" for _ in range(14)) + ")",
            tuple(row.values())
            + (
                fold(row["block"], "resource_block", seed),
                fold(row["family"], "family", seed),
                fold(row["block"], "resource_block", seed),
            ),
        )
    db.execute(
        "CREATE TABLE predictions(task TEXT,panel TEXT,fold INTEGER,seq INTEGER,pair INTEGER,"
        "model TEXT,probability REAL,train_n INTEGER,UNIQUE(task,seq,model))"
    )
    result = evaluate(db, protocol)["sampled_common"]
    for task in ["resource_block", "family"]:
        for model, score in result[task]["models"].items():
            expected = reference[task]["models"][model]
            assert score["n"] == expected["n"]
            assert score["log_loss_bits"] == pytest.approx(expected["log_loss_bits"], abs=1e-12)
            assert score["brier"] == pytest.approx(expected["brier"], abs=1e-12)
            assert result[task]["error_sensitivity"][model]["rates"][0]["log_loss_bits"] == pytest.approx(
                expected["log_loss_bits"], abs=1e-12
            )
    assert db.execute("SELECT COUNT(*) FROM predictions").fetchone()[0] == 45 * 4 * 3
