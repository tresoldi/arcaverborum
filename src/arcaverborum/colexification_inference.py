"""Bounded exploratory prediction and uncertainty for recorded colexification.

No output certifies polysemy, world prevalence, independence or linguistic truth.
"""

from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import random
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

from arcaverborum.colexification import digest, sha, verify_database


def rank(value):
    return hashlib.sha256(str(value).encode()).hexdigest()


def length(key):
    if key.startswith("["):
        key = json.loads(key)[1]
    return sum(bool(t) and t != "+" for t in key.split(" "))


def compatible(left, right):
    return any(a[1] != b[1] and a[2] != b[2] for a in left for b in right)


def outcome(left, right):
    if not left or not right or not compatible(left, right):
        return None
    grouped = defaultdict(list)
    for r in right:
        grouped[r[0]].append(r)
    return int(any(compatible([a], grouped[a[0]]) for a in left if a[0] in grouped))


def read_protocol(root):
    path = Path(root) / "src/arcaverborum/data/colexification/inference_protocol.json"
    protocol = json.loads(path.read_text())
    concepts = {r["concept_id"]: r for r in csv.DictReader((Path(root) / "src/arcaverborum/data/concepts.csv").open())}
    for p in protocol["pairs"]:
        for cid, key in [(p["a"], "concept_a_sha256"), (p["b"], "concept_b_sha256")]:
            if cid not in concepts or digest(concepts[cid]) != p[key]:
                raise ValueError("Frozen pilot definition drift: " + cid)
    return protocol, concepts, sha(path)


def publication_outcome(left, right):
    """Sensitivity limited to common singleton citations; pooled/absent refs stay unknown."""
    grouped = []
    for readings in [left, right]:
        by_publication = defaultdict(list)
        for row in readings:
            refs = {ref.strip().split("[", 1)[0] for ref in row[3].split(";") if ref.strip()}
            if len(refs) == 1:
                by_publication[next(iter(refs))].append(row)
        grouped.append(by_publication)
    outcomes = [outcome(grouped[0][ref], grouped[1][ref]) for ref in sorted(grouped[0].keys() & grouped[1].keys())]
    observed = [y for y in outcomes if y is not None]
    return (max(observed) if observed else None), len(observed), len(set(observed)) > 1


def contexts(db, protocol, *, publication=False):
    scopes = db.execute("""SELECT DISTINCT s.id,s.av,s.source,s.member,s.tags,s.basis,
      v.language,v.family,v.area,b.block FROM scopes s JOIN readings r ON r.sid=s.id
      JOIN varieties v ON v.av=s.av JOIN resource_blocks b ON b.source=s.source
      WHERE r.layer='segmented' ORDER BY s.id""").fetchall()
    if len(scopes) > protocol["scope_cap"]:
        raise ValueError("Pilot scope budget exceeded")
    metadata = {
        s[0]: dict(zip(["sid", "av", "source", "member", "tags", "basis", "language", "family", "area", "block"], s))
        for s in scopes
    }
    coverage = dict(
        db.execute(
            "SELECT sid,COUNT(DISTINCT cid) FROM valid WHERE layer='segmented' "
            "AND semantic<>'unreviewed_dictionary_sense' GROUP BY sid"
        )
    )
    for i, pair in enumerate(protocol["pairs"]):
        groups = defaultdict(lambda: defaultdict(list))
        for sid, cid, key, fid, param, bib in db.execute(
            """SELECT sid,cid,key,fid,param,bib FROM valid
          WHERE layer='segmented' AND cid IN (?,?) AND semantic<>'unreviewed_dictionary_sense'
          ORDER BY sid,cid,key,fid,param""",
            (pair["a"], pair["b"]),
        ):
            g = groups[sid][cid]
            if len(g) >= protocol["reading_cap_per_scope_pair"]:
                raise ValueError("Pilot reading budget exceeded; no truncated contexts exported")
            g.append((key, fid, param, bib))
        for sid, meta in metadata.items():
            left, right = groups[sid][pair["a"]], groups[sid][pair["b"]]
            if len(left) + len(right) > protocol["reading_cap_per_scope_pair"]:
                raise ValueError("Pilot pair reading budget exceeded")
            y = outcome(left, right)
            chosen = next(
                ((a, b) for a in left for b in right if a[1] != b[1] and a[2] != b[2] and (y != 1 or a[0] == b[0])),
                (left[0] if left else None, right[0] if right else None),
            )
            la = sum(map(length, {r[0] for r in left})) / max(1, len({r[0] for r in left}))
            lb = sum(map(length, {r[0] for r in right})) / max(1, len({r[0] for r in right}))
            extra = {}
            if publication:
                pub_y, pub_n, pub_conflict = publication_outcome(left, right)
                extra = dict(publication_y=pub_y, comparable_publications=pub_n,
                             conflicting_publications=int(pub_conflict))
            yield meta | extra | dict(
                pair=i,
                a=pair["a"],
                b=pair["b"],
                role=pair["role"],
                y=y,
                coverage=coverage.get(sid, 0),
                length_a=la,
                length_b=lb,
                form_a=chosen[0][1] if chosen[0] else "",
                form_b=chosen[1][1] if chosen[1] else "",
                param_a=chosen[0][2] if chosen[0] else "",
                param_b=chosen[1][2] if chosen[1] else "",
            )


