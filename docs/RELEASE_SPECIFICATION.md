# Release Specification — Arca Verborum Core v0.1.0

Status: **scoped, ready to implement** (2026-08-22). Defines the first
downloadable Arca Verborum dataset release. See
`CURATION_WORKFLOW_SPECIFICATION.md` for the broader curation model and
`CURATION_MACHINERY.md` for authority recipes/packets.

## Product

**Arca Verborum Core** — a basic-vocabulary lexical dataset for computational
historical linguistics: one accepted construction per variety, across the 13
curated CORE families, with per-form provenance and quality scoring.

## Scope

- **Varieties:** every variety whose accepted source is one of the 13
  **CORE-flagged datasets** (`datasets.csv`, CORE=TRUE): bdpa, bowernpny,
  gravinachadic, grollemundbantu, iecor, kahd, peirosaustroasiatic, robinsonap,
  sagartst, savelyevturkic, tuled, utoaztecan, walworthpolynesian. One curated
  source per family (same-family-same-dataset).
- **Forms:** ALL forms the CORE sources provide (~158k), NOT restricted to the
  core concept list. The basic-vocabulary core is shipped as a **view, not a
  cut**: each form carries `is_core_concept` (∈ the 161 frozen basic-vocab
  concepts, `src/arcaverborum/data/concept_core.csv`) so users can filter.
- **Cognates:** source/expert cognacy as built. Computed cognates are out of
  scope for v0.1.0 (deferred; would arrive as an evaluated candidate layer).

## Format

**CLDF-compatible Wordlist + plain CSV**, both emitted by Arca itself with **no
pycldf/cldfbench runtime dependency** (honors the project's no-CLDF-machinery
rule). The CLDF metadata JSON is written directly.

## Files (`output/release/arca-verborum-core-<version>/`)

| File | CLDF role | Contents |
|---|---|---|
| `forms.csv` | FormTable | 28-col aggregate schema **+ `is_core_concept` + `License`** (per-source) |
| `languages.csv` | LanguageTable | av_id, name, glottocode, family, macroarea, coords, tier, forms/cognates scores |
| `parameters.csv` | ParameterTable | concept_id, concepticon_id, label, pos, semantic_field, `is_core` |
| `cognates.csv` | CognateTable | cognate judgements keyed to forms |
| `sources.bib` | sources | BibTeX for every cited source |
| `cldf-metadata.json` | Wordlist metadata | table/column definitions + component wiring |
| `README.md` | — | datasheet: scope, method, per-source attribution + licenses, tier model, citation, provenance |
| `MANIFEST.json` | — | version, counts, source list + versions, merkmal version, license summary, build date |

## Licensing

The aggregate inherits per-dataset licenses (recorded per row in `License` and
summarised in the datasheet/MANIFEST):

- **12 of 13 CORE datasets: CC-BY-4.0** — redistributable with attribution.
- **grollemundbantu (Bantu): CC-BY-NC-4.0** — NonCommercial. Kept in the
  release; its NC restriction is flagged per-row and in the datasheet.

The release is built and **staged internally first**; the public Zenodo deposit
is deferred until licensing (esp. the NC source and attribution requirements)
is reviewed. Code: MIT.

## Versioning & mechanics

- Semver, starting **v0.1.0**. The release is a **build artifact** under the
  gitignored `output/release/`; the release code, datasheet template, and this
  spec are committed.
- New CLI: `build.py release [--version X.Y.Z]` — reads the CORE aggregate,
  joins per-source license/metadata, adds `is_core_concept`, writes all files
  above. Requires `aggregate` first.
- Provenance for reproducibility: MANIFEST records merkmal version, each source
  repo version (intake `metadata.csv` `Repository_Version`), build date, and
  per-table row counts.

## Out of scope for v0.1.0 (later milestones)

- Public Zenodo deposit (after license review).
- Web interface (Phase 5; `explore.py` → static browser page, *.tresoldi.org).
- Computed cognates as an evaluated candidate layer.
- Beyond-CORE expansion (Wiktionary/GLED fallbacks) via curation packets.
