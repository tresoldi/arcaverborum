# Current project state

Updated 2026-10-29. Accepted baseline and portable handoff. Latest batch:
[African follow-up AX01–AX06](AFRICA_FOLLOWUP_2026-10-29.md), all six authorized
tracks completed with bounded admissions or evidence holds. Earlier AF01–AF09
baseline data commit: `a1f8e941692d5e1f6ec893e37edf916d5b40058e`.
[Realized metrics](africa_followup_summary_2026-10-29.json) are authoritative.

## Accepted baseline

| Measure | Accepted value |
| --- | ---: |
| Varieties | 7,332 |
| Forms | 2,070,480 |
| Supplied-source forms | 1,746,500 |
| Profile-derived forms | 14,390 |
| Supported core slots | 468,581 |
| Mapped core slots | 542,492 |
| Supported all-concept slots | 1,206,914 |
| Mapped all-concept slots | 1,334,347 |
| GLED primary selections | 1,573 |
| Core-source varieties | 906 |

Frozen vocabulary3,787 concepts/161 core. Added363 records (30 supplied upstream
conversions,204 profile,129 written-only), +256 supported slots (80 core), and
recovered readings for80 earlier records. Gimnime is one new written-only language;
no new named varieties. Momi corrects existing scope at stable atl-mom-jango, now
Momi (Vere Kaadam), vere1252. Fwe/Sidaama replace two GLED primaries, retaining all96
prior GLED rows and their cognacy. Ten earlier semantic mappings are corrected.

Bantu ancestry scope485 constructions:150,574 forms/35,101 supported core;
95 GLED primaries,23 zero-supported-core cases. Written-only entries add no
supported phonetic slots. Source origin is not certification: TLS/Grollemund
conversions retain profile-genealogy disclosure, finite Arca profiles are derived,
and Kam retains the author's M-tone caveat. Core-source collection is independent
of the161-concept vocabulary. Mechanical quality scores are not linguistic judgments.

## Verification and publication

447 tests and full lint pass; all7,332 accepted builds update with zero failures.
All2,070,117 earlier records and original comments/JSON evidence are preserved,
with exactly reviewed80 readings,10 semantic mappings and37 Momi metadata changes.
Derived IDs/captions and97 quality scores may change. All662 original intake rows
reproduce from immutable source bytes. 401 web hashes and3 aggregate-input hashes
match. Local research, African, ancient and mixed-source browser/export checks pass.
Data commit: `f1e6f1a9bddf09c6fa1c524f39252eaf328eff18`.
[CI](https://github.com/tresoldi/arcaverborum/actions/runs/40848955077) passed on
Python3.12/3.13 and [Pages](https://github.com/tresoldi/arcaverborum/actions/runs/40848955070)
succeeded. Canonical live manifest, catalog, recordings, source bibliography and
Atlantic-Congo/Afro-Asiatic/Mande/Songhay/Etruscan/Elamite shards match committed
bytes. Updated African live browser/export checks pass. This is the lexical data
commit; subsequent documentation-only commits do not change its artifact hashes.

The site publishes tracked web artifacts: manifest, compressed catalog,399 family
shards, bibliography and recording metadata. Pages does not rebuild lexical data.

## Evidence and next work

[Execution report](AFRICA_FOLLOWUP_2026-10-29.md), dated AX decision/source manifests,
[registry](../src/arcaverborum/data/african_lexical_sources.json),
[current member screen](africa_followup_opportunities_2026-10-29.csv) and
[GLED screen](africa_followup_gled_2026-10-29.csv) support planning. Raw alternatives
are overlapping unreviewed potential. [NEXT](NEXT.md) contains proposals after
completed AX tracks; [HELD](planning/HELD.md) defines exact reopening evidence.
Americas/South America and Etruscan/Elamite remain standing priorities. Earlier
African, ancient, Romance and American reports preserve historical observations.

## Build state

Configs, guarded custom ledgers/profiles, source registries, packets and recipes
are authoritative. Intake now7,192,595 rows. Eight African original namespaces
contain662 rows; cumulative counts92/120/169/50/88/45/45/53 are in the report.
Existing-source guarded expansions and the new reflexdiversity append are done:
never replay old counts/appends or subset-ingest over active tables. Materialized
metadata reports actual table extents. Generated intake/aggregates remain local.
Jê remains463 admitted forms across five members; older251/371 migrations are done.

Use [ONBOARDING](../ONBOARDING.md),
[coverage workflow](workflows/arca-coverage-planning/SKILL.md),
[journal](JOURNAL.md) and [history](history/README.md) for reproducible continuation.
