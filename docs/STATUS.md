# Current project state

Updated 2026-10-28. This is the current-state entry point. Update it at the close
of each data batch; dated reports retain their original before/after observations.
The active work queue is [NEXT.md](NEXT.md); planning procedure is
[coverage-planning](workflows/arca-coverage-planning/SKILL.md).

Latest batch: [ancient languages AN01–AN09](ANCIENT_EXPANSION_2026-10-28.md).
All nine tracks received reviewed admissions or documented evidence holds.
Etruscan and Elamite are explicit standing priorities. Earlier Romance RP and
American NB/P proposals remain parked; NEXT now carries proposed AE follow-ups.

## Accepted baseline

Data commit: this ancient-batch commit; immutable hash recorded after publication.
Authoritative counts: [ancient summary](ancient_expansion_summary_2026-10-28.json),
`after` object. Publication artifacts: [manifest](../web/data/manifest.json) and
compressed `web/data/catalog.json.gz`.

| Measure | Accepted value |
| --- | ---: |
| Varieties | 7,329 |
| Forms | 2,069,498 |
| Supplied-source forms | 1,746,190 |
| Profile-derived forms | 13,885 |
| Supported core-concept slots | 468,037 |
| Mapped core-concept slots | 541,874 |
| GLED primary selections | 1,577 |
| Core-source collection varieties | 906 |
| Frozen concepts / core concepts | 3,787 / 161 |

Supported slots are distinct variety–concept pairs with `source` or `profile`
evidence. Historical `source` identifies segment origin, not direct observation
of ancient pronunciation. Mapped slots can include unresolved/written-only
transcription. Core-source is a row-level collection, independent of161-core scope.

284 forms added in14 existing constructions:169 supplied historical readings and
115 explicitly written-only lexical rows. Gain165 supported core slots and237
mapped core slots. No new languages/named varieties, profile readings or GLED swaps.
Etruscan70→94 forms and14→19 mapped core (supported9 unchanged); Elamite787→790
forms (supported71 unchanged). Full787-record Elamite source-text audit and
historical reading-basis metadata for the58-construction shortlist accompany
these gains. Qualified Sanskrit43→141, Attic128→152, Latin128→142 supported core;
Latin filius maps to SON, not generic CHILD. Written-only rows add zero phonetic
support. Actual source terms remain attached.

Verification:436 tests and full lint pass. All7,329 accepted constructions rebuilt
with zero failures; aggregate, curation report and web artifacts rebuilt.
All2,069,214 earlier lexical rows preserved apart from additive comment metadata
(global aggregate IDs may shift). All401 website artifact hashes and three
aggregate-input hashes verified. Local generic, historical and mixed-source
browser/export checks cover scope, licenses, Etruscan/Elamite orthography,
conversion disclosure, exact Attic note and Mayan sign/context. Four pinned
original lexical slices reproduced outside intake. CI/Pages/live checks pending
publication; no freshness claim based solely on a deployment run.

Previous data baseline:`6009c09e58021f203beb920677418d9f7f51f805`,
[Romance report](ROMANCE_EXPANSION_2026-10-28.md). Its430-test CI and Pages
verification are recorded in that batch's journal/history; older baseline
`7de14ecd8710ad399189cd12405d1a4afc50fc54` and correction`74c4468c` belong to the
[American batch](NORTH_AMERICA_EXPANSION_2026-10-28.md).

## Evidence for planning

The [ancient batch report](ANCIENT_EXPANSION_2026-10-28.md), authored review
CSVs and [realized metrics](ancient_expansion_summary_2026-10-28.json) supersede
its earlier58-construction and74-member planning ceilings. Follow-ups prioritize
Etruscan attestations and Elamite original dictionary/period evidence, then
Coptic/Egyptian expansion, BHSA linkage and Old Khmer/Mayan source pilots.
Acquisition/sense/reading holds have precise reopening evidence in HELD.

* [Original ancient investigation](ANCIENT_LANGUAGES_INVESTIGATION_2026-10-28.md)
  remains historical discovery evidence, not an unspent admission queue.
* [Romance decisions/results](ROMANCE_EXPANSION_2026-10-28.md) retain the earlier
  source/locality evidence. Fresh full opportunity ranking is generated locally
  under `output/report/coverage_opportunities.csv`; opportunities overlap and
  require source/member/sense review before admission.
* [Latest missing-language decisions](south_america_depth_missing_languages_2026-10-28.csv)
  and [four-source screen](south_america_depth_source_screen_2026-10-28.json).
* [Held-work register](planning/HELD.md): current blockers across earlier batches.
* [Journal](JOURNAL.md): chronological decisions and operational handoffs.
* [History index](history/README.md): completed reports and their evidence files.

The additive ranking excludes a construction's primary source and does not
model recovery through its existing profile. Use a separate GLED replacement
scan and inspect primary-source profile/dictionary opportunities explicitly.
A source language table without lexical rows establishes no coverage gain.

## Build and publication state

Accepted constructions live in `varieties/*/config.yaml` plus guarded `custom/*`;
packets and recipes document their rationale. Generated intake/aggregate files
are local products. The website publishes tracked `web/data/` artifacts from
the accepted aggregate; a successful Pages run does not regenerate lexical data.

Current Jê namespace:463 admitted forms/five members,657 reviewed candidates
(194 held). This expansion preserved all371 earlier source rows. Intake database:
7,191,883 rows. Two new dictionary namespaces contributed9,998 rows. The historical251/371-row migrations are complete; any later
expansion must guard the actual current source count463.

Use [ONBOARDING.md](../ONBOARDING.md) for commands and environment details.

[Guarded primary subsets and recording metadata](GUARDED_PRIMARY_AND_RECORDINGS.md)
explain bounded dictionary admission, exact unlinked-member selection and separate
recording exports. Current public recording metadata has755 rows.
