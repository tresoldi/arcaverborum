# Current project state

Updated 2026-10-28. This is the current-state entry point. Update it at the close
of each data batch; dated reports retain their original before/after observations.
The active work queue is [NEXT.md](NEXT.md); planning procedure is
[coverage-planning](workflows/arca-coverage-planning/SKILL.md).

## Accepted baseline

Data baseline: completed NA01–NA07 expansion; publication verification pending.
Prior data commit:`9b1a16c282e8dddc6f52d2a8e325d663505169d1`.
Authoritative batch counts: [regional expansion summary](north_america_expansion_summary_2026-10-28.json),
`after` object. Publication artifacts: [manifest](../web/data/manifest.json) and
compressed `web/data/catalog.json.gz`.

| Measure | Accepted value |
| --- | ---: |
| Varieties | 7,315 |
| Forms | 2,067,575 |
| Supplied-source forms | 1,744,382 |
| Profile-derived forms | 13,869 |
| Supported core-concept slots | 466,443 |
| Mapped core-concept slots | 540,270 |
| GLED primary selections | 1,577 |
| Core-source collection varieties | 906 |
| Frozen concepts / core concepts | 3,787 / 161 |

Supported slots are distinct variety–concept pairs with `source` or `profile`
evidence. Mapped slots can include unresolved transcription. Core-source is a
row-level source collection; the 161-concept vocabulary filter is independent.

Latest data batch: [Central/North America NA01–NA07](NORTH_AMERICA_EXPANSION_2026-10-28.md).
508 lexical forms added;755 recording placeholders retained separately; net−247
lexical forms.377 additional supported core slots, including126 in the new named
Nizaviguiti community variety. No distinct-new-language claim or guessed code.
Tseltal replaces GLED as primary with104 bounded profile forms, retaining all87
prior GLED records. Alutiiq gains six profile readings on existing forms.

Verification:424 tests; full7,315-output rebuild without failures;1,982 earlier
lexical and755 recording records preserved;401 artifact hashes verified;
core-pilot/Vakh and dictionary/profile compilers passed. Local research and
mixed-source browser/export checks passed, including guarded profiles,
Nizaviguiti and zero-form/recording-only pages. Publication checks follow the push.

## Evidence for planning

Current regional focus: Central/North America. Authorized batch complete;
NB01–NB04 in NEXT are proposed. The initial investigation retains its historical
baselines. Current regional totals:611 varieties/95,316 lexical forms/33,415 supported core
slots,254 GLED primaries and129 profile readings. Global data
counts above include the eight extra placeholders in a broader catalog node.

* [Latest opportunity CSV](north_america_expansion_opportunities_2026-10-28.csv) and
  [method/counts](north_america_expansion_opportunities_2026-10-28.json):6,811 member
  opportunities, including 611 South American. Counts overlap and remain unreviewed.
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
7,191,850 rows. Two new dictionary namespaces contributed9,998 rows. The historical251/371-row migrations are complete; any later
expansion must guard the actual current source count463.

Use [ONBOARDING.md](../ONBOARDING.md) for commands and environment details.

[Guarded primary subsets and recording metadata](GUARDED_PRIMARY_AND_RECORDINGS.md)
explain bounded dictionary admission, exact unlinked-member selection and separate
recording exports. Current public recording metadata has755 rows.
