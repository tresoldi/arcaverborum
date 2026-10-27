# Source expansion review — 2026-10-27

The [repository inventory](source_inventory_2026-10-27.csv) screens 189 Lexibank repositories. Names absent from datasets.csv are candidates, not 44 new language datasets: the list includes software, syntheses and overlapping sources. Eight language tables were inspected. Glottocode novelty and GLED overlap columns are provisional discovery signals, never identity decisions. Language-table Git blob hashes record the inspected snapshots.

Lote and Tomoip were accepted after primary fieldwork metadata, licenses, source members and supplied IPA were checked. Amazonian Voices offers three potentially novel Glottocodes, but independence remains unreviewed. Pahoturi, West Papuan and Rutul candidates overlap existing evidence; Borch Rutul already has an accepted member. Oceanic ABVD is a migration/partition of existing evidence and Seabor a synthesis. Do not count these as automatic new coverage.

[Freshness checks](source_freshness_2026-10-27.csv) compare five cached sources with exact upstream commits. ABVD is nine commits ahead with extensive forms/languages changes; IECOR is two ahead with parameter/language changes but unchanged forms. Both require a staged mapping audit before refresh. Mixe-Zoquean Voices, UraLex and NorthEuraLex match the inspected upstream heads. These findings describe this date, not a persistent freshness guarantee.

[Candidate decisions](intake_decisions_2026-10-27.csv) admit Santiago Tutla under canonical Mazatlán Mixe identity and defer three samples with specific identity/transcription blockers. The Chickasaw profile is an inactive proposal with native dictionary evidence, not a GLED replacement yet.

Reproduce the inventory with `python scripts/audit_source_inventory.py` (cached) or `--fetch` (public metadata refresh). `--output` selects the report destination. The script never changes accepted configurations.

For a new Lexibank source, ingest into a separate staging directory first. The ordinary subset ingest must not target the active intake because it replaces tables. `python scripts/append_source_intake.py --help` describes the append workflow; its default is validation only. `--write` appends only wholly new datasets after schema/provenance checks, preserves existing bytes, and rolls back replacement failures. Existing-source refreshes need a separate migration review. Raw caches and full dictionary query responses remain ignored; reviewed decisions, recipes and correction ledgers are tracked.
