# Colexification: evidence, inference and information

Living research record begun 2026-11-01. Intended as the reproducible basis for
a future paper, not a finished manuscript or preregistered confirmatory study.

## Research questions and claims ledger

1. Which reported whole-form identities survive source/sense/representation review?
2. How much predictive information do other documented scopes provide for a
   held-out comparable source scope? How does this change across resources/families?
3. How sensitive are excess-association measures to the null, observation unit,
   dependence, coverage and priors?
4. Which additional linguistic annotations reduce uncertainty most effectively?

Current counts are fixed-corpus descriptions. New model probabilities concern
recorded identity conditional on a declared sampling frame, not semantic truth,
world prevalence, polysemy or cognitive universals. Missing evidence is unknown.
Source fidelity, identity, excess association and linguistic interpretation are
separate targets. A model can predict an extraction error accurately.

## Prior work and adversarial review

[Initial v2 method](../COLEXIFICATION_ROBUSTNESS_2026-11-01.md),
[independent adversarial reviews](../reviews/2026-11-01-adversarial-assessment.md),
[independent inference reviews and critical assessment](../reviews/2026-11-01-inference-assessment.md).
Both independent reviewer submissions are retained unmodified. Rejected prototype
claims and verified counterexamples remain part of the research history; they
are not accepted statistical results. In particular, no calibration claim follows
from 49 permutations and unvalidated Poisson tail extrapolation.

## Frozen exploratory protocol