def scores(rows, predictions):
    bins = [dict(n=0, positive=0, predicted=0.0) for _ in range(10)]
    ll = brier = 0.0
    families = defaultdict(lambda: [0, 0.0, 0.0])
    for row, p in zip(rows, predictions, strict=True):
        p = min(1 - 1e-6, max(1e-6, float(p)))
        y = row["y"]
        loss = -(y * math.log2(p) + (1 - y) * math.log2(1 - p))
        square = (p - y) ** 2
        ll += loss
        brier += square
        b = bins[min(9, int(p * 10))]
        b["n"] += 1
        b["positive"] += y
        b["predicted"] += p
        if row["family"]:
            f = families[row["family"]]
            f[0] += 1
            f[1] += loss
            f[2] += square
    return dict(
        n=len(rows),
        positive=sum(r["y"] for r in rows),
        log_loss_bits=ll / len(rows) if rows else None,
        brier=brier / len(rows) if rows else None,
        known_family_macro_log_loss_bits=sum(f[1] / f[0] for f in families.values()) / len(families)
        if families
        else None,
        calibration_bins=bins,
    )


def ridge_predict(train, test, count, *, streaming=False):
    """Exact small sparse Newton system; no dense observation matrix or BLAS."""

    def raw(r):
        return (math.log1p(r["coverage"]), r["length_a"], r["length_b"])

    mean = [sum(raw(r)[j] for r in train) / len(train) for j in range(3)]
    sd = [math.sqrt(sum((raw(r)[j] - mean[j]) ** 2 for r in train) / len(train)) for j in range(3)]
    sd = [v if v > 1e-8 else 1.0 for v in sd]

    def features(r):
        z = raw(r)
        return [(r["pair"], 1.0)] + [(count + j, (z[j] - mean[j]) / sd[j]) for j in range(3)]

    class Examples:
        def __iter__(self):
            for r in train:
                yield r["y"], features(r)

    examples = Examples() if streaming else [(r["y"], features(r)) for r in train]
    base = (sum(r["y"] for r in train) + 1) / (len(train) + 2)
    offset = math.log(base / (1 - base))
    beta = [0.0] * (count + 3)
    penalty = [2.0] * count + [1.0] * 3

    def objective(values):
        result = sum(p * b * b / 2 for p, b in zip(penalty, values))
        for y, x in examples:
            eta = offset + sum(values[j] * v for j, v in x)
            result += max(0, eta) + math.log1p(math.exp(-abs(eta))) - y * eta
        return result

    def solve(matrix, vector):
        # Partial-pivot elimination on the (pairs + 3) parameter Hessian.
        n = len(vector)
        aug = [r.copy() + [v] for r, v in zip(matrix, vector)]
        for k in range(n):
            pivot = max(range(k, n), key=lambda i: abs(aug[i][k]))
            aug[k], aug[pivot] = aug[pivot], aug[k]
            if abs(aug[k][k]) < 1e-12:
                raise ArithmeticError("Singular penalized Hessian")
            for i in range(k + 1, n):
                factor = aug[i][k] / aug[k][k]
                for j in range(k, n + 1):
                    aug[i][j] -= factor * aug[k][j]
        result = [0.0] * n
        for i in range(n - 1, -1, -1):
            result[i] = (aug[i][n] - sum(aug[i][j] * result[j] for j in range(i + 1, n))) / aug[i][i]
        return result

    for _ in range(25):
        gradient = [p * b for p, b in zip(penalty, beta)]
        hessian = [[0.0] * len(beta) for _ in beta]
        for j, p in enumerate(penalty):
            hessian[j][j] = p
        for y, x in examples:
            eta = offset + sum(beta[j] * v for j, v in x)
            probability = 1 / (1 + math.exp(-max(-40, min(40, eta))))
            w = probability * (1 - probability)
            for j, v in x:
                gradient[j] += (probability - y) * v
                for k, u in x:
                    hessian[j][k] += w * v * u
        step = solve(hessian, gradient)
        old = objective(beta)
        scale = 1.0
        candidate = [b - scale * d for b, d in zip(beta, step)]
        while scale > 1 / 1024 and objective(candidate) > old:
            scale *= 0.5
            candidate = [b - scale * d for b, d in zip(beta, step)]
        if objective(candidate) > old + 1e-8:
            raise ArithmeticError("Penalized likelihood did not descend")
        beta = candidate
        if max(abs(scale * d) for d in step) < 1e-7:
            break
    return [1 / (1 + math.exp(-max(-40, min(40, offset + sum(beta[j] * v for j, v in features(r)))))) for r in test]


