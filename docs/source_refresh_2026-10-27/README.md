# Staged source refresh review — 2026-10-27

Both upstream snapshots were cloned into `raw/curation/refresh-raw/lexibank/` and ingested into separate staging directories. Active intake, original cached repositories, accepted identities and source pins were not replaced. The summary files record exact commits and SHA-256 hashes of the inspected CLDF tables and bibliography.

## IECOR

Cached `700b635a04786427b78841489c46eefbe2843509` → staged `dd1ebc997bc38c824fb18a1ef234bbf2c229420b`.

All 25,731 forms, cognate rows, 160 language IDs and 170 parameter IDs remain stable. All Concepticon mappings remain stable. The only language-table changes update three Glottolog display names: Apulia-Calabrian Greek → Apulian-Calabrian Greek, and two Old Cornish entries → Old South-West British. No canonical Arca identity is automatically renamed. All 160 accepted IECOR member selections are unchanged.

Each of 170 parameters gains `Description_md`, the source author's detailed target-sense guidance. This is valuable evidence for future semantic audits, but adds no lexical coverage. The current normalizer does not carry `Description_md` into its five-column Lexibank parameter table; the descriptions remain available in the staged raw snapshot. Do not claim they have become effective concept corrections or that the transcription-policy documentation changed any supplied forms.

The staged refresh has no identity/mapping migration blocker. It is retained as a reviewed candidate rather than rewriting active intake merely to change a version label. Future promotion should preserve these descriptions for review and verify unchanged built outputs.

## ABVD

Cached `2af9f4ef6fff6250e0a31f383f249c3c9cf42e55` → staged `81748db0c5fcf3bf1d8c8372b86df75c375e1f22`.

The new snapshot has 349,424 forms versus 346,919: 14,261 added IDs, 11,756 removed IDs, and 335,163 shared rows changed. Much of that churn is provenance (`Source` and `Contribution_ID`), but 693 shared form spellings also change. Cognate row IDs change substantially, so neither old cognate IDs nor citations may simply be attached to the new rows.

Language IDs decrease from 2,040 to 1,982, with 58 removed and no added IDs. Forty-six retained member IDs change Glottocode. All 210 parameter IDs and Concepticon mappings are stable; 59 parameter comments change. These facts are more precise than treating the GitHub line diff as a wholly new source partition.

632 accepted varieties currently use ABVD in at least one block. Forty-two would select a different set of language members. Some removed metadata aliases had no forms and cause no actual loss; the per-variety table distinguishes that from real row changes. Examples needing explicit decisions include Tolaki (1,262 → 209 raw source forms), Bungku (1,198 → 418), and Squliq (248 → 668). These are **unreviewed source-slice counts**, not gains/losses in validated core support. Reclassification must be reconciled with Arca's accepted varieties before promotion. The old source remains intact.

## Reproduce and inspect

Run `python scripts/audit_source_refresh.py DATASET --staged-repository PATH --output DIRECTORY`. The tool is read-only with respect to raw snapshots and active intake. `summary.json` covers every row. `changes.csv` hashes every language/parameter field change and the first 500 form/cognate field changes per table; it avoids redistributing full source descriptions or a giant form dump. `language_migration.csv` exposes changed names and Glottocodes; `accepted_varieties.csv` exposes exact configured member selection and form-ID changes. Re-run from the recorded commits to recover full details.

The audit's status describes identity and mapping stability, not blanket semantic or phonetic approval. No automatic refresh or source switch is performed.
