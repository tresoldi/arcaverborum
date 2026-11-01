# Arca Verborum colexification: what can be inferred, how confidently, and against which baselines

**An independent methodological research review (information theory, Bayesian inference and transparent baselines)**

- **Reviewer model:** `claude-opus-5-5` (Claude Opus 5.5), run as a Claude Agent SDK agent.
- **Date:** 2026-11-01.
- **What was reviewed:** repository HEAD `9bc2ad28d`, sealed analytical build `d5c9b49da8851392bac2e2e0`, segmented layer unless stated otherwise.
- **Independence:** I did not read any `2026-11-01-inference-codex*` or `2026-11-01-inference-assessment*` report, and I did not communicate with other reviewers. As permitted, I read the earlier adversarial reviews and assessment for context.
- **No changes were made.** No repository file, dataset, algorithm, commit, push or deployment was touched; `git status` is the same as at the start. All experiments were read-only (`mode=ro&immutable=1`), each process ran under `ulimit -v 262144` (256 MiB), and peak RSS was 43–114 MiB. Scripts and outputs are in `/home/agent/scratch/colexinf/`, outside the repository.

---

## 0. Executive summary

1. **Arca currently reports a corpus fact, not an estimate.** The current layer records source-scoped exact identity. Its weights (family counts, unit group mass, minimax deletion) are robustness diagnostics. None of them estimates a defined population quantity, and none is calibrated against chance. The docs say this honestly. My recommendation is to keep the descriptive layer as the base and add *explicitly defined estimands* on top of it. It should not be replaced by "a Bayesian model".

2. **Chance homophony is large, strongly length-dependent and model-sensitive. It has to be estimated empirically, not assumed.**
   - The pooled per-pair identity rate within a scope is 3.3×10⁻⁴.
   - Between concepts from *different* semantic fields, the identity rate for same-length forms falls from **0.15 at 1 segment** to 9.5×10⁻³ at 2, 1.8×10⁻³ at 3 and 7.8×10⁻⁴ at 4. From 6 segments upwards it **plateaus at about 4×10⁻⁴**. A plateau cannot be chance: it is a floor made of real cross-field polysemy, derivation, mapping and extraction errors.
   - Three textbook phonotactic nulls (unigram, length-conditioned bigram, bigram with an end state) predict 0.07× to 12× the observed cross-field identity count. They are not usable as calibrated baselines.

3. **A conditional label-permutation null is cheap and informative.** It shuffles concept labels among same-length forms within each source scope, which keeps every scope's homophony structure exactly.
   - One replicate takes 9 s at about 93 MiB; 49 replicates peaked at 114 MiB.
   - Under this null, **≈10,000 edges reach ≥2 families and ≈2,000 reach ≥3 families**. Observed: 7,234 and 3,422.
   - The plug-in null expectation for the observed edges is 983 for ≥3 families, 158 for ≥5 and 3 for ≥10. Family-count thresholds below about 5 are therefore not calibrated filters at Arca's scale.

4. **The current replicated backbone mixes chance-compatible pairs with strong ones.**
   - Of 5,551 backbone edges, **1,544 pass** a conservative Benjamini–Hochberg screen against the permutation null (q<0.05, m = all catalog pairs). 4,007 do not pass.
   - Some backbone edges are *below* chance. I–THOU: 3 families observed vs 11 expected under permutation, 7.75 under the analytic length null. FATHER–MOTHER: 5 vs ≈6.
   - Conversely, 248 non-backbone edges are far above chance. Some of these are clearly **single-source elicitation artefacts**: LOWER LEG–UPPER LEG has 42 families, all from one source (`johanssonsoundsymbolic`), with p≈10⁻⁵⁶ against chance.
   - So a chance null and a source-dependence safeguard detect **different** failure modes. Neither replaces the other.

5. **Dependence is substantial and measurable.** For frequent edges, the within-family intraclass correlation of language-level positives is 0.27–0.34. Effective sample sizes are 29–42% of the language-unit counts (e.g. TREE–WOOD: n_eff ≈ 206 of 716).

6. **Measurement error is mostly not identifiable with current data.**
   - Only 282 Glottolog language units have two or more distinct segmented sources.
   - For top edges there are at most about 50 within-language source pairs, often with zero concordant positives.
   - Latent-truth models (Dawid–Skene, Hui–Walter) therefore need either pooled source-class parameters with strong assumptions, or a new adjudicated gold sample. A prior does not fix this.

7. **Priors move answers when information is weak, and "information gain" is prior-relative.**
   - In a chance-corrected family-presence model, TREE–WOOD (76 families) has a posterior mean excess propensity of 0.65 under Beta(1,1) but 0.47 under Beta(1,30).
   - Over the same data, the Lindley information gain is 2.2 vs 23.9 bits.
   - For weak pairs, log₁₀ Bayes factors range from −2.3 to −0.2 depending on the prior.
   - Bayes factors against chance are enormous for common pairs (log₁₀ BF ≈ 105 for TREE–WOOD), but they only reject a model nobody believes.

8. **Side finding: a data defect not covered by the existing guards.** Ventureño (Huntergatherer member 40) has `Value=k'oko "my fa"` and `k'ete "my mother"`, but `Form=k`, `Segments=k`. This is the same apostrophe-prefix truncation already documented for members 30 and 43. It produces a FATHER–MOTHER witness. The length-aware null automatically assigns it a high chance probability (0.15), which shows that short-form diagnostics have value beyond chance correction.

9. **Recommended MVP (fits in 256 MiB):** an additive diagnostics layer per observed edge, holding:
   1. family-level observed vs chance-expected support from an empirical, shrunk, length-stratified chance model;
   2. a permutation-calibrated tail probability with BH q-values under two declared m conventions;
   3. a posterior interval for chance-corrected excess propensity under two declared priors;
   4. dependence summaries: ICC/n_eff, and the effective number of resource blocks (Hill numbers);
   5. flags such as short-form share and single-block share.

   Nothing would be deleted. The default graph would stay as it is until the sensitivity contrasts have been published.

---

## 1. What the current pipeline actually estimates

Sources: `docs/COLEXIFICATION.md`, `docs/COLEXIFICATION_ROBUSTNESS_2026-11-01.md`, `src/arcaverborum/colexification.py` (ingest/infer/pair_status), `src/arcaverborum/colexification_evidence.py` (`SemanticEligibility`, `summarize`, `assess`).

