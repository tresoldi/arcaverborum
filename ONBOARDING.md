# Arca Verborum Onboarding

This guide is for a local checkout that already has the tracked repo state.
Generated products under `varieties/*/generated/`, `intake/`, `raw/`, and
`output/` are intentionally not part of the committed source of truth.

Read this first, then use `docs/README.md` to choose the relevant design
specification.

## 1. Project Shape

Arca Verborum is a per-variety lexical database for computational
historical linguistics. Each variety has a stable `av_id`, selected source
configuration, optional curated extensions, and generated per-variety forms.
The aggregate product is built from those per-variety outputs.

The current goal is not just to pick a source mechanically. Arca builds one
accepted authoritative construction per language. That construction may use
a source as-is, use a source plus explicit corrections, or eventually use
Arca-derived layers and computed/curated cognates when they are reviewed.

## 2. Data Flow

```
fetch     -> raw/<source>/...                         downloaded; gitignored
ingest    -> intake/<source>/{forms,languages,...}    normalized intake; gitignored
bootstrap -> varieties/<av_id>/config.yaml            tracked source choices
update    -> varieties/<av_id>/generated/forms.csv    generated; gitignored
aggregate -> output/aggregate/...                     generated; gitignored
report    -> output/report/curation.*                 generated; gitignored
explore   -> output/explore.sqlite                    generated; gitignored
```

Tracked source of truth:

* code under `src/arcaverborum/`;
* stable registries under `src/arcaverborum/data/`;
* `varieties/<av_id>/config.yaml`;
* hand-authored `varieties/<av_id>/custom/*` files when present;
* documentation and tests.

## 3. Environment

Python 3.11+ is expected. The phonology library `merkmal` (≥0.9.0) is
developed next to this repo at `../merkmal`; install its Python package from
there. merkmal is an undeclared runtime dependency (it is not on PyPI and is
built from the sibling checkout), so it is installed out-of-band rather than
via `arcaverborum`'s own dependency list.

```bash
cd /home/tiagot/repos/arcaverborum
python -m venv .venv
source .venv/bin/activate
pip install -e .
pip install -e ../merkmal/python
pip install pytest
python -c "import merkmal; print(merkmal.list_systems())"
pytest -q
```

The project intentionally avoids the CLDF ecosystem as runtime machinery.
Do not add `pycldf`, `pylexibank`, or `cldfbench` unless there is a
specific reviewed reason.

## 4. Common Commands

Build or refresh all generated data from available intake:

```bash
python build.py update --all
python build.py aggregate
python build.py report
python explore.py index
```

Build a single variety after editing its config or custom files:

```bash
python build.py update ine-latin
python build.py aggregate
python build.py report
```

Scaffold curation files for a variety:

```bash
python build.py extend ine-latin
```

Inspect the aggregate:

```bash
python explore.py stats
python explore.py langs --family Indo-European
python explore.py lang ine-latin
python explore.py concept phy-water
python explore.py sql "SELECT tier, COUNT(*) FROM varieties GROUP BY tier"
```

Audit concept drift against Concepticon:

```bash
python build.py concepts
python build.py concepts --mint
```

## 5. Current Baseline

The latest local aggregate reviewed while reorganizing the docs contained:

* 7,308 varieties;
* 2,007,699 forms;
* 1,701,250 source-clean forms;
* 5,682 profile-clean forms;
* 195,357 resegmented forms;
* 105,410 unclean forms;
* 160 pinned selections;
* 1,271 varieties whose selected cognate candidate differs from the
  selected transcription source;
* 236,246 forms without `concept_id`;
* 369 varieties with zero mapped concepts.

These numbers will change after rebuilds. Treat them as a recent snapshot,
not a contract.

## 6. Source Policy

The current implementation still uses a priority floor in
`src/arcaverborum/selection.py`: Lexibank first, then GLED, then
Wiktionary. Fallback picks never exceed `copper`.

The intended curation policy is different and is documented in
`docs/CURATION_WORKFLOW_SPECIFICATION.md`: curated lexical sources first,
Wiktionary as an important fallback and research entry point, and GLED only
as last-resort scaffolding. Do not change source-priority behavior casually;
the policy, docs, and rebuild consequences need to move together.

## 7. Curation Rules

Per-language work should become a structured curation packet, not ad hoc
edits. A packet should document the current construction, candidate sources,
concept mapping, transcription quality, cognates, provenance, tradeoffs, and
recommended authority recipe.

Small fixes can live in `varieties/<av_id>/custom/*`:

* `transcriptions.csv` overrides source transcription columns;
* `forms.csv` adds new forms;
* `cognates.csv` overrides cognate fields by form id;
* `concept_map.csv` fixes source parameter-to-concept mapping;
* `profile.tsv` maps orthographic graphemes to IPA.

Heavy correction or newly authored data should graduate into a named
Arca-derived layer once the data's scholarly identity is effectively Arca's
construction rather than the upstream source alone.

## 8. Gotchas

* `av_id` is the primary key. It is a frozen Arca identifier of the form
  `<family_code>-<name_slug>`, not a Glottocode.
* `concept_id` is also an Arca-controlled frozen key. Concepticon remains a
  mapped external column.
* `build.py status` checks config/custom/recipe freshness, but intake
  changes are detected by `build.py update`.
* `build_one` accepts pre-loaded intake DataFrames so `update --all` does
  not re-read huge CSVs per variety.
* Phonology uses merkmal's `descriptive` system. Source segments are
  normalized, tone digits are merged onto their nucleus before validation,
  and invalid source segments are preserved as `unclean`.
* Generated outputs are gitignored. Commit configs, custom curation files,
  data registries, docs, tests, and code.

## 9. Documentation Map

Use `docs/README.md` as the index. The main specs are:

* `docs/BESTOF_SPECIFICATION.md` for current build mechanics;
* `docs/CONCEPTS_SPECIFICATION.md` for concept IDs and Concepticon mapping;
* `docs/CURATION_WORKFLOW_SPECIFICATION.md` for the next curation workflow.
