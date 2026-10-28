# Current project state

Updated 2026-10-28. This is the current-state entry point. Update it at the close
of each data batch; dated reports retain their original before/after observations.
The active work queue is [NEXT.md](NEXT.md); planning procedure is
[coverage-planning](workflows/arca-coverage-planning/SKILL.md).

Latest batch: [Romance R01–R06](ROMANCE_EXPANSION_2026-10-28.md), executed in order.
American NB proposals remain parked. Bounded admissions and evidence holds are
recorded separately; R01–R06 is no longer a proposed queue.

## Accepted baseline

Data commit: this Romance batch (publication commit recorded after push).
Authoritative counts: [Romance summary](romance_expansion_summary_2026-10-28.json),
`after` object. Publication artifacts: [manifest](../web/data/manifest.json) and
compressed `web/data/catalog.json.gz`.

| Measure | Accepted value |
| --- | ---: |
| Varieties | 7,329 |
| Forms | 2,069,214 |
| Supplied-source forms | 1,746,021 |
| Profile-derived forms | 13,885 |
| Supported core-concept slots | 467,872 |
| Mapped core-concept slots | 541,637 |
| GLED primary selections | 1,577 |
| Core-source collection varieties | 906 |
| Frozen concepts / core concepts | 3,787 / 161 |

Supported slots are distinct variety–concept pairs with `source` or `profile`
evidence. Mapped slots can include unresolved transcription. Core-source is a
row-level source collection; the 161-concept vocabulary filter is independent.

176 newly admitted source forms;16 profile readings on existing Gallurese rows;
138 new supported core slots in existing constructions. Four more slots in new
Cremona, plus1,287 in13 isolated Saenko samples, give1,429 total slot gain.
The1,639-row increase includes1,463 previously pooled Saenko rows exposed again
as named constructions. No distinct-new-language or independent-GLD-source claim.
All parents retained;14 new named constructions. No GLED replacement that would
lose supported evidence. RVID infinitive derivative retains GPLv3 terms and a
public notice; etyma are not inferred modern meanings or expert cognacy.

Verification:430 tests, full lint, affected builds and compilers pass. Aggregate
and web artifacts rebuilt;2,463 prior affected rows retained, with only reviewed
Gallurese reading/mapping changes. All401 artifact hashes and catalog totals
verified. Publication/browser outcomes are recorded at closure below.

Previous data baseline: `7de14ecd8710ad399189cd12405d1a4afc50fc54`, with build/test
correction `74c4468cebe183dd6df3a28a88f1b13c658119e8`; see the
[American report](NORTH_AMERICA_EXPANSION_2026-10-28.md) for that batch's checks.

## Evidence for planning

Current focus: Romance, especially Italian local varieties. R01–R06 bounded
batch complete. Remaining profiles/Alpine acquisition have explicit reopening
evidence in HELD. New prospective work is in NEXT; earlier American proposals
are parked, not completed.

* [Latest opportunity CSV](romance_expansion_opportunities_2026-10-28.csv) and
  [method/counts](romance_expansion_opportunities_2026-10-28.json): overlapping,
  unreviewed discovery counts. Blank-code named samples are not automatically
  matched to alternative sources.
* [Romance decisions/results](ROMANCE_EXPANSION_2026-10-28.md), including separate
  acquisition and locality audits.
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
