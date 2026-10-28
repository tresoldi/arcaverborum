# Current project state

Updated 2026-10-28. Current baseline and handoff; dated reports preserve their
original observations. Active proposals are in [NEXT](NEXT.md), with evidence
requirements in [HELD](planning/HELD.md).

Latest batch: [Sub-Saharan Africa/Bantu AF01–AF09](AFRICA_EXPANSION_2026-10-28.md).
All nine authorized tracks received bounded admissions or explicit evidence holds.
Data commit: publication commit containing this batch's manifest; exact SHA and
live verification will be recorded after deployment.
Authoritative counts: [realized metrics](africa_expansion_summary_2026-10-28.json).

## Accepted baseline

| Measure | Accepted value |
| --- | ---: |
| Varieties | 7,331 |
| Forms | 2,070,117 |
| Supplied-source forms | 1,746,470 |
| Profile-derived forms | 14,106 |
| Supported core-concept slots | 468,501 |
| Mapped core-concept slots | 542,429 |
| GLED primary selections | 1,575 |
| Core-source collection varieties | 906 |
| Frozen concepts / core concepts | 3,787 / 161 |

619 new records:280 supplied readings,221 profile readings and118 explicitly
written-only entries. Gains464 supported and555 mapped core slots. Two new
canonical languages, Konyagi/Wamey and Kam, have20/30 written entries respectively;
no phonetic coverage is claimed for them. Zero new named sample/dialect varieties.
Gyeli and Hdi original dictionaries replace two GLED primaries, retaining all68
previous GLED rows and their cognacy. Fwe remains GLED-primary pending a larger
supported dictionary slice. Ruruuli and Sidaama additions remain written-only.

Narrow Bantu ancestry scope remains485 constructions:150,276 forms and35,084
supported core slots, gains403 forms/352 slots. GLED primaries97→96;23 zero-core
cases remain. Ngoni's blank Macroarea remains an explicit metadata hold; do not
replace ancestry-based scope with a geography-only filter.

Supported slots are distinct variety–concept pairs with source/profile evidence.
Source labels describe segment origin:302 Bantu upstream Grollemund/TLS
conversions now disclose their profile genealogy; they are not independent
phonetic elicitation. Historical source readings likewise require their reading
basis and period qualifiers. Written-only entries have blank segments and add
zero supported phonetic slots. Core-source is a row-level collection independent
of the161-concept vocabulary filter. Mechanical quality scores are not linguistic
certification; guarded concept mappings recomputed scores on68 retained GLED rows.

## Verification and publication

440 tests and full lint pass. All7,331 accepted constructions rebuilt, zero
failures; aggregate, curation report and web artifacts regenerated. All2,069,498
earlier lexical rows and original comments preserved, including multiplicity;
aggregate IDs, additive review metadata and derived scores may change.
401 website artifact hashes and three aggregate-input hashes verified.
All329 original-source intake records reproduce from immutable source bytes.
Generic research, African, ancient and mixed-source browser/export checks pass.
CI, Pages and canonical live verification are pending the publication push.

Publication artifacts: [manifest](../web/data/manifest.json), compressed catalog,
399 family shards, bibliography and755 recording-metadata rows. The site deploys
tracked artifacts; Pages does not rebuild lexical data.

## Evidence for planning

* [Completed execution and boundaries](AFRICA_EXPANSION_2026-10-28.md),
  [source pins](africa_execution_sources_2026-10-28.json), authored AF01–AF09 reviews
  and the [lexical registry](../src/arcaverborum/data/african_lexical_sources.json).
* [Fresh African member opportunities](africa_postbatch_opportunities_2026-10-28.csv)
  and [method/counts](africa_postbatch_opportunities_2026-10-28.json):579 overlapping
  member opportunities, not admissions. The
  [post-batch GLED screen](africa_postbatch_gled_2026-10-28.csv) has432 alternatives,
  zero lossless positive supplied-reading replacements. Existing profiles and
  original-source acquisition need separate review.
* [Original investigation](SUBSAHARAN_AFRICA_INVESTIGATION_2026-10-28.md),
  [historical485-construction scope](africa_baseline_2026-10-28.csv) and
  [RefLex source identities](africa_reflex_source_screen_2026-10-28.csv).
  RefLex's actual932,836 archived records differ from the live-site927,845
  description; raw source records are not accepted gains. Konyagi and Kam are
  now admitted; other missing-language candidates remain provisional.
* [Prior ancient baseline](ANCIENT_EXPANSION_2026-10-28.md), data commit
  `5d0981260945f7d90b827f8ade7ac9d603ca1f6d`, and
  [earlier Romance](ROMANCE_EXPANSION_2026-10-28.md) and
  [American](NORTH_AMERICA_EXPANSION_2026-10-28.md) results remain historical evidence.
* [Journal](JOURNAL.md), [history](history/README.md) and [held register](planning/HELD.md).

Americas/South America and Etruscan/Elamite remain standing priorities. Parked
ancient, Romance and American proposals are retained in NEXT. The AX follow-ups
are recommendations after this completed batch, not newly authorized work.

## Build state

Source of truth: configs, guarded custom ledgers/profiles, source registries,
packets and recipes. Generated intake/aggregate files remain local products.
Intake now has7,192,262 rows. The seven African namespaces contain329 records and
have been appended once; future expansion must use a complete staged guarded
migration, never subset-ingest or repeat that append. Jê remains463 admitted forms
across five members; its historical251/371 migrations are complete.

Use [ONBOARDING](../ONBOARDING.md) for commands and environment details, and
[guarded primary/recording formats](GUARDED_PRIMARY_AND_RECORDINGS.md) for bounded
source selections. The [coverage-planning workflow](workflows/arca-coverage-planning/SKILL.md)
connects accepted evidence to the next proposal.
