# Exploratory global colexification communities

**Prepared refresh (2026-11-01):** [bounded-influence method](COLEXIFICATION_ROBUSTNESS_2026-11-01.md)
and [executed validation/source review](research/CINF_EXECUTION_2026-11-01.md).
Core `3a3898b1362a5c2d2c30bf73`, communities `617951c483ddc3f569627471`:
medoid seed4,239 exploratory groups/1,610 assigned concepts from5,362 eligible
weighted edges;81 model/perturbation runs. [Independent verification](research/cinf_community_verification_2026-11-01.json)
reproduces the selected partition and checks all memberships and25,450 preview
edges. Raw/regularized/Leiden/whole-block contrasts remain explicit. The broader
inference experiment does not justify replacing these evidence weights with
model probabilities. This is not calibrated significance, a unique semantic
classification, or proof of lexeme-level polysemy. Older counts below are historical.

The selected model partitions the eligible conservative backbone of the
**observed segmented** graph, with raw-graph contrasts available. It complements
the existing local neighborhoods. A community is a result of a stated graph model,
not a certified semantic field or a set of newly observed lexical connections.

## Evidence, eligibility and weights

Input is the closed, sealed analytical SQLite database. Publication binds its
file digest, embedded/public manifest, concept identities, pipeline code and
runtime. Reconstruction and reviewed extraction exclusions affect both positive
witnesses and comparison opportunities; original lexical records are retained.

The initial undirected flow model uses distinct known Glottolog family lineages
as edge weights. Edges with zero known-family support remain in the observed
exports and local explorer, but do not receive invented positive model weights.
Every catalog concept has explicit assignment or nonassignment status. Merged,
unsampled, isolated and unclassified evidence must not be pooled into a cluster.

No three-family screen is applied to the default partition. It would exclude
most observed edges and much rare/regional evidence. A separate three-family
run measures that choice's effect. Inferred broad-slot and reduced ASJP/GLED
layers are not mixed into this observed model. Exact identity is neutral between
polysemy and homophony; global family support does not resolve that distinction.

## Algorithms and perturbations

The offline optional research dependencies are pinned: Infomap 2.16.0 and
python-igraph 1.0.0. The main model is two-level undirected Infomap, with ten fixed
seeds and five trials per seed, one worker thread. The minimum codelength selects
the displayed partition; ties use seed order. Community labels are anchored by
the smallest stable concept identifier, rather than arbitrary engine numbers.

Leiden modularity at resolutions 0.5, 1 and 2 uses a different objective and
provides a model comparison. Every partition executes in a fresh sequential
worker process, releasing native engine allocations between calls; the address
space cap applies to each worker as well as the orchestrator. Additional Infomap runs remove each of the three
largest contributing resource namespaces and the targeted huntergatherer/Johansson
resources, remove each recorded macroarea, and
restrict support to the Americas. Semicolon-separated area memberships are
treated as memberships in each listed area; these metadata do not establish
original fieldwork location. Family support is recomputed from surviving
source-scoped witnesses in every such run. A namespace is a resource/compilation,
not necessarily an independent original dictionary or elicitation event.

Fifty sequential perturbations resample known accepted family-lineage blocks
with replacement, using seed 104729. A family's draw multiplicity contributes
to the weight; repeated blocks are not collapsed back to one. This exercises
sensitivity to the sampled family composition. It does not supply independent
population draws, calibrated confidence, or a significance test. Unknown family
classification remains unknown. Family sampling and algorithm seeds measure
different forms of variability and are reported separately.

Adjusted Rand comparisons use only nodes eligible in both runs. Full partitions
retain each run's own eligibility. Edge coassignment probes cover only the
sparse observed graph with positive known-family weights; their denominator is
the number of perturbations in which both endpoints are eligible. Unavailable
nodes are never treated as one common community. These probes cannot establish
stability of every pair inside a displayed community.

## Source and projection diagnostics

The complete CSV reports resource namespace counts, the largest resource's share
of supporting known families, the minimum family support after removing any one
resource, and the largest source-scoped identity group that supplied a witness.
The resource-removal minimum is diagnostic, not the default rank or a filter:
single-resource dictionaries can be valuable, especially for small American
families. Conversely, multiple namespace labels may reproduce one original source.
Ultimate-source independence remains unreviewed unless separately established.

Whole-form identity groups project into all eligible concept pairs. A genuine
20-meaning identity and a corrupted 20-meaning prefix both project up to 190
pairs; graph clustering cannot distinguish their origin. The extraction audit
and original-source review therefore precede linguistic interpretation.

The positive-family fraction is positive known lineages divided by comparable
known lineages, meaning at least one eligible positive within each lineage. It
is distinct from the variety fraction and from an average of within-family
rates. Neither fraction estimates a population probability. Questionnaire
coverage, synonym depth, source selection, inheritance and contact remain relevant.

Refined concepts such as upper/lower limb segments, speaker-sex kin terms,
aged/used and inclusive/exclusive pronouns need source-semantic inspection.
Shared native words for distinct meanings can be valid evidence. Neither a
shared label fragment nor a common WordNet parent establishes an artifact.
No automatic subdivision-edge deletion or new observed similarity links occurs.
Mixed transcription bases remain conservative unknowns across bases; their
source conventions need review before changing comparison opportunities.

