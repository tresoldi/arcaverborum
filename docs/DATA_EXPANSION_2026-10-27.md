# Coverage and source-quality batch, 2026-10-27

The rebuilt collection contains **7,312 varieties and 2,062,473 forms**
(+2 varieties, +13,820 forms), with **1,087 additional supported core-concept
slots**. Source-supplied segment coverage increases by 35,904 forms. The final
accepted selections contain 35,454 recovered Wiktionary IPA forms across 100
varieties, including the newly activated Asturian selection. Core collection
membership remains 892 varieties. See `data_expansion_summary_2026-10-27.json`.

Five tracks were completed in sequence. Raw source snapshots remain unchanged;
corrections and construction decisions are explicit and reproducible.

## 1. Recover supplied Wiktionary pronunciation

The frozen Wiktextract dump contains 10,806,865 entries (2,826,672,112 compressed
bytes; SHA256 `a6a32d41e35990b79a886d9082ebb3459a16fbaed6d2995aaedf6ef46d3ee643`).
The new pronunciation index requires exact language, NFC spelling and POS.
Every matching entry must supply the same unqualified raw IPA. Conflicting
homographs, dialect labels, alternative/optional readings and unsupported
multiword analyses are withheld. Stress is retained in the raw evidence but
removed from canonical Arca segments; the canonical phonology layer is not a
prosodic transcription.

545,383 intake alternatives gained supplied IPA; existing lexical forms, IDs,
senses and cognacy were preserved. Of those, 35,288 forms reach the existing
accepted selections across 99 varieties, with a net 769 additional supported
core-concept slots before shared semantic corrections. Intake-wide gains must
not be confused with accepted output. See the `wiktionary_ipa_*_2026-10-27`
reports. Original IPA, entry URL, dump hash and matched entry lines survive in
comments and the intake pronunciation ledger. Normal Wiktionary ingestion uses
the reviewed index only while its snapshot and policy still match.

Reproduce with `scripts/enrich_wiktionary_ipa.py --index --apply`; after a policy
change use `--refresh-decisions --apply`. The SQLite index and raw evidence are
local regenerable intake, not additional authored source data.

## 2. Replace GLED where the evidence supports it

Asturian now selects the exact Wiktionary `wikt_ast` member, using source IPA
first and an exact-word conservative profile based on the Academia de la
Llingua Asturiana grammar. Supported core coverage rises from **37 to 92/161**.
Of 9,715 retained forms, 166 have source IPA, 3,548 use the reviewed profile,
and 6,001 remain unresolved. The catalog's frozen Asturian–Leonese–Cantabrian
identifier contains a named Asturian sample; no other varieties are pooled.

The profile excludes ambiguous x/y, foreign letters, dialect signs, adjacent
vowels and insufficiently specified rhotics. It specifies broad phonemes,
without stress or surface allophones. English-sense review is separate from
native lexical accuracy. No GLED cognate IDs were transferred. See its
`PACKET.md`, profile evidence and 203 core-sense decisions (42 corrections).

The refreshed GLED replacement ranking is in
`gled_ipa_candidates_2026-10-27.csv`. The other screened candidates do not yet
beat their existing clean core coverage with supplied IPA alone. They remain
unchanged pending defensible native profiles or richer lexical sources.

## 3. Add scholarly coverage

Three source repositories were staged and appended (1,831 forms). Two previously
unrepresented accepted languages have been admitted with named-member filters:

| Accepted construction | Source | Forms | Supported core |
| --- | --- | ---: | ---: |
| Asuri | Khalid 2020 / `khalidasur_Asuri` | 200 | 122/161 |
| Eastern Newari (Dolakha) | Liu et al. / `liunewari_DolakhaNewari` | 178 | 105/161 |
| Proto-Hmong-Mien (upgrade) | Wang / `wanghmongmien_ProtoHmongMien` | 118 | 30/161 |

