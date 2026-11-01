# Colexification inference: critical assessment and proposed research design

Date: 2026-11-01. Target: current v2 analytical core
`d5c9b49da8851392bac2e2e0`, code commit `9bc2ad28d8d64ba44530a74a696436aa0c92e78e`.
This is a research proposal, not an implemented estimator or new publication.
No production lexical records, graph weights or clusters changed.

## Independent reports and critical decision

The user-requested reviewers worked separately: [Codex (`gpt-6.1-terra`)](2026-11-01-inference-codex.md)
and [Claude Opus 5.5](2026-11-01-inference-claude.md). Each was instructed not to
read the other's new report. Claude CLI metadata confirms Opus 5.5 as the
reviewer and also records Haiku 5.5 helper usage. The initial reports were
independent; Codex subsequently answered the parent's methodological stress
questions without receiving Claude's proposal. Both reports are preserved
unmodified as reviewer submissions, not accepted specifications.

**Decision:** adopt Codex's held-out prediction/validation design as the first
inferential pilot, supplemented by explicitly experimental baseline and
prior-sensitivity comparisons inspired by Claude. Do **not** adopt Claude's
proposed calibrated p/q-values, chance-corrected polysemy labels, effective
independent-block counts or default posterior intervals as publication outputs.
The prototype is valuable for feasibility and exposing model sensitivity; its
inferential claims exceed what its null, selection and dependence treatment
justify.

### What survives critical assessment

* Both reviewers correctly separate fixed-corpus facts from inference and
  emphasize missingness, measurement, dependence and linguistic annotation.
  A prior does not create missing independent evidence or establish meanings.
* Claude demonstrates practical small-model and null-prototype feasibility,
  reporting 43–114MiB under 256MiB process limits. I inspected its scripts but
  did not rerun the 49-replicate (~8-minute) experiment. This is feasibility
  evidence for those scripts, not a verified production resource budget.
* Its empirical contrasts support investigating length, source notation,
  baseline choice and prior sensitivity. The reported rates are **recorded
  identity backgrounds**, not validated accidental-homophony estimates.
* Codex's proposal provides a clearer evaluation target and stronger safeguards
  against interpreting association as linguistic truth. Its model still needs
  audited labels, dependence-aware splits and sufficient observations; it is a
  design, not a fitted or validated estimator.

### Claims or prototype behavior I reject or qualify