def evaluate(rows, protocol, prediction_sink=None):
    result = {}
    available = [r for r in rows if r["y"] is not None]
    count = len(protocol["pairs"])
    seed = protocol["evaluation"]["hash_seed"]
    for unit in protocol["evaluation"]["split_units"]:
        field = "block" if unit == "resource_block" else "family"
        sample = [r for r in available if r[field]]
        folds = {r[field]: int(rank(seed + "/" + unit + "/" + r[field])[:12], 16) % 5 for r in sample}
        accum = defaultdict(list)
        actual = []
        details = []
        for fold in range(5):
            train = [r for r in sample if folds[r[field]] != fold]
            test = [r for r in sample if folds[r[field]] == fold]
            if not train or not test:
                continue
            pos = sum(r["y"] for r in train)
            base = (pos + 1) / (len(train) + 2)
            totals = Counter(r["pair"] for r in train)
            positives = Counter(r["pair"] for r in train if r["y"])
            predictions = {
                "pooled_laplace": [base] * len(test),
                "pair_laplace": [(positives[r["pair"]] + 1) / (totals[r["pair"]] + 2) for r in test],
                "pair_shrinkage_10": [(positives[r["pair"]] + 10 * base) / (totals[r["pair"]] + 10) for r in test],
                "ridge_pair_coverage": ridge_predict(train, test, count),
            }
            if prediction_sink:
                for name, ps in predictions.items():
                    for r, probability in zip(test, ps, strict=True):
                        prediction_sink(
                            dict(
                                task=unit,
                                fold=fold,
                                sid=r["sid"],
                                pair=r["pair"],
                                y=r["y"],
                                model=name,
                                probability=probability,
                                heldout_group=r[field],
                                train_n=len(train),
                                train_positive=pos,
                            )
                        )
            actual.extend(test)
            for name, ps in predictions.items():
                accum[name].extend(ps)
            details.append(
                dict(
                    fold=fold,
                    train=len(train),
                    test=len(test),
                    train_groups=len({r[field] for r in train}),
                    test_groups=len({r[field] for r in test}),
                )
            )
        model_scores = {name: scores(actual, p) for name, p in accum.items()}
        for v in model_scores.values():
            v["gain_bits_vs_pooled"] = model_scores["pooled_laplace"]["log_loss_bits"] - v["log_loss_bits"]
        per_pair = {}
        for i, pair in enumerate(protocol["pairs"]):
            ix = [j for j, r in enumerate(actual) if r["pair"] == i]
            per_pair[pair["a"] + "|" + pair["b"]] = {
                name: scores([actual[j] for j in ix], [ps[j] for j in ix]) for name, ps in accum.items()
            }
        result[unit] = dict(
            target="Transfer to held-out " + unit + " conditional on comparable recorded evidence",
            excluded_unknown_group=sum(not r[field] for r in available),
            folds=details,
            group_assignments=folds,
            models=model_scores,
            per_pair=per_pair,
            per_area={
                area: {
                    name: scores(
                        [r for r in actual if area in r["area"].split(";")],
                        [p for r, p in zip(actual, ps) if area in r["area"].split(";")],
                    )
                    for name, ps in accum.items()
                }
                for area in ["North America", "South America"]
            },
        )
    return result


