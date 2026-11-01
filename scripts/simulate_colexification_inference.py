"""Synthetic prior-predictive calibration checks; these do not validate real lexical data."""

import argparse
import json
import math
import random
import resource
from pathlib import Path

from arcaverborum.colexification import sha
from arcaverborum.colexification_inference import beta_cdf, beta_quantile


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    resource.setrlimit(resource.RLIMIT_AS, (256 * 1024**2, 256 * 1024**2))
    rng = random.Random(641)
    trials = 500
    n = 20
    copies = 10
    counters = {
        k: dict(covered=0, total_width=0.0, posterior_cdf_bins=[0] * 10)
        for k in [
            "independent_reference",
            "naive_exact_copies",
            "deduplicated_exact_copies",
            "unmodelled_measurement_error",
        ]
    }
    for _ in range(trials):
        theta = rng.random()
        success = sum(rng.random() < theta for _ in range(n))
        noisy = sum(rng.random() < (0.8 * theta + 0.1 * (1 - theta)) for _ in range(n))
        for name, (positive, total) in {
            "independent_reference": (success, n),
            "naive_exact_copies": (copies * success, copies * n),
            "deduplicated_exact_copies": (success, n),
            "unmodelled_measurement_error": (noisy, n),
        }.items():
            al, be = 1 + positive, 1 + total - positive
            low, high = beta_quantile(0.05, al, be), beta_quantile(0.95, al, be)
            c = counters[name]
            c["covered"] += low <= theta <= high
            c["total_width"] += high - low
            c["posterior_cdf_bins"][min(9, int(beta_cdf(theta, al, be) * 10))] += 1
    for c in counters.values():
        c["coverage"] = c["covered"] / trials
        c["mean_interval_width"] = c["total_width"] / trials
        c["coverage_monte_carlo_se"] = math.sqrt(c["coverage"] * (1 - c["coverage"]) / trials)
        del c["total_width"]
    result = dict(
        status="Synthetic model check only, not real-data or linguistic calibration",
        seed=641,
        replicates=trials,
        independent_units=n,
        copies_per_unit=copies,
        prior=[1, 1],
        interval_mass=0.9,
        measurement_error=dict(sensitivity=0.8, false_positive_rate=0.1),
        results=counters,
        code_sha256=sha(Path(__file__)),
        module_sha256=sha(Path(__file__).parents[1] / "src/arcaverborum/colexification_inference.py"),
        caveats=[
            "Uniform latent rate, Bernoulli independent units in the reference model",
            "Posterior CDF ranks/interval coverage under prior-predictive replication; no MCMC sampler tested",
            "Copies are exact stipulated duplicates; deduplication is known by construction",
            "No calibration claim for Arca lexical data or source-error estimates",
        ],
    )
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {k: dict(coverage=v["coverage"], width=v["mean_interval_width"]) for k, v in counters.items()}, indent=2
        )
    )


if __name__ == "__main__":
    main()
