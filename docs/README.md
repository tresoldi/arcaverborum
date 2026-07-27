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
