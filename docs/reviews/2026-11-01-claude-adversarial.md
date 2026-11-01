# Independent adversarial review: Arca Verborum colexification method

**Reviewer model:** Claude Opus 5.5 (`claude-opus-5-5`) · **Date:** 2026-11-01
**Build examined:** `d5c9b49da8851392bac2e2e0`, the published build in `web/data/manifest.json`. Communities: `d1388af4b69018f3a92012f0`.
**Scope:** I read `AGENTS.md`, `docs/COLEXIFICATION_ROBUSTNESS_2026-11-01.md`, `policy.json`, `resource_blocks.json`, all five `src/arcaverborum/colexification*.py` modules and the related tests. I queried the production SQLite in read-only/immutable mode and ran small Python experiments that import the project's own `summarize`. I did not read `docs/COLEXIFICATION_REVIEW_2026-10-31.md`, `docs/reviews/` or any other review, and I edited no repository files.

**Labels used below.** **BUG** means a reproducible defect. **DATA** means a reproducible defect in the input data that the method fails to guard against. **DESIGN** means a deliberate choice whose consequences I measured. **SPEC** means speculation that has not been verified.

---

## 0. Summary

The bookkeeping is careful, and several core claims hold when checked against the code (§10). The weak points are elsewhere:

1. **"Replicated" is weaker than the name suggests.** 60% of backbone edges (3,353 of 5,551) rest on a single family once the worst resource block is deleted.
2. **Truncated forms and bound morphemes reach the backbone.** Examples are Ineseño *č* for BAG/ANTELOPE/BEAVER and Alekano *_l* for BURN/SAY. 201 backbone edges depend on such one-segment forms, mostly in American and New Guinea data.
3. **Concepts that contain each other are linked as if they were colexified.** For example, PATH ~ PATH OR ROAD has weight 8.5 across 17 families.
4. **Family counting has two defects.** Glottolog's pseudo-families (Bookkeeping, Sign Language, Artificial, …) are counted as lineages. Isolates are split into two families whenever a dialect is coded.
5. **Taking the maximum within a family brings back sample-size bias.** A family seen in one variety contributes 0.61 on average; a family seen in ten or more contributes 0.96. This works against isolates and thinly sampled American families.
6. **The 1/C(k,2) weight penalises dense or homophone-rich lexicons quadratically,** and can outweigh breadth across families.
7. **The CLICS comparison never tests the new model.** It compares the raw network only.

---

## 1. "Replicated backbone" mostly means one family after deletion — DESIGN, High

**Evidence**
- `colexification_evidence.py:120` computes `families_without_one_block_min`, but the eligibility test at `:123` (`eligible = len(weights)>=2 and survivor>0`) never uses it.
- The documentation (`ROBUSTNESS.md:58`) says the backbone needs "at least two distinct eligible known families" and `R(e)>0`. The code does exactly that, but the two conditions are checked separately. Nothing requires two families to *survive* the deletion.

**Toy example** (run against the real `summarize`):
- Input: F1 = {W: 1, C: 1/45}, F2 = {W: 1}.
- Result: A = 2, R = 0.0222, families after the worst deletion = 1, eligible, weight 0.022.
- Once block W is removed, the edge rests on one family's k = 10 witness.

**Production:** distribution of `families_without_one_block_min` across backbone edges: 1 → 3,353 edges; 2 → 928; 3 → 437; 4 → 242; and so on. Edge `act-launder ~ bod-spit` rests on Laitu Chin (chindialectsurvey, k = 2) plus Lalo (suntb, k = 4), so R = 1/6 (see also §5).

**Remedy (P1)**
- Either require `families_without_one_block_min ≥ 2` for the backbone, or rename the tier honestly (for example, "two-family, one-block-robust").
- Publish both variants and the community-agreement contrast between them.

## 2. Truncated forms and bound morphemes are treated as whole words — DATA, High (concentrated in priority regions)

