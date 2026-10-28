# Current project state

Updated 2026-10-28. This is the current-state entry point. Update it at the close
of each data batch; dated reports retain their original before/after observations.
The active work queue is [NEXT.md](NEXT.md); planning procedure is
[coverage-planning](workflows/arca-coverage-planning/SKILL.md).

## Accepted baseline

Data commit: `b2ba04ca7b8082fb6576bfb95383b96541b39b5d`.
Authoritative batch counts: [depth summary](south_america_depth_summary_2026-10-28.json),
`after` object. Publication artifacts: [manifest](../web/data/manifest.json) and
compressed `web/data/catalog.json.gz`.

| Measure | Accepted value |
| --- | ---: |
| Varieties | 7,314 |
| Forms | 2,067,553 |
| Supplied-source forms | 1,743,820 |
| Profile-derived forms | 13,648 |
| Supported core-concept slots | 465,902 |
| Mapped core-concept slots | 539,995 |
| GLED primary selections | 1,578 |
| Core-source collection varieties | 901 |
| Frozen concepts / core concepts | 3,787 / 161 |

Supported slots are distinct variety–concept pairs with `source` or `profile`
evidence. Mapped slots can include unresolved transcription. Core-source is a
row-level source collection; the 161-concept vocabulary filter is independent.

Latest data batch: [South American depth](SOUTH_AMERICA_DEPTH_2026-10-28.md),
+399 forms / +312 supported core slots across nine existing constructions.
Panará and Apinayé replaced GLED as primary while retaining earlier records.
The new-language screen made zero admissions and recorded six explicit holds.
Ingain and Bangru were genuinely new language admissions in preceding batches.
Asturian remains 82 supported core concepts.

Verification for this data baseline: 416 tests; core-pilot and Vakh audits;
all 7,314 accepted outputs fresh; 1,396 earlier affected records preserved;
400 artifact hashes checked; local and live browser checks passed.
[CI](https://github.com/tresoldi/arcaverborum/actions/runs/40659628109) and
[Pages deployment](https://github.com/tresoldi/arcaverborum/actions/runs/40659628167)
succeeded. The public manifest matched the committed artifacts.
These checks describe the recorded data commit; verify subsequent changes separately.

## Evidence for planning

* [Latest opportunity CSV](south_america_depth_opportunities_2026-10-28.csv) and
  [method/counts](south_america_depth_opportunities_2026-10-28.json): 6,818 member
  opportunities, including 615 South American. Counts overlap and remain unreviewed.
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

Current Jê namespace: 371 admitted forms / five members, 549 reviewed candidates
(178 held). Its expansion preserved the earlier 251 source rows. Intake database:
7,181,760 rows. The historical `--expected-old-forms 251` migration is already
complete; later expansions must guard the actual current source count.

Use [ONBOARDING.md](../ONBOARDING.md) for commands and environment details.
