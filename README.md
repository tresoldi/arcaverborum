# Arca Verborum

Per-variety lexical database for computational historical linguistics.
For each language variety, one source is selected for transcription
and one for cognate judgments, with full provenance, per-form quality
scoring, and hand-curatable extensions.

> Per-variety redesign of the project. The earlier merged-tier layout
> (Full / Curated / Expert-Cognates) is fully replaced. New here? Start
> with `ONBOARDING.md`.

## Layout

```
raw/                            downloaded source data (gitignored)
  lexibank/<dataset>/cldf/...
  wiktionary/raw.jsonl.gz
  glottolog/languages.csv
  concepticon/concepticon.tsv

intake/                         pre-processed per-source CSVs (gitignored)
  lexibank/{forms,languages,parameters_raw,metadata}.csv
  wiktionary/{forms,languages,parameters_raw}.csv

varieties/<av_id>/              one dir per variety (tracked)
  config.yaml                   source picks, extensions, notes, scoring
  custom/transcriptions.csv     per-form transcription column overrides
  custom/forms.csv              additive new (concept, form) rows
  custom/cognates.csv           per-form cognate overrides
  custom/concept_map.csv        per-Parameter_ID Concepticon fixes
  generated/forms.csv           gitignored — output of `build.py update`
  generated/build_manifest.json gitignored — input fingerprint (skip-if-unchanged)

output/aggregate/               (gitignored) union across enrolled varieties

src/arcaverborum/               package code
  catalog.py · score.py · selection.py · phonology.py
  variety.py · aggregate.py · report.py · tracking.py · avid.py · explore.py
  sources/{lexibank,gled,wiktionary,glottolog,concepticon}.py
  data/{score_weights.yaml, selection.csv, family_codes.csv, varieties.csv, ...}

build.py                        top-level build CLI
explore.py                      top-level query CLI (SQLite-indexed)
```

## Variety IDs (`av_id`)

Each variety has a stable, human-readable primary key of the form
`<family_code>-<name_slug>` — e.g. `ine-latin`, `sit-mandarin-chinese`,
`bas-basque` — with a `-2`, `-3` … suffix only to break collisions.

* `family_code` is a 3-char code for the variety's **top-level Glottolog
  family** (the only genealogical dimension in the key, so IDs survive
  Glottolog reclassifications of subgroups). Codes live in the committed,
  curatable `src/arcaverborum/data/family_codes.csv`; `und` = undetermined
  family. Macroarea, subfamily, and coordinates stay as columns, not in
  the key.
* IDs are **assigned once and frozen** in `src/arcaverborum/data/varieties.csv`
  (Glottocode ↔ av_id). The Glottocode is kept as a column (mapping to
  Glottolog/ISO) but is no longer the av_id. See `arcaverborum.avid`.

## CLI

```bash
python build.py fetch --source lexibank      # clone Lexibank repos
python build.py fetch --source all           # fetch every source

python build.py ingest --source lexibank     # raw/lexibank → intake/lexibank
python build.py ingest --source wiktionary   # raw/wiktionary → intake/wiktionary

python build.py register lati1261            # create varieties/ine-latin/ (accepts Glottocode or av_id)
python build.py extend ine-latin            # scaffold custom/*.csv templates
python build.py update ine-latin            # build generated/forms.csv
python build.py update --all                 # build everything (skips unchanged)
python build.py update --family Indo-European
python build.py update --all --force         # rebuild even if unchanged

python build.py aggregate                    # union into output/aggregate/
python build.py status                       # enrollment / freshness
```

### Incremental builds

`update` rebuilds a variety only when one of its inputs changed. Each
build records a fingerprint in `generated/build_manifest.json` over four
components:

- **config** — the output-relevant fields of `config.yaml` (source picks,
  scoring, identity; not the auto-managed `extensions` flags or `notes`).
- **custom** — the bytes of the four `custom/*.csv` override files.
- **slice** — the variety's own intake rows (Glottocode × transcription
  source), with Concepticon resolution folded in.
- **recipe** — the transform code (`variety.py`, `phonology.py`,
  `aggregate.py`), `score_weights.yaml`, and the merkmal version.

Re-running `update` with nothing changed skips every variety; re-ingesting
one source rebuilds only the varieties whose slice actually changed;
editing the build code (or `--force`) rebuilds all. Manifests live under
the gitignored `generated/`, so a fresh checkout rebuilds from scratch.

### Source universe and priority

Selection considers every source — all Lexibank datasets, GLED, and
Wiktionary. A priority floor keeps the noisier sources as pure
fallback:

| Priority | Sources | When they win |
|---|---|---|
| 1 | All Lexibank datasets | Always preferred; best composite score wins |
| 2 | GLED | Only when no Lexibank source covers the variety |
| 3 | Wiktionary | Only when neither Lexibank nor GLED covers it |

Fallback picks (priority 2–3) never rank above the `copper` tier.

### Variety dirs are config-only by default

`register` writes just `config.yaml`. The `custom/*.csv` templates are
scaffolded on demand with `build.py extend <av_id>` (keeps the tree
light at thousands of varieties). The build treats missing custom files
as "no extension".

## Exploring the data (`explore.py`)

A small console "database interface" over the aggregate output. It loads
`output/aggregate/*.csv` once into a local SQLite index
(`output/explore.sqlite`, gitignored) with the obvious indexes, then
answers queries instantly.

Run `python explore.py` with no arguments for detailed help with worked
examples for every command (and `python explore.py <command> -h` for one
command's own options).

```bash
python explore.py index                       # build/refresh the index (~25s; needs `aggregate` first)

python explore.py langs --family Indo-European # list varieties (filters: --family/--macroarea/--tier/--source/--search)
python explore.py lang Latin                   # all forms of a variety (av_id, Glottocode, or name)
python explore.py lang lati1261 --concept WATER
python explore.py concept WATER --family Indo-European   # a concept across varieties
python explore.py cognate --concept WATER      # cognate sets attested for a concept
python explore.py cognate iecor_335            # members of one cognate set
python explore.py form '水' --concept WATER     # search surface forms (Form/Value)
python explore.py concepts                     # concepts ranked by coverage
python explore.py stats --family Indo-European # summary statistics (omit --family for global)
python explore.py sql "SELECT tier, COUNT(*) FROM forms GROUP BY tier"   # read-only SQL
python explore.py info                         # tables, columns, build provenance
```

Notes:

* Every command takes `--limit N` (`0` = all) and `--csv` (full-fidelity,
  `\n`-terminated, pipe-friendly). The console view shows a curated column
  subset; `--csv` and `sql` emit all columns.
* `lang` resolves an av_id, a Glottocode, or a name (exact, then
  substring) and reports the resolution.
* Cognate identity is keyed on `canonical_cognate_id` when present, else
  the per-source `Cognacy` code (the canonical id is reserved and not yet
  populated).
* `descendants` is a stub: etymological descent links aren't in the schema
  yet (Wiktionary descendant chains aren't ingested); it points to the
  cognate commands, which are the nearest available relation.
* `sql` accepts a single read-only statement (`SELECT`/`WITH`/`PRAGMA`/
  `EXPLAIN`); writes are rejected and the connection is opened query-only.
* The index is rebuilt only when the aggregate CSVs change; other commands
  warn if the index is older than `output/aggregate/`.

## Variety config (`varieties/<av_id>/config.yaml`)

```yaml
av_id: ine-latin
name: Latin
glottocode: lati1261
family: Indo-European
macroarea: Eurasia
sources:
  transcription: kesslersignificance
  cognates: kesslersignificance
extensions:
  transcriptions: false
  forms: false
  cognates: false
  concept_map: false
scoring:
  forms_score: 0.9938
  cognates_score: 0.7000
  tier: bronze
pinned: false
notes: |
  auto: forms=kesslersignificance (0.99); cognates=kesslersignificance (0.70)
```

## Extension semantics

* **transcriptions.csv** — per-form column override matched by
  `source_form_id` or `Concepticon_ID`. Source row's other columns are
  preserved. Use for hand-cleaned phonology on top of source data.
* **forms.csv** — purely additive new rows (e.g. a form your source
  didn't include). Get auto-assigned `custom_<av_id>_<n>` IDs and
  `transcription_source=custom`.
* **cognates.csv** — per-`source_form_id` cognate column overrides.
* **concept_map.csv** — per-`Parameter_ID` Concepticon mapping fixes.

When custom columns are non-empty they override the source's; empty
columns leave source values intact.

## Phonology

Source segments are kept when present and merkmal-validated. Otherwise,
the form is re-segmented via merkmal's phoible inventory (greedy
longest match). `Segments_Source` in every output row records `source`,
`resegmented`, or `unclean`.

## Documentation

* `docs/BESTOF_SPECIFICATION.md` — design rationale, quality model,
  selection logic, cross-source cognate policy.
* `AGENT_NOTES.md` — current build state, known issues, conventions.

## License

* Code: MIT (`LICENSE`).
* Aggregated lexical data inherits per-dataset licenses from the
  sources it draws from (recorded in `metadata.csv`).