def digamma(x):
    result = 0.0
    while x < 12:
        result -= 1 / x
        x += 1
    z = 1 / (x * x)
    return result + math.log(x) - 0.5 / x - z * (1 / 12 - z * (1 / 120 - z * (1 / 252 - z / 240)))


def beta_cdf(x, a, b):
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0

    def fraction(aa, bb, xx):
        qab = aa + bb
        qap = aa + 1
        qam = aa - 1
        c = 1.0
        d = 1 - qab * xx / qap
        if abs(d) < 1e-300:
            d = 1e-300
        d = 1 / d
        h = d
        for m in range(1, 401):
            for term in [
                m * (bb - m) * xx / ((qam + 2 * m) * (aa + 2 * m)),
                -(aa + m) * (qab + m) * xx / ((aa + 2 * m) * (qap + 2 * m)),
            ]:
                d = 1 + term * d
                c = 1 + term / c
                if abs(d) < 1e-300:
                    d = 1e-300
                if abs(c) < 1e-300:
                    c = 1e-300
                d = 1 / d
                delta = d * c
                h *= delta
            if abs(delta - 1) < 1e-13:
                return h
        raise ArithmeticError("Incomplete beta did not converge")

    bt = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log1p(-x))
    return bt * fraction(a, b, x) / a if x < (a + 1) / (a + b + 2) else 1 - bt * fraction(b, a, 1 - x) / b


def beta_quantile(q, a, b):
    low, high = 0.0, 1.0
    for _ in range(60):
        mid = (low + high) / 2
        if beta_cdf(mid, a, b) < q:
            low = mid
        else:
            high = mid
    return (low + high) / 2


def bayesian(rows, protocol):
    result = []
    for i, pair in enumerate(protocol["pairs"]):
        candidates = defaultdict(list)
        for row in rows:
            if row["pair"] == i and row["family"] and row["y"] is not None:
                candidates[row["family"]].append(row)
        for seed in protocol["seeds"]:
            chosen = [
                min(
                    rs,
                    key=lambda r: rank(
                        str(seed) + "/" + json.dumps([r[k] for k in ["av", "source", "member", "tags", "basis"]])
                    ),
                )
                for rs in candidates.values()
            ]
            n = len(chosen)
            k = sum(r["y"] for r in chosen)
            for a0, b0 in protocol["bayesian_sensitivity"]["priors"]:
                a, b = a0 + k, b0 + n - k
                mean = a / (a + b)
                entropy = -mean * math.log2(mean) - (1 - mean) * math.log2(1 - mean)
                conditional = (digamma(a + b + 1) - (a * digamma(a + 1) + b * digamma(b + 1)) / (a + b)) / math.log(2)

                def logbeta(u, v):
                    return math.lgamma(u) + math.lgamma(v) - math.lgamma(u + v)

                kl = (
                    logbeta(a0, b0)
                    - logbeta(a, b)
                    + (a - a0) * digamma(a)
                    + (b - b0) * digamma(b)
                    + (a0 + b0 - a - b) * digamma(a + b)
                ) / math.log(2)
                result.append(
                    dict(
                        a=pair["a"],
                        b=pair["b"],
                        selection_seed=seed,
                        known_families=n,
                        evidence_status="conditional_family_sample" if n else "prior_only_no_comparable_families",
                        positive=k,
                        prior=[a0, b0],
                        mean=mean,
                        interval_90=[beta_quantile(0.05, a, b), beta_quantile(0.95, a, b)],
                        posterior_prior_kl_bits=max(0, kl),
                        predictive_entropy_bits=entropy,
                        next_independent_trial_information_bits=max(0, entropy - conditional),
                        selected_scope_ids=[r["sid"] for r in chosen],
                    )
                )
    return dict(status="Assumption-conditional sensitivity; not calibrated linguistic confidence", results=result)


