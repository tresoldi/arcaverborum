# Arca Verborum — Project Context

This document is the domain glossary and architectural map for agents and
contributors working on the codebase. Read it before touching code; update
it when the domain language changes. Current session decisions and operational
handoff are maintained in [docs/JOURNAL.md](docs/JOURNAL.md). Current metrics
live in [STATUS](docs/STATUS.md); proposed work lives in [NEXT](docs/NEXT.md).


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
| **WordNet link** | A versioned sidecar association between a frozen concept and a synset. Accepted exact/typed relations, inherited Concepticon associations and unreviewed candidates are distinct; see [WordNet](docs/WORDNET.md). |
| **concept catalog** | The frozen registry of concept_ids (`data/concepts.csv`). Extended by minting, never re-keyed. |
| **concept core** | The 161 basic-vocabulary concepts attested across ≥7 of the 13 CORE families (`data/concept_core.csv`). |
| **construction** | The accepted build of a variety: primary source, reviewed source-specific supplements, cognate source, and custom corrections. Recorded in `config.yaml` + `custom/*`. |
| **form** | A single lexical entry: a (variety, concept, word-form, transcription) tuple with provenance. |
| **intake** | Normalized, source-prefixed CSVs produced by ingest from raw CLDF data. The common input format for the build. |
| **profile** | An orthographic profile (`custom/profile.tsv`): a grapheme→IPA table replacing re-segmentation within a reviewed source scope; supplemental profiles use guarded whole-form keys. |
| **segments** | Space-separated IPA tokens for a form, validated by merkmal. |
| **segments source** | How the segments were obtained: `source` (validated supplied transcription, with original conventions retained), `profile` (documented derived reading), `resegmented` (re-tokenized form string), or `unclean` (unresolved validation). Token validity is not independent pronunciation verification. |
| **tier** | Quality band recorded in the accepted config: gold / silver / bronze / copper. Per-form scores and transcription evidence are separate diagnostics. |
| **pin** | A manually fixed source choice for a variety (overrides automatic selection). |
| **recipe** | The authority recipe (`recipe.yaml`): a descriptive record of a variety's accepted construction, authored or scaffolded then reviewed. Enforced choices remain in config/custom files. |
| **packet** | The curation packet (`PACKET.md`): a human-readable summary of a variety's current state for a curator. |
| **aggregate** | The union of all per-variety `generated/forms.csv` files into `output/aggregate/`. |
| **release** | A versioned, CLDF-compatible dataset sliced from the aggregate (CORE families only). |
| **Core-source collection** | Sources flagged `CORE=TRUE` in `datasets.csv`; the live explorer filters lexical rows by this membership. It is distinct from the 161-concept vocabulary and archived Core v0.1.0 release. |
| **reviewed unmapped entry** | An explicitly admitted source citation whose literal native sense is retained without a catalog equivalence. It keeps identity, provenance and reading guards, blocks inherited concept mapping and adds no mapped/core slot. |
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


## CLI entry points

| Entry point | Role |
|---|---|
| `build.py` | Main CLI: fetch, ingest, register, extend, update, aggregate, release, report, concepts, packet, status |
| `explore.py` (root) | Thin relay to `arcaverborum.explore.main()` |

`build.py` is an orchestrator with real logic (incremental rebuild,
fingerprinting, concept resolution), not a shallow dispatcher.


## Key design decisions

1. **One construction per variety.** Arca picks one source per variety and
   adds explicit corrections and individually reviewed source supplements. Each
   row keeps its own source identity and cognacy scope; sources are not pooled
   automatically.

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
   it is authoritative within its reviewed source scope; form-level
   re-segmentation is not attempted as a fallback. Primary and supplemental
   profiles are separate.

6. **merkmal as the phonological backbone.** IPA validation,
   segmentation, canonicalization, and tone handling go through merkmal's
   `descriptive` system.

7. **No framework for the web explorer.** Vanilla JS + sql.js + Leaflet.
   The current browser loads a lightweight catalog and family shards into an
   in-browser SQLite worker. Console indexing and the archived Core explorer
   are separate products; see `web/README.md`.


## Maintenance boundaries

- Shared form schema, quality and parameter helpers live in `forms_schema.py`;
  the build imports that public module. Older private-coupling notes are obsolete.
- Legacy bootstrap scripts reference a removed selection module. Review/repair
  that path before using it to recreate configs; normal curation updates accepted
  configs and guarded custom data directly.
- Planning specifications contain historical diagnostics and intended mechanisms.
  Use STATUS, current code and per-variety packets to establish implemented state.
- The repeatable planning procedure is
  [coverage-planning](docs/workflows/arca-coverage-planning/SKILL.md); it keeps
  completed work and held candidates from resurfacing as fresh proposals.

Explicit analytical reconstruction inventories are distinct from documented
language varieties and attested historical stages. Their named member scopes have
blank canonical Glottocodes and no inferred dates or coordinates. The reviewed
`data/construction_kinds.csv` registry marks these inventories in the research
catalog; builds fail on a conflicting primary or identity. Written reconstruction
pilots retain original stars, bound stems and uncertainty, with empty segments and
`source_reported_reconstruction` evidence. They do not count as newly documented
extant languages or supported pronunciations.