## Browser and reproducibility

Concept pages offer a local-neighborhood view and a global-community preview.
The preview retains the focal concept plus at most 30 members ranked by
within-community family-weighted degree, and all eligible edges between those
selected nodes. It discloses the complete community size. Line width still shows
the selected support measure; layout distance and membership color do not encode
confidence. Other representation/evidence modes retain their own local networks.
The full membership table contains every run and eligible concept; complete
edge diagnostics are separately downloadable. Per-concept downloads are bounded
and checksummed; the complete graph and all replicate partitions are never
loaded into the browser.

```sh
uv pip install --python .venv/bin/python '.[research]'
.venv/bin/python scripts/build_colexification.py --memory-mb 256
.venv/bin/python scripts/build_colexification_communities.py \
  --build output/colexification/BUILD_ID --memory-mb 256 --publish
```

Publish the matching evidence and local subgraphs before the community pointer.
The CLI takes an exclusive build lock. The generator stages complete artifacts,
verifies hashes, then switches the
small manifest pointer last. It uses sparse edges and sequential runs, not a
dense concept-pair-by-replicate tensor. The pilot fails above 10,000 concepts or
250,000 edges and enforces per-file limits; the CLI imposes the 256 MiB address
space cap. Corpus measurements and accepted results accompany batch closure.

## References

[CLICS³](https://doi.org/10.1038/s41597-019-0341-x) motivates global community
exploration. [CLICS⁴](https://aclanthology.org/2025.iwcs-main.1/) discusses sample,
transcription and meaning-scope limitations. [Infomap's theory and tutorial](https://arxiv.org/abs/2311.04036)
and [incomplete-observation work](https://arxiv.org/abs/2106.14798) motivate model
and missingness sensitivity. [Leiden](https://doi.org/10.1038/s41598-019-41695-z)
offers a separate optimization objective; agreement between algorithms is not
proof of a universal semantic partition.


## Accepted pilot, 2026-10-31

Input `db68b765a4a3e48d2129b656`; community build
`2e58569c5ba7972feab60dc3`. The selected seed is 9: **237 communities and
2,974 assigned concepts**, from 44,396 positive-known-family edges. The 25
zero-known-family edges remain observed evidence in the ordinary explorer.
All 3,828 catalog concepts have a sidecar and explicit assignment status.

| Comparison with selected partition | Adjusted Rand result |
| --- | --- |
| Ten fixed seeds | 0.697–1.000, on 2,974 common eligible nodes |
| Fifty family-block perturbations | 0.265–0.524, each on its common eligible nodes |
| Leiden resolutions 0.5 / 1 / 2 | 0.005 / 0.108 / 0.348 |
| Without IDS | 0.524, 2,966 common nodes |
| Without huntergatherer | 0.688, 2,953 common nodes |
| Without Johansson | 0.704, 2,973 common nodes |
| Americas-only | 0.379, 1,809 common nodes |

These results establish substantial sampling and model dependence. The selected
partition is useful for exploration, while a claim of robust universal semantic
communities would exceed this evidence. Different eligible node sets also affect
comparisons: these figures are not accuracy scores or directly exchangeable
estimates of one population quantity. The actual number of Leiden communities
also varies nonmonotonically across these optimization runs; resolution is a model
setting, not a calibrated semantic granularity scale.

37,775/44,421 observed edges have one resource namespace. Of 3,404 three-family
edges, 2,117 fall below that threshold after removing at least one namespace.
That describes dependence on the sampled compilations and coverage; it does not
establish bad data or resolve their original-source independence. All-support
exploration retains rare evidence, including evidence in small American families.

[Independent verification](colexification_communities_verification_2026-10-31.json)
checks every preview edge and count against sealed SQLite, complete memberships,
all asset hashes, source diagnostic bounds and exact reproduction of the selected
full partition. The full pilot peaked at 103.59 MiB in the orchestrator and
92.22 MiB in a worker, each under 256 MiB. The preliminary in-process engine run
hit the cap and failed without publication; fresh sequential workers resolved
the accumulation. The verifier separately peaked at 58.76/58.51 MiB.

Member inspection also finds instructive outliers: the HAND community includes
EMU through one Dhudhuroa identity in Bowern's Pama-Nyungan resource (`murra` in
both `bowernpny_Dhudhuroa-12_emu-1` and
`bowernpny_Dhudhuroa-148_hand-1`). This is an inspectable source observation,
not evidence that emus form a semantic field with human limbs. Homophony,
historical transcription and original meaning attribution need dictionary review.
The observation remains available with one-family support, and the community is
labelled exploratory. No edge is deleted merely for disagreeing with intuition.


[Publication proof](colexification_communities_publication_2026-10-31.json):
data commit `1da9b7f61` is deployed, CI and Pages succeed, all20,129 checked active
assets and five comparison artifacts match https://arcaverborum.org/, and all
five live browser suites pass. The earlier lexical/WordNet/concept-table manifest
fields and source hashes remain unchanged.
