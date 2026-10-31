# Comparing Arca Verborum with CLICS

Comparison date: 2026-10-31. Arca analytical snapshot `b198f6cb17cb9817b91686cc`. No lexical readings, semantic mappings, source selections or underlying network edges were changed to obtain agreement.

The reference releases are [CLICS³ v1.1](https://github.com/clics/clics3/tree/v1.1) and [CLICS⁴ v1.0](https://github.com/clics/clics4/tree/v1.0). Downloads are pinned to full commits and SHA-256 in [the source lock](../src/arcaverborum/data/colexification/clics_sources.json); both releases use CC BY 4.0. The analysis uses published data artifacts, rather than numbers copied from a paper or README.

[Machine-readable results and 38 diagnostic pairs](colexification_clics_comparison_2026-10-31.json) · [Complete pair comparison CSV](colexification_clics_comparison_2026-10-31.csv) · [Arca method](COLEXIFICATION.md)

## Agreement on recurring connections

Only active concepts with unique, identical Concepticon IDs are aligned. Labels alone do not join meanings. Arca’s segmented **observed** layer is compared with each reference; citation-form, reduced ASJP/GLED and broad-slot inference layers are excluded from this primary comparison. Each side must independently meet the three-known-family threshold.

| Reference | Shared concept IDs | Arca recurring pairs | Reference recurring pairs | Pairs in both | Arca only at this threshold | Reference only at this threshold |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| clics3 | 2,888 | 3,361 | 4,188 | 2,702 | 659 | 1,486 |
| clics4 | 1,727 | 2,930 | 3,986 | 2,628 | 302 | 1,358 |

Among Arca’s 2,930 recurring pairs within the CLICS⁴ concept universe, 2,628 (89.7%) also reach the reference’s recurrence threshold. This describes agreement in these samples; it is not an accuracy score. The thresholds use each release’s own classification and family counts, so they do not fully control classification revisions.

CLICS³’s distributed `network-3-families.gml` contains 4,228 edges before restricting its concept universe; it censors lower-support connections. An unlisted CLICS³ pair must **not** be called absent below three families. The 2,967-edge Infomap output described in its README is a different artifact. CLICS⁴’s colexification table contains 51,562 edges at all support levels. Within the 1,727 common concept IDs, its 51,531 edges overlap 29,350 of our 35,339 edges. Lower-support differences are much more numerous than recurring-pattern differences.

Family-count ranks on shared pairs correlate positively, but counts differ substantially: Spearman’s rho is 0.794 for CLICS³ and 0.779 for CLICS⁴. Ties receive average ranks. These are descriptive correlations, with no significance or independence claim.

## Familiar patterns: actual family counts

| Meaning pair | Arca observed | CLICS³ | CLICS⁴ |
| --- | ---: | ---: | ---: |
| TREE–WOOD | 48 | 59 | 58 |
| MOON–MONTH | 49 | 57 | 60 |
| CLAW–FINGERNAIL | 46 | 55 | 65 |
| HAND–ARM | 39 | 48 | 53 |
| LEG–FOOT | 44 | 52 | 100 |
| BARK–SKIN | 67 | 49 | 62 |
| BLUE–GREEN | 52 | 46 | 70 |
| FLESH–MEAT | 35 | 47 | 105 |

These are support counts, not rates or probabilities. CLICS⁴ counts may include expanded source slots, while the Arca column is observed evidence only. For example, Arca separately records 837 inferred varieties for LEG–FOOT, 1,109 for FLESH–MEAT and 328 for HAND–ARM; these overlapping counts are not added to the observed totals.

## Broad-source meanings explain major differences

CLICS⁴ publishes 108,491 forms marked `ConceptInSource`, and 131 target concepts carry expansion metadata. Tracing every published form pair finds 201,183 pairs: 122,908 have two unexpanded readings with distinct native `Local_ID`; 76,275 involve an expanded reading or shared native ID. Of all pairs, 53,737 reuse the same native ID on both sides. These are method differences, not a declaration that CLICS’s inferred relations are invalid.

For example, HE–SHE has 226 reference families versus 15 observed Arca families. In the current Glottolog collapse, the reference has 1,295 supporting language units when all its readings are included, but 48 when both readings must be unexpanded with distinct native IDs. One concrete reference witness duplicates WOLD Dutch `wold-Dutch-2-93-1` into both target slots. Likewise, the 88-family BREAK(2558)–BREAK(3020) reference edge has no unexpanded, distinct-native-ID witnesses in this screening. Arca does not assert such pairs as independently observed.

The conservative unexpanded screen also removes legitimate comparisons in which only one endpoint was refined from a broader meaning. It is a sensitivity analysis, not a replacement reference network. CLICS⁴’s concept-level `Original_Concept` field alone would be too coarse; this analysis reads the individual form-level flags.

## Control the language sample, then inspect missingness

All CLICS⁴ Glottocodes are collapsed with the same current Glottolog language mapping used by Arca. There are 1,903 shared language units with usable Arca segmented coverage. Concepts remain exact-ID matches. A pair–language observation is counted once even if multiple questionnaires or forms support it.

| Comparison within shared concepts/languages | Arca positive pair–language cells | Reference positive cells | In both | Arca only | Reference only |
| --- | ---: | ---: | ---: | ---: | ---: |
| All CLICS⁴ readings | 77,661 | 150,780 | 66,842 | 10,819 | 83,938 |
| Unexpanded, distinct-native-ID reference readings | 77,661 | 105,626 | 66,725 | 10,936 | 38,901 |

Removing expanded readings reduces reference-only positive cells from 83,938 to 38,901, while shared cells change from 66,842 to 66,725. This establishes that expansion accounts for much of the raw difference in this controlled sample. It does not explain every remaining discrepancy. Source questionnaires, versions, synonyms and selected readings still differ.

Every discordant unexpanded positive cell was then queried against the other sample’s source-comparable coverage. Arca requires both meanings within one native source/member/pronunciation/basis scope and distinct native form/parameter evidence. Reference comparability requires both unexpanded meanings with distinct native IDs within one questionnaire variety. Positive evidence wins when collapsing questionnaires to languages.

| Positive cells found only on one side | Other sample has comparable but distinct readings | Other sample has no comparable readings |
| --- | ---: | ---: |
| 38,901 CLICS⁴-only unexpanded cells | 12,759 | 26,142 |
| 10,936 Arca-only cells | 3,061 | 7,875 |

Thus 67.2% of reference-only cells are unknown in Arca under this comparison rule, rather than sampled distinctions. Neither column is a claim about lexical absence in the language. The remaining sampled distinctions are the appropriate place for source/reading review, still allowing synonyms, dialects and source versions to differ.

## Source-traced examples

**Hausa TREE–WOOD:** Arca selects IDS segmented evidence: TREE `bishiya` / `itaci`, WOOD `itace`. CLICS⁴ retains those distinctions in IDS, but additionally has WOLD TREE/WOOD `ítàacée` and Kraft TREE/WOOD `itā̀cē`. Its positive Hausa cell and our sampled nonmatch concern different accepted source constructions. Reference varieties 39 (WOLD), 104 (IDS), and 789 (Kraft) retain their separate source identities.

**Negidal MOON–MONTH:** Arca uses Oskolskaya `bɛːga` / `bɛːɣa`. CLICS⁴’s Oskolskaya variety 1710 also preserves that distinction; its Robbeets variety 1792 gives `beːga` for both. This is a selected-source difference, not proof that either record or the /g/–/ɣ/ contrast should be discarded.

**Tsez TREE–WOOD:** Arca’s selected IDS dialect records have TREE `ɣun` versus WOOD `qaca` / `cʼaraʕ`; CLICS⁴ additionally includes NorthEuraLex variety 390 with `ʁun` for both. Collapsing all these to one Glottolog language makes the summaries differ, while the source-level readings are compatible.

These examples were inspected in the frozen reference form table and Arca’s source-scoped readings. They demonstrate specific explanations; they do not establish that every discrepancy has the same cause. The JSON report provides source IDs and representative reference witnesses for 38 diagnostic pairs, plus source-comparable missingness counts.

## What should remain different

1. **Meaning scope and historical IDs:** strict matching excludes 31 CLICS³ concepts and three CLICS⁴ concepts. The three are Concepticon 776 TRUNK OF TREE, 800 THIGH and 2275 SHADOW; Arca marks these merged into 344 TREE TRUNK, 471 UPPER LEG and 1388 SHADE. This does not imply that Arca lacks the meanings. A reviewed historical-ID crosswalk can be a separate sensitivity analysis; automatic label matching would obscure the decision.
2. **Source selection and depth:** Arca constructs one accepted variety from selected primaries and reviewed supplements. CLICS aggregates separate source questionnaires. There are 88 matching source namespaces with segmented Arca evidence, seven reference namespaces without such an exact match, and 92 Arca namespaces without a reference match. Matching namespaces do not imply matching versions or members, and overlapping source material is not independent confirmation.
3. **Representation:** CLICS⁴ requires transcribed material and applies its sound representation; Arca’s main identity preserves accepted segments jointly with original supplied IPA or explicit-stress citation when available. Citation, normalized fallback, profile-derived and reduced evidence have explicit scopes. Normalization differences need record-level review, not automatic merging.
4. **Sampling and missingness:** CLICS⁴ selects frequent concepts and imposes a 180-concept variety screen; Arca admits reviewed narrow dictionaries and historical slices as well. A positive edge in one sample and unknown or sampled-distinct entries in another is expected.
5. **Graph presentation:** our 31-node induced neighborhood is a bounded subset of actual connections. CLICS communities and full networks are different views. A connection outside our selected neighborhood is not missing from the database. We do not add inferred similarity or transitive edges for visual agreement.

## Strength in the explorer

Graph line width now selects **known family lineages** (default), **known language units**, or **accepted varieties**. A visible legend uses the same mapping across concepts: `1 + 0.8 × log₂(1 + count)`. It has no high-count saturation cap. Exact three-level support counts are available in tooltips and by selecting an edge with a mouse or keyboard; the metric is preserved in the URL. Zero known classified support uses a dashed line, not an absent-edge symbol.

Orange/blue distinguishes focal from neighbor links; it does not encode statistical significance. Neighbor selection remains ranked by family support when the width metric changes. Layout distances have no statistical interpretation. These counts measure sampled breadth, not polysemy versus homophony, independence, effect size or coverage-adjusted association. CLICS⁴’s `Family_Weight` is a different quantity: on all 51,562 published edges, it matches `10 × f² / min(Fa, Fb)²`, with `f` set to zero for singleton-family edges and `Fa/Fb` the endpoint family counts. That uses marginal concept coverage, not the number of source-comparable opportunities for the pair. We retain it in the comparison CSV but do not label it as a probability or silently substitute it for the graph’s support counts. [Verification](colexification_clics_verification_2026-10-31.json).

The table separately exposes source-comparable denominators for observed focal pairs. No denominator is invented for cross-neighbor or inferred links.

## Reproduction and next investigations

```sh
.venv/bin/python scripts/compare_clics.py --fetch --memory-mb 256
```

The first run downloads pinned reference archives; later runs verify their hashes without network access. CSV/GML/form rows stream into a scratch SQLite database under `output/colexification-comparison/`. The accepted analytical database is attached read-only. No NetworkX graph, CLDF runtime dependency, dense concept-by-language matrix or global all-pairs coverage table is constructed. CSV fields and GML lines are bounded at 8 MiB; the process has a 256 MiB address-space cap. Results pin the analytical manifest, concept/classification hashes, reference hashes and comparison code.

Follow-up should target original-source evidence: review the remaining sampled distinctions for reading/version differences; consider source-backed supplements where the reference exposes a well-supported missing reading; audit expanded kinship and pronoun meanings; and review historical Concepticon redirects. Broader profile or normalization changes need independent linguistic justification. Agreement with CLICS alone is never the admission criterion.

Validation: 550 tests pass. The complete comparison and sparse missingness audit peaked at **216.46 MiB RSS under a 256 MiB address-space cap**. The 112,171 CSV rows were independently recounted, and all reference/input/code hashes checked. Local colexification-strength, WordNet and general research browser suites pass. Analytical and lexical data are unchanged.