1. **The reported 1,544 significant backbone edges are not established.**
   `calib.py` uses Poisson tail extrapolation from a mean estimated by 49
   permutations, ignoring uncertainty in that mean and without validating tail
   accuracy. Direct plus-one Monte Carlo p-values have minimum 0.02 at 49
   replicates; tails such as 1e-56 are parametric assumptions, not empirical
   permutation resolution. A Poisson approximation is not inherently forbidden,
   but its extreme tails and error rates must be independently justified.
   Applying BH does not validate its input p-values. Therefore 4,007 backbone
   edges failing this screen are not demonstrated chance-compatible or false.
   See [Phipson & Smyth 2010](https://pubmed.ncbi.nlm.nih.gov/21044043/) on random
   permutation p-values and multiple-testing consequences.
2. **The purported exact group-size-preserving shuffle does not preserve those
   sizes.** `perm_edges.py` shuffles repeated concept labels among cells and then
   collapses them with `groups[key].add(cid)`. For keys `[w1,w1,w2,w2]` and
   labels `[A,B,A,C]`, a permitted shuffle `[A,A,B,C]` changes unique group sizes
   from `[2,2]` to `[1,2]`. I verified this counterexample and found actual
   same-scope/same-length repeated concept labels in the database. It also does
   not carry native-ID eligibility through permutations. Matching the unshuffled
   edge count is a useful sanity check, not validation of the randomized state
   space. A simple-bipartite constrained sampler needs valid states and mixing
   checks before inferential use.
3. **Testing only observed edges is outcome-dependent selection.** Treating
   `m=observed edges` and `m=all pairs` as equally legitimate multiplicity
   conventions is unjustified without accounting for selection. A prespecified
   universe and valid p-values are needed; the dependence conditions behind the
   multiple-testing procedure also matter. Retain this as a sensitivity
   comparison, not two calibrated q-value conventions.
   [Benjamini & Yekutieli 2001](https://www.math.tau.ac.il/~ybenja/depApr27.pdf)
   establish specific dependence conditions and a conservative alternative;
   they do not make arbitrary p-value inputs valid.
4. **Cross-field identity is not pure accidental homophony.** It contains true
   cross-domain polysemy, overlap, shared morphology and known parser errors.
   A pooled long-form plateau does not prove that its entire mass is non-chance,
   nor identify a removable constant floor. Subtracting `3.8e-4` and flooring
   the result at `1e-6` in `pairs.py` is an unvalidated modelling choice. Neither
   this background nor its subtraction identifies aggregate motivated identity
   in the presence of unknown source error and ascertainment.
5. **The baseline event must match the observed event.** `pairs.py` unions
   positives across varieties for a language but averages their chance rates;
   it also picks a source scope with positive precedence. Two independent
   varieties with marginal chance 0.1 have any-positive chance 0.19, not 0.1.
   Selecting a positive source to define the baseline is outcome-dependent.
   Compare matched source-scope events first, or model the union and its
   dependence explicitly. The raw-prototype eligibility and classification also
   differ from the accepted backbone's gates, as Claude acknowledges.
6. **Independence is not a universal upper bound for union probability.**
   `1-prod(1-p)` is the independent case. Two mutually exclusive events each
   with probability 0.5 have union 1, exceeding the independent 0.75. General
   bounds are `max(p_i) <= P(union) <= min(1,sum p_i)`. Positive dependence may
   make independence a useful sensitivity extreme in a specified model, not a
   distribution-free bound. The prototype's "upper bound" language is wrong.
7. **Diversity is not independence or effective sample size.** Hill numbers
   describe concentration across labels. Two equally weighted exact copies
   have D2=2 but one independent original. Likewise a one-way ANOVA ICC and a
   simple design-effect correction do not establish ESS under unequal family
   sizes, crossed resource dependence, contact and heterogeneous binary rates.
   Use concentration/ICC as descriptive diagnostics, not certified information
   counts. Multiplying plug-in KL by such an ESS is not a calibrated evidence
   total.
8. **The Bayesian prototypes are conditional sensitivity exercises.** Their
   fixed chance rates, missingness assumptions, independent families, finite
   grids, restricted concentration grid and no measurement error preclude
   treating the displayed intervals as validated linguistic confidence. The
   positive-only excess model cannot estimate negative association. Posterior
   KL relative to a prior is realized model-relative update, not an intrinsic
   amount of evidence; expected review information is a different quantity.
9. **Some literature interpretations are too restrictive.** Claude says
   measurement-error network models need repeated or annotated edges, but
   Peixoto 2018 explicitly permits single measurements through a structured
   generative network model. Such structure adds assumptions that require
   validation here; it is not equivalent to repeated observations or automatic
   identification from lexical data alone. Its use is a research option, not
   ruled out categorically by lack of repeats.

The toy counterexamples are recorded in the linked verification JSON below.
Claude's separate Ventureño prefix-truncation lead was independently checked
against retained aggregate Value/Form/Segments fields, but is not used here to
validate its statistical model. Source repairs remain in the preceding review's
work queue. Its scripts and outputs are archived privately under
`raw/curation/colexification-inference-2026-11-01/claude/`, with exact hashes in
the [experiment manifest](2026-11-01-inference-experiment-manifest.json).

### Research extension worth retaining

Claude identifies a directly relevant phylogenetic study:
[Gfeller, Stoll, Cathcart & Widmer 2025](https://arxiv.org/abs/2510.13407).
I verified the primary abstract: it models colexification dynamics in
Austronesian, Indo-European and Uralic with associativity, borrowability and
usage frequency, reporting considerable family differences. This supports a
curated within-family research track, not a ready worldwide estimator. The
primary homophony debate also supports baseline scrutiny:
[Pimentel et al. 2021](https://arxiv.org/abs/2109.13766) change conclusions after
correcting a baseline methodological issue. Neither paper validates our null.

## What we should estimate

A single confidence score would conflate several different questions:

| Quantity | Meaning | Main evidence required |
| --- | --- | --- |
| Evidence fidelity | Did we preserve and interpret the source correctly? | Original readings, senses, extraction/profile review and independently adjudicated samples |
| Recorded identity probability | Will another comparable scope record this identity? | Explicit coverage, outcomes, scope and train/test design |
| Excess association | Is this pair more associated than a named baseline predicts? | A justified null/reference model, uncertainty and dependence treatment |
| Linguistic interpretation | Polysemy, homonymy, broad sense, morphology, catalog overlap or error? | Lexeme/sense/context evidence; identity and recurrence alone do not settle this |
| Community uncertainty | How does a partition vary under data and model uncertainty? | Multiple defensible network models and, if Bayesian, a validated generative likelihood |

The immediate estimand should be conditional on this collection and its sampling
protocol, not an unspecified population of world languages. For a fixed pair
`e` and source scope `s`, define `A_se=1` only when both meanings have usable,
semantically admissible comparable evidence. Define `Y_se=1` for permitted exact
identity, `Y_se=0` for sampled nonidentity, and leave it undefined when `A_se=0`.
The first predictive target is `P(Y_se=1 | A_se=1, declared frame/covariates)`.
Unreviewed mappings must not become negative observations. Separate source
scopes, historical stages and representation layers remain separate.

Counts in a fixed, completely observed database are deterministic descriptions.
An uncertainty interval must say whether it concerns measurement, completion of
missing records, transfer to new scopes, model parameters or something else.

## What information theory can give us

The most immediately useful information measure is held-out predictive gain:

```
G = mean_i log2( P_model(Y_i | training data) /
                 P_baseline(Y_i | training data) ).
```

Positive gain means the model makes the specified test observations less
surprising than the specified baseline. It is measured in bits per test case;
it can be negative. It is not automatically mutual information, cognitive
information, a Bayes factor for a universal semantic relation or evidence that
the observations are linguistically correct. A model can predict parser errors.
Use a separate blinded fidelity evaluation. Evaluate log loss and Brier score,
calibration and sample counts together; for rare outcomes, an apparently small
Brier score can simply reflect a low event rate. Proper scores support this
evaluation, not a guarantee of external validity
([Gneiting & Raftery 2007](https://doi.org/10.1198/016214506000001437)).

Bayes and information theory also meet in a useful uncertainty decomposition:

```
H(Y_new | D) = E_theta[H(Y_new | theta,D)] + I(Y_new; theta | D).
```

The first term describes outcome variability under a fixed model state; the
second is expected information a new observation provides about the uncertain
state. A next-outcome probability of 0.5 could mean a known fair coin (one bit
of predictive entropy, zero information about its already known rate) or an
unknown choice between always-heads and always-tails coins (one bit, all about
the uncertain rate). The same point prediction therefore does not establish
how much has been learned. In a stipulated Beta(2,1) Bernoulli model, the next
independent trial has predictive entropy 0.918 bits but expected information
about the rate only 0.197 bits. A copied observation is not such an independent
trial. This is an operational way to quantify what a review could teach us,
once its observation/measurement model is defensible; it is not a measure of
human semantic information or a substitute for source validation.
An information-theoretic acquisition framework is developed by
[Houlsby et al. 2011](https://arxiv.org/abs/1112.5745); adapting it to linguistic
review requires the observation and utility assumptions above.

Do not estimate communicative efficiency from dictionary entry counts as if they
were usage frequencies. Shannon measures require a specified distribution over
meanings/forms/contexts. A uniform concept-panel task is a possible explicit
convention, not an empirical estimate of communicative need. Small-sample
entropy/MI estimates also have serious bias problems
([Paninski 2003](https://www.cns.nyu.edu/~lcv/pubs/makeAbs.php?loc=Paninski03)).

Information gain for choosing a review can be defined as expected KL divergence
between updated and current parameter distributions, conditional on a model of
review outcomes and reviewer reliability. This is a future acquisition tool,
not an identifiable priority score now. Combine it with repair impact, review
cost, exploration and regional coverage. Pure gain maximization can neglect
isolates and poorly documented American languages.

## Three baselines, three different questions

1. **Predictive baselines:** smoothed training prevalence, pair-specific rates,
   then simple coverage/representation predictors. Compare a regularized model
   to these before calling it useful. Recompute current robustness scores on
   training evidence only if using them as features; the full-data score leaks
   held-out outcomes.
2. **Incidence null:** randomize concept/group membership under stated scope,
   coverage and degree constraints. This asks whether this particular pair's
   co-membership is unusual given observed ambiguity and sampling margins. It
   does not estimate accidental homophony: shared-form groups are held fixed.
   Constraints, connected swap spaces, mixing, multiplicity and null selection
   matter. Projection nulls with different degree constraints test different
   hypotheses ([Domagalski, Neal & Sagan 2021](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0244363)).
3. **Form-collision null:** generate lexical forms under a separately justified
   variety/source model. For independent draws, collision probability is
   `sum_w P_a(w) P_b(w)`; the common-distribution special case is
   `sum_w P(w)^2`. Length, syllable structure, tone, phonation, quantity,
   morphology and transcription loss affect this probability. Rich reviewed
   inventories are needed; unigrams and tiny lists cannot supply reliable
   universal probabilities. Synonyms require set-overlap probabilities rather
   than a single two-draw formula. Such a model still does not prove polysemy.

Independent label shuffles across copied dictionaries or inherited observations
can manufacture extreme null results. Dependence needs a joint null mechanism,
not merely a post-hoc family count. Restrict the initial null pilot to a curated
frame whose assumptions can be defended; use wider nulls as sensitivity checks.
Mechanistic lexical baselines can produce apparently functional correlations
without the proposed functional pressure
([Caplan, Kodner & Yang 2021, summarizing their 2020 study](https://aclanthology.org/2021.scil-1.33.pdf)).

A null conditional on test-data degree margins can be legitimate as a
conditional test but must not be presented as a prospective prediction using
only training information. The predictive and conditional-null experiments
need separate manifests and labels.

## Bayesian confidence: useful, conditional and sometimes unidentified

A modest partially pooled model is a candidate, not an automatic upgrade:

```
Y_se | A_se=1 ~ Bernoulli(p_se)
logit(p_se) = alpha_e + beta X_s + u_family(s) + v_resource(s).
```

The family effect here is only a coarse dependence proxy; it does not model a
tree or pair-specific inheritance. Compare simpler models before adding
pair-by-family effects, phylogenetic covariance or contact. Source and family
effects can be confounded: when their membership is identical the likelihood
learns only their sum. Priors can select an allocation without the data
identifying it. Unknown classifications are not one invented family.

Pairwise prediction is also not a complete generative model of a lexicon.
With exactly one form per meaning, A=B and B=C require A=C; with synonyms,
overlapping form sets can yield different pair relations. Independent pairwise
Bernoulli draws need not respect the stipulated lexical structure. A marginal
prediction pilot can still be useful, but must account for shared-scope
dependence in evaluation and must not generate supposedly coherent posterior
lexicons or community confidence by independently sampling its edges. A future
joint model should retain lexical groups/sets and their availability constraints.

Separately, a measurement model could connect recorded `Y` to a carefully
defined latent linguistic state `Z`. With sensitivity `s`, false-positive rate
`f` and latent positive rate `theta`,

```
P(Y=1) = s theta + f (1-theta).
```

An observed rate 0.2 is compatible with `(theta,s,f)=(0.2,1,0)`,
`(0.4,0.5,0)` or `(0,1,0.2)`. One observed rate cannot distinguish these.
Source-mapping error and phonological collision are not necessarily the same
measurement process; true homonymy is an identity, not an error in the
colexification observation. Validation labels must distinguish these targets.
Repeated derivative sources do not supply independent measurements. Classical
latent-class identification itself requires substantive population and
conditional-independence assumptions
([Hui & Walter 1980](https://pubmed.ncbi.nlm.nih.gov/7370371/)).

Bayesian models can still give useful explicitly conditional intervals. State
priors and external error evidence, perform prior/posterior predictive checks,
compare materially different plausible error and missingness assumptions, and
show where the prior dominates. Simulation-based calibration checks computation
under the assumed model, not whether real lexical data follow that model
([Talts et al.](https://arxiv.org/abs/1804.06788),
[Bayesian Workflow](https://arxiv.org/abs/2011.01808)).

For example, if a rate 0.2 were known and sensitivity were stipulated to lie in
`[0.6,1]` and false-positive rate in `[0,0.05]`, possible latent rates range from
about 0.158 to 0.333. These are assumption-based identification bounds, not
Arca estimates or a 95% interval. Human validation is valuable because it can
constrain these nuisance rates, rather than because a prior makes them vanish.

Network-reconstruction models such as
[Peixoto 2018](https://journals.aps.org/prx/abstract/10.1103/PhysRevX.8.041011)
are relevant research options. Their structured generative assumptions supply
information and must be tested here. Projected colexification edges share
hyperedges, source processes and overlapping concepts; a generic independent
edge likelihood can produce false precision. There is also no self-evident
binary universal semantic graph waiting to be reconstructed.

## Concrete checks of the reasoning

[Toy checks and the bounded design query](2026-11-01-inference-toy-checks.json)
contain synthetic calculations, not fitted production confidence scores:

* Under a stipulated independent noiseless Bernoulli model and Beta(1,1) prior,
  one success gives Beta(2,1), with central 95% interval approximately
  `[0.158,0.987]`. Treating 100 exact copies as independent instead gives
  Beta(101,1), interval `[0.964,0.99975]`: unjustified precision in this toy.
* A four-concept/two-group label null gives target-pair co-membership probability
  `1/3`. Independently randomizing 100 exact copies assigns probability
  `(1/3)^100 ≈ 1.94e-48` to all being positive; randomizing copies jointly leaves
  probability `1/3`. This is not a calibrated null for the production corpus.
* In a fixed completion frame with 20 positive, 80 sampled nonmatch and 100
  unknown scopes, the completed positive fraction lies in `[0.10,0.60]` if known
  outcomes are accepted as correct. The observed comparable rate is 0.20.
  These bounds require a defined completion protocol, not just counting absent
  entries; they do not bound worldwide prevalence or remove measurement error.
* The current positive-witness family/resource incidence subgraph has a connected
  component containing 306 family keys and 144 resource blocks. This uses
  current, not yet repaired classifications and is not a full coverage audit.
  Connectivity does not prove every observation dependent, but shows why
  component-based joint holdouts may be uninformative or infeasible.

## Recommended bounded pilot

1. Repair the demonstrated extraction/classification/approval defects in the
   previous review before using the analytical outputs as trustworthy labels.
   Freeze the snapshot, observation/availability protocol and review target.
2. Select a fixed, stratified panel of pairs and sources, including positives,
   sampled nonmatches and unknowns. Include short/long forms, catalog-overlap
   controls, surprising pairs and Americas/small-family cases. Record selection
   probabilities where population/frame summaries are intended. Purposeful
   challenge cases remain a separate benchmark, not a prevalence sample.
3. Independently adjudicate source fidelity, exact sense equivalence and
   representation for a manageable validation sample. Preserve unresolved
   outcomes and disagreement. Document original fieldwork and derivatives,
   questionnaire coverage, lexeme identity, stage and notation. Missing loan or
   cognacy flags mean unknown, not absence.
4. Compare baselines with a simple regularized predictive model, then a Bayesian
   version if it adds useful uncertainty. Use separate leave-source-lineage,
   leave-family and leave-area experiments with their conditional targets.
   When joint independence is infeasible, report the overlap rather than claim
   a clean dual holdout. Include a prospective original-source test if possible.
5. Report held-out information gain, calibration, annotation fidelity, sample
   sizes and missingness/error-prior sensitivity by region and basis. New-source
   prediction for known pairs and prediction of unseen pairs are different tasks.
   Fix target pairs and thresholds before testing; positive-only or balanced
   samples cannot calibrate probabilities for the full pair universe without a
   sampling correction and a declared target distribution.
6. Pilot incidence and phonological nulls separately. Do not turn their tail
   probabilities, posterior contrasts or predictive skill into one confidence
   score. Keep all observed evidence visible; only consider default graph changes
   after the comparison supports them.

Use SQLite streaming of only selected pairs, sparse features, sequential workers
and explicit time/disk/address-space budgets. No dense scope-by-all-pair matrix.
Model-fitting library overhead and approximation accuracy must be measured;
an elaborate MCMC model is not promised to fit 256MiB. Posterior samples and null
statistics can be processed in bounded batches. No production experiment was
run as part of this review.

External semantic information, including reviewed WordNet relations, can be an
explanatory covariate or a separate baseline, with missingness and English-pivot
bias disclosed. It must not define the truth label or filter surprising edges.
Use semantic-feature ablations and leave-pair/concept tests if claiming novel
semantic prediction. A high semantic similarity is not a universal monotonic
colexification expectation
([Brochhagen & Boleda 2022](https://doi.org/10.1016/j.cognition.2022.105179)).

## What a future edge assessment should show

Keep separate fields for reported identities and sampled nonmatches/unknowns;
source-fidelity and sense-review status; expected support under each named
baseline; effect magnitude and its model-conditional interval; held-out
predictive performance where enough tests exist; and resource/family/model
sensitivity. An uncertainty interval for an excess-association effect must name
its reference frame and baseline. Do not call it the probability that the edge
is true polysemy. Small or local observations can be genuine even when global
generalization remains weak. Model probabilities should carry their version,
target, validation status and assumptions alongside downloadable evidence.
