# Colexification robustness: sense alignment, bounded influence and replication

The user’s BAG–WITCH example exposed an English-interlingua sense-alignment error. This revision corrects the data and separates reported identity, semantic eligibility and replicated network inference. It does not tune Arca to reproduce CLICS²/³/⁴, and does not claim that a new weighting scheme discovers semantic truth automatically.

## Case and data audit

The frozen native parameter `wikt_bag_noun_cba23ba4` is **“bag (noun): ugly woman”**, but upstream headword matching assigned it Concepticon2468, Arca `act-bag`, whose frozen definition is a portable container. English *bag* has a derogatory human sense; this is not evidence that Galician denotes a container with the word for a witch. The original mapping code passed the English headword and POS to the matcher and ignored the retained source sense. Correct IPA cannot repair this semantic mismatch.

The [original Galician entry](https://en.wiktionary.org/wiki/antaruxa) and [extracted native sense](https://kaikki.org/dictionary/Galician/meaning/a/an/antaruxa.html) give the witch/hag reading. The old Arca graph actually has **two Galician identity witnesses**, `antaruxa` and `lurpia`, in both segmented and citation layers; their combined support is one variety, one language and one family, not four independent observations. [Lurpia’s original entry](https://en.wiktionary.org/wiki/lurpia) also distinguishes its supernatural and derogatory uses. Neither entry supports a container sense here.

The wider review checks54 English source senses against frozen definitions. Fourteen earlier unmapping decisions are reconfirmed;40 new guarded shared rules comprise28 unmaps and12 explicit positive sense equivalences. They correct95 accepted concept assignments across15 constructions. All native records/readings/cognacy/comments remain; no substitute concept is forced for the rejected equivalence.156 scores change mechanically where explicit positive rules populate the source mapping field used by the existing scorer; these are not pronunciation improvements. [Sense decisions](colexification_sense_reviews_2026-11-01.json), [exact changed records](colexification_mapping_changes_2026-11-01.json), [full preservation](colexification_robustness_preservation_2026-11-01.json).

Examples include sports BAT versus the flying mammal; industrial CRANE versus the bird; non-animal SEAL and MOLE senses; political/directional LEFT and RIGHT; learner versus eye PUPIL; musical versus geological ROCK. These decisions inspect source sense/POS/definition, not edit distance, graph proximity or a language model’s estimate of plausibility. Original intake remains unchanged, with its erroneous candidate alignment traceable. The shared build overlay enforces reviewed corrections across affected accepted constructions and future builds.

All7,366 constructions/2,119,818 records remain. Core mapped/supported slots remain544,347/470,209. Correcting false coverage removes nine mapped and five supported all-concept slots:1,337,327 mapped/1,209,478 supported. [Metrics](colexification_robustness_metrics_2026-11-01.json). Etruscan/Elamite historical readings and previous source-specific exclusions are retained.

## Research and critical assessment

The following are primary methodological sources. Their findings motivate distinct choices; they do not collectively prescribe Arca’s implementation.

* [François’s lexical-typological framework, as operationalized by CLICS²](https://doi.org/10.1515/lingty-2018-0010), [CLICS³](https://doi.org/10.1038/s41597-019-0341-x) and [CLICS⁴](https://aclanthology.org/2025.iwcs-main.1/) require comparable meaning units and inspectable form evidence. Distinct IDs and phonetic validity do not themselves validate sense equivalence. Our case is an Arca alignment failure, not evidence that those releases contain this error.
* [Snee & List2026](https://doi.org/10.15475/calcip.2026.1.2) separate recorded identity, sampled nonidentity and unavailable evidence. Arca retains its three-way comparison and actual source/member coverage; unreviewed mappings do not become negative lexical facts.
* [Newman2001](https://doi.org/10.1103/PhysRevE.64.016132) motivates accounting for affiliation-group size in projected networks. [Eriksson et al.2021](https://doi.org/10.1038/s42005-021-00634-z) show that representation and random-walk choice affect hypergraph communities. Treating every pair from one many-meaning identity as an independent full-strength observation creates correlated cliques. Arca chooses unit total pair mass per identity, a stricter influence convention than Newman’s per-node normalization, and preserves the original groups so the convention can be challenged.
* [Tumminello et al.2011](https://arxiv.org/abs/1008.1414) and [Domagalski, Neal & Sagan2021](https://doi.org/10.1371/journal.pone.0244363) distinguish arbitrary thresholds from statistically validated bipartite projections. Fixed-degree nulls preserve different margins from simple overlap models; Monte Carlo accuracy and multiple testing matter. A family cutoff, high observed fraction or high PMI is not a calibrated significance test. Arca does **not** label the new backbone statistically significant: a validated null respecting source scopes, sense inventories, degrees, coverage and genealogy is not established by this revision.
* [Smiljanić, Edler & Rosvall2020](https://doi.org/10.1103/PhysRevE.102.012302) show how sparse or incompletely observed networks can overfit Infomap communities. The [pinned Infomap2.16 options](https://mapequation.org/infomap-python-docs/examples/options-guide.html) provide a regularized sensitivity model; its Bayesian prior is a clustering assumption and never becomes lexical evidence.
* [Peixoto2018](https://doi.org/10.1103/PhysRevX.8.041011) demonstrates why heterogeneous measurement errors belong in network inference. We do not fit an unidentifiable universal error rate from these lexical observations. Source deletion and explicit semantic holds expose specific vulnerabilities without pretending to estimate unknown measurement error.
* [Brochhagen & Boleda2022](https://doi.org/10.1016/j.cognition.2022.105179) caution against reducing colexification to a monotonic synonymy measure. Unexpected semantic relations remain research evidence. Embedding similarity, WordNet distance and agreement with CLICS are not filters for deleting surprising pairs.

Private acquisition/readings and exact fetched resource hashes are under `raw/curation/colexification-robustness-2026-11-01`. Some direct HTTP fetches returned403 even though the web reader supplied the page; the pin manifest records those failures rather than inventing downloaded originals.

## Linguistic eligibility

Whole-form identity remains exact and source/member/pronunciation/basis scoped. The reported network retains rare observations and distinguishes polysemy, homophony and underspecification only when separate linguistic evidence permits. It does not infer partial colexification from substrings.

For the replicated model, legacy English Wiktionary **headword-only concept assignments are unreviewed** until a source-level rule or explicit variety/native-record sense review agrees with the accepted concept. Valid IPA, tokenization and repeated translations cannot approve their own meanings. `needs_review` decisions do not qualify. Conflicting parameter-level approvals remain unreviewed; a guarded native-record judgment has its own scope. Controlled upstream concept mappings remain labelled `source_mapping`, not independently certified semantics. Other resources can still contain errors; this gate addresses the demonstrated automatic-headword failure class, not every possible semantic problem.

A reported identity is kept even if it cannot enter the replicated backbone. Native English sense labels are now exported beside example IDs. Legacy slug/hash collisions for Reykjavik/Reykjavík, Boy Scout/boy scout and krona/króna retain all source labels; an ambiguous parameter ID cannot acquire a parameter-level semantic approval silently. A valid reviewed pair is preferred over earlier unreviewed alternatives within the same identity; bounded representative selection preserves pair existence without Cartesian joins.

## Mathematical model

Let an eligible source-scoped identity group contain `k` distinct reported concepts, with `2 ≤ k ≤ 64`. For every actual observed pair in that group, assign

```
m(g) = 1 / choose(k,2) = 2 / (k(k−1)).
```

The total projected mass of one group is at most1, even if it creates a dense clique. Gating out a questionable pair does not redistribute its mass to the remaining pairs. Observed records and group sizes remain downloadable; no new edge is created by this weighting.

For pair `e`, known family `f`, and resource block `r`, retain the maximum eligible group mass `q(e,f,r)`. Define

```
A(e) = sum_f max_r q(e,f,r)
R(e) = min_deleted_block sum_f max_remaining_blocks q(e,f,r)
```

Empty maxima equal0. Each known family contributes at most1 to `A`, regardless of synonym counts, dialect duplication, multiple pronunciation scopes or repeated resources. `R` measures the worst loss after deleting any one known resource block. Identical editions/derivatives in a known block cannot manufacture resource replication. [Block registry](../src/arcaverborum/data/colexification/resource_blocks.json) groups the named Wiktionary editions, IDS variants, HGN derivatives, LexiRumah derivatives and RefLex compilation slices conservatively. Different blocks are not certified independent original dictionaries.

The replicated backbone uses `R(e)` only if **at least two distinct eligible known families** contribute and `R(e)>0`. A singleton, a one-family association or an association confined to one resource block has zero clustering weight. These conditions are operational robustness safeguards, not universal linguistic criteria or p-values. Unclassified or rare American evidence remains visible in the reported network, with a zero adjusted weight explained as insufficient replication rather than falsity or absence.

This is a minimax deletion diagnostic and bounded-influence projection. It is not a coverage-corrected population estimate: family sampling, contact and resource availability remain uneven. High-quality patterns known only from one source may be excluded from global clustering. That tradeoff is explicit and can be examined through the raw-network sensitivity model and complete reported data.

## Clusters and uncertainty

Infomap runs ten seeds/five trials on the weighted replicated backbone. The displayed partition is the **medoid by mean adjusted Rand agreement** among seeded solutions; ties use codelength and seed. Thus a lone extreme optimum does not automatically become the representative map. Only incident eligible nodes receive assignments.

The pipeline additionally fits the raw family-count graph, regularized Infomap, three Leiden resolutions, the legacy three-family screen, source/whole-resource-block/area deletions, an Americas subset and50 family-block perturbations. Each perturbation recomputes capped resource-deletion support from eligible witnesses. Repeated draws weight a family but cannot turn one distinct lineage into two. Adjusted Rand uses common eligible nodes; non-observed nodes are not padded into fake clusters. Complete partitions and per-edge diagnostics are exported.

Seed coassignment and block coassignment are sensitivity frequencies, not confidence intervals or posterior probabilities that two meanings share a universal semantic category. Regularized flow priors and algorithmic community membership never add reported colexifications. Preview links retain exact raw family/language/variety counts and carry the separate model weight. Layout distance remains illustrative.

## Display, reproduction and limits

Concept pages retain all reported pairs, native examples and normal filters. Tables distinguish **sense review required**, **limited replication** and **replicated backbone**. The default line width is bounded replicated support; raw family/language/variety widths remain available. A dashed zero does not reject a documented local pattern. Community previews use the new global replicated model; missing assignments are explained.

The implementation remains disk-backed and sparse: no dense concept-pair/language matrix, no unbounded Cartesian join, source-sense tables and projection blocks in SQLite, bounded JSON pages/31-node previews and isolated sequential native clustering workers. The full core and community runs retain a256MiB address-space budget. Input hashes include semantic review files, source labels, resource blocks and the new evidence code. Publication cannot reuse a stale analysis after changed mappings or eligibility.

```
.venv/bin/python scripts/build_colexification.py --memory-mb 256 --publish --with-communities
.venv/bin/python scripts/verify_colexification_robustness.py
.venv/bin/python scripts/audit_colexification_semantics.py --build output/colexification/BUILD --output REPORT.csv
```

The audit is a review queue, not automatic corrections: it ranks unreviewed dictionary senses that contribute representative reported witnesses, with original English senses, frozen definitions and source/family breadth. Semantic distance or frequency alone never clears a mapping. Before substantially more data is published, measure the static-site budget and retire obsolete generations as whole immutable directories; active data must remain complete.

Production metrics, independent community verification, final browser checks and publication proof are linked from STATUS at closure. Historical CLICS comparisons retain their dated inputs; matching them is not the success criterion for this method.

## Production outcome and critical assessment

The rebuilt reported graph has44,414 segmented observed pairs (seven fewer) and43,669 citation pairs (eleven fewer); ASJP-derived508 and inferred six-per-eligible-layer counts remain separate. BAG–WITCH is absent. The replicated weighted backbone has5,551 edges and1,613 incident concepts. The selected medoid seed8 yields237 communities; this equal count to the old model is coincidental, not matched labels or equivalence of membership.81 partitions were fit, including whole-resource-block deletions in addition to namespace deletions. All26,993 exported community preview edges are independently checked against sealed evidence and positive model weights; the full selected partition reproduces exactly. Core634.05s/112.77MiB RSS; fresh community parent90.63MiB/worker67.32MiB, each under256MiB AS.

Seed-to-medoid adjusted Rand values range0.915–1.000. Family-block perturbations have median agreement0.669 (range0.580–0.756), demonstrating substantial lineage-sampling sensitivity. Regularized Infomap has245 groups and0.930 agreement; raw family-count clustering has239 groups and0.446 agreement on common nodes. Leiden gives56–86 coarser groups and0.107–0.389 agreement. These contrasts materially limit any claim that the displayed237 groups are unique linguistic categories. The safeguards address demonstrable alignment and influence failures; they do not establish globally superior cognitive validity or calibrated semantic probabilities. [Detailed metrics and model contrasts](colexification_robustness_metrics_2026-11-01.json), [independent verification](colexification_robustness_communities_2026-11-01.json).

The ranked [semantic queue](colexification_semantic_queue_2026-11-01.csv) contains1,129 unreviewed parameter/concept pairs implicated in representative reported identities. That is not1,129 proven errors. Review original senses and definitions before further corrections, especially high-contribution mappings. Keeping these candidates inspectable while withholding unreviewed dictionary equivalences from replicated inference is an intentional completeness/precision distinction.