All these forms have validated supplied segments. Proto-Hmong-Mien replaces
107 unresolved ABVD forms and is explicitly a reconstruction, not an additional
living language. Dolakha's source dialect code belongs to Eastern Newari in the
cached classification; it is not Kathmandu Newari. Old and Classical Newari
remain deferred for identity/chronology review. Other Wang samples were screened
but do not displace their current constructions. Repository commits and all 17
member decisions are in `scholarly_batch_2026-10-27.csv`; each accepted variety
has a source/identity packet. Core release membership is unchanged.

## 4. Reuse independently reviewed semantic corrections

Thirty guarded rules reconcile English senses with the frozen concept catalog,
affecting 3,364 Wiktionary intake rows. Each requires agreement from at least
two independent language review ledgers, including an explicit correction,
without conflicting or unresolved reviews. Source parameter names and original
Concepticon IDs must still match. Rules live in
`src/arcaverborum/data/wiktionary_sense_overrides.csv`; the raw mapping remains
intact. Local authored decisions take precedence. The explorer exposes the
shared decision and its evidence languages alongside source glosses.

The seven pilot audits pass after explicit reviews of newly core senses.
These are semantic mapping checks, not native-speaker certification.

## 5. Promote the reviewed ABVD snapshot

ABVD source commit `81748db0c5fcf3bf1d8c8372b86df75c375e1f22` is appended under
versioned namespace `abvd2026` (349,424 forms). The previous `abvd` intake is
retained. All **477 current ABVD transcription constructions** pass explicit
canonical identity, authored-overlay, mapped-concept and supplied-segment
retention gates and are pinned to reviewed member lists. Quality scores are
recomputed from the new blocks. Cognate sets retain the new namespace; old
judgments are not grafted onto changed forms.

The earlier refresh audit exposed 42 accepted member changes: 32 now have
promoted transcription selections; ten use other current transcription sources
and remain unchanged. See `abvd_identity_review_2026-10-27.csv`. The complete
477-construction ledger is `abvd_promotion_2026-10-27.csv`.

Bungku and Tolaki include explicitly enumerated dialect samples belonging to
the same canonical languages. Squliq excludes the separately classified S’uli
member and adds the correctly relabeled Squliq lists: core coverage **96 → 133**.
Across these 477 selections, source forms increase from 133,207 to 136,969 and mapped core-concept slots from 54,276 to 54,506. No new dialect varieties were created just to raise language counts.

The compact ingest now preserves contribution IDs/URLs, cognacy qualifications
and raw loan notes in form comments. Where the refresh supplies no individual
bibliographic reference, the genuine dataset citation is explicitly labeled
as dataset-level only. It must not be read as an individual lexical citation.
The source contribution table remains available in the cached upstream CLDF.
Raw ABVD cognacy labels (for example `1,64`) are retained as within-concept
notes. Only the structured CognateTable's meaning-scoped IDs (for example
`hand-1;hand-64`) define accepted memberships. This corrects 252,040 intake
rows that otherwise acquired additional raw-label sets, preventing spurious
cross-meaning connections without dropping the structured judgments.

Citation collection now resolves CLDF page locators to their base bibliography
keys, while preserving the complete reference on each lexical record. Additional
intake namespaces contribute their own bibliography and metadata to aggregation.
Wiktionary exports now include a dataset citation and the exact local snapshot
hash; its unrecorded original dump date and snapshot-specific license remain
explicitly unrecorded. The legacy citation key's year is not treated as an
independently verified dump date.

After staging/ingesting the versioned snapshot, run
`python scripts/promote_abvd_snapshot.py --apply`. Repeated runs preserve the
same membership ledger and do not append duplicate selection decisions.

## Validation and publication

Rebuild all accepted varieties (those with existing generated output), then
`python build.py aggregate`, `python scripts/build_research_web.py`, and the
pilot audits. All 336 tests pass. The test suite includes citation-locator resolution, secondary-intake metadata, exact pronunciation matching, source
identity retention, shared-rule snapshot guards/local precedence, reviewed
member unions with stable intake order, missing-member rejection, union-aware
fingerprints, contribution provenance, and raw-label versus structured-cognate scoping. Full lint and browser workflows pass, including unique-source-ID resolution for older form links after coverage additions shift row numbers.
