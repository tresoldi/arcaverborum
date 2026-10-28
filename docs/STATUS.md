# Current project state

Updated 2026-10-28. This is the current-state entry point. Update it at the close
of each data batch; dated reports retain their original before/after observations.
The active work queue is [NEXT.md](NEXT.md); planning procedure is
[coverage-planning](workflows/arca-coverage-planning/SKILL.md).

## Accepted baseline

Data commit: `9b1a16c282e8dddc6f52d2a8e325d663505169d1`.
Authoritative batch counts: [source-led summary](source_led_summary_2026-10-28.json),
`after` object. Publication artifacts: [manifest](../web/data/manifest.json) and
compressed `web/data/catalog.json.gz`.

| Measure | Accepted value |
| --- | ---: |
| Varieties | 7,314 |
| Forms | 2,067,822 |
| Supplied-source forms | 1,743,997 |
| Profile-derived forms | 13,740 |
| Supported core-concept slots | 466,066 |
| Mapped core-concept slots | 540,159 |
| GLED primary selections | 1,578 |
| Core-source collection varieties | 904 |
| Frozen concepts / core concepts | 3,787 / 161 |

Supported slots are distinct variety–concept pairs with `source` or `profile`
evidence. Mapped slots can include unresolved transcription. Core-source is a
row-level source collection; the 161-concept vocabulary filter is independent.

Latest data batch: [Source-led N01–N05](SOURCE_LED_EXPANSION_2026-10-28.md),
+269 forms/+164 supported core slots across seven existing constructions.
177 supplied-source and92 profile-derived additions. Panará/Apinayé gain broader
non-core vocabulary; primary selections stay unchanged. Lule transcription and
Apolista original-source acquisition remain held, with zero new-language admissions.
Ingain and Bangru were genuine new language admissions in preceding batches.
Asturian remains82 supported core concepts.

Verification:417 tests; core-pilot and Vakh audits; all7,314 accepted outputs fresh;
1,359 earlier affected records preserved;549 earlier Jê review rows unchanged;
371 earlier Jê source rows preserved;400 artifact hashes checked. Local research and mixed-source browser/export checks passed.
[CI](https://github.com/tresoldi/arcaverborum/actions/runs/40670038699) and
[Pages](https://github.com/tresoldi/arcaverborum/actions/runs/40670038798) succeeded.
The public manifest matches all committed counts and artifact hashes exactly.
Live research and mixed-source browser/export checks passed. The research
keyboard-focus check now waits for the catalog to render after navigation.

## Evidence for planning

Current regional focus: Central/North America, requested2026-10-28.
[Investigation](NORTH_AMERICA_INVESTIGATION_2026-10-28.md) and
[regional summary](north_america_planning_summary_2026-10-28.json):610 accepted
varieties/95,555 forms/33,038 supported core slots;255 GLED primaries.
306 additive alternatives and221 GLED alternatives screened; none of the latter
is net-positive on supplied segments alone. NA01–NA07 in NEXT are proposed.
This planning update makes **zero accepted-data changes**; no web-data rebuild.


* [Latest opportunity CSV](source_led_opportunities_2026-10-28.csv) and
  [method/counts](source_led_opportunities_2026-10-28.json): 6,814 member
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
7,181,852 rows. The historical251/371-row migrations are complete; any later
expansion must guard the actual current source count463.

Use [ONBOARDING.md](../ONBOARDING.md) for commands and environment details.