def permutation_strata(nodes, pos):
    strata = defaultdict(list)
    for cid, records in nodes.items():
        profile = tuple(sorted(length(k) for k in {r[0] for r in records}))
        strata[pos.get(cid, ""), profile].append(cid)
    return strata


def permutation(nodes, pos, rng, strata=None):
    """A bijection of whole concepts preserves simple incidences and profile degrees."""
    if strata is None:
        strata = permutation_strata(nodes, pos)
    inverse = {}
    mobile = 0
    for group in strata.values():
        group = sorted(group)
        targets = group.copy()
        rng.shuffle(targets)
        inverse.update(zip(targets, group))
        if len(group) > 1:
            mobile += len(group)
    return inverse, mobile


def incidence_null(db, protocol, concepts):
    reps = protocol["nulls"]["replicates"]
    rngs = [random.Random(1009 + i) for i in range(reps)]
    families = [defaultdict(set) for _ in range(reps)]
    observed = defaultdict(set)
    comparable = defaultdict(set)
    pos = {k: r["pos"] for k, r in concepts.items()}
    scope_meta = dict(db.execute("SELECT av,family FROM varieties"))
    avs = dict(db.execute("SELECT id,av FROM scopes"))
    excluded = Counter()
    scopes = mobile = total = 0
    backgrounds = defaultdict(lambda: [0, 0, 0.0])
    cursor = db.execute(
        "SELECT sid,cid,key,fid,param FROM valid WHERE layer='segmented' "
        "AND semantic<>'unreviewed_dictionary_sense' ORDER BY sid,cid"
    )
    for sid, group in itertools.groupby(cursor, key=lambda r: r[0]):
        nodes = defaultdict(list)
        ids = defaultdict(set)
        count = 0
        for _, cid, key, fid, param in group:
            count += 1
            if count > 20000:
                raise ValueError("Null scope reading budget exceeded")
            nodes[cid].append((key, fid, param))
            ids["f", fid].add(cid)
            ids["p", param].add(cid)
        conflicting = {cid for cs in ids.values() if len(cs) > 1 for cid in cs}
        excluded["concepts_with_shared_native_ids"] += len(conflicting)
        nodes = {cid: rs for cid, rs in nodes.items() if cid not in conflicting}
        keys = {cid: {r[0] for r in rs} for cid, rs in nodes.items()}
        family = scope_meta[avs[sid]]
        if not family:
            excluded["unknown_family_scopes"] += 1
            continue
        scopes += 1
        total += len(nodes)
        strata = permutation_strata(nodes, pos)
        # Background comparisons are descriptive cell pairs, not pure homophony.
        by_length = defaultdict(Counter)
        by_key = defaultdict(Counter)
        tokens = Counter(
            t
            for key in {r[0] for rs in nodes.values() for r in rs}
            for t in (json.loads(key)[1] if key.startswith("[") else key).split()
            if t != "+"
        )
        norm = sum(tokens.values()) + 0.5 * len(tokens)
        token_collision = sum(((n + 0.5) / norm) ** 2 for n in tokens.values()) if norm else 0
        for cid, rs in nodes.items():
            field = concepts[cid]["semantic_field"]
            for key in {r[0] for r in rs}:
                by_length[length(key)][field] += 1
                by_key[key][field] += 1
        for n, fields in by_length.items():
            size = sum(fields.values())
            pairs = (size * (size - 1) - sum(v * (v - 1) for v in fields.values())) // 2
            backgrounds[n][0] += pairs
            backgrounds[n][2] += pairs * token_collision**n
        for key, fields in by_key.items():
            size = sum(fields.values())
            backgrounds[length(key)][1] += (size * (size - 1) - sum(v * (v - 1) for v in fields.values())) // 2
        for j, p in enumerate(protocol["pairs"]):
            if p["a"] in nodes and p["b"] in nodes:
                comparable[j].add(family)
                if keys[p["a"]] & keys[p["b"]]:
                    observed[j].add(family)
        for rep, rng in enumerate(rngs):
            inv, m = permutation(nodes, pos, rng, strata)
            if set(inv) != set(inv.values()) or len(inv) != len(nodes):
                raise AssertionError("Null concept assignment is not bijective")
            if rep == 0:
                mobile += m
            for j, p in enumerate(protocol["pairs"]):
                if p["a"] in inv and p["b"] in inv and keys[inv[p["a"]]] & keys[inv[p["b"]]]:
                    families[rep][j].add(family)
    return dict(
        status="POS/profile-stratified incidence sensitivity null; independent scopes assumed; not a homophony model",
        replicates=reps,
        exclusions=dict(excluded),
        scopes=scopes,
        concept_instances=total,
        mobile_concept_instances=mobile,
        background_collision_sensitivity=dict(
            target="Cross-field same-token-length cell identities in the known-family native-ID-disjoint pool",
            length="Reported token count; may include tone tokens, not a validated segmental length",
            counterfactual="Independent unigram token draws at fixed lengths, fit on distinct keys per scope; "
            "add-.5 observed-vocabulary smoothing; in-sample sensitivity only, not calibrated homophony",
            strata={
                str(n): dict(cell_pairs=p, identities=k, unigram_expected=e) for n, (p, k, e) in backgrounds.items()
            },
            synthetic_uniform_form_collisions={"10_forms": 0.1, "100_forms": 0.01},
        ),
        pairs=[
            dict(
                a=p["a"],
                b=p["b"],
                observed_families=len(observed[j]),
                comparable_families=len(comparable[j]),
                null_counts=[len(f[j]) for f in families],
                empirical_upper_tail=(1 + sum(len(f[j]) >= len(observed[j]) for f in families)) / (reps + 1)
                if comparable[j]
                else None,
                evidence_status="sensitivity_null_only" if comparable[j] else "unknown_no_comparable_contexts",
            )
            for j, p in enumerate(protocol["pairs"])
        ],
    )


