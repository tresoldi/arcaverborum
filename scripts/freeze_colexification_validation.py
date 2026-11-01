"""Freeze outcome-blind marginal-coverage sampling frames before broader inference."""

import argparse
import csv
import heapq
import itertools
import json
import resource
import sqlite3
from pathlib import Path

from arcaverborum.colexification import digest, sha, verify_database
from arcaverborum.colexification_inference import rank


def sample(frame, n, seed, excluded):
    chosen = []
    total = 0
    for pair in frame:
        if pair in excluded:
            continue
        total += 1
        key = int(rank(seed + "/" + "|".join(pair)), 16)
        item = (-key, pair)
        if len(chosen) < n:
            heapq.heappush(chosen, item)
        elif item > chosen[0]:
            heapq.heapreplace(chosen, item)
    if total < n:
        raise ValueError("Insufficient outcome-blind frame")
    return sorted(pair for _, pair in chosen), total


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument("--build", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    resource.setrlimit(resource.RLIMIT_AS, (256 * 1024**2, 256 * 1024**2))
    if a.output.exists():
        raise ValueError("Refuse to overwrite frozen protocol")
    seal = verify_database(a.build)
    old_path = a.root / "src/arcaverborum/data/colexification/inference_protocol.json"
    old = json.loads(old_path.read_text())
    db = sqlite3.connect(f"file:{a.build / 'index.sqlite'}?mode=ro", uri=True)
    db.execute("PRAGMA cache_size=-8000")
    db.execute("PRAGMA temp_store=FILE")
    db.execute("PRAGMA mmap_size=0")
    counts = db.execute("""SELECT r.cid, COUNT(DISTINCT v.family),
      COUNT(DISTINCT CASE WHEN v.area LIKE '%South America%' THEN v.family END)
      FROM valid r JOIN scopes s ON s.id=r.sid JOIN varieties v ON v.av=s.av
      WHERE r.layer='segmented' AND r.semantic<>'unreviewed_dictionary_sense'
      AND v.family<>'' GROUP BY r.cid ORDER BY r.cid""").fetchall()
    common = sorted(cid for cid, n, _ in counts if n >= 50)
    rare = sorted(cid for cid, n, sa in counts if 2 <= n <= 20 and sa >= 2)
    controls = {tuple(sorted((p["a"], p["b"]))) for p in old["pairs"]}
    uniform, total = sample(itertools.combinations(common, 2), 40, "CINF04-2026-11-01-common-v1", controls)
    # Distinct low-marginal-coverage concepts anchored to widely represented concepts.
    rare_pairs, rare_total = sample(
        (tuple(sorted((x, y))) for x in rare for y in common),
        18,
        "CINF04-2026-11-01-americas-v1",
        controls | set(uniform),
    )
    concepts = {r["concept_id"]: r for r in csv.DictReader((a.root / "src/arcaverborum/data/concepts.csv").open())}
    pairs = []
    for panel, chosen, size, draw in [
        ("sampled_common", uniform, total, 40),
        ("sampled_rare_south_america", rare_pairs, rare_total, 18),
        ("purposive_legacy_controls", sorted(controls), None, 18),
    ]:
        for x, y in chosen:
            pairs.append(
                dict(
                    a=x,
                    b=y,
                    role=panel,
                    concept_a_sha256=digest(concepts[x]),
                    concept_b_sha256=digest(concepts[y]),
                    sampling_probability=draw / size if size else None,
                    frame_size=size,
                )
            )
    protocol = old | dict(
        schema=2,
        created_utc="2026-11-01",
        status="Frozen before broader context outcomes",
        target="Conditional recorded-identity transfer within separately reported sampled frames; not world polysemy",
        pairs=pairs,
        frame_core=seal,
        frame_counts=counts,
        sampling=dict(
            common_concepts=len(common),
            rare_south_american_concepts=len(rare),
            common_frame=total,
            rare_frame=rare_total,
            common_n=40,
            rare_n=18,
            method="Lowest SHA256 ranks without replacement; fixed seeds in generator; marginal coverage only",
            limitations="Not sampled from all concepts or directly from comparable pairs; legacy controls excluded",
        ),
        publication_sensitivity="Common singleton native citations only; pooled/absent references unknown",
        score_panels_separately=True,
        fit_panels_separately=True,
        evaluation=old["evaluation"]
        | dict(split_units=["resource_block", "family", "questionnaire_lineage_sensitivity"]),
        questionnaire_lineage_sensitivity={"ids_wold": ["ids", "wold"]},
        max_context_database_mb=512,
        diagnostic_error_rates=[0.0, 0.05, 0.10],
        measurement_error_caveat="Hypothetical symmetric label flips, not empirical error estimates",
        pipeline_sha256=sha(Path(__file__)),
        legacy_protocol_sha256=sha(old_path),
    )
    a.output.write_text(json.dumps(protocol, ensure_ascii=False, indent=2) + "\n")
    print(
        json.dumps(
            dict(
                pairs=len(pairs),
                sampling=protocol["sampling"],
                protocol_sha256=sha(a.output),
                peak_rss_mb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
