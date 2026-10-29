# Current project state

Planning: [worldwide follow-up WF01–WF10](WORLDWIDE_FOLLOWUP_2026-10-29.md) is proposed; no new lexical batch authorized.

Updated2026-10-29. Latest accepted batch:
[Worldwide GW01–GW10](WORLDWIDE_EXPANSION_2026-10-29.md), all ten authorized tracks
completed sequentially with admissions, corrections or evidence holds.
[Realized metrics](worldwide_expansion_summary_2026-10-29.json) are authoritative.
Previous African data baseline:`f1e6f1a9bddf09c6fa1c524f39252eaf328eff18`.

## Accepted baseline

| Measure | Accepted value |
| --- | ---: |
| Varieties | 7,336 |
| Forms | 2,071,137 |
| Supplied-source forms | 1,746,959 |
| Profile-derived forms | 14,506 |
| Supported core slots | 469,063 |
| Mapped core slots | 542,891 |
| Supported all-concept slots | 1,207,446 |
| Mapped all-concept slots | 1,334,838 |
| GLED primaries | 1,573 |
| Core-source varieties | 912 |

Frozen vocabulary3,787 concepts/161 core. Added657 records (459 supplied/source
conversions,116 finite profiles,82 written), +532 net supported slots including482
core. Corrected3 earlier slot overcounts;83 earlier row mappings change. Broome
Pearling Lugger Pidgin is one new language,11 written records; Travo/Lugo/Ascrea are
three new named samples,13 infinitives, not new languages. Ten previously held
Bribri original IPA readings recovered as new records; no earlier reading changed.
All787 Elamite readings now carry original dictionary/period/uncertainty context.

Core-source is a row-level source preset, independent of the161-concept vocabulary.
Source status is not independent phonetic elicitation: upstream conversions remain
disclosed; finite profiles are derived, and written-only evidence adds no phonetic
support. GLED1573 unchanged: no forced primary promotion from an incomplete slice.
Earlier quality scores are unchanged and are not linguistic certification.

## Verification and publication

449 tests/full lint pass. All7,336 accepted builds pass, zero failures.
All2,070,480 earlier lexical records, readings, source cognacy and original comments/
JSON evidence preserved with exactly83 reviewed semantic changes. 401 website
hashes and3 aggregate-input hashes match. All19,768 new original dictionary rows,
726 African-original rows,46 RVID and36 Coptic rows reproduce. 78 source resources
and23 BHSA feature hashes verified;15 original lemma/verse/language witnesses.
All five local research/worldwide/African/ancient/mixed-source browser suites pass.
Lexical data commit: `b115e6806783f0b9e5d94df71ef232e2ac586814`.
[CI](https://github.com/tresoldi/arcaverborum/actions/runs/40867211283) passes Python3.12/3.13;
[Pages](https://github.com/tresoldi/arcaverborum/actions/runs/40867211550) succeeds.
Canonical live manifest, catalog, bibliography, recordings and17 worldwide family
shards match committed bytes. Updated worldwide live browser/export checks pass.
Subsequent documentation-only closure keeps these lexical artifact hashes unchanged.

The site publishes tracked catalog,399 family shards, bibliography and755 recording
metadata rows. Pages publishes tracked artifacts; it does not rebuild lexical data.

## Evidence, source state and next work

[Execution and decisions](WORLDWIDE_EXPANSION_2026-10-29.md),
[immutable pins](worldwide_execution_sources_2026-10-29.json),
[post-batch selected members](worldwide_postbatch_selected_members_2026-10-29.csv) and
[method/counts](worldwide_postbatch_opportunities_2026-10-29.json) support planning.
[NEXT](NEXT.md) closes GW01–GW10; [HELD](planning/HELD.md) defines exact reopening
evidence. Americas/South America and Etruscan/Elamite remain standing priorities.

Intake7,212,459 rows. Four original dictionary namespaces total19,768 rows, appended
once. Existing-source expansions are complete: African originals111/142/192/50/88/
45/45/53 (726 total); RVID46, Coptic36. Do not replay old namespace appends or old
expected-count migrations; never subset-ingest over active tables. RVID's title-only
metadata migration is recorded separately. Jê463 and its older251/371 migrations
remain unchanged. See the report for full source-specific safeguards.

Configs, guarded ledgers/profiles, registries, packets and recipes remain the source
of truth. Generated intake/aggregates are local products. Use [ONBOARDING](../ONBOARDING.md),
[coverage workflow](workflows/arca-coverage-planning/SKILL.md), [journal](JOURNAL.md)
and [history](history/README.md) for continuation.
