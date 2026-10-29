# Current project state

Updated2026-10-29. Latest accepted batch:
[Worldwide follow-up WF01–WF12](WORLDWIDE_FOLLOWUP_EXECUTION_2026-10-29.md), all twelve
closed after the user added West Papua and Torricelli. [Metrics](worldwide_followup_summary_2026-10-29.json)
are authoritative. Baseline commit:`0ad3789e8ee2502d8dfc39349fe6051a8bfb8954` (preceding GW data:`b115e6806783f0b9e5d94df71ef232e2ac586814`).

## Accepted baseline

| Measure | Accepted value |
| --- | ---: |
| Varieties | 7,338 |
| Forms | 2,071,680 |
| Supplied/upstream-converted forms | 1,747,252 |
| Profile-derived forms | 14,686 |
| Supported core slots | 469,305 |
| Mapped core slots | 543,144 |
| Supported all-concept slots | 1,207,854 |
| Mapped all-concept slots | 1,335,284 |
| GLED primaries | 1,573 |
| Core-source varieties | 915 |

Frozen vocabulary3,787 concepts/161 core. Added543 records:293 supplied/source
conversions,180 finite profiles,70 written. +408 net supported slots:411 gross
minus3 earlier overcounts;242 core/166 non-core net. Corrected47 earlier mappings
through six exact source-sense rules. All2,071,137 earlier records/readings/cognacy
and original evidence retained.403 derived profile-digest annotations revalidated;
no earlier reading or mechanical quality score changed.

Two new named varieties: Sanzhi Dargwa20 profile readings and Biblical Aramaic
(BHSA corpus)5 written lexemes. Zero new distinct-language claims or GLED swaps.
West Papua61 records across six existing languages; Torricelli8 written records
across three. BHSA14 substantive lexemes in all, Coptic22 more Beta forms; no new
Etruscan/Elamite readings inferred. Three sail/drill POS-conflicting profiles held
before publication and excluded from the543 additions.

Core-source is a row-level collection preset, independent of the161-concept filter.
Upstream conversions are disclosed, finite profiles are derived, and written-only
records do not add phonetic support. Palula's43 dictionary readings cover22 core,
versus33 core in108 preserved GLED records; no promotion from that incomplete slice.

## Verification and publication

456 tests/full lint pass. All7,338 accepted builds pass, followed by three corrected
POS-affected builds. Preservation checks validate every earlier record and original
comment/evidence (only checked profile-artifact digests change),401 website hashes
and3 aggregate-input hashes.89 follow-up source-resource checks plus78 legacy GW
checks,23 BHSA feature pins; complete staged lexical/parameter/citation/terms
reproduction recorded in [proof](worldwide_followup_reproduction_2026-10-29.json).
Local browser workflows cover research/worldwide/African/ancient/Romance/mixed-source.
Lexical data commit:`05eeb0df5020eacd1e152640cfc5638f3e7b28ee`.
[CI](https://github.com/tresoldi/arcaverborum/actions/runs/40881329197) succeeds;
[Pages](https://github.com/tresoldi/arcaverborum/actions/runs/40881329126) succeeds.
Canonical live manifest/catalog/recordings/bibliography and23 family shards match
committed bytes (27 checked artifacts). Worldwide live browser/export checks pass.
This subsequent documentation-only closure preserves the verified lexical artifacts.

The site publishes tracked artifacts:399 family shards, source bibliography and755
recording metadata rows. Pages copies committed data; it does not rebuild lexica.

## Evidence, source state and next work

[Execution](WORLDWIDE_FOLLOWUP_EXECUTION_2026-10-29.md),
[pins](worldwide_followup_sources_2026-10-29.json),
[acquisitions](worldwide_followup_acquisitions_2026-10-29.json),
[remaining members](worldwide_followup_remaining_members_2026-10-29.csv),
[rank method/counts](worldwide_followup_opportunities_2026-10-29.json).
[NEXT](NEXT.md) closes all twelve and leaves unapproved proposals;
[HELD](planning/HELD.md) records exact reopening evidence. Americas/South America
and Etruscan/Elamite retain standing priority; added West Papua/Torricelli interest
is retained separately from genealogical classification.

Intake7,236,931 rows (+24,472). Five new full dictionaries total24,382 raw rows;
African-original namespaces total734 (Fwe147,Gyeli195,Ruruuli111 and the other
unchanged namespaces); RVID92,Coptic58,BHSA14 reproduce. New namespaces appended
once; existing expansions are complete. Never replay earlier142/192/36/46 expected
counts or overwrite active intake with a subset. Jê463 and older migrations unchanged.
Unknown frozen Wiktionary snapshot metadata were not backfilled from current terms.

Configs, guarded ledgers/profiles, registries, packets and recipes remain truth.
Generated intake/aggregates are local products. See [ONBOARDING](../ONBOARDING.md),
[workflow](workflows/arca-coverage-planning/SKILL.md), [journal](JOURNAL.md),
[history](history/README.md) and [earlier GW execution](WORLDWIDE_EXPANSION_2026-10-29.md).
