# Arca Verborum — Project Context

This document is the domain glossary and architectural map for agents and
contributors working on the codebase. Read it before touching code; update
it when the domain language changes.


## What Arca Verborum is

A multi-source lexical database builder for computational historical
linguistics. For each language **variety**, Arca selects one accepted
**construction** from the best available source, optionally overlays
hand-curated corrections, normalizes phonological transcriptions, maps
forms to a frozen **concept catalog**, and emits per-variety output that is
aggregated into a single dataset and then sliced into a versioned
**release** (Arca Verborum Core).

The database is consumed by two downstream tools:

- **cognator** — automated cognate detection (reads Arca's aggregate).
- **regulae** — sound-change rule inference (reads Arca's aggregate).

Arca's job is to be the single, highest-quality lexical substrate for both.


## Domain glossary

Use these terms when naming things in code, commits, and conversation.

| Term | Meaning |
|---|---|
| **variety** | A language variety (a language, dialect, or historical stage) with a stable `av_id`. The primary unit of work. |
| **av_id** | Family-prefixed, human-readable variety identifier: `<family_code>-<name_slug>` (e.g. `ine-latin`). Assigned once and frozen. Maps to a Glottocode as a column. |
| **concept** | A cross-linguistic meaning slot (e.g. "water", "eye"). Has a frozen `concept_id` prefixed by semantic field: `<field_code>-<label_slug>` (e.g. `bod-eye`). Maps to a Concepticon ID as a column. |
| **concept catalog** | The frozen registry of concept_ids (`data/concepts.csv`). Extended by minting, never re-keyed. |
| **concept core** | The 161 basic-vocabulary concepts attested across ≥7 of the 13 CORE families (`data/concept_core.csv`). |
| **construction** | The accepted build of a variety: which source's forms, which cognate source, plus any custom corrections. Recorded in `config.yaml` + `custom/*`. |
| **form** | A single lexical entry: a (variety, concept, word-form, transcription) tuple with provenance. |
| **intake** | Normalized, source-prefixed CSVs produced by ingest from raw CLDF data. The common input format for the build. |
| **profile** | An orthographic profile (`custom/profile.tsv`): a grapheme→IPA mapping table that replaces re-segmentation for a variety. |
| **segments** | Space-separated IPA tokens for a form, validated by merkmal. |
| **segments source** | How the segments were obtained: `source` (valid source IPA), `profile` (orthographic profile), `resegmented` (re-tokenized from the form string), or `unclean` (failed validation). |
| **tier** | Quality band: gold / silver / bronze / copper. Derived from source quality scoring. |
| **pin** | A manually fixed source choice for a variety (overrides automatic selection). |
| **recipe** | The authority recipe (`recipe.yaml`): a structured record of a variety's accepted construction, produced by the packet scaffolder. |
| **packet** | The curation packet (`PACKET.md`): a human-readable summary of a variety's current state for a curator. |
| **aggregate** | The union of all per-variety `generated/forms.csv` files into `output/aggregate/`. |
| **release** | A versioned, CLDF-compatible dataset sliced from the aggregate (CORE families only). |
| **CORE** | The 13 curated source families flagged in `datasets.csv`; the release includes only CORE data. |
| **merkmal** | External library for IPA phonology: segment validation, tokenization, feature extraction, tone handling. The phonological backbone. |
| **Glottolog** | External authority for language classification (Glottocodes, families, macroareas, coordinates). |
| **Concepticon** | External authority for cross-linguistic concept sets (Concepticon IDs, glosses, semantic fields). |
| **fingerprint** | A content-addressed hash of a variety's four build inputs (config, custom overrides, intake slice, recipe code). Used for incremental rebuilds. |


## Data pipeline

```
 fetch        raw/<source>/...                raw CLDF downloads (gitignored)
    │
 ingest       intake/<source>/forms.csv ...   normalized intake (gitignored)
    │
 register     varieties/<av_id>/config.yaml   tracked source choices
    │
 update       varieties/<av_id>/generated/    per-variety output (gitignored)
    │
 aggregate    output/aggregate/               union of all varieties (gitignored)
    │
 ├─ release   output/release/                 versioned CLDF dataset (gitignored)
 ├─ report    output/report/curation.*        curation priority ranking (gitignored)
 └─ explore   SQLite index / web explorer     browsing and querying
```

Each stage reads the previous stage's output. Tracked source of truth:

- Python code under `src/arcaverborum/`
- Frozen registries under `src/arcaverborum/data/` (concepts, family codes,
  field codes, varieties, score weights, variety overrides)
- Per-variety `config.yaml` and hand-authored `custom/*` files
- `datasets.csv` (source universe, CORE/ExpertCognates flags)
- Documentation and tests


## Module map

Modules are grouped by their role in the pipeline.

### External data loading (no intra-package dependencies)

| Module | Role | Key interface |
|---|---|---|
| `glottolog` | Load Glottolog language classification | `load_glottolog() → {gc: GlottologEntry}` |
| `concepticon` | Load Concepticon concept sets | `load_concepticon_by_id() → {id: ConcepticonEntry}` |
| `bibtex` | BibTeX key namespacing for multi-source ingest | `prefix_bibtex_keys()`, `prefix_bibtex_file()` |
| `sources/` | Fetch raw data per source (lexibank, wiktionary, gled, glottolog, concepticon) | `dispatch_fetch(name, raw_root)` |

### ID schemes (parallel design, shared machinery)

| Module | Role | Key interface |
|---|---|---|
| `avid` | Family-prefixed variety IDs | `mint_av_id()`, `assign_av_ids()`, `slugify_name()` |
| `concepts` | Field-prefixed concept IDs + frozen catalog | `mint_concept_id()`, `load_concept_maps()`, `Concept` |

`concepts` reuses `avid.slugify_name` and `avid._derive_family_code` so
both ID spaces follow the same `<3-char-code>-<slug>[-qualifier]` pattern.

### Ingest

| Module | Role | Key interface |
|---|---|---|
| `ingest` | Raw CLDF → normalized intake CSVs | `ingest_lexibank(raw_root, intake_root)` |

### Catalog and scoring

| Module | Role | Key interface |
|---|---|---|
| `catalog` | Build variety catalog from intake + Glottolog + overrides | `build_catalog()`, `Variety` |
| `score` | Two-block quality scoring (forms + cognates) | `compute_signals_for_group()`, `score_forms_block()` |
| `selection` | Source auto-selection with pin overrides | `select_all()`, `Selection` |

### Per-variety build

| Module | Role | Key interface |
|---|---|---|
| `variety` | Per-variety transform: intake slice → generated forms | `build_one()`, `VarietyDir`, `register()` |
| `phonology` | IPA validation, re-segmentation, orthographic profiles | `normalize_segments()`, `apply_profile()` |
| `tracking` | Content-addressed build fingerprinting for incremental rebuilds | `fingerprint()`, `is_fresh()`, `recipe_hash()` |

### Aggregation and output

| Module | Role | Key interface |
|---|---|---|
| `aggregate` | Union per-variety output into aggregate tables | `aggregate_all()`, `FORMS_OUT_FIELDS` |
| `curation` | Rank varieties by curation priority | `build_curation_report()` |
| `release` | Build versioned CLDF release from CORE slice | `build_release()` |
| `packet` | Scaffold authority recipes and curation packets | `scaffold_packet()` |
| `explore` | SQLite-indexed console and web data explorer | `build_index()`, `q_*()` queries |

### Auditing

| Module | Role | Key interface |
|---|---|---|
| `concept_audit` | Detect drift between frozen catalog and live Concepticon | `audit_registry()`, `mint_missing()` |

### Support (shallow)

| Module | Role | Notes |
|---|---|---|
| `schema` | Column tuples and structural dataclasses | Pure definitions, no logic |
| `validation` | Statistical accumulator for dataset QA | Possibly vestigial — not called from current pipeline |
| `report` | Selection report JSON assembly | Companion to `selection`; not called from `build.py` |
| `util` | Formatting and JSON helpers | Possibly unused |


## CLI entry points

| Entry point | Role |
|---|---|
| `build.py` | Main CLI: fetch, ingest, register, extend, update, aggregate, release, report, concepts, packet, status |
| `explore.py` (root) | Thin relay to `arcaverborum.explore.main()` |

`build.py` is an orchestrator with real logic (incremental rebuild,
fingerprinting, concept resolution), not a shallow dispatcher.


## Key design decisions

1. **One construction per variety.** Arca picks one source per variety and
   optionally layers corrections on top. It does not merge multiple sources.

2. **Frozen IDs.** Both `av_id` (varieties) and `concept_id` (concepts)
   are assigned once and never re-keyed. External authority drift
   (Glottolog reclassification, Concepticon merges) is flagged, not
   silently absorbed.

3. **Content-addressed incremental builds.** `tracking.py` fingerprints
   each variety's four inputs (config, custom, intake slice, recipe code).
   `update` skips varieties whose fingerprint hasn't changed.

4. **Phonology policy: trust source IPA.** `phonology.normalize_segments`
   prefers source segments over re-segmentation. Unclean source segments
   are kept verbatim for later recovery, not discarded.

5. **Orthographic profiles over re-segmentation.** When a profile exists,
   it is authoritative for the variety; form-level re-segmentation is not
   attempted as a fallback.

6. **merkmal as the phonological backbone.** All IPA validation,
   segmentation, canonicalization, and tone handling go through merkmal's
   `descriptive` system.

7. **No framework for the web explorer.** Vanilla JS + sql.js + Leaflet.
   The SQLite database is the same one the console explorer uses.


## Known structural issues

- **Private-function coupling.** `variety.py` and `build.py` import
  `aggregate._form_quality_score`, `aggregate._load_parameter_index`, and
  `aggregate.FORMS_OUT_FIELDS`. These are shared infrastructure used as
  private functions.

- **Potentially dead modules.** `selection.py`, `report.py`, `util.py`,
  and `validation.py` appear to not be called from the current `build.py`
  pipeline. They may represent an earlier architecture phase or be used by
  offline scripts not in the repo.
