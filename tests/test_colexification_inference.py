"""Inference mathematics, leakage controls and valid incidence permutations."""

import copy
import math
import random
from collections import Counter

import pytest

from arcaverborum.colexification_inference import (
    bayesian,
    beta_cdf,
    beta_quantile,
    evaluate,
    outcome,
    permutation,
    scores,
)


def test_unknown_and_native_duplicate_are_not_negative_labels():
    assert outcome([], [("ma", "f", "p")]) is None
    assert outcome([("ma", "f", "p")], [("mi", "f", "p")]) is None
    assert outcome([("ma", "a", "p")], [("ma", "b", "q")]) == 1
    assert outcome([("ma", "a", "p")], [("mi", "b", "q")]) == 0


def test_beta_quantiles_match_analytic_cases_including_sparse_boundaries():
    for a in [0.5, 1, 2, 101]:
        for q in [0.001, 0.05, 0.5, 0.95, 0.999]:
            assert beta_quantile(q, a, 1) == pytest.approx(q ** (1 / a), abs=2e-11)
    for b in [0.5, 1, 9, 101]:
        for q in [0.001, 0.05, 0.5, 0.95, 0.999]:
            assert beta_quantile(q, 1, b) == pytest.approx(1 - (1 - q) ** (1 / b), abs=2e-11)
    assert beta_cdf(0.5, 100, 100) == pytest.approx(0.5, abs=1e-11)


def test_bijection_preserves_degrees_even_with_synonyms_and_duplicate_labels():
    nodes = {
        "A": [("m a", "a1", "pA"), ("n a", "a2", "pA")],
        "B": [("m a", "b", "pB")],
        "C": [("n a", "c", "pC")],
        "D": [("l a", "d", "pD")],
    }
    original = Counter(k for records in nodes.values() for k in {r[0] for r in records})
    for seed in range(30):
        inv, _ = permutation(nodes, dict.fromkeys(nodes, "n"), random.Random(seed))
        assert set(inv) == set(inv.values()) == set(nodes)
        groups = Counter(k for new, old in inv.items() for k in {r[0] for r in nodes[old]})
        assert groups == original
        assert all(len({r[0] for r in nodes[new]}) == len({r[0] for r in nodes[old]}) for new, old in inv.items())
        assert inv["A"] == "A"  # Two-form degree cannot move into a one-form node.


def test_one_selected_context_per_family_and_information_quantities():
    protocol = {"pairs": [{"a": "a", "b": "b"}], "seeds": [7], "bayesian_sensitivity": {"priors": [[1, 1]]}}
    row = dict(pair=0, family="F", y=1, sid=1, av="v", source="s", member="m", tags="", basis="ipa")
    result = bayesian([row, row | dict(sid=2)], protocol)["results"][0]
    assert result["known_families"] == 1 and result["positive"] == 1
    assert result["mean"] == pytest.approx(2 / 3)
    assert result["posterior_prior_kl_bits"] == pytest.approx((math.log(2) - 0.5) / math.log(2), abs=1e-9)
    assert result["next_independent_trial_information_bits"] == pytest.approx(0.19694831361, abs=1e-9)
    assert len(result["selected_scope_ids"]) == 1


def test_prediction_score_counts_negatives_and_rewards_honest_probabilities():
    rows = [dict(y=1, family="a"), dict(y=0, family="b")]
    assert scores(rows, [0.5, 0.5])["log_loss_bits"] == 1
    assert scores(rows, [0.9, 0.1])["brier"] == pytest.approx(0.01)
    assert scores(rows, [0.1, 0.9])["log_loss_bits"] > 1


def test_grouped_evaluation_separates_test_groups_and_does_not_modify_records():
    rows = [
        dict(
            pair=0,
            y=i % 2,
            family="f" + str(i % 8),
            block="s" + str(i % 7),
            coverage=30 + i,
            length_a=2,
            length_b=3,
            area="South America",
        )
        for i in range(56)
    ]
    protocol = dict(
        pairs=[dict(a="a", b="b")], evaluation=dict(hash_seed="test", split_units=["family", "resource_block"])
    )
    before = copy.deepcopy(rows)
    result = evaluate(rows, protocol)
    assert rows == before
    for task in result.values():
        assert task["models"]["pair_laplace"]["n"] == 56
        assert sum(f["test"] for f in task["folds"]) == 56
        assert all(f["train"] + f["test"] == 56 for f in task["folds"])
        assert math.isfinite(task["models"]["ridge_pair_coverage"]["log_loss_bits"])


def test_small_sealed_pilot_exports_evidence_and_predictions(tmp_path):
    import json

    from test_colexification import fixture, form

    from arcaverborum.colexification import build, digest
    from arcaverborum.colexification_inference import run

    concepts = fixture(
        tmp_path,
        [
            form(i, av=av, source=source, word="ma" if i < 2 else str(i) + "na")
            for av, source in [("a", "source"), ("b", "second")]
            for i in range(4)
        ],
    )
    protocol = dict(
        scope_cap=100,
        reading_cap_per_scope_pair=100,
        seeds=[7],
        pairs=[
            dict(
                a="x-0",
                b="x-1",
                role="challenge",
                concept_a_sha256=digest(concepts[0]),
                concept_b_sha256=digest(concepts[1]),
            )
        ],
        evaluation=dict(hash_seed="test", split_units=["resource_block", "family"]),
        bayesian_sensitivity=dict(priors=[[1, 1]]),
        nulls=dict(replicates=3),
        audit=dict(sample_per_pair_per_state=2, review_columns=["reviewer", "decision"]),
    )
    (tmp_path / "src/arcaverborum/data/colexification/inference_protocol.json").write_text(json.dumps(protocol))
    script = tmp_path / "scripts/pilot_colexification_inference.py"
    script.parent.mkdir()
    script.write_text("# fixture CLI identity\n")
    built = build(tmp_path)
    result = run(tmp_path, built, tmp_path / "pilot")
    assert result["positives"] == 2 and result["contexts"] == 2
    assert result["independently_adjudicated_rows"] == 0
    assert (tmp_path / "pilot/complete.json").exists()
    assert (tmp_path / "pilot/predictions.csv").read_text().startswith("task,fold,sid")
    assert "aggregate_evidence_a" in (tmp_path / "pilot/audit_packet.csv").read_text()


def test_prior_only_is_explicit_and_empty_comparability_has_no_tail(tmp_path):
    from test_colexification import form
    from test_colexification import run as build_fixture

    from arcaverborum.colexification_inference import incidence_null

    _, db = build_fixture(tmp_path, [form(0)])
    protocol = dict(
        pairs=[dict(a="x-0", b="x-1")], seeds=[7], bayesian_sensitivity=dict(priors=[[1, 1]]), nulls=dict(replicates=3)
    )
    concepts = {"x-0": dict(pos="n", semantic_field="Test")}
    pair = incidence_null(db, protocol, concepts)["pairs"][0]
    assert pair["empirical_upper_tail"] is None and pair["comparable_families"] == 0
    assert bayesian([], protocol)["results"][0]["evidence_status"] == "prior_only_no_comparable_families"
    db.close()