**Evidence**
- `usable()` (`colexification.py:85-86`) accepts any string that contains a letter. That includes single segments and affix-marked strings such as `_l`.
- `analytical_exclusion()` (`:89-110`) guards the Huntergatherer apostrophe truncation for `huntergatherer_30` only.

**Production**
- Eligible one-segment witnesses: huntergatherer 1,626; transnewguineaorg 235; zgraggenmadang 144; idssegmented 132; and others.
- Examples:
  - Ineseño `tʃ` ('č') for act-bag / ani-antelope / ani-beaver (k = 3).
  - Wappo `t` for bag / bat.
  - Alekano `_l` and Dano / Inoke-Yate `l` for act-burn ~ lng-say / act-hit.
  - Wintu `k`, with k = 14 (flea, wind, one, bow, gun, …).
  - Yuhup `ts`, with k = 15.
- **201 backbone edges lose eligibility** when single-segment identities are removed. Examples: act-burn ~ ani-dog, act-burn ~ phy-thunder, act-burn ~ spa-near.
- Huntergatherer's mean group size is 5.36 against a median of 271 concepts per scope, the highest of all large sources. The usual figure is 2.3–3.4.
- The 1/C(k,2) weight dampens the large groups but not the small ones: `_l` with k = 2 has full mass 1.

**Linguistic point:** `_l`/`-l` is almost certainly a bound morpheme, and `č` looks like a nominal prefix left after truncation. Neither is a lexical colexification.

**Remedy (P1)**
- Hold forms containing `_`/`-` affix markers out of segmented identity.
- Hold one-segment identities from replicated inference unless the source is reviewed for the language's phonotactics (French /o/ is a genuine one-segment word).
- Extend the Huntergatherer extraction audit to every member with group sizes that are outliers for its concept count.

## 3. Nested or disjunctive concepts produce links by definition — DESIGN (catalog), High

**Evidence:** neither the gate nor the weight checks whether one concept contains the other. In `expansions.csv`, only explicitly expanded readings become `inferred`. Two observed records mapped to A and to A-OR-B count as a full colexification.

**Production backbone (19 edges).** Examples:

| Edge | Families | Weight |
|---|---|---|
| mot-path ~ mot-path-or-road | 17 | 8.5 |
| act-braid-verb-or-weave ~ clo-weave | 26 | 7.67 |
| act-break-destroy-or-get-destroyed ~ pss-destroy | 10 | 6.33 |
| bod-foot ~ bod-foot-or-leg | — | 2.0 |
| spa-below-or-under ~ spa-down-or-below | — | 2.0 |
| bod-hair ~ bod-hair-or-fur | — | 1.0 |

The catalog has 128 active disjunctive concepts.

**Near misses.** Of 3,404 raw edges with ≥3 families, 454 are excluded from the backbone, and only because they are confined to one block. Examples:
- lower-leg ~ upper-leg: 42 families, all from `johanssonsoundsymbolic`. This is a questionnaire-split artefact.
- fingernail ~ fingernail-or-toenail: 17 families.
- dream-something ~ dreaming-or-dream: 23 families.

A second source using the same concept split would promote all of these.

**Effect:** strong, semantically trivial links pull a concept and its own superset into one community, inflating community cohesion.

**Remedy (P1)**
- Add a reviewed concept-relation table (contains / overlaps / same-POS variant).
- Exclude those pairs from the backbone, or merge the nodes for clustering.
- Report them separately as "catalog-overlap identities".

## 4. Isolates are counted twice when a dialect is coded — BUG, Medium

**Evidence:** `colexification.py:191-195`.
- A language-level isolate gets `Family_ID = ''` and is relabelled `isolate:<ID>`.
- Its dialects carry `Family_ID = <ID>` with no prefix.

**Affected (reproduced):**
- Abun / Abun Tat
- Berta / Fadashi, Gobato, Mayu, Undu
- Burushaski / Hunza, Nagar, Yasin
- Comecrudan / Comecrudo
- Mosetén-Chimané / Chimané

Five backbone edges count the same isolate twice. None leaves the backbone if the duplicates are merged, but their weights are inflated. The same split also enters:
- the raw `families` counts (`:402`),
- the family-bootstrap population (`communities.py:255`),
- the CLICS three-family overlap.