Machine-readable protocol:
[frozen machine-readable protocol](https://github.com/tresoldi/arcaverborum/blob/a1379a1d28950ef622ccb056ce49104714f6f8f1/src/arcaverborum/data/colexification/inference_protocol.json).
Initial SHA256: `f21134924d34e2e259441fec272dbf8a880ca1c4c77bf99df8be89652cecf371`.
Created before running the corrected-core pilot. Earlier papers, reviews and old
corpus outcomes informed pair selection; this is not discovery-blind registration.
Amendments must retain the original protocol hash and explain the reason.

Eighteen targeted pairs include recurrent, sparse/localized, short-form,
mapping-error, contrast and catalog-overlap cases. Compare pooled/pair-smoothed
baselines and a regularized pair-plus-coverage predictor, using separate five-fold
resource-block and known-family transfer tasks. Hash-defined folds and train-only
preprocessing avoid outcome-based selection. Joint independence is not claimed.
Report proper log loss in bits, Brier score, baseline-relative predictive gain,
calibration bins and known-family macro scores. Unknowns are never negatives.

Bayesian sensitivity uses one outcome-blind hashed comparable context per known
family/pair, three fixed selection seeds and three declared Beta priors. Its
independence, measurement and selection assumptions remain explicit. Intervals
are model-conditional sensitivity results, not calibrated linguistic confidence.

The incidence-null pilot must preserve a simple incidence graph: use whole-concept
bijections within POS and full form-length-profile strata. Preserve group sizes
and concept degrees exactly, test these invariants, and label independent scope
randomization as a limited sensitivity null. Use empirical plus-one tails only;
no q-values or extreme-tail extrapolation. Form-collision checks are separate and
must not relabel cross-field identity as pure accidental homophony.

## Correctness repairs implemented before new inference

- Huntergatherer exact apostrophe-prefix truncations are held analytically across
  members, preserving native lexical records. This is a conservative source-specific
  guard, not a ban on short words or invented restoration of the lost reading.
- Canonical isolate family keys include dialects. Glottolog pseudo-categories
  are unknown genealogy for support, not extra independent lineages.
- Shared/local approval conflicts, local ambiguous parameters and explicit holds
  fail closed; exact record-level review has its own scope and precedence.
- Four definition-hash-bound catalog-overlap pairs are kept as reported identities
  but excluded from the replicated model. No automatic rule scans labels for “or”.

These repairs change analytical eligibility, not the accepted lexical records or
source pronunciations. Parser-level restoration/lexical rebuilding needs its own
source-specific notation review; original Value/Form evidence is retained.

## Validation and human review

A bounded stratified audit packet will include positive, sampled-nonmatching and
unknown contexts with definitions and native evidence. Mechanical checks can
verify provenance and internal consistency; they cannot supply independent human
adjudication. Reviewer, decision, evidence and linguistic-interpretation columns
remain explicitly pending unless an actual review is performed. No LLM or hash
selection is labelled an independent expert gold standard.

A pilot can therefore evaluate prediction of source observations now. Calibrated
probabilities of linguistic validity require a separately adjudicated sample and
an assessment of reviewer disagreement and source dependence.

## Executed methods and findings (2026-11-01)

The corrected sealed core is `346e40d2896330f6afc55400`; the recorded pilot is
`output/colexification-inference/2026-11-01-v1-1`. [Complete results](colexification_pilot_results_2026-11-01.json),
[execution/provenance ledger](colexification_pilot_execution_2026-11-01.json),
[implementation-version publication checks](colexification_pilot_publication_2026-11-01.json),
[independent SQL/score verification](colexification_pilot_verification_2026-11-01.json),
[secondary role diagnostics](colexification_pilot_role_diagnostics_2026-11-01.json).

### Data corrections and preservation

| Measure | Published predecessor | Corrected offline core |
| --- | ---: | ---: |
| Accepted lexical records | 2,119,818 | 2,119,818 |
| Reported segmented pairs | 44,414 | 42,741 |
| Reported written pairs | 43,669 | 42,201 |
| Reported reduced pairs | 508 | 508 |
| Replicated-backbone edges | 5,551 | 5,362 |
| Exact source-prefix holds | 88 | 3,921 |

The lexical aggregate SHA256 is unchanged. No reported pair was added; 3,141
layer/kind pair records were withdrawn (1,673 segmented and 1,468 written), not
3,141 independent lexical facts. Native records and readings remain intact.
The [source-hold ledger](colexification_source_holds_2026-11-01.json) covers 102
accepted varieties. These are conservative analytical holds for a known
source-parser pattern, not a claim of independently adjudicating 3,921 records.
Some counters for unmapped/reconstructed records change because the prefix guard
runs earlier; this is not improved lexical coverage. Restoring correct readings
requires source-specific notation review.

The four catalog relation flags are canonical *undirected pair exclusions*:
`contains` denotes containment in one direction, documented in the rationale;
it does not assert that lexicographically ordered endpoint A contains B. They
are not automatic WordNet entailments. Observed catalog-overlap identities are
retained and labelled separately from distinct-sense replicated inference.

### Observation and evaluation design

There are 98,784 potential scope/pair contexts: 28,633 comparable, 70,151 unknown
and 1,383 recorded positives. Unknown is not negative. Resource-block transfer
uses all comparable contexts; known-family transfer excludes 177 contexts with
unknown genealogy, leaving 28,456. The panel was purpose-selected using prior
knowledge, so none of these rates estimates world-language or world-pair
prevalence.

The regularized model has a pair intercept plus log coverage and the two mean
reported token-length descriptors. Token counts may include tone/prosody; they
are not certified phonemic lengths. Covariates are standardized on training data
only. A fixed quadratic penalty is 2 for pair coefficients and 1 for the three
metadata coefficients; the pooled training logit is an offset. A sparse Newton
solver with line search minimizes penalized Bernoulli negative log likelihood.
Exported predictions retain their raw probabilities; scoring and calibration bins
apply the declared 1e-6 probability floor. Numerical predictions agreed with
the initial dense solver to 1.67e-16 on a bounded synthetic comparison.

The task conditions on having these descriptors for a comparable held-out
scope, with identity strings hidden from the predictor. It is not forecasting
unknown words before collection. The model is potentially useful for reference
expectations and audit triage; it does not improve deterministic identity
extraction or certify source fidelity.

| Predictor | Held-out resource log loss, bits | Held-out family log loss, bits |
| --- | ---: | ---: |
| Pooled Laplace-smoothed rate | 0.283830 | 0.278905 |
| Pair-specific Laplace rate | 0.163779 | 0.160917 |
| Pair rate shrunk toward pooled, strength 10 | 0.162037 | 0.160177 |
| Regularized pair + coverage/length | 0.148765 | 0.147720 |

The complex model gains about 0.1351 and 0.1312 bits per test observation over
the pooled rate. Against the stronger smoothed-pair baseline, the extra gain is
only about 0.0133 and 0.0125 bits. Brier scores likewise improve overall, from
0.03389 to 0.03067 in resource transfer and 0.03347 to 0.03039 in family transfer.
These are descriptive held-out results on the declared panel, not significance
or calibration guarantees. Group separation retains other dependence through
sources, ancestry, contact and duplicated original fieldwork.

**Regional counterexample:** in South America the complex model is worse than
the simpler pair models. Resource-transfer loss is 0.18110 versus 0.17436 for the
shrunk pair predictor (2,676 tests); family-transfer loss is 0.17059 versus
0.16707 for the Laplace pair predictor (2,669 tests). Sparse-pair and overlap
subgroups also do not uniformly benefit. No universal model promotion is
justified by the overall average. Excluding overlap controls in a secondary
score stratification preserves the overall gain, but does not repair regional
variation or turn the purposive panel into a random sample.

### Bayesian information and selection sensitivity

For each pair and each of three fixed hash seeds, one comparable context is
selected without consulting its outcome from each known family. Priors are
Beta(1,1), Beta(1,9) and Beta(0.5,0.5); given k positives in n selected contexts,
the reference posterior is Beta(a+k,b+n-k). We report a 90% interval, posterior
KL relative to that prior, predictive entropy, and expected information from a
hypothetical new independent trial. The last three quantities are different.
The Beta CDF/quantile implementation is checked against analytic cases.

These are reference-model sensitivity calculations under accurate labels and
independent exchangeable families. Source/contact dependence and ascertainment
remain unresolved; no calibrated linguistic-confidence claim is made. TREE–WOOD
has 71 comparable known families but 27–36 selected positives across seeds;
posterior means span approximately 0.346–0.507 across seeds and priors. Selection
of an observation within a family can matter more than the prior.

BAG–WITCH has **zero comparable contexts in the admissible panel**, not a measured
zero propensity. Its Bayesian outputs are explicitly prior-only; its null tail
is undefined. Reporting amendment v1.1 corrects these no-data labels. Predictions,
score values and null draws are unchanged from v1. No hyperparameters or pairs
were tuned after reading the pilot scores.

### Incidence versus form-collision diagnostics

The incidence sensitivity null uses 49 whole-concept bijections within POS/full
length-profile strata. It preserves simple group and concept degrees, unlike
the earlier cell shuffle. The declared native-ID-disjoint pool has 1,325,681
concept instances across 5,362 known-family scopes; 1,233,797 instances belong
to movable strata. Independent scope shuffling is still a substantive and often
unrealistic dependence assumption. Plus-one empirical tails have resolution
0.02; no extreme-tail extrapolation, q-values or significance labels are used.

Examples of observed versus mean randomized family support:

| Pair | Observed families | Mean null families |
| --- | ---: | ---: |
| TREE–WOOD | 47 | 8.14 |
| MOON–MONTH | 48 | 4.69 |
| HEAD–MOTHER | 2 | 2.96 |
| FATHER–MOTHER | 3 | 6.94 |
| PATH–PATH OR ROAD, overlap control | 17 | 1.41 |

The overlap control demonstrates that exceeding a baseline does not establish
distinct-sense polysemy. Values below a null mean do not establish avoidance.
A sparse/immobile or unavailable comparison must not be called evidence against
an observed local relation. Recurrence, rare local identity and source fidelity
remain separate questions.

The separate form-collision sensitivity uses independent unigram token draws at
fixed reported lengths, with add-0.5 smoothing over the observed per-scope token
vocabulary. This is an in-sample counterfactual check. Cross-field cell identities
are also tabulated empirically, explicitly including real polysemy, overlap and
possible errors. Neither is a validated accidental-homophony rate, and neither
is subtracted from the observations to estimate polysemy. These diagnostics
expose assumptions to test in richer, phonologically reviewed inventories.

### Synthetic calibration checks

[Simulation data and code hashes](colexification_inference_simulations_2026-11-01.json)
record 500 fixed-seed prior-predictive replications of a Beta(1,1)/Bernoulli
reference with 20 independent units. These are synthetic checks, not real-data
calibration or a complete MCMC SBC experiment.

| Scenario | Coverage of nominal 90% interval | Mean interval width |
| --- | ---: | ---: |
| Correct independent reference | 90.0% | 0.2745 |
| Ten exact copies counted as independent | 38.4% | 0.0861 |
| Copies deduplicated using known provenance | 90.0% | 0.2745 |
| Unmodelled sensitivity 0.8 / false positives 0.1 | 68.8% | 0.3023 |

The copying case creates narrow false precision. The measurement-error case
has *wider* intervals yet poor coverage because the target is biased. These
stipulated error rates are not estimates for Arca. More elaborate priors or
wider intervals alone do not solve source and semantic errors.

### Human validation and remaining gates

The audit sample contains 146 cases: 41 recorded positives, 51 sampled nonmatches
and 54 unknowns; 18 cases are South American and nine North American. It is not
an independently adjudicated benchmark. Independent adjudications completed: **0**.

The prepared worksheet at
`output/colexification-inference/review-2026-11-01-v2/blinded_worksheet.csv` includes
original source rows, frozen definitions and native source sense labels where
available. It also exposes unreviewed/excluded records rather than presenting
absence of admissible readings as absence of source evidence. Model outputs,
selection roles, outcome labels and current semantic-gate judgments are omitted;
case order is hash-shuffled, curation comments are omitted, and the analyst join key is separate. Familiar pairs and visible forms limit full
blinding. Unresolved judgments must stay unresolved.

Next gates: actual independent linguistic adjudication; questionnaire availability;
original-source genealogy; phonological/morphological fidelity annotations; then
a new frozen, broader evaluation protocol. A within-family phylogenetic research
track requires appropriate trees and stage/contact evidence. No present result
identifies world prevalence, motivated polysemy or universal semantic communities.

### Reproducibility, resource use and failures

The corrected final core took 749.64 seconds with 110.06MiB peak RSS under a
256MiB address-space limit. A preceding behaviorally identical build had identical
statistics. Concurrent workloads affect timing; these are measured runs, not
hardware-normalized benchmarks.

The final pilot takes about one minute and peaks below 170MiB under the same
limit; exact version-specific values and software versions are in the execution
ledger. Independent SQL checks reproduce all comparable/positive labels, and
228,356 exported predictions reproduce scores and train/test counts. All accepted
lexical aggregate bytes are unchanged.

The first dense engineering run failed OpenBLAS allocation under the cap. Its
code/log and incomplete output are preserved; no results were accepted. The
sparse solver avoids a dense observation matrix and BLAS allocation. The optimized
null caches scope strata without changing seeded null draws. Versioned outputs,
protocol/code/input hashes, predictions and the private audit material retain the
execution history, including the reporting correction for no-data cases.

Reproduce locally with the pinned inputs available:

```bash
.venv/bin/python scripts/build_colexification.py --memory-mb 256
.venv/bin/python scripts/pilot_colexification_inference.py \
  --build output/colexification/346e40d2896330f6afc55400 \
  --output output/colexification-inference/NEW_RUN --memory-mb 256
.venv/bin/python scripts/verify_colexification_inference.py \
  --build output/colexification/346e40d2896330f6afc55400 \
  --pilot output/colexification-inference/NEW_RUN \
  --baseline output/colexification/d5c9b49da8851392bac2e2e0 \
  --output output/NEW_VERIFICATION.json
```

Raw/intake and large derived artifacts remain local, with hashes and provenance;
a fresh checkout alone is not a frozen-data replication archive. An eventual
paper needs an appropriate versioned data release. Experimental probabilities
are not wired into the public explorer. The deployed network remains the
published predecessor; this document reports the corrected offline research core.

## Paper development rules

Retain failures and null results; separate hypotheses from post-hoc explanations.
Publish all baselines, tested universes, availability rules, fold assignments,
priors, seeds, model versions, memory limits and code. Do not treat CLICS as an
independent gold standard when source material overlaps. Report Americas and
small-family consequences explicitly. No cognitive or historical explanation
follows merely from a statistically unusual or stable network cluster.


## Implementation version and literature anchors

The implementation, original reviews, frozen protocol and full pilot results are
versioned at commit `a1379a1d28950ef622ccb056ce49104714f6f8f1`. Subsequent closure
edits add provenance and references without changing the analysis. Exact file
hashes and runtime versions remain authoritative for replication.

These references motivate separate parts of the design; they do not collectively
validate this implementation or prescribe its modelling assumptions:

- [CLICS²](https://doi.org/10.1515/lingty-2018-0010),
  [CLICS³](https://doi.org/10.1038/s41597-019-0341-x),
  [CLICS⁴](https://aclanthology.org/2025.iwcs-main.1/): comparable lexical evidence,
  provenance and network construction.
- [Snee & List 2026](https://doi.org/10.15475/calcip.2026.1.2): detailed missing-data
  treatment in colexification comparisons.
- [Domagalski, Neal & Sagan 2021](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0244363):
  different bipartite null constraints answer different projection questions.
- [Gneiting & Raftery 2007](https://doi.org/10.1198/016214506000001437): proper
  predictive scores and their relationship to information measures.
- [Talts et al.](https://arxiv.org/abs/1804.06788),
  [Bayesian Workflow](https://arxiv.org/abs/2011.01808): computational calibration,
  predictive checking and model criticism, distinct from real-data validation.
- [Houlsby et al. 2011](https://arxiv.org/abs/1112.5745): information-based data
  acquisition; adapting it to source review needs a reviewer/observation model.
- [Peixoto 2018](https://doi.org/10.1103/PhysRevX.8.041011): structured Bayesian
  network reconstruction with uncertain measurements; a research option requiring
  justified generative structure here.
- [Pimentel et al. 2021](https://arxiv.org/abs/2109.13766),
  [Brochhagen & Boleda 2022](https://doi.org/10.1016/j.cognition.2022.105179):
  homophony baseline sensitivity and nontrivial semantic expectations.
- [Gfeller et al. 2025](https://arxiv.org/abs/2510.13407): family-specific
  phylogenetic investigation as a future, separately validated research track.


## Proposed continuation after the first pilot

The active [CINF-01–05 proposal](../NEXT.md) prioritizes real source validation,
South American reading recovery, original-source/questionnaire provenance, a
broader frozen experiment and a correctness-only public analytical refresh.
This is planning, not a new completed batch. Piaroa/Wa’ikhana/Yucuna together
supply 364 held-record candidates; potential recovery must be measured after
notation/sense review and must not be described as 364 new words or supported slots.
The new experiment needs streamed context storage before expanding the 18-pair
panel. Actual independent adjudication and original-source evidence remain the
basis for any measurement-error confidence claim.