- **Observation unit:** a *source scope* `s = (variety, source, member, pronunciation tags, basis)`. A scope contains readings `(key, concept)`. An **identity group** `g = (s, layer, key)` with `k ≥ 2` distinct concepts produces witnesses for every pair, provided the native form ID and native parameter ID both differ. Groups with k>64 are quarantined.
- **Edge statistics:**
  - counts of distinct varieties, language units and families;
  - pair mass `m(g) = 1/C(k,2)`;
  - `A(e) = Σ_f max_r q(e,f,r)` and `R(e) = min over deleted blocks` (see `summarize`);
  - backbone eligibility: at least 2 eligible families and `R>0`.
- **Three-way comparison** (`pair_status`): positive / sampled non-match / unknown, with a descriptive comparable-variety fraction.
- **Status:** these are deterministic summaries of a convenience corpus. They contain no generative model, no chance correction, no dependence model and no model of measurement error. The documentation explicitly disclaims probability and significance, which is correct. The gap is that **no stated estimand** sits behind the backbone weight, so its numbers cannot be "right" or "wrong", only more or less robust.

---

## 2. Estimands: separate what is being claimed

Each level adds assumptions. Each claim should be tagged with the level it belongs to.

| Level | Estimand | Unit | What it needs beyond the level above | Can Arca estimate it now? |
|---|---|---|---|---|
| **E0 – corpus fact** | `D_{s,e} ∈ {1, 0, NA}`: exact recorded identity / sampled non-match / not comparable | source scope | – | **Yes** (already done) |
| **E1 – lexical identity in a variety** | `Z_{ℓ,e}`: the variety's lexicon has one form covering both defined senses | language unit ℓ (or variety) | a measurement model linking D to Z (sensitivity, false identity) | Partially. False identity can be bounded; sensitivity is mostly unidentified (§6) |
| **E2 – motivated identity (polysemy) vs homophony** | `W_{ℓ,e}`: identity is semantically motivated rather than accidental | ℓ | a chance-homophony model, plus etymological/lemma annotation for individual cases | **In aggregate, yes** (excess over chance, §4). **Per case, no** without annotation |
| **E3 – cross-linguistic propensity** | `θ_e` (or the excess `ψ_e`): probability that a randomly drawn lineage from a *declared* population shows E1/E2 | lineage (family), or one language per family | sampling frame, dependence model, missingness assumptions | Model-based, with explicit weights. Not a census of the world's languages |
| **E4 – diachronic dynamics** | gain/loss rates and stationary probability of colexification on trees | branch | dated trees, cognacy, CTMC model | Only for families with trees and dense coverage. Offline (Pelle/EOSC) |
| **E5 – cognitive association** | strength of conceptual association | speakers/concepts | external measures (norms, experiments) | **No.** Colexification is at most a correlate |

Key consequences:

- "Colexified in 50 families" is E0. "TREE–WOOD colexification is common" is an E3 claim and needs a population and weights. "TREE and WOOD are cognitively close" is E5 and is not licensed by any of the data here.
- **Homophony is a real lexical fact (E1), but it is not polysemy (E2).** Chance correction estimates E2-type excess *in aggregate*. It cannot classify a single identity.
- **The definition of the unit changes the number.** In my toy runs the family-presence propensity for TREE–WOOD is 0.65, while the family-averaged language-level rate is 0.47. Family presence ("≥1 language in the family positive") grows with family size and sampling depth. Prefer "one random language unit per lineage", or a hierarchical mean over lineages. Do not use family presence as a propensity.

---

## 3. A generative model (latent truth plus measurement)

### 3.1 Structure

For a concept pair `e = (a, b)`, lineage `f`, language unit `ℓ ∈ f` and source scope `s ∈ ℓ`:

```
Lineage/semantic level:   logit θ_{ℓe} = α_e + u_{f(ℓ),e} + v_{area(ℓ),e}       (u, v: genealogical / areal effects)
Latent motivated identity: W_{ℓe} ~ Bernoulli(θ_{ℓe})
Accidental homophony:      H_{ℓe} ~ Bernoulli(h_{ℓe}),  h_{ℓe} = c_ℓ(L_a, L_b, tone, inventory)
Lexical identity:          Z_{ℓe} = W_{ℓe} ∨ H_{ℓe}
Measurement (scope s):     P(D_{se}=1 | Z=1) = σ_s(e)     # sensitivity: both senses elicited, same lexeme chosen, notation faithful
                           P(D_{se}=1 | Z=0) = φ_s(e)     # false identity: mapping error, truncation, notation merger, catalog overlap
Comparability:             R_{se} = 1 if both meanings have separately identifiable usable records (else D=NA)
```

The marginal, which is what the data constrain:

```
P(D_{se}=1 | R=1) = σ_s [1 − (1−θ)(1−h)] + φ_s (1−θ)(1−h)
```

### 3.2 Identifiability (the core limitation)

With one scope per language and one observation per pair, the data identify only a single number per cell, the marginal rate. A worked toy:

- (θ=0.30, σ=0.80, φ=0.002, h=0.0005) gives P(D=1) = 0.8·0.30035 + 0.002·0.69965 ≈ **0.2417**.
- (θ=0.25, σ=0.96, φ=0.002, h=0.0005) gives 0.96·0.25037 + 0.002·0.74963 ≈ **0.2418**.

The prevalence and sensitivity trade off along a ridge. A prior picks a point on that ridge. It does not learn which point is right.

What breaks the ridge:

- **Repeated measurement of the same latent Z.** Two or more conditionally independent sources for the same language. Hui–Walter needs two tests in two populations with different prevalence ([Hui & Walter 1980](https://jhanley.biostat.mcgill.ca/bios601/CandH-ch0102/HuiWalter1980.pdf), Biometrics 36:167–171, doi:10.2307/2530508). Dawid–Skene-style confusion models need several raters ([Dawid & Skene 1979](https://ideas.repec.org/a/bla/jorssc/v28y1979i1p20-28.html), doi:10.2307/2346806).
- **A gold sample**, i.e. adjudicated readings.
- **Structural constraints**, e.g. σ shared by a source class across many pairs.

**What Arca has now:** 282 language units with two or more distinct segmented sources. Within-language source-pair concordance for top edges (`within_lang.py`):

| Pair | both + | discordant | both − | implied symmetric σ (if φ≈0) |
|---|---|---|---|---|
| TREE–WOOD | 7 | 3 | 6 | 0.82 |
| MOON–MONTH | 9 | 3 | 6 | 0.86 |
| ARM–HAND | 0 | 3 | 9 | 0.00 |
| SUN–DAY | 0 | 3 | 41 | 0.00 |
| MAN–PERSON | 0 | 5 | 30 | 0.00 |
| NECK–THROAT | 0 | 1 | 17 | 0.00 |

These counts are tiny, and "same language unit" can still mean different dialects or stages. The zero-concordance rows strongly suggest **source/questionnaire effects** (whether a broad term was elicited) rather than lexical variation. Per-edge sensitivity is therefore **not estimable now**. At most, a pooled source-class σ could be estimated, under a conditional-independence assumption that compilations sharing upstream data violate. This is also the honest reading of [Peixoto 2018](https://doi.org/10.1103/PhysRevX.8.041011) and [Newman 2018](https://arxiv.org/abs/1703.07376) (Nature Physics 14:542, doi:10.1038/s41567-018-0076-1): measurement-error network models need repeated or annotated observations of the same tie.

### 3.3 Missingness

`R_{se}=0` arises from four different mechanisms:

1. the concept was not in the questionnaire;
2. it was elicited but not extracted or mapped;
3. a semantic gate excluded it;
4. it was quarantined or truncated.

Under [Rubin 1976](https://doi.org/10.1093/biomet/63.3.581), ignoring R is justified only if missingness is at random given the modelled covariates and its parameters are distinct from θ. That fails for:

- **Questionnaire design.** Sources that list both UPPER LEG and LOWER LEG differ systematically from those that list only LEG.
- **Dictionary sources.** Senses are recorded *because* they are distinct or salient.
- **The "both senses separately identifiable" rule.** By construction this conditions on distinctness of native IDs, so sources that elicited a broad slot once are excluded from the denominator, where they would otherwise count as positives.

None of these is ignorable for E3. All are ignorable for E0, which is why the three-way E0 layer is sound. The repo's citation of [Snee & List 2026](https://ojs.uni-passau.de/index.php/calcip/article/view/273) (CALCIP, doi:10.15475/calcip.2026.1.2) on explicit three-way missingness is apt. Arca's documented inability to separate "not elicited" from "elicited but unavailable" is the binding constraint on any population estimand.

---

## 4. Chance homophony: what the data say

### 4.1 Pooled rates (`scope_null.py`, 5,408 segmented scopes, 3.70×10⁸ within-scope concept pairs)

| Stratum | Any identity / pair | Within-field | Cross-field | Within÷cross | Unigram null | Length-bigram null | Bigram+end null |
|---|---|---|---|---|---|---|---|
| All | 3.32e-4 | 2.16e-3 | 2.06e-4 | 10.5 | 1.5e-5 | 8.1e-5 | 2.45e-3 |
| supplied_ipa | 2.29e-4 | 1.74e-3 | 1.38e-4 | 12.6 | 3.3e-6 | 1.6e-5 | 1.96e-3 |
| mean length [3,4) | 1.04e-3 | 2.72e-3 | 8.89e-4 | 3.1 | 1.0e-4 | 4.1e-4 | 2.7e-3 |
| mean length [6,8) | 2.43e-4 | 2.12e-3 | 1.25e-4 | 16.9 | 4.5e-6 | 2.6e-5 | 2.3e-3 |
| N concepts [2,100) | 7.50e-4 | 2.37e-3 | 5.07e-4 | 4.7 | 8.4e-5 | 3.3e-4 | 4.0e-3 |
| N ≥ 600 | 2.86e-4 | 2.23e-3 | 1.67e-4 | 13.3 | 7.6e-6 | 5.6e-5 | 2.2e-3 |
| North America | 5.73e-4 | 3.34e-3 | 3.73e-4 | 8.9 | – | – | – |
| South America | 4.46e-4 | 2.91e-3 | 2.57e-4 | 11.3 | – | – | – |

- **Observed / expected for cross-field identities:** unigram 14.1, length-conditioned bigram 2.54, bigram with geometric length 0.08. A choice between textbook phonotactic nulls changes the "chance" expectation by about 170×.
- This matches the literature. [Dautriche et al. 2017](https://dspace.mit.edu/handle/1721.1/115884) (Cognition 163:128–145, doi:10.1016/j.cognition.2017.02.001) find that real lexicons cluster beyond phonotactic baselines, so n-gram nulls underpredict collisions.
- The homophony-baseline debate shows that the direction of conclusions depends on baseline details: [Trott & Bergen 2020](https://pages.ucsd.edu/~bkbergen/papers/trott_bergen_2020.pdf) (Cognition 205:104449), the critique by [Pimentel et al. 2021](https://www.arxiv.org/abs/2109.13766) (EMNLP), and Trott & Bergen's [2022 follow-up](https://pages.ucsd.edu/~bkbergen/papers/CogSci_2022__neighborhoods_final.pdf).
- **Recommendation:** do not use a generative phonotactic null as the calibrated baseline. Use it only as a sensitivity contrast.

### 4.2 Empirical length-stratified cross-field identity rate (`length_null.py`)

Cross-field rate by segment count L (pooled; "tone-marked" means ≥20% of the scope's words carry tone marks):

| L | All | Tone-marked scopes | Others |
|---|---|---|---|
| 1 | **1.50e-1** | 1.44e-1 | 1.50e-1 |
| 2 | 9.47e-3 | 1.40e-2 | 9.41e-3 |
| 3 | 1.83e-3 | 1.79e-3 | 1.87e-3 |
| 4 | 7.82e-4 | 7.74e-4 | 7.84e-4 |
| 5 | 4.93e-4 | 1.52e-3 | 4.64e-4 |
| 6 | 3.93e-4 | 1.48e-4 | 4.49e-4 |
| 7 | 4.02e-4 | 1.74e-4 | 4.53e-4 |
| 8 | 3.76e-4 | 8.8e-5 | 5.01e-4 |

At L = 3–4, the rate is 1.69e-3 for inventories under 25 segments, 1.20e-3 for 25–40, and 1.10e-3 for 40 or more.

Interpretation:

- **Two components.** `rate(L) ≈ chance(L) + floor`, with the floor at about 3.8×10⁻⁴. The chance component decays roughly geometrically (×5–6 per segment at short lengths). The floor does not decay, so it is not chance: it holds genuine cross-field polysemy (e.g. body/action), derivational and compound identity, catalog overlap across field prefixes, and mapping or extraction errors.
- **Identifiability point:** the floor cannot be split into "real polysemy" and "errors" without annotation. Treating the floor as chance is conservative; subtracting it is liberal. Report both (I do so below as "length-rate" vs "chance-only").
- **Tone and inventory.** Tone tokens are counted as segments in the current keys (e.g. `tsʰ e ²¹` has L=3), so "length" is mis-measured for tonal languages. A defensible length is the count of segmental tokens plus a separate tone-distinctiveness factor. Inventory size has the expected modest effect.
- Field prefixes are a crude semantic-distance proxy. Cross-field pairs include real polysemy, so the floor is an upper bound on chance.

### 4.3 Information content of the field relation

- Of 122,927 within-scope identities, 42.0% fall within a field, although within-field pairs are only 6.5% of all pairs.
- The mutual information between "identical" and "same field" is I(Y;S) = 2.4×10⁻⁴ bits per pair, against H(Y) = 4.3×10⁻³ bits. The uncertainty coefficient I/H(Y) is 0.056.
- For rare events, absolute bits look tiny even when the lift is 10×. Report log-lift, PMI or excess with intervals, not raw mutual information.

---

## 5. Calibration: a conditional label-permutation null

### 5.1 Design (`perm_null.py`, `perm_edges.py`)

Within each scope and within each segment-length stratum L, shuffle concept labels among the length-L cells.

**What this preserves exactly:**
- every scope's set of identity groups and their sizes (all homophony, including real polysemy);
- each concept's length profile within the scope;
- coverage and missingness patterns (which concepts are present);
- per-scope genealogy labels.

**What it destroys:** which concepts share a form.

**Null hypothesis:** given this scope's identities and length profile, the specific pair is no more likely to be identical than any length-matched pair.

Properties:
- **Conservative for discovery.** Shuffling real polysemy mass inflates the null expectation for all pairs.
- **Not degree-preserving.** Concepts with high colexification propensity (broad meanings) are not held fixed. A Tumminello-style or configuration variant would be stricter for hubs ([Tumminello et al. 2011](https://doi.org/10.1371/journal.pone.0017994), PLoS ONE 6:e17994).
- **Blind to source artefacts.** Scopes are treated as independent, so the null does **not** model shared questionnaires, compilations or inheritance.

**Sanity check:** my unpermuted re-implementation gives exactly 44,414 edges, matching production.

### 5.2 Results (49 replicates; 9 s per replicate; peak 114 MiB)

**Observed vs permuted edges reaching ≥k families**

| k | Observed edges | Permuted (mean of 3 shown) | Σ_e P_null(X_e ≥ k) over observed edges |
|---|---|---|---|
| ≥1 | 44,414 | ≈109,200 | – |
| ≥2 | 7,234 | ≈10,100 | 2,750 |
| ≥3 | 3,422 | ≈2,010 | 983 |
| ≥4 | 2,298 | ≈570 | 385 |
| ≥5 | 1,692 | ≈190 | 158 |
| ≥8 | 885 | – | 13 |
| ≥10 | 628 | ≈2 | 3 |

The last column is a rough plug-in for false discoveries among edges that pass a threshold. **The CLICS-style ≥3-family screen is not calibrated at this scale.** That is no criticism of CLICS, whose context and inventories differed. Thresholds of at least 8–10 families are almost never reached by chance, but this null says nothing about source artefacts.

**Per-edge Poisson tail**, with λ̂_e = (Σ null families + 0.5)/49, then BH:
- m = 44,414 observed edges: 3,940 edges pass at q<0.05.
- m = C(3828,2) = 7.3M catalog pairs: 1,792 pass.

The choice of m is a substantive decision ("which pairs were hypotheses?"). Report both.

**Cross-tabulation (conservative m):**

| Current status | Pass | Fail |
|---|---|---|
| replicated_backbone | 1,544 | 4,007 |
| limited_replication | 248 | 38,022 |
| semantic_review_required | 0 | 593 |

**Instructive cases**

| Edge | Families | Null λ | p (Poisson) | Status | Reading |
|---|---|---|---|---|---|
| TREE–WOOD | 50 | 4.03 | 1e-36 | backbone | far above chance |
| SUN–DAY | 60 | 2.56 | 3e-59 | backbone | far above chance |
| FIRE–RED | 7 | 1.56 | 1.2e-3 | backbone | modest. Credible as a pre-specified hypothesis, not under all-pairs multiplicity |
| ANI DEER–BELLY | 2 | 0.32 | 0.04 | **backbone** | chance-compatible under multiplicity |
| HEAD–MOTHER | 2 | 2.85 | 0.78 | **backbone** | chance-compatible |
| I–THOU | 3 | **10.99** | 0.999 | **backbone** | **below chance** (short pronouns). The 3 observed are fewer than expected. Possible avoidance; worth study, not backbone weight |
| FATHER–MOTHER | 5 | 6.11 | 0.73 | **backbone** | chance-compatible. Includes the Ventureño `k` truncation (§9) |
| LOWER LEG–UPPER LEG | 42 | 0.81 | 4e-56 | limited | **one source** (`johanssonsoundsymbolic`), so an elicitation artefact. The chance null "passes" it; the block safeguard correctly does not |
| BRANCH–TWIG, CLAW–PAW | 14, 10 | ≈0.01–0.03 | <1e-27 | limited | worth source review. May be granularity artefacts or genuine |

**Conclusion:** the existing resource-deletion criterion and a chance calibration are **complementary**. A defensible backbone needs both, plus lineage-key repair. Either one alone admits a characteristic class of false positives.

---

## 6. Dependence: genealogy, source, area

- **Genealogy.** ANOVA intraclass correlation of language-unit positives within families (`pairs.py`): TREE–WOOD ρ=0.32 (n_eff 206/716), MOON–MONTH 0.34 (148/446), ARM–HAND 0.27 (291/690), FIRE–RED 0.26 (862/2390).
  - Design effect: `DEFF = 1 + (m̄ − 1)ρ`, so `n_eff = n/DEFF`.
  - Inherited homophony is the extreme case. FALL–TEN in 8 Yi varieties, all from one source (`yangyi`), shares an inherited syllable `tsʰe/tsʰi` with tone. That is one historical event, and possibly one chance event.
  - The current "max per family" convention handles this. A language-level count does not.
- **Source/compilation.** Report the *effective number of independent resource blocks* among positive witnesses as a Hill number:
  - `D₁ = exp(−Σ p_r ln p_r)`, `D₂ = 1/Σ p_r²`, where `p_r` is block r's share of positive family-level witnesses.
  - LOWER–UPPER LEG has D=1, which is decisive. This is an information-theoretic redundancy measure (*unverified suggestion*, after Hill 1973, Ecology 54:427, doi:10.2307/1934352, not re-fetched).
  - It complements, rather than replaces, the minimax deletion R(e).
- **Area and contact.** The mixed-effect approach of [Jaeger, Graff, Croft & Pontillo 2011](https://dspace.mit.edu/handle/1721.1/103092) (Linguistic Typology 15:281–319) handles areal dependence with random effects. The phylogenetic-regression plus Gaussian-process approach of [Guzmán Naranjo & Becker 2022](https://publikationen.uni-tuebingen.de/xmlui/handle/10900/139715) (Linguistic Typology 26:605–670, doi:10.1515/lingty-2021-0002) handles it with a spatial Gaussian process. Both are feasible offline for selected pairs. They are not MVP material.
- **Phylogenetic dynamics.** The closest recent work, [Gfeller, Stoll, Cathcart & Widmer 2025](https://arxiv.org/html/2510.13407v1), models binary colexification as a two-state CTMC with gain = s·p and loss = s·(1−p). It regresses logit p and log s on associativity, borrowability and frequency, uses 100 posterior trees per family, compares models with PSIS-LOO, and fits in RStan. Notably, they require ≥5 colexifying languages per family and attestation in ≥30 languages, and they find **no effect consistent across Austronesian, Indo-European and Uralic**. This is the model class for E4, and a caution against universal E5 claims.

---

## 7. Bayesian models, and why a prior is not confidence

### 7.1 Hierarchical beta-binomial (language units within lineages)

```
y_f | θ_f ~ Binomial(n_f, θ_f),   θ_f ~ Beta(μκ, (1−μ)κ)
p(y | μ, κ) = Π_f C(n_f, y_f) B(y_f + μκ, n_f − y_f + (1−μ)κ) / B(μκ, (1−μ)κ)
```

Estimand: μ is the lineage-averaged probability for a random language unit (E1, not chance-corrected). κ is concentration; low κ means strong family clustering. A grid posterior gave:

| Pair | Families (+) | μ̂ (Jeffreys) 90% | μ̂ (logit-N at chance, sd 2) 90% | κ mode |
|---|---|---|---|---|
| TREE–WOOD | 76 (50) | 0.47 [0.40, 0.54] | 0.46 [0.38, 0.54] | 3 |
| MOON–MONTH | 60 (49) | 0.70 [0.62, 0.77] | 0.68 [0.60, 0.75] | 3 |
| ARM–HAND | 105 (40) | 0.25 [0.19, 0.29] | 0.24 [0.19, 0.29] | 3 |
| FIRE–RED | 286 (7) | 0.009 [0.003, 0.018] | 0.007 [0.003, 0.013] | 10 |
| FALL–TEN | 191 (1) | 0.004 [0.0004, 0.011] | 0.0016 [0.0001, 0.005] | 10 |

For FALL–TEN, the chance-only expectation per language unit is about 1.4×10⁻⁴. Under the Jeffreys prior the posterior sits 30× above that, and the prior did that work, not the data.

### 7.2 Chance-corrected excess (family presence; `excess.py`)

```
P(z_f = 1) = 1 − (1 − p0_f)(1 − ψ_e),    p0_f = 1 − Π_{ℓ∈f}(1 − h_ℓe)   (upper bound: within-family independence)
log10 BF = log10 ∫ L(ψ) π(ψ) dψ − log10 L(0)
```

| Pair | Families (+) | Chance-expected + families | ψ mean, Beta(1,1) | ψ mean, Beta(1,30) | log₁₀ BF range over 3 priors | Info gain (bits), Beta(1,1) / Beta(1,30) |
|---|---|---|---|---|---|---|
| TREE–WOOD | 76 (50) | 1.17 | 0.65 [0.55, 0.73] | 0.47 [0.39, 0.55] | 96.8–105.4 | 2.2 / 23.9 |
| FIRE–RED | 287 (7) | 0.66 | 0.025 [0.011, 0.042] | 0.022 | 5.3–6.5 | 4.7 / 0.9 |
| HEAD–MOTHER | 190 (2) | 1.13 | 0.006 | 0.005 | −2.2 to −0.8 | 6.0 / 1.5 |
| DEER–BELLY | 68 (2) | 0.14 | 0.028 | 0.018 | −1.4 to −0.2 | 3.8 / 0.3 |
| I–THOU | 306 (3) | 7.75 | 0.004 | 0.003 | −2.5 to −1.0 | 6.7 / 2.1 |
| FATHER–MOTHER | 192 (5) | 3.01 | 0.007 | 0.006 | −2.2 to −0.8 | 5.7 / 1.3 |

Lessons:

1. **A prior can dominate even with 76 families.** Beta(1,30) is worth about 30 pseudo-negative families. Priors must be elicited and justified (e.g. from the empirical distribution of ψ across many pairs, via empirical Bayes), reported, and accompanied by sensitivity analysis.
2. **Lindley information gain** ([Lindley 1956](https://projecteuclid.org/journals/annals-of-mathematical-statistics/volume-27/issue-4/On-a-Measure-of-the-Information-Provided-by-an-Experiment/10.1214/aoms/1177728069.full), doi:10.1214/aoms/1177728069) is KL(posterior‖prior). It measures how much the data moved *this* prior. It is not an intrinsic "amount of evidence": a vague prior can yield fewer bits than a sharp, wrong prior. Report it only with the prior.
3. **Bayes factors against chance are enormous for common pairs** (10¹⁰⁵) and prior-sensitive near zero (the Bartlett/Lindley paradox). They answer "is this pure homophony?", which is the least interesting question for frequent pairs. For frequent pairs, report the **excess ψ with an interval**. For rare pairs, report BF or q **plus** source and lineage diagnostics.
4. **Posterior intervals here are conditional on an optimistic model.** It assumes h is known, families are independent (no contact), there is no measurement error, sources are independent, and comparability is ignorable. LOWER–UPPER LEG would receive a narrow, confident interval near 1 from one questionnaire. **Unmodelled dependence produces overconfidence that no prior can repair.**

### 7.3 Posterior predictive checks (to run before any model is believed)

Following [Gelman, Meng & Stern 1996](https://www.cs.columbia.edu/~blei/fogm/2023F/readings/GelmanMengStern1996.pdf) (Statistica Sinica 6:733–807), simulate replicate corpora from the fitted model, using the real scopes, coverage and length profiles, and compare these discrepancies:

- the distribution of family counts per edge, including the ≥k table in §5.2;
- the within-field share (42%) and the length curve (§4.2);
- per-block concentration (the D₁/D₂ distribution);
- within-family ICC per edge;
- within-language cross-source concordance (§3.2);
- concept degree distribution and hub structure;
- the Americas/South America subset, separately.

A model that cannot reproduce single-source 40-family edges, or the zero within-language concordance for ARM–HAND, is mis-specified for those edges.

### 7.4 Calibration of probabilistic outputs

If Arca ever publishes probabilities, for example "P(motivated | identity)", evaluate them with proper scoring rules ([Gneiting & Raftery 2007](https://apps.dtic.mil/sti/html/tr/ADA459827/index.html), JASA 102:359–378, doi:10.1198/016214506000001437). Use a **stratified, independently adjudicated sample**, stratified by length, source type, region and field relation, and report the Brier score, log score and reliability diagrams. Without such a sample, "calibrated" cannot be claimed.

---

## 8. Information-theoretic effect measures (recommended set)

For an edge e, with observed lineage-level rate p̂_e and chance rate p0_e:

| Measure | Formula | Use | Caveat |
|---|---|---|---|
| Lift / log-lift | `p̂/p0`, `log₂(p̂/p0)` | how far above chance | TREE–WOOD log₂ lift 7.8; FIRE–RED 3.5. Unstable when p0 is tiny; shrink |
| Excess propensity | ψ = (θ − p0)/(1 − p0) | the E2/E3 estimand | needs a lineage-level model (§7.2) |
| Per-unit KL | `KL(Bern(p̂)‖Bern(p0))` bits per independent unit | expected evidence per new lineage, useful for sampling design | TREE–WOOD 2.3 bits per language unit; FIRE–RED 0.0065. Multiply by **n_eff, not n** |
| Evidence total | log BF or `−log₁₀ q` | screening | huge for common pairs; prior/multiplicity-dependent |
| Normalised PMI | `log(p_ab/(p_a p_b)) / −log p_ab` | concept-pair association net of each concept's colexification degree | CLICS-style; ignores length chance unless p_a, p_b are chance-adjusted |
| Redundancy | Hill D₁, D₂ over blocks and families | effective independent support | complements minimax R(e) |
| Uncertainty coefficient | `I(Y;S)/H(Y)` | how much a linguistic covariate (field, WordNet relation, metonymy type) explains | 0.056 for "same field". Rare-event bits look small |

The information-bottleneck framing of naming systems, for example [Zaslavsky, Kemp, Regier & Tishby 2018](https://pmc.ncbi.nlm.nih.gov/articles/PMC6077716) (PNAS 115:7937, doi:10.1073/pnas.1800521115), is a *theory of why* colexification patterns arise (E5-adjacent). It needs a need distribution and a meaning space, which Arca does not have. Use it as a research direction, not a corpus statistic.

---

## 9. Data-quality interactions and a side finding

- **Ventureño (`chb-ventureno`, Huntergatherer member 40):** `Value=k'oko "my fa"` → `Form=k`, `Segments=k`; `k'ete "my mother (but root is tete)"` → `Form=k`. This is an apostrophe-prefix truncation like members 30 (guarded) and 43 (Ineseño, found earlier), and it is not covered by the current guard. It produces a FATHER–MOTHER witness. The full forms also share the possessive prefix `k'-` ("my"), so even correctly extracted forms need morphological segmentation before whole-form identity says anything about lexical roots. I recommend an audit of all Huntergatherer members, especially Chumashan (not executed here; out of scope).
- **Lineage keys:** SNS DRY–SPA FAR shows `languages=1, families=2`. Witnesses are `sit-loloish` (no Glottolog language) and Tübatulabal, so the language and family counts use different missing-key conventions. Combined with the known isolate and pseudo-family key defects, **every lineage-level estimand above inherits these errors**. Fix the keys before computing n_eff, ICC or ψ.
- **Catalog overlap** (PATH–PATH OR ROAD; ARM–ARM OR HAND appears with 11 families) and **questionnaire granularity** (UPPER/LOWER LEG) are not colexification between distinct senses. They need a reviewed concept-relation table (containment, overlap, disjoint). A chance or Bayesian model cannot infer this.

---

## 10. Semantic granularity and the linguistic annotations needed

Statistical modelling can separate *chance* from *excess*. It cannot separate polysemy, homophony, catalog overlap, elicitation underspecification and errors without these annotations, roughly in order of value per effort:

1. **Concept-relation table** for frozen concepts: identical / containment / overlap / disjoint, plus "disjunctive slot" (`X or Y`). This governs which pairs are hypotheses at all, and therefore the denominator of every test.
2. **Questionnaire inventories per source** (which items were elicited, with item text). This turns `unknown` into "not elicited" vs "not recorded", and makes missingness modelable (§3.3).
3. **Homophony vs polysemy evidence per identity**, where available:
   - Wiktionary separate *Etymology N* sections indicate homonymy (*unverified suggestion*: this is extractable from kaikki/wiktextract JSON);
   - dictionary homonym numbering;
   - cognacy/etymology linking each sense to different proto-forms.
4. **Morphological segmentation / boundness** (possessive prefixes such as `k'-`, classifiers, noun-class prefixes), so that identity can be computed on roots or stems in a separate, labelled layer.
5. **Source-notation fidelity flags:** whether the source marks tone, length, stress and glottalisation. A non-match is only meaningful if the source could have encoded the distinction.
6. **Source genealogy** (derivative datasets, shared questionnaires), extending `resource_blocks.json` from "conservative blocks" to an actual dependency graph.
7. **Loan flags**, already retained. Make them a model covariate (contact) rather than a filter.
8. **External semantic covariates** for E5-oriented work: association norms ([Xu, Duong, Malt, Jiang & Srinivasan 2020](https://par.nsf.gov/biblio/10194717), Cognition 201:104280, doi:10.1016/j.cognition.2020.104280), frequency and metonymy/metaphor type. These are used as *predictors*, never as filters.
   - The repository already notes [Brochhagen & Boleda 2022](https://doi.org/10.1016/j.cognition.2022.105179) against reducing colexification to a monotonic similarity measure (repo-cited, not re-fetched).
   - Emotion-colexification work such as [Jackson et al. 2019](https://pub.uni-bielefeld.de/record/2946579) (Science 366:1517, doi:10.1126/science.aaw8160) shows family/area variation that makes "universal" E3 claims fragile.

**Linguistic information is used defensibly in three places:**
- (a) in defining *which pairs are hypotheses*: weighted or grouped multiple testing, where pre-specified semantic relations get lower multiplicity. *Unverified pointer:* Genovese, Roeder & Wasserman 2006, Biometrika, "False discovery control with p-value weighting".
- (b) as **covariates** in θ;
- (c) in **measurement-error structure** (notation fidelity, source class).

It should not enter as a prior that silently raises confidence in favoured pairs.

---

## 11. Comparison of defensible approaches

| Approach | Estimand | Handles chance | Handles dependence | Handles measurement error | Cost / feasibility (256 MiB) | Verdict |
|---|---|---|---|---|---|---|
| A. Current descriptive counts + minimax deletion | E0 robustness | No | Partly (family max, block deletion) | No | Done | **Keep as base layer** |
| B. CLICS-style family threshold | E0 screen | No | Partly | No | Trivial | Uncalibrated below about 5–8 families (§5.2); keep as a view only |
| C. Empirical length-stratified chance model (shrunk per scope) | expected chance support, lift | **Yes** (aggregate) | No | No | Trivial (5k scopes × ~10 lengths) | **MVP** |
| D. Conditional label-permutation null + BH | calibrated "more than chance-placed" | **Yes** | No (scopes independent) | No | 9 s and 114 MiB per replicate | **MVP** (R=200 ≈ 30 min) |
| E. Degree-preserving / SVN-style null | as D, controlling hub propensity | Yes | No | No | Moderate | Next step |
| F. Hierarchical beta-binomial with chance-corrected ψ | E2/E3 lineage-level excess | Yes | Genealogy (exchangeable families) | No | Grid per edge, tiny | **MVP for edges with ≥2 families, under declared priors** |
| G. Dawid–Skene / Hui–Walter latent truth | E1 with σ, φ | Yes | – | **Yes, if identifiable** | Small, but needs overlap or gold data | Research. Pooled source-class only |
| H. Phylogenetic CTMC (Gfeller et al.) and areal GP | E4 / E3 with tree and space | Via covariates | **Yes** | No (usually) | Heavy MCMC → Pelle/EOSC | Research, selected families/pairs |
| I. Network-reconstruction models (Newman, Peixoto) | latent graph | Partly | No | Yes, with repeats | Moderate–heavy | Not until repeated measurements exist |
| J. Information-bottleneck / communicative-need models | E5 | – | – | – | Needs need distributions | Theory track only |

**Parsimonious recommendation:** A + C + D + F, plus source-redundancy (Hill) diagnostics, presented side by side. G and H are research tracks gated on annotations and compute.

---

## 12. Sparse MVP specification (≤ 256 MiB, SQLite-backed)

This is an additive diagnostics stage. It does not change the reported network, backbone or communities until a separate decision is made.

**Prerequisites (correctness before inference):** canonical lineage keys (isolates, pseudo-families, missing language units); the truncation audit (members 30/40/43 and siblings); the conflict guards already recommended. Otherwise every estimate below inherits key errors.

**Stage 1 — scope chance model (seconds, under 60 MiB)**
- Table `chance_scope(sid, L, pairs_cross, ids_cross)`, using a tone-aware length (segmental tokens only, plus a tone flag).
- Pooled `c(L)` by basis, and by tonal flag and inventory tertile.
- Scope-shrunk estimate: `ĉ_s(L) = (ids_sL + α·c(L)) / (pairs_sL + α)`, with α chosen by empirical-Bayes beta-binomial fit across scopes.
- Store two variants: *floor-included* (conservative) and *chance-only* (`ĉ − floor`, floored at a small positive value).

**Stage 2 — permutation calibration (about 30 min for R=200, under 120 MiB)**
- Re-use the streaming loop from `perm_edges.py`.
- Apply the native-ID guard, the semantic gate (a backbone-compatible variant) and canonical lineage keys.
- Statistic: distinct canonical lineages, per layer.
- Store, per observed edge: `null_sum`, `null_sumsq`, `exceed_count`.
- Derive λ̂, a negative-binomial tail when the null variance exceeds its mean, the Monte-Carlo p as (exceed+1)/(R+1), and BH q under **m₁ = observed edges** and **m₂ = all catalog pairs**, both stored.
- Optional variant: degree-stratified shuffling (Stage 2b).

**Stage 3 — per-edge analytic expectation and excess posterior (minutes, under 80 MiB)**
- Table `concept_lengths(sid, cid, L, n)` (≈1.5M rows) from `cells`.
- For each observed edge with ≥2 lineages: an indexed coverage join gives comparable scopes (a cheap approximation to `pair_status`; use exact `pair_status` only for the published top-k).
- Compute per-lineage `p0_f`, then a grid posterior for ψ under Beta(1,1) and an empirical-Bayes prior fitted across edges.
- Store the mean, the 90% interval, log₁₀ BF for both priors, and the prior-sensitivity range.

**Stage 4 — dependence and redundancy (minutes)**
- Per edge: the within-lineage ICC (language units), n_eff, and Hill D₁/D₂ over resource blocks and over sources among positive witnesses.
- Shares of single-segment and two-segment witnesses.
- Share of positives from the largest block.

**Labels (descriptive, not verdicts):**
- `chance_compatible` (q ≥ 0.05 under m₁)
- `excess_single_block` (q < 0.05 and D₂ < 1.5)
- `excess_replicated` (q < 0.05, D₂ ≥ 2, ≥2 canonical lineages after any block deletion)
- `below_chance` (observed < 5th percentile of the null)
- `short_form_dominated` (more than 50% of positive witnesses with L ≤ 2)

**Outputs:** one gzip CSV sharded at 50k rows, plus a manifest with input hashes, R, seeds, m conventions and prior definitions. The UI shows "observed vs chance-expected lineages" and the ψ interval beside the existing counts.

**Posterior predictive check job:** simulate 50 corpora from Stage 1/3 parameters and report the §7.3 discrepancies, the Americas and South America separately.

**Tests:**
- fixtures where the null is known analytically (a single scope with known groups);
- an invariance test (the unpermuted run reproduces production edge counts);
- determinism under fixed seeds;
- a memory cap test.

**Decision gate:** publish the contrasts first: backbone vs `excess_replicated`, retention by macro-area (especially South America), and changes to communities. Change the default graph only by explicit decision.

---

## 13. Research roadmap

1. **Now (MVP):** §12, preceded by the lineage-key and truncation fixes.
2. **Short term:**
   - concept-relation table and questionnaire inventories for the 20 largest sources;
   - tone-aware length;
   - degree-preserving null;
   - Hill redundancy;
   - a stratified **adjudicated benchmark** (≈300–500 identities across length, source type, region and field relation), labelled as polysemy / homophony / overlap / elicitation artefact / error. This is the only route to calibrated error rates and proper-score evaluation.
3. **Medium term:**
   - pooled source-class measurement model (Dawid–Skene-like), using the 282 multi-source language units plus the benchmark;
   - a Wiktionary etymology-section signal for homophony;
   - morphological-stem layer for selected well-described families.
4. **Long term (offline compute):**
   - phylogenetic CTMC per family for pre-registered pairs, in the style of Gfeller et al. 2025, together with an areal Gaussian process;
   - E5 work only with external association/frequency data and explicit sampling frames.

---

## 14. What can be claimed now

- **Defensible now:**
  - E0 statements with scope;
  - "observed in X canonical lineages vs Y expected under a length-preserving chance null";
  - "support concentrated in one resource block";
  - lineage-level excess intervals that are explicitly conditional on stated model assumptions and priors;
  - for top pairs (TREE–WOOD, SUN–DAY, MOON–MONTH, ARM–HAND, MAN–PERSON): "identity far exceeds chance across many lineages and sources".
- **Not defensible now:**
  - probabilities that an individual identity is polysemy;
  - world-population prevalence without a sampling frame and a missingness model;
  - calibrated "significance" for any family-count threshold below about 8 without a null;
  - cognitive association strength;
  - per-edge measurement error rates.

---

## 15. Reproducibility of this review's experiments

All in `/home/agent/scratch/colexinf/`, run with `.venv/bin/python -I` under `ulimit -v 262144`, against `output/colexification/d5c9b49da8851392bac2e2e0/index.sqlite`, read-only.

| Script | Purpose | Time / peak RSS |
|---|---|---|
| `scope_null.py`, `agg.py` | per-scope rates and phonotactic nulls | 13 s / 57 MiB |
| `length_null.py` | length/tone/inventory cross-field rates | ~15 s / 43 MiB |
| `perm_null.py` | permutation-null family distributions (3 replicates) | 9 s / 93 MiB |
| `perm_edges.py`, `calib.py` | 49 replicates, per-edge tails, BH, cross-tabs | ~8 min / 114 MiB |
| `pairs.py`, `excess.py` | pair-level chance expectation, ICC, hierarchical and excess posteriors | 0.2–2 s per pair / 48 MiB |
| `within_lang.py` | within-language cross-source concordance | seconds |

**Limitations of these experiments:**
- raw `varieties.family` keys (known defects) were used;
- unreviewed dictionary senses are included (production backbone gates them);
- lengths count tone tokens;
- the analytic `p0_f` assumes within-family independence (an upper bound);
- the grid posteriors are coarse;
- R=49 limits Monte-Carlo resolution (Poisson tails are used beyond it).

The numbers are diagnostic toy results, not publication values.

---

## 16. References (verification status)

**Verified by fetch or search in this session**
- Dawid & Skene 1979, JRSS C 28:20–28, doi:10.2307/2346806 — https://ideas.repec.org/a/bla/jorssc/v28y1979i1p20-28.html
- Hui & Walter 1980, Biometrics 36:167–171, doi:10.2307/2530508 — https://jhanley.biostat.mcgill.ca/bios601/CandH-ch0102/HuiWalter1980.pdf
- Newman 2018, Nature Physics 14:542, doi:10.1038/s41567-018-0076-1 — https://arxiv.org/abs/1703.07376
- Trott & Bergen 2020, Cognition 205:104449 — https://pages.ucsd.edu/~bkbergen/papers/trott_bergen_2020.pdf
- Trott & Bergen 2022, CogSci — https://pages.ucsd.edu/~bkbergen/papers/CogSci_2022__neighborhoods_final.pdf
- Pimentel, Meister, Teufel & Cotterell 2021, EMNLP — https://www.arxiv.org/abs/2109.13766
- Dautriche et al. 2017, Cognition 163:128–145, doi:10.1016/j.cognition.2017.02.001 — https://dspace.mit.edu/handle/1721.1/115884
- Xu, Duong, Malt, Jiang & Srinivasan 2020, Cognition 201:104280, doi:10.1016/j.cognition.2020.104280 — https://par.nsf.gov/biblio/10194717 (the direct fetch failed; verified via search)
- Jaeger, Graff, Croft & Pontillo 2011, Linguistic Typology 15:281–319 — https://dspace.mit.edu/handle/1721.1/103092
- Guzmán Naranjo & Becker 2022, Linguistic Typology 26:605–670, doi:10.1515/lingty-2021-0002 — https://publikationen.uni-tuebingen.de/xmlui/handle/10900/139715
- Gfeller, Stoll, Cathcart & Widmer 2025, arXiv:2510.13407 — https://arxiv.org/html/2510.13407v1 (method details fetched)
- Jackson et al. 2019, Science 366:1517–1522, doi:10.1126/science.aaw8160 — https://pub.uni-bielefeld.de/record/2946579
- Zaslavsky, Kemp, Regier & Tishby 2018, PNAS 115:7937, doi:10.1073/pnas.1800521115 — https://pmc.ncbi.nlm.nih.gov/articles/PMC6077716
- Lindley 1956, Ann. Math. Stat. 27:986–1005, doi:10.1214/aoms/1177728069 — https://projecteuclid.org/journals/annals-of-mathematical-statistics/volume-27/issue-4/On-a-Measure-of-the-Information-Provided-by-an-Experiment/10.1214/aoms/1177728069.full
- Gelman, Meng & Stern 1996, Statistica Sinica 6:733–807 — https://www.cs.columbia.edu/~blei/fogm/2023F/readings/GelmanMengStern1996.pdf
- Gneiting & Raftery 2007, JASA 102:359–378, doi:10.1198/016214506000001437 — https://apps.dtic.mil/sti/html/tr/ADA459827/index.html
- Rubin 1976, Biometrika 63:581–592 — https://doi.org/10.1093/biomet/63.3.581
- Tumminello et al. 2011, PLoS ONE 6:e17994 — https://doi.org/10.1371/journal.pone.0017994
- Snee & List 2026, CALCIP, doi:10.15475/calcip.2026.1.2 — https://ojs.uni-passau.de/index.php/calcip/article/view/273

**Cited in the repository; not re-fetched**
- Peixoto 2018 — https://doi.org/10.1103/PhysRevX.8.041011
- Brochhagen & Boleda 2022 — https://doi.org/10.1016/j.cognition.2022.105179
- CLICS², CLICS³, CLICS⁴ papers — links in `docs/COLEXIFICATION.md`

**Unverified suggestions (standard references, not fetched)**
- Hill 1973, Ecology 54:427 (Hill numbers)
- Genovese, Roeder & Wasserman 2006, Biometrika (weighted FDR)
- Benjamini & Hochberg 1995, JRSS B
- Kish 1965, *Survey Sampling* (design effect)
- Wiktionary/kaikki etymology sections as a homophony signal
