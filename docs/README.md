# Documentation Map

Start with the root `README.md` for the project overview and
`ONBOARDING.md` for local setup and common workflows.

## Project Specs

* `BESTOF_SPECIFICATION.md` describes the current per-variety build
  mechanics: source selection as implemented today, config/custom file
  schemas, scoring, phonology, output schema, and curation report.
* `CONCEPTS_SPECIFICATION.md` describes Arca's frozen concept catalog,
  `concept_id` design, Concepticon mapping, and concept drift audit.
* `CURATION_WORKFLOW_SPECIFICATION.md` describes the planned language
  curation workflow: authority recipes, curation packets, Arca-derived
  layers, computed cognates, tier metadata, source-policy direction, and
  pilot scope.
* `coverage_recovery_2026-10-23.csv` records the review of 34 apparently
  unregistered lexical-source slices, including accepted additions,
  duplicate samples, family-level identifiers, and unresolved identities.
  Language-specific profile decisions and pronunciation evidence live in
  each variety's `PACKET.md` and `recipe.yaml`.

Run `python scripts/audit_coverage.py` after refreshing the intake store to
rank remaining alternatives to GLED. Its metrics describe uncorrected intake,
so inspect curation packets and applied profiles before accepting a source.
For Galician, `scripts/galician_dictionary.py` records exact dictionary
pronunciation evidence and produces a dictionary-only profile; unresolved
spellings remain unclean rather than receiving guessed pronunciations.
Its core selection respects accepted concept corrections and preserves
previously recorded pronunciations when a sense moves out of the core.

The 2026-10-24 core-sense audit is recorded in the five profile pilots'
`custom/core_review.csv` files. `scripts/audit_core_pilots.py --write-maps`
compiles those decisions; running without flags checks rebuilt output and
source drift. Individual translation corrections have guarded source-form IDs
and supporting evidence in `custom/form_review.csv`. See each `PACKET.md`
for corrected coverage, unresolved senses and remaining recovery work.

## Reading Order

For normal development:

1. `ONBOARDING.md`
2. `BESTOF_SPECIFICATION.md`
3. The module or test relevant to the change

For concept work:

1. `CONCEPTS_SPECIFICATION.md`
2. `src/arcaverborum/concepts.py`
3. `src/arcaverborum/concept_audit.py`

For language curation planning:

1. `CURATION_WORKFLOW_SPECIFICATION.md`
2. `BESTOF_SPECIFICATION.md`
3. The current `output/report/curation.csv` generated locally

## Current vs Planned Behavior

`BESTOF_SPECIFICATION.md` documents behavior that exists today.
`CURATION_WORKFLOW_SPECIFICATION.md` documents the agreed direction for the
next curation layer. When the two differ, treat the curation workflow as a
planning target, not as implemented behavior.