def run(root, built, destination):
    root, built, destination = Path(root), Path(built), Path(destination)
    seal = verify_database(built)
    protocol, concepts, protocol_hash = read_protocol(root)
    core_manifest = json.loads((built / "public/manifest.json").read_text())
    aggregate_hash = sha(root / "output/aggregate/forms.csv")
    if aggregate_hash != core_manifest["inputs"]["output/aggregate/forms.csv"]:
        raise ValueError("Audit aggregate differs from analytical core input")
    signature = dict(
        core=seal["build_id"],
        database_sha256=seal["database_sha256"],
        protocol_sha256=protocol_hash,
        pipeline_sha256=sha(Path(__file__)),
        cli_sha256=sha(root / "scripts/pilot_colexification_inference.py"),
        aggregate_sha256=aggregate_hash,
    )
    if destination.exists():
        raise ValueError("Use a new result directory; refuse to overwrite research outcomes")
    destination.mkdir(parents=True)
    db = sqlite3.connect(f"file:{built / 'index.sqlite'}?mode=ro", uri=True)
    db.execute("PRAGMA cache_size=-16000")
    db.execute("PRAGMA temp_store=FILE")
    db.execute("PRAGMA mmap_size=0")
    try:
        rows = list(contexts(db, protocol))
        print("Inference pilot: contexts", len(rows), flush=True)
        with (destination / "contexts.csv").open("w") as h:
            writer = csv.DictWriter(h, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        with (destination / "predictions.csv").open("w") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "task",
                    "fold",
                    "sid",
                    "pair",
                    "y",
                    "model",
                    "probability",
                    "heldout_group",
                    "train_n",
                    "train_positive",
                ],
            )
            writer.writeheader()
            evaluation = evaluate(rows, protocol, writer.writerow)
        print("Inference pilot: held-out predictions complete", flush=True)
        bayes = bayesian(rows, protocol)
        null = incidence_null(db, protocol, concepts)
        print("Inference pilot: null sensitivity complete", flush=True)
        audit = []
        for i in range(len(protocol["pairs"])):
            for state in [None, 0, 1]:
                candidates = sorted(
                    (r for r in rows if r["pair"] == i and r["y"] == state),
                    key=lambda r: rank("audit/" + str(i) + "/" + str(state) + "/" + str(r["sid"])),
                )
                for r in candidates[: protocol["audit"]["sample_per_pair_per_state"]]:
                    audit.append(
                        r
                        | dict(
                            definition_a=concepts[r["a"]]["definition"],
                            definition_b=concepts[r["b"]]["definition"],
                            review_status="pending_independent_review",
                            readings_a=json.dumps(
                                db.execute(
                                    "SELECT key,fid,param,word,semantic FROM valid WHERE sid=? AND cid=? "
                                    "AND layer='segmented' AND semantic<>'unreviewed_dictionary_sense' "
                                    "ORDER BY key,fid,param",
                                    (r["sid"], r["a"]),
                                ).fetchall(),
                                ensure_ascii=False,
                            ),
                            readings_b=json.dumps(
                                db.execute(
                                    "SELECT key,fid,param,word,semantic FROM valid WHERE sid=? AND cid=? "
                                    "AND layer='segmented' AND semantic<>'unreviewed_dictionary_sense' "
                                    "ORDER BY key,fid,param",
                                    (r["sid"], r["b"]),
                                ).fetchall(),
                                ensure_ascii=False,
                            ),
                            **{k: "" for k in protocol["audit"]["review_columns"]},
                        )
                    )
        wanted = {
            (r["av"], reading[1])
            for r in audit
            for field in ["readings_a", "readings_b"]
            for reading in json.loads(r[field])
        }
        originals = defaultdict(list)
        fields = [
            "concept_id",
            "source_form_id",
            "source_parameter_id",
            "transcription_source",
            "source_language_id",
            "Value",
            "Form",
            "Segments",
            "Segments_Source",
            "raw_ipa",
            "pronunciation_tags",
            "bibtex_key",
            "Comment",
        ]
        with (root / "output/aggregate/forms.csv").open() as handle:
            for row in csv.DictReader(handle):
                key = row["av_id"], row["source_form_id"]
                if key in wanted:
                    if len(originals[key]) >= 1024:
                        raise ValueError("Audit native record budget exceeded")
                    originals[key].append({k: row.get(k, "") for k in fields})
        for r in audit:
            for side in ["a", "b"]:
                r["aggregate_evidence_" + side] = json.dumps(
                    [
                        original
                        for reading in json.loads(r["readings_" + side])
                        for original in originals[r["av"], reading[1]]
                    ],
                    ensure_ascii=False,
                )
        with (destination / "audit_packet.csv").open("w") as h:
            writer = csv.DictWriter(h, fieldnames=list(audit[0]))
            writer.writeheader()
            writer.writerows(audit)
        result = dict(
            signature=signature,
            status="Exploratory recorded-identity inference; not independently adjudicated",
            protocol=protocol,
            contexts=len(rows),
            available=sum(r["y"] is not None for r in rows),
            unknown=sum(r["y"] is None for r in rows),
            positives=sum(r["y"] == 1 for r in rows),
            evaluation=evaluation,
            bayesian_sensitivity=bayes,
            incidence_null=null,
            audit_rows=len(audit),
            independently_adjudicated_rows=0,
            caveats=[
                "Purpose-selected panel, not worldwide pair distribution",
                "Source/family transfer tasks retain other forms of dependence",
                "Source/contact dependence not resolved by Bayesian context selection",
                "Null is conditional incidence sensitivity, not calibrated homophony or significance",
            ],
        )
        (destination / "results.json").write_text(json.dumps(result, indent=2) + "\n")
        if sha(Path(__file__)) != signature["pipeline_sha256"] or read_protocol(root)[2] != protocol_hash:
            raise ValueError("Inference code or protocol changed during the run")
        if sha(root / "output/aggregate/forms.csv") != aggregate_hash:
            raise ValueError("Audit aggregate changed during the run")
        (destination / "complete.json").write_text(
            json.dumps(
                dict(signature=signature, files={p.name: sha(p) for p in destination.iterdir() if p.is_file()}),
                indent=2,
            )
            + "\n"
        )
        return result
    finally:
        db.close()
