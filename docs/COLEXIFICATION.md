# Colexification: method, evidence and bounded-memory pipeline

Arca computes whole-form colexification from its own accepted constructions.
This is a derived analytical layer: it does not change words, readings, concept
assignments, WordNet links, source selection or cognacy. An observed identity is
neutral between polysemy, homophony and underspecification; it does not certify
polysemy or semantic equivalence.

## Studies informing the implementation

* List, Greenhill, Anderson, Mayer, Tresoldi & Forkel (2018),
  [CLICS²](https://doi.org/10.1515/lingty-2018-0010): comparable concept/language
  identities, family support and inspectable original evidence. Its ASCII-based
  cleaning is deliberately not reproduced here.
* Rzymski, Tresoldi et al. (2020),
  [CLICS³](https://doi.org/10.1038/s41597-019-0341-x): reproducible aggregation,
  source-based equality and networks with explicit supporting observations.
* Tjuka, Forkel, Rzymski & List (2025),
  [CLICS⁴](https://aclanthology.org/2025.iwcs-main.1/): transcription quality,
  underspecified concepts, actual per-variety coverage and transparent data.
* Snee & List (2026),
  [missing-data computation](https://doi.org/10.15475/calcip.2026.1.2): distinguish
  recorded colexification, sampled distinctions and unavailable evidence.
* List (2023),
  [partial colexifications](https://arxiv.org/abs/2302.00739): partial overlap needs
  its own method because shared grammatical material can produce noisy networks.

The publications were read for the method; their lexical datasets and code are
not imported into this pipeline. Private paper snapshots and reading/benchmark
logs are under `raw/curation/colexification/`. Methodological choices below are
Arca's implementation decisions, not claims that the cited studies mandate them.

## What counts as an observed connection

An undirected edge joins two **different active frozen concepts** when eligible
records have exactly the same comparison form inside one scope:

```
accepted variety + source namespace + source member + pronunciation tags
+ comparison basis
```

Both the native source-form IDs and native parameter IDs must differ. This
checks identifiers recoverable from the source dataset, not original field
elicitation: upstream recodings may already give distinct IDs to expanded slots.
“Observed” describes the accepted source records, not certified independent
elicitation events. Reusing
one source questionnaire slot or multiplying one native record into multiple
catalog slots does not create an independently observed meaning pair. Different
sources, dialect tags, historical constructions and representation bases are
not stitched together to fabricate a match.

Unicode NFC and whitespace are normalized. Case, diacritics, tone, quantity,
word/morpheme boundaries and other retained distinctions are not stripped.
There is no ASCII folding, fuzzy string matching, cognate-based matching or
WordNet-based propagation.

### Representation and source fidelity

Three networks remain separate:

| Layer | Evidence | Interpretation |
| --- | --- | --- |
| `segmented` | Supplied IPA when available; source citations retaining explicit IPA stress; otherwise labelled supplied/profile normalized segments | Identity as represented, with its original reading basis |
| `written` | Exact case-sensitive stored `Form`, excluding known ASJP-derived sources | Citation identity, not independent phonetic equivalence; `Form` may contain source spelling or a normalized citation |
| `reduced` | Known ASJP/GLED-derived segment sequences | Diagnostic only; absent contrasts cannot be restored |

The comparison basis is part of the source scope and is retained in witnesses
and comparison coverage. A supplied-IPA record is not compared against a
normalized-segment record as though their notation were interchangeable.
Original notation and the accepted segment sequence must both match, so a raw
reading cannot override a correction in the accepted construction. Witness CSV
identity keys for these bases are JSON pairs of original notation and accepted
segments. This also prevents treating a mismatched basis as negative evidence.

Arca's upstream phonological normalizer can strip stress. Consequently the
pipeline prefers retained `raw_ipa` for source readings, or an explicitly stressed
source citation, over a stress-stripped aggregate sequence. Other fallback
segments remain labelled `normalized_segments`; they cannot recover prosodic or
other information already absent upstream. Profiles remain inferred readings.
Neither a valid token sequence nor equality establishes a complete phonetic or
phonemic analysis. Exact comparison is conservative and may miss genuine
identity expressed with different source conventions.

Unmapped and merged concepts, doubtful entries, analytical reconstructions,
missing provenance and unusable/oversized identities are excluded with reason
counts. Citation strings containing unresolved alternative/comment separators
are not split heuristically. Original lexical records remain unchanged.

### Underspecified concepts

The guarded registry
[`expansions.csv`](../src/arcaverborum/data/colexification/expansions.csv)
initially covers six explicitly disjunctive slots: arm/hand, foot/leg,
blue/green, bark/skin, flesh/meat and path/road. Each source and target definition
is hash-bound. These produce **`inferred`** connections, retaining the original
broad concept and native record; the two target meanings are not claimed to have
been independently elicited. Default networks use **`observed`** connections.
The two kinds are never summed as independent confirmations.

Generic broader concepts and WordNet broader/narrower links are not expanded.
For example, a word elicited for BIRD does not automatically establish a
colexification of every species of bird.

### Source duplication, sampling and weights

One witness represents a source-scoped identity group for a concept pair, rather
than every Cartesian combination of duplicate source records. Representative
native records provide inspectable examples; coverage shards preserve native
form/parameter identities. Original entries remain available in the lexical data.

Edges report distinct accepted varieties, distinct **Glottolog language units**
(dialects collapse via `Language_ID`), and distinct known family lineages.
Known isolates have their own lineage; unknown classification does not become
one invented family or one invented language. Language stages can share a
Glottolog language unit while retaining separate variety/source evidence.
Shared-ID dictionary entries may encode genuine independently documented senses;
without a reviewed sense-level admission they remain conservative unknowns.
Source witnesses, varieties and families are different units, and none should be
interpreted as a set of statistically independent confirmations. Borrowing and
inherited semantic patterns remain possible; original loan flags are retained.

All supported edges remain available, including rare and regional patterns.
The optional three-family view follows the useful CLICS recurrence screen without
throwing away small-family or American evidence. Three families is not a proof
of polysemy, universality or statistical significance. No minimum questionnaire
size is applied at the dataset level: eligibility and coverage are counted from
actual usable records inside each source scope.

## Three-way comparison and denominators

For a requested concept pair and representation:

1. **`colexified`**: an eligible shared form is recorded.
2. **`no_shared_form_observed`**: both meanings have usable, separately identifiable
   records in one comparable scope, but no eligible shared form is observed there.
3. **`unknown`**: comparable evidence is unavailable.

At variety level, a positive observation takes precedence over a sampled
nonmatch from another source. Edge coverage denominators count comparable
varieties once; the reported fraction is positive varieties divided by comparable
varieties. It is a descriptive sample fraction, not a probability estimate or
proof of a language's lexical organization. A source with only one meaning does
not supply negative evidence.

Arca's accepted aggregate does not fully preserve questionnaire-level elicitation
inventories. Therefore `unknown` does **not** pretend to distinguish “not elicited”
from “elicited but unavailable”, and a sampled nonmatch is never labelled proof
that a language lacks a colexification. Coverage exports retain source scope and
native IDs so these distinctions can be refined with independently reviewed
questionnaire evidence.

The default concept status describes segmented data: observed connections,
usable records without observed connections, no usable records, or a merged
entry. Citation and reduced-representation views have their own counts.

## Resource bounds and failure behavior

The implementation uses Python's standard library and disk-backed SQLite;
there is no pandas dataframe, NetworkX object, full language-by-concept-pair
matrix or corpus-sized Python list.

* CSVs stream record by record. Individual fields are capped at 8 MiB; identity
  and provenance strings have separate smaller limits.
* SQLite uses a 24 MiB page cache, file-backed temporary storage, disabled mmap,
  one database worker and bounded transaction batches. Scratch is outside `/tmp`
  by default, beneath the output build directory.
* The CLI sets a hard Unix address-space limit (384 MiB by default). The full
  corpus is additionally verified under 256 MiB. This bounds the analytical
  process, not unrelated programs or the pre-existing lexical web builder.
* A source-scoped identity covering more than 64 concepts is quarantined whole.
  It is not truncated into an apparently complete network. Such records do not
  supply usable comparison coverage when they are the only evidence.
* At most five native form/parameter representatives per concept preserve the
  existence of a valid witness. This avoids quadratic joins over thousands of
  duplicated readings; the representative property is exhaustively tested over
  all nonempty subsets of a small identifier space.
* Only observed edges receive coverage denominators. Arbitrary pairs are queried
  on demand. No dense all-pairs table is materialized.
* A 5,000,000-witness budget and 3 GiB database ceiling fail closed. Free scratch
  space is checked during input. SQL temporary files additionally require disk
  headroom; a database page budget is not a quota on every temporary file.
* Complete witnesses and coverage stream into deterministic gzip CSV shards of
  at most 50,000 rows, with a 90 MiB public-file limit. No complete evidence CSV
  is read into the browser.
* Every concept has a small metadata file. Adjacency pages contain at most 40
  connections and are capped at 1 MiB; the node index is capped at 4 MiB. The
  browser enforces declared sizes and SHA-256, retains only eight cached JSON
  assets plus the node index. Graphs contain at most 31 nodes and 465 edges.
  Each concept’s 12 views share a checksummed sidecar capped at 1 MiB; its index
  is capped at 4 MiB.

A budget is a fail-closed bound, not a promise that arbitrary input fits any
chosen machine. Invalid input, resource exhaustion or drift must not replace
previous published assets. Builds finish in a temporary directory and become
cacheable only after completion, input rechecks and SQLite integrity checking.
Cached assets are checked before reuse. Input/configuration/code/runtime hashes
identify immutable build directories; publishing verifies their contents and
switches the small web manifest last. Old immutable assets remain usable by
open browser sessions. Interrupted private builds can be retried safely.

The initial corpus benchmark also holds TLS Mbunga `ku`: one segmented identity
covering 154 concepts and one citation identity covering 151. This is an outlier
requiring source/morphological review, not automatically evidence of 154-way
lexical polysemy. No original forms are deleted.

## Running and reproducing the pipeline

Use the existing environment and accepted aggregate:

```sh
.venv/bin/python scripts/build_colexification.py --memory-mb 256 --publish
```

This adds only derived assets and the web-manifest pointer; it does not rebuild
lexical shards or load the explorer catalog into Python memory. Builds are stored
under `output/colexification/<build-id>/`, with `index.sqlite`, `public/`,
`complete.json` and timing information. Source hashes bind aggregate forms,
varieties, parameters, metadata, the frozen concept catalog, Glottolog when
available, construction kinds, policy, expansion rules, pipeline code and runtime.

The ordinary default `scripts/build_research_web.py` command refreshes
colexification automatically after the lexical stage, replacing its process so
that the lexical builder's larger working set is released first. Custom lexical
output directories and `--without-colexification` omit this automatic stage;
those exports explicitly lack a current network until separately integrated.
Never carry an old network pointer across a changed lexical snapshot.

For a requested pair, use its exact frozen concept IDs and the printed build path:

```sh
.venv/bin/python scripts/build_colexification.py \
  --database output/colexification/BUILD_ID/index.sqlite \
  --pair agr-tree phy-wood --layer segmented
```

The command emits three-way status for each accepted variety, with the build ID.
The database's `meta` table retains the full manifest. Edge CSV, witness shards,
coverage shards, source citations/licenses, quarantines, and node/page JSON are
hash-indexed in the public colexification manifest. The witnesses retain native
record IDs, source members, pronunciation scopes, reading basis, loan flags,
bibliography keys, original broad concepts, licenses and source versions.

For testing:

```sh
.venv/bin/pytest -q tests/test_colexification.py tests/test_research_web.py
node --check web/colexification.js
```

Browser checks cover independent concept loading, representation/inference
switches, source examples, family thresholds, missing/merged concepts, bounded
neighborhoods, mobile layout, navigation and corrupt-asset rejection.

## Scope and further work

No claim is made that all source meanings have been mapped, all identical
citations are lexicalized units, or every unknown entry represents an elicitation
gap. Source/semantic review can improve the evidence without rewriting the
analytical method. Partial colexification, global community inference and
questionnaire-level missingness need separate validated layers; they are not
simulated with substring search, generic category expansion or absent-edge zeros.

## Accepted build and verification, 2026-10-30

[Verification](colexification_verification_2026-10-30.json) records the complete
2,119,754-record build under a 256 MiB address-space limit, with **107.48 MiB peak
RSS** and a 555.57-second analytical build. The input lexical data and WordNet
layer are unchanged. All 12,496 public network assets are hash-checked; 8,592
adjacency pages cover all 3,828 catalog concepts. The largest page is 47,563 bytes.

The default segmented network has **44,856 observed concept-pair edges** and
2,974 connected concepts. Citation identity has 44,025 edges; reduced ASJP/GLED
identity has 508. Six broad-concept pairs are separately inferred in each eligible
representation. These overlapping networks must not be summed as distinct
linguistic patterns. Complete exports contain 264,835 witness groups and
3,250,905 comparison-coverage records.

540 tests pass, including 21 colexification tests. Two independent fixture builds
produce byte-identical public files. A 20,000-reading duplicate-identity case
finishes under a 128 MiB process limit. Local colexification, WordNet and general
research browser suites pass, including URL-state restoration, missingness, mobile
layout and deliberate checksum corruption. Browser views do not require loading
a lexical family. Selection manifests carry the colexification build pointer;
the network manifest pins the exact inputs and asset hashes.

[Publication proof](colexification_publication_2026-10-30.json): data commit
`10ac9133` is pushed; CI and Pages succeed. All **12,912** checked canonical assets
on https://arcaverborum.org/ match their local hashes, including all 12,496
colexification files. Colexification, WordNet and general research browser suites
pass on the live site. [Example: hand](https://arcaverborum.org/#concept:bod-hand).

## Interconnected concept subgraphs, 2026-10-31

The earlier drawing showed only focal spokes. The viewer now displays an induced
subgraph: the focal concept’s strongest 30 direct neighbors, ranked by family,
language and variety support, plus **all actual edges among those concepts**.
Representation, observed/inferred status and the three-family threshold apply to
neighbor links as well as focal links. No transitive or similarity edges are
added. A genuinely star-shaped sample can still appear as a star. This is a
bounded local view, not a global community assignment or an Infomap partition.

A deterministic force layout supports node dragging, background panning and
zoom. Focal links and neighbor links have different colors; widths show known
family support. Edge tooltips and selection show endpoint names and weights.
Concept links open their evidence and neighborhood. Table pagination does not
change the selected graph.

The normal publication pipeline exports these sidecars automatically. To refresh
only the graph view from an existing accepted analytical database:

```sh
.venv/bin/python scripts/build_colexification_graphs.py --memory-mb 256 --publish
```

[Verification](colexification_subgraphs_verification_2026-10-31.json): 3,828
concept files contain 45,936 bounded views; 6,918 have links among neighbors.
HAND has 31 nodes and 178 recorded segmented links, including 148 neighbor links.
The export peaked at 44.02 MiB RSS under a 256 MiB address-space limit. All graph
edges and weights match the frozen SQLite network; lexical data, WordNet and
analytical colexification counts are unchanged. 544 tests and local colexification,
WordNet and general research browser checks pass.

[Subgraph publication proof](colexification_subgraphs_publication_2026-10-31.json): commit `a92a5495` deployed; CI and Pages passed. All 3,834 checked canonical assets match, and all three live browser suites pass.
