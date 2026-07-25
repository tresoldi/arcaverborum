# Arca Verborum — Onboarding (fresh local checkout)

This repo was migrated to local disk (`~/repos/arcaverborum`) from a
slow NAS mount. The code is complete and tested; the per-variety data
needs to be generated here (it's fast on local disk — minutes, where the
NAS took hours).

Read this top to bottom before touching anything. The companion design
doc is `docs/BESTOF_SPECIFICATION.md` — read it second.

---

## 1. What this project is

Arca Verborum is a **per-variety lexical database** for computational
historical linguistics. For each language variety it selects the best
available source for transcription and (separately) for cognate
judgments, with provenance, a per-form quality score, and hand-curatable
extensions.

### Data flow

```
fetch     → raw/<source>/...                 (downloaded; gitignored)
ingest    → intake/<source>/...              (pre-processed CSVs; gitignored)
bootstrap → varieties/<av_id>/config.yaml    (auto source pick per variety)
update    → varieties/<av_id>/generated/forms.csv  (gitignored)
aggregate → output/aggregate/...             (unified product; gitignored)
```

### The unit: a "variety"

- Keyed by `av_id` — the lowercased Glottocode by default. Custom
  entries (proto-languages, sub-Glottocode dialects, unmapped) use
  `x-...` av_ids declared in `src/arcaverborum/data/variety_overrides.csv`.
- Each `varieties/<av_id>/` holds `config.yaml` (source picks + scoring +
  notes) and, on demand, `custom/*.csv` extension files.

### Source universe + priority floor (key design)

Every source competes: all Lexibank datasets, GLED, and Wiktionary.
A priority floor keeps the noisier sources as pure fallback:

| Priority | Source | Wins when |
|---|---|---|
| 1 | any Lexibank dataset | always preferred; best composite score wins |
| 2 | GLED | no Lexibank source covers the variety |
| 3 | Wiktionary | neither Lexibank nor GLED covers it |

Fallback picks (priority 2–3) never exceed the `copper` tier.

Measured under the expanded universe: **7,301 varieties** selected
(5,106 Lexibank · 1,596 GLED · 599 Wiktionary). Kusunda (`kusu1250`)
resolves to the `aaleykusunda` source.

---

## 2. Repository layout

```
build.py                     CLI: fetch/ingest/register/extend/update/aggregate/status
scripts/bootstrap_varieties.py   one-shot: auto-register every selected variety
src/arcaverborum/
  catalog.py                 av_id catalog + enrich_glottocodes()
  ingest.py                  raw/lexibank → intake/lexibank
  score.py                   composite per-block quality signals (weights in data/score_weights.yaml)
  selection.py               source priority floor + auto-pick + pins
  phonology.py               merkmal-backed CLTS validation + re-segmentation (descriptive system)
  variety.py                 register / build_one / custom-data merge / scaffold_custom_files
  aggregate.py               union per-variety output into output/aggregate/
  report.py                  selection report JSON
  glottolog.py concepticon.py   loaders (cache to raw/ if present, else download)
  sources/{lexibank,gled,wiktionary,glottolog,concepticon}.py   fetchers + wiktionary pipeline
  data/                      score_weights.yaml, selection.csv (pins), *_overrides.csv
tests/                       pytest suite (77 passing)
docs/BESTOF_SPECIFICATION.md design spec
```

---

## 3. What's already here vs. what to generate

**Present (copied from the previous machine):**
- All code, tests, docs, config.
- `raw/wiktionary/raw.jsonl.gz` (2.4 GB kaikki dump).
- `intake/lexibank/` and `intake/wiktionary/` — the **pre-processed,
  validated** per-source CSVs. Lexibank intake was verified byte-for-byte
  against the previous merge (3,837,470 forms, 166 datasets); Wiktionary
  intake is 2,861,008 forms, 90.5% Glottocode-filled.

**Absent (regenerate only if needed):**
- `raw/lexibank/` — the 170 cloned CLDF repos. Only needed to *re-ingest*
  lexibank. The intake is already present, so you do **not** need this to
  build. To refresh later: `python build.py fetch --source lexibank`.
- `raw/glottolog/`, `raw/concepticon/` — caches. Downloaded automatically
  on first use; pre-populate with `python build.py fetch --source glottolog`
  / `--source concepticon` to avoid network during the build.
- `varieties/`, `output/` — generated below.

---

## 4. Environment setup

Python 3.11+ (developed on 3.14). merkmal (≥0.6.0) lives next to this
repo at `../merkmal` — install the Python package from its `python/`
subdir.

```bash
cd ~/repos/arcaverborum
python -m venv .venv && source .venv/bin/activate
pip install -e .                                   # pandas, pyyaml, requests
pip install -e ../merkmal/python                   # phonology library (separate repo)
python -c "import merkmal; print(merkmal.list_systems())"   # sanity check
pip install pytest ruff mypy          # dev tools (optional)
pytest tests/ -q                      # expect 155 passing
```

Dependencies are intentionally lean — **no CLDF ecosystem**
(no pylexibank/pycldf/cldfbench). Keep it that way.

---

## 5. First task: generate the per-variety data

The intake is present, so skip fetch/ingest and go straight to bootstrap.
On local disk this is minutes, not hours.