**Remedy (P2):** use one canonical key, `family = Family_ID or ID` for top-level nodes, then add an `isolate:` label only for display.

## 5. Glottolog pseudo-families are counted as genealogical lineages — DATA/DESIGN, Medium

**Present as "families":**

| Pseudo-family | Varieties |
|---|---|
| Bookkeeping (`book1242`) | 19 |
| Sign Language | 13 |
| Unclassifiable | 8 |
| Pidgin | 7 |
| Artificial | 6 |
| Speech Register | 4 |
| Mixed | 3 |
| Unattested | 2 |

**Counterexamples**
- Bookkeeping includes four Kuki-Chin varieties (Laitu, Rungtu, Songlai, Thaipum), as well as Old Turkish, Khalaj, Ahirani, Chetco, Rufiji and Uradhi. One lumped "family" therefore mixes unrelated lineages and also splits Sino-Tibetan from itself.
  - Backbone edge `act-launder ~ bod-spit` = Laitu Chin (`book1242`) + Lalo (`sino1245`). That is two Sino-Tibetan varieties counted as two families.
- Esperanto, Ido, Interlingua and Volapük largely calque European polysemies, yet they count as one independent lineage.
- 13 unrelated sign languages share one "family". (Applying spoken-form identity to sign languages is itself questionable.)
- 28 backbone edges need a pseudo-family to stay eligible.

**Remedy (P2)**
- Resolve Bookkeeping entries to their replacement glottocodes.
- Treat Unclassifiable / Unattested entries as per-language singletons (as isolates are) or as unknown.
- Flag Artificial / Pidgin / Mixed entries as contact-derived and exclude them from the independence count.
- Exclude sign languages, or justify their inclusion.

## 6. The family maximum is an extreme-value statistic that reintroduces sample size — DESIGN, Medium-High

**Evidence:** `MAX(...)` per (family, block) at `colexification_evidence.py:138,168`, then `max(blocks.values())` at `:113`.

**Toy model:** each witnessing language independently has k = 2 with probability 0.5, otherwise k = 3. The expected family contribution is

> E[max] = 1/3 + (2/3)·(1 − 0.5ⁿ)

That gives 0.667 for n = 1 and 0.999 for n = 10.

**Production:** mean family contribution by number of witnessing varieties in the family.

| Witnessing varieties | Mean contribution | Share at the 1.0 cap | (pair, family) cells |
|---|---|---|---|
| 1 | 0.606 | 50% | 55,167 |
| 2 | 0.803 | 73% | |
| 3–4 | 0.883 | 84% | |
| 5–9 | 0.939 | 91% | |
| ≥10 | 0.955 | 94% | |

Large, well-documented families (Indo-European, Sino-Tibetan, Austronesian) are therefore worth about 1.6 times a singly attested isolate or a small American family. This runs against the stated Americas priority.

