# Concept entries in the research explorer

Concept pages automatically show a normal entries table across all families.
Visitors can use the existing family, collection, vocabulary, macroarea, tier,
transcription and coverage filters, column sorting, column selection, pagination
and exports. A family is an optional filter, not a prerequisite. Empty concepts
show the normal empty-table message. WordNet and colexification panels remain.

The table is generated at runtime by querying the browser worker’s in-memory
SQLite `forms` table. No concept HTML or result table is precomputed. To avoid
loading every lexical family, the browser downloads only the current concept’s
lexical rows in checksummed chunks and inserts them into that same database.
The full original field schema and form IDs are retained. Clicking an already
loaded form opens its details without first downloading its whole family.

Only one concept’s temporary rows are retained. Switching concepts deletes its
concept-only forms and cognate memberships. Fully loaded family data stays in
memory; overlapping concept/family loads insert each form and membership once.
A completed family load promotes its temporary rows to retained family rows.
Transactions roll back failed downloads to the preceding valid state. SQLite
remains read-only outside these controlled load transactions.

Selection manifests record the concept-transport build and index hash alongside
the lexical snapshot and any fully loaded family hashes. Filters and sorting
operate on the queried rows as in other explorer tables. Exports contain the
whole filtered selection, not just the visible page.

## Data transport and reproduction

```sh
.venv/bin/python scripts/build_concept_rows.py
```

This streams the existing accepted family assets into scratch SQLite, preserves
all mapped rows and fields, and partitions them into at most 1,000 rows per
chunk. Each chunk is bounded at 8 MiB expanded / 1 MiB compressed, and the index
at 4 MiB. The browser enforces declared size, expanded size and SHA-256 before
insertion. Chunks and their index live in an immutable snapshot directory;
publication switches the main manifest after verification. Input fields,
aggregate hashes and family asset hashes bind the index to the lexical release.
Source drift, stale index inputs or cache corruption fail closed.

The standalone exporter runs under a 256 MiB address-space limit. The normal
research-web CLI executes this exporter in a fresh process before the separately
bounded colexification stage; `--without-colexification` still creates concept
transports. The colexification publisher also refreshes the transports when run
independently. Custom-output web fixture builds remain separate.

## Accepted verification, 2026-10-31

[Verification](concept_entries_verification_2026-10-31.json) compares every field
and ID against the 2,119,754 source records. All **1,792,516 mapped records** are
preserved in 4,760 chunks covering 3,787 concepts with entries; unmapped records
have no concept page. The catalog’s other concepts display an empty table. The
largest concept has 8,947 rows, the largest expanded chunk 892,980 bytes and the
largest compressed chunk 90,118 bytes. The export peaked at **57.11 MiB RSS**
under its 256 MiB address-space limit. The browser downloads the current
concept’s chunks, not the entire 127 MB collection.

553 tests pass, including chunk/stream corruption and preservation fixtures.
The concept browser suite verifies automatic loading without family downloads,
SQL row counts, filters, sorting, selection manifests, direct form links,
concept-row eviction, family promotion without duplicate memberships, mobile
layout and checksum-failure rollback. Colexification, WordNet and general
research browser suites also pass. The publication command chain was exercised
against the cached analytical build. Lexical readings, concept assignments,
source provenance, cognacy, WordNet and underlying colexification assets are
unchanged.

[Publication proof](concept_entries_publication_2026-10-31.json): commit `e6a96bca` is deployed; CI and Pages passed. All 4,767 checked canonical assets match, and all four live browser suites pass.
