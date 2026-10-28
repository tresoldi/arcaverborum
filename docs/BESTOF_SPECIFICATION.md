# Per-Variety Build Specification

The project produces a per-variety lexical database. Each variety lives
in its own directory under `varieties/<av_id>/` with a configuration
file, optional custom data, and a generated output.

This document describes current build mechanics. The planned language
curation workflow, including authority recipes, Arca-derived layers, and the
intended source-priority revision, lives in
`docs/CURATION_WORKFLOW_SPECIFICATION.md`.

## Current supplementation and planning entry points

Current accepted builds use explicit config source/member selections and guarded
custom data. An accepted construction can combine its primary with individually
reviewed source supplements (`custom/supplements.csv`); each row retains its
source identity, semantics, transcription status and cognacy scope. Supplemental
profiles are separately scoped and hashed. See `src/arcaverborum/supplements.py`
and the current [coverage workflow](workflows/arca-coverage-planning/SKILL.md).

Historical automatic selection/priority/tier policies below are original design
context. The legacy bootstrap path currently references a removed selection
module; it is not the active mechanism for accepting a curation batch. The
build consumes config/custom choices, and recipes/packets document them.
[STATUS](STATUS.md) and [NEXT](NEXT.md) hold the current baseline and priorities.

## Design constraints

1. **One accepted construction per variety.** The current build emits one
   selected construction for each variety. In the implemented v1 mechanics,
   the primary transcription comes from one selected source, with guarded
   additive source supplements. Source-specific cognacy is retained separately;
   cross-source cognate reconciliation remains reserved for later.
2. **Two quality dimensions.** Config records forms and cognate scores;
   per-form quality is computed through `forms_schema.py`. A separate configured
   cognate-source label does not imply reconciled cross-source judgments.
3. **Variety = av_id.** `av_id` is Arca's frozen primary key, assigned in
   `src/arcaverborum/data/varieties.csv`. It normally has the form
   `<family_code>-<name_slug>`, e.g. `ine-latin`; Glottocode remains a
   mapped external column.
4. **Explicit accepted sources.** Current builds read the selected source,
   exact member filters and pinned status from `config.yaml`. The historical
   `selection.csv` whitelist and automatic ranking policy do not replace a
   reviewed config/custom admission.
5. **Custom data extends source data per-column.**
   `varieties/<av_id>/custom/transcriptions.csv` overrides specific
   columns by `source_form_id` or `Concepticon_ID`; empty cells leave
   the source value intact.
6. **Historical automatic priority policy.** The original selector used
   Lexibank = 1, GLED = 2, Wiktionary = 3, then composite scores within a
   priority tier. This describes the original selection design. Current curation
   prefers strong lexical evidence, treats Wiktionary as a research/fallback
   source, and reduces GLED dependence through reviewed config/custom choices.
7. **Variety dirs are config-only by default.** `register` writes just
   `config.yaml`; `custom/*.csv` templates are scaffolded on demand
   (`build.py extend`). Missing custom files mean "no extension".

## Variety directory

```
varieties/<av_id>/
├── config.yaml
├── custom/
│   ├── transcriptions.csv     col override; matched by source_form_id
│   ├── forms.csv              additive new rows
│   ├── cognates.csv           per-source_form_id cognate overrides
│   ├── concept_map.csv        per-Parameter_ID Concepticon fixes
│   ├── supplements.csv        reviewed, guarded source-form admissions
│   ├── profile.tsv            primary source profile
│   └── supplement_profiles/  source-specific supplemental profiles
└── generated/
    └── forms.csv              gitignored — written by build.py update
```

### `config.yaml` schema

| Field | Type | Notes |
|---|---|---|
| `av_id` | str | matches directory name |
| `name` | str | from Glottolog or custom catalog |
| `glottocode` | str | "" for proto-languages |
| `family`, `macroarea` | str | from Glottolog |
| `sources.transcription` | str | dataset name from intake |
| `sources.cognates` | str | dataset name; usually equals transcription |
| `extensions.transcriptions` etc. | bool | true if `custom/*.csv` has rows |
| `scoring.forms_score` | float [0,1] | accepted construction base score |
| `scoring.cognates_score` | float [0,1] | accepted cognacy assessment |
| `scoring.tier` | str | gold/silver/bronze/copper |
| `pinned` | bool | reviewed/manual source-selection marker |
| `notes` | str | free-form |

### Custom CSV schemas

`transcriptions.csv`:
```
Concepticon_ID,source_form_id,Value,Form,Segments,Comment,notes
```
Match by `source_form_id` (preferred) or by `Concepticon_ID` alone.
Non-empty cells override; empty cells preserve source values.

`forms.csv`:
```
concept_id,Concepticon_ID,Value,Form,Segments,Cognacy,Loan,Comment,notes
```
Additive only. Give a `concept_id` (preferred) or a `Concepticon_ID` to
resolve one; forms get auto-assigned IDs `custom_<av_id>_<n>` and
`transcription_source="custom"`.

`cognates.csv`:
```
form_id,Cognacy,Alignment,Cognate_Detection_Method,Doubt,notes
```
Match by `source_form_id`.

`concept_map.csv`:
```
Parameter_ID,Concepticon_ID,Concepticon_Gloss,concept_id,action,notes,source_form_id,expected_form
```
Fixes wrong source concept mappings before any other processing. Correct
the Concepticon mapping (re-resolved to our `concept_id`) and/or pin a
`concept_id` directly.