**Remedy (P2)**
- Use a mean or median over languages within a family, or a per-language weight averaged within the family (closer to CLICS's family weight).
- At minimum, report the rank stability of edges under max versus mean versus binary aggregation.

## 7. The quadratic weight can outweigh breadth and is not monotone in coverage — DESIGN, Medium

**Evidence:**
- Mass 1/C(k,2): `colexification_evidence.py:138`.
- k is `groups.concepts` (`colexification.py:358-360`). It counts every concept mapped to the identity, including unreviewed headword mappings and unrelated homophones, even though such pairs carry no mass themselves (`ROBUSTNESS.md:47`).

**Toy examples (real `summarize`)**
- *Breadth is outweighed:*
  - 3 families, each at k = 2 in distinct blocks: R = 2.0.
  - 30 families, each at k = 9 in distinct blocks: R = 0.81.
  - Recurrence across 30 lineages scores below 3 sparse lists.
- *Not monotone in coverage:*
  - Two families at k = 2: weight 1.0.
  - Add one unrelated homophone, or one erroneous unreviewed sense, to F1's identity: weight 0.333.
  - Better lexical coverage, or a wrong mapping, lowers unrelated pairs' weights.
- *In production:* Spearman correlation between eligible families and weight is 0.71, so breadth explains only part of the weight. Pearson correlation between log scope density and mass is −0.13, so the density effect is modest overall but concentrated in specific sources.

**Remedy (P2)**
- Compute k over semantically eligible concepts only.
- Run a sensitivity analysis with Newman's 1/(k−1) and with exponent families such as k⁻ᵅ.
- Better: cluster the hypergraph directly, as Eriksson et al. 2021 already cite, instead of choosing a projection convention.

## 8. Resource-block independence is asserted, not tested — DESIGN with SPEC, Medium

**Evidence:**
- Unregistered sources each become their own block: `blocks.get(source, source)` at `colexification_evidence.py:135`.
- The registry lists only five blocks.
- `idssegmented` is the worst-case deletion for 2,255 of 5,551 backbone edges, so in practice R ≈ "support outside IDS".
- Removing the IDS block drops 136 nodes (1,477 remain), with ARI 0.698.

**Unverified dependence candidates (SPEC):**
- WOLD and IDS share meaning lists and some contributors.
- `transnewguineaorg` and `zgraggenmadang` plausibly overlap in their Madang data.
- `johanssonsoundsymbolic` is a compilation.

I found no shared bibliography keys across blocks, but those keys are source-local, so that is not evidence of independence.

**Remedy (P3)**
- Audit provenance through per-language, per-concept identical-form overlap between sources and through the cited primary sources.
- Make "unregistered = independent" an explicit, reported assumption.

## 9. Missingness and representation

**(a) Splitting scopes by comparison basis loses identities — DESIGN, Low-Medium.**
- Scope includes `basis` (`colexification.py:33-34, 279-292`). The identity key for IPA or stress-marked records is a JSON pair of raw form and segments (`:284`).
- 103 identity groups split only by basis, and 89 split by raw key within one basis. Together they lose 243 variety-level pairs.
- Example: West Circassian (NorthEuraLex) *maːza* MOON vs *maːˈza* MONTH. A missing stress mark means stress is unknown, not that the forms differ. Other examples: GAP/SPACE vs BETWEEN; NOISE vs VOICE.
- Remedy: compare on accepted segments when one side lacks prosody, labelled as a "prosody-unresolved identity".

**(b) The semantic gate covers Wiktionary only — DESIGN, acknowledged, Medium.**
- `colexification_evidence.py:72-73` gives every non-Wiktionary record `source_mapping`, which passes.
- English-gloss mapping errors in lexibank-style lists are not gated. (`act-bag` recurs in the truncated Huntergatherer groups.)
- Remedy: extend the semantic queue to every source, ranked by backbone contribution.

**(c) No null model for chance homophony — DESIGN/SPEC, Medium.**
- Short forms, small inventories and normalisation that drops tone or length all raise accidental identity. The project rightly makes no significance claim, yet the backbone ranks edges as if chance collisions were spread evenly.
- Remedy: a within-scope permutation null that preserves segment-length and concept-frequency distributions, used as a diagnostic and not as a filter.

**(d) Last write wins in local sense approvals — BUG (latent), Low.**
- `colexification_evidence.py:66,69` silently overwrite earlier approvals. That contradicts `ROBUSTNESS.md:35` ("conflicting parameter-level approvals remain unreviewed").
- Current data has 0 conflicts. Remedy: raise or mark unreviewed when a conflict appears.

## 10. Communities: selection and stability — DESIGN, Medium

- **Granularity depends on the method.** Infomap gives 237 modules (about 6.8 nodes each); Leiden gives 56–86, with ARI 0.107–0.389. The seed medoid (`colexification_communities.py:140-147`) only addresses variation across seeds (ARI ≥ 0.915). The documentation's caveat at `ROBUSTNESS.md:90` is fair.
- **Agreement is computed on surviving nodes only** (`:94-111`), which flatters stability:

  | Run | Nodes compared | ARI |
  |---|---|---|
  | Americas subset | 920 / 1,613 | 0.57 |
  | Without Eurasia | 1,379 | 0.673 |
  | Family-block run 1 | 1,442 | 0.661 |

  Nodes that disappear are exactly the unstable ones. Remedy: report node retention beside every ARI, and a lower bound that counts dropped nodes as singletons.
- **Bootstrap results mix in seed variation.** Each bootstrap run uses seed 1, but is compared with the seed-8 medoid (`:263`), so part of the measured instability is seed variation (minor).
- **A test covers dead code.** `family_block_edges` (`:150-158`) is not used in production; production uses `projection_edges(..., multiplicity)`. `test_family_blocks_count_repeated_draws_and_collapse_duplicate_sources` therefore tests code that never runs.
- **Remedy (P3):** report per-community stability (best-match Jaccard across bootstraps), consensus or co-assignment clustering, and hierarchical Infomap, instead of one flat medoid.

## 11. The CLICS comparison does not test the new model — DESIGN, Medium

- `colexification_comparison.py:266-278` builds Arca support from every segmented observed witness. That includes unreviewed senses, pseudo-families, double-counted isolates and truncated forms.
- `:301` applies the three-family threshold to raw `families`.
- Neither the backbone, R(e), nor the communities is ever compared. The reported Jaccard values (CLICS³ 0.559, CLICS⁴ 0.611) therefore describe the old raw network, not the robustness revision.
- The crosswalk itself is sound: the CLICS³ GML labels are Concepticon IDs, giving 2,888 common concepts.
- **Remedy (P3):** add, as a diagnostic only, backbone-vs-CLICS⁴ and community-vs-CLICS⁴ overlap restricted to matched languages, alongside the effect of each gate.

## 12. Claims checked and found correct (for fairness)

- **`representatives()` keeps pair existence** (`colexification.py:322-352`). Proof by cases on the test point (f′, p′): when p₀ = p′, the query `p≠p₀ ∧ f≠f₁` is exactly the needed condition; the f₀ = f′ case is symmetric. Applying it to both sides keeps the A×B result.
- **The `pair_status` range shortcut** (`:423-426`) looked wrong at first, but the singleton guard at `:423` covers every counterexample. A toy database confirmed correct output, and the data has 0 cases. Not a bug.
- **Single-block and single-family edges get zero weight** (`colexification_evidence.py:121-127`). Correct.
- **Bootstrap multiplicity cannot create new families:** eligibility counts distinct families (`:109-123`). Correct.
- **The semantic gate is applied consistently** to both witness sides, and approved representatives are preferred (`colexification.py:384`).
- **The medoid tie-break** follows the documentation.

## 13. Prioritised remedies

| Priority | Remedy | Sections |
|---|---|---|
| P1 | Require ≥2 surviving families after the worst block deletion, or rename the tier; publish both | 1 |
| P1 | Guard against affix markers and one-segment / truncated identities; extend the extraction audit to Huntergatherer, TNG and Z'graggen members | 2 |
| P1 | Add a concept-containment / overlap table and exclude those pairs from the backbone | 3 |
| P2 | Canonical family key (isolates); handle pseudo-families properly | 4, 5 |
| P2 | Replace or contrast the family maximum with mean or per-language aggregation; compute k over eligible concepts; sensitivity analysis over the exponent | 6, 7 |
| P3 | Resource-provenance audit; within-scope chance-homophony null as a diagnostic | 8, 9c |
| P3 | Report node retention alongside every ARI; per-community stability | 10 |
| P3 | CLICS comparison of the backbone and communities | 11 |
| P4 | Prosody-unresolved identity comparison; extend the semantic queue beyond Wiktionary; raise on conflicting local approvals; move the bootstrap test to the production path | 9a, 9b, 9d, 10 |

Absence of an edge remains unknown, not negative, throughout. None of the findings above shows that a reported identity is false at source level. They show that the replicated weighting and the clustering built on it currently encode representation, catalog and classification artefacts.