```bash
source .venv/bin/activate

# 1. Bootstrap every selected variety (config-only; ~7,301 dirs)
python scripts/bootstrap_varieties.py            # CLTS on; --no-clts-check to skip

# 2. Build per-variety output
python build.py update --all                      # writes generated/forms.csv per variety

# 3. Aggregate into one product
python build.py aggregate                         # → output/aggregate/{forms,varieties,parameters,metadata,sources.bib}

# 4. Sanity checks
python build.py status
python - <<'PY'
import pandas as pd
v = pd.read_csv("output/aggregate/varieties.csv")
print("varieties:", len(v))
print("kusu1250 present:", (v.av_id == "kusu1250").any())
PY

# 5. Commit the bootstrap (config-only configs; generated/ is gitignored)
git add -A varieties && git commit -m "Bootstrap 7,301 config-only varieties (expanded universe)"
```

Expect ~7,301 varieties. Verify Kusunda (`kusu1250`) resolves to
`aaleykusunda`.

### Curating a variety later

```bash
python build.py extend lati1261     # scaffolds varieties/lati1261/custom/*.csv templates
# edit custom/transcriptions.csv (override Segments by source_form_id),
#      custom/forms.csv (additive rows), custom/cognates.csv, custom/concept_map.csv
python build.py update lati1261      # rebuild — extensions auto-detected
```

Override semantics: matched per `source_form_id` (or `Concepticon_ID`);
non-empty cells override the source, empty cells leave it intact. See
`docs/BESTOF_SPECIFICATION.md` for the custom CSV schemas.

---

## 6. Open work (priority order)

1. **Run the first-task build above** and commit it. — *DONE* (7,301
   varieties built + aggregated; 2,043,862 forms; commit `ff0cecb`).
2. **Cross-source cognates**: when `cognate_source != transcription_source`
   the build still emits cognates from the transcription source. The
   `canonical_cognate_id` column is reserved for a future pass that
   unifies cognate set IDs across sources via form-string + concept
   overlap. Highest-effort item. (1,318 varieties currently have a
   cross-source pick.)
3. **Quality/curation report** — *DONE*. `build.py report` reads
   `output/aggregate/` and writes `output/report/curation.csv`
   (one row per variety, sorted by curation priority) +
   `curation_summary.json`. Priority =
   `form_density(n_forms) · (1 − forms_score)` — data-rich, weak varieties
   rank first; tiny or already-good ones sink. Columns surface tier,
   `pct_unclean`, `concept_coverage`, `pct_tone_blocked`, etc. Code in
   `curation.py`. Run `aggregate` first.
4. **Tone-aware phonology** — *handled by merkmal (≥0.6.0)*. merkmal
   attaches tone marks (digits/superscripts/Chao letters) to their
   syllabic nucleus via `merge_tone_digits` and validates the result, so
   tone-bearing forms now count as clean. The previously-deferred cohort
   (~197k forms, concentrated in Sino-Tibetan / Tai-Kadai / Hmong-Mien /
   Austroasiatic / Otomanguean) re-cleans on rebuild with no
   re-transcription. **Do not** add a preprocessing/strip pass here —
   `phonology.segments_are_valid`/`resegment` already merge tone digits.
   The curation report's `pct_tone_blocked` column now tracks only the
   residual (forms that are tonal *and* otherwise malformed).
5. **GLED/Wiktionary metadata in aggregate**: aggregate pulls
   metadata.csv + sources.bib from lexibank only. Minor gap.

---

## 7. Conventions

- KISS/DRY/YAGNI. No abstractions beyond need.
- No comments by default — only when the WHY is non-obvious.
- No legacy terminology ("Full"/"Curated"/"Expert-Cognates"/"best-of").
  Use varieties / intake / aggregate / fallback.
- Generated outputs are gitignored; commit config + custom data only.
- Challenge proposals that reintroduce traditional historical-linguistics
  concepts under formal dress.
- Sound change is directionally asymmetric — priors/inference should
  encode known asymmetries even though correspondences are stored
  bidirectionally.

---

## 8. Gotchas

- **Phonology uses the merkmal `descriptive` system** — the merkmal-native
  categorical engine that the downstream cognate toolchain (cognator,
  proteus) also defaults to. Validity is generative (base + diacritics
  derived compositionally), so well-formed IPA validates whether or not the
  exact string is attested; `tʃ`, `ʊˑ`, clicks, apical vowels and
  tone-bearing nuclei all pass. Source segments are **canonicalized** via
  `merkmal.normalize` (`phonology.canonicalize`): CLTS slash notation
  `a/b → b`, ligatures `ʤ → dʒ`, ASCII `:` → `ː`, stress stripped. See
  `phonology.SYSTEM`.
- **Wiktionary intake has no Glottocodes from the kaikki pipeline** —
  filled by `catalog.enrich_glottocodes()` (vectorised; ISO 639-3 or
  `wikt_<iso>` suffix → Glottolog) during ingest. Don't iterrows over
  2.86M forms.
- **`build_one` accepts a pre-loaded DataFrame** so `update --all` loads
  the (large) intake once and filters per variety — don't reintroduce a
  per-variety full read.
- **Two intake sources**: signal computation, catalog building, per-variety
  builds, and aggregation all read across `intake/lexibank` +
  `intake/wiktionary`.

---

## 9. Provenance

Migrated from `…/nas-dev/new_chl/arcaverborum` (branch `bestof-rewrite`,
which had 7 commits restructuring the project from the old merged-tier
design). Git history was intentionally not carried over — this is a fresh
repo. The previous design (merged Full/Curated/Expert-Cognates Lexibank
tiers, a browse site, and a Zenodo flow) was fully replaced by the
per-variety system described here.