`action` is optional and defaults to `map`. `unmap` keeps the lexical form,
transcription, source IDs and provenance while leaving both concept identifiers
empty. It blocks parameter-index fallback, so a rejected sense cannot silently
regain its old mapping. An `unmap` row must leave the three concept fields empty;
unknown actions are rejected.

An optional `source_form_id` restricts the correction to one translation and
takes precedence over a parameter-wide correction. Supply `Parameter_ID` and
`expected_form` as identity guards: a reused source ID with a different parameter
or spelling fails the build. This allows one incorrect translation to be
unmapped while other translations of the same English sense remain accepted.
Disappearance of a reviewed source-form ID also fails rather than silently
dropping its correction.

The five Wiktionary profile pilots keep authored decisions in
`custom/core_review.csv`, with optional `custom/form_review.csv` for individual
translations. `python scripts/audit_core_pilots.py --write-maps` compiles these
records into concept-map corrections. After rebuilding the pilots, run the
same command without flags to check source-sense drift, review completeness,
and emitted concept IDs. It writes `output/report/core_audit.json`, including
remaining GLED core gaps and the number supported by clean transcriptions.
The review checks English sense compatibility with frozen definitions;
translation, dialect and inflection accuracy still need specialist review.

## Quality model

`src/arcaverborum/data/score_weights.yaml` defines per-block signal
weights. Signals, all in [0, 1]:

| Signal | Block | Computed as |
|---|---|---|
| has_segments | forms | fraction with non-empty Segments |
| clts_compliant | forms | fraction whose tokens are recognized by merkmal |
| concepticon_mapped | forms | fraction with non-empty Concepticon_ID |
| concept_coverage | forms | min(distinct concepts / 200, 1) |
| loan_annotated | forms | 1 if Loan column has any non-null value |
| form_density | forms | log10(N+1)/log10(500), capped |
| has_cognates | cognates | fraction with non-empty Cognacy |
| expert | cognates | fraction with Cognate_Detection_Method == 'expert' |
| alignment_present | cognates | fraction with non-empty Alignment |
| partial_cognacy | cognates | 1 if dataset has Morpheme_Index or Segment_Slice |

Tier bands (forms_block score thresholds):

* gold — pinned + both block scores ≥ gold threshold
* silver — pinned, otherwise
* bronze — auto-selected, forms_score ≥ bronze threshold
* copper — auto-selected, lowest band

## Phonology

`src/arcaverborum/phonology.py` validates and re-segments via merkmal's
`descriptive` system (the merkmal-native categorical engine shared with the
downstream cognate toolchain). Validity is generative — features are derived
compositionally from base + diacritics — and tone digits are merged onto
their nucleus before checking.

* Source segments are canonicalized to clean BIPA via `merkmal.normalize`
  (CLTS slash `a/b → b`, ligatures `ʤ → dʒ`, ASCII `:` → `ː`, stress
  stripped), plus Arca source aliases such as `mb → ᵐb` and `nd → ⁿd`,
  and kept when all tokens are recognized.
* Otherwise, resegmentation via merkmal's IPA tokenizer (`segment_ipa`).
* `Segments_Source` records `source`, `resegmented`, or `unclean`.

## Cross-source cognates

When `cognate_source != transcription_source`, the variety's selection
still emits cognates from `transcription_source` for v1. The
`canonical_cognate_id` column is reserved for a future pass that
unifies cognate IDs across sources via form-string + concept overlap.
The selection report flags cross-source picks for review.

## Output schema

`varieties/<av_id>/generated/forms.csv` and the aggregate
`output/aggregate/forms.csv` share the same 28-column schema. Concept
identity is our `concept_id` + clean `concept_label`; `Concepticon_ID` is
retained as the external mapping (`Concepticon_Gloss` is dropped — the
clean label lives in the concept registry):

```
av_id, Glottocode, Variety_Name,
concept_id, concept_label, Concepticon_ID,
Value, Form, Segments, Segments_Source,
Cognacy, canonical_cognate_id,
Alignment, Morpheme_Index, Segment_Slice, Doubt,
Cognate_Detection_Method, Cognate_Source,
Loan, Comment,
transcription_source, cognate_source,
source_form_id, source_language_id, source_parameter_id,
bibtex_key, quality_score, tier
```

## CLI

```bash
build.py fetch [--source SOURCE]
build.py register <av_id>
build.py update [<av_id> ...] [--all] [--family X] [--macroarea Y] [--force]
build.py aggregate
build.py report
build.py status
```

## Curation report

`build.py report` reads the aggregate product and writes
`output/report/curation.csv` (one row per variety) and
`curation_summary.json`. It surfaces the weak end of the database so
hand-curation can be aimed where it pays off.

Per-variety columns include `tier`, `n_forms`, `n_concepts`,
`concept_coverage`, the segment split (`pct_clean` / `pct_resegmented` /
`pct_unclean`), `pct_tone_blocked`, `pct_cognacy`, and a `priority_score`.
Rows are sorted by descending priority, defined as

```
priority_score = form_density(n_forms) · ((n_unclean − n_tone_blocked) / n_forms)
```

so a variety with substantial data and many hand-fixable unclean forms ranks
highest; tiny, clean, profiled, or only residual tone-malformed varieties
sink. Code lives in `curation.py`; run `aggregate` first.

**Tone is handled.** merkmal (≥0.9.0) attaches tone marks
(digits/superscripts/Chao letters) to their syllabic nucleus
(`merge_tone_digits`) and validates the result, so tone-bearing forms count
as clean. The build carries forms as-is and does **not** strip or rewrite
them. The report's `pct_tone_blocked` column now isolates only the residual
(forms that are tonal *and* otherwise malformed), via a heuristic match on
tone-like characters in `Segments`.
