# Per-Variety Build Specification

The project produces a per-variety lexical database. Each variety lives
in its own directory under `varieties/<av_id>/` with a configuration
file, optional custom data, and a generated output.

## Design constraints

1. **One winner per cell.** For each (variety, concept, form) cell, all
   transcription columns come from a single source. Cognate columns
   come from a (possibly different) single source.
2. **Two-block model.** Forms-block and cognates-block compete
   independently. A source is eligible for the cognates-block only when
   it also provides forms for the variety.
3. **Variety = av_id.** Glottocode (lowercased) is the default key.
   Custom entries (proto-languages, sub-Glottocode dialects, unmapped
   varieties) use "x-..." prefixed av_ids declared in
   `src/arcaverborum/data/variety_overrides.csv`.
4. **Pins beat the score.** `data/selection.csv` is the manual
   whitelist. Unpinned varieties auto-select the highest-scoring source.
5. **Custom data extends source data per-column.**
   `varieties/<av_id>/custom/transcriptions.csv` overrides specific
   columns by `source_form_id` or `Concepticon_ID`; empty cells leave
   the source value intact.
6. **All sources compete, with a priority floor.** Every Lexibank
   dataset, GLED, and Wiktionary is a candidate. Source priority:
   Lexibank = 1, GLED = 2, Wiktionary = 3. Selection restricts to the
   most-preferred priority tier that has a candidate, then ranks by
   composite score within it — so GLED/Wiktionary win only when nothing
   better covers the variety. Fallback picks never exceed `copper`.
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
│   └── concept_map.csv        per-Parameter_ID Concepticon fixes
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
| `scoring.forms_score` | float [0,1] | auto-computed |
| `scoring.cognates_score` | float [0,1] | auto-computed |
| `scoring.tier` | str | gold/silver/bronze/copper |
| `pinned` | bool | true = whitelisted, source choice locked |
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
Parameter_ID,Concepticon_ID,Concepticon_Gloss,concept_id,notes
```
Fixes wrong source concept mappings before any other processing. Correct
the Concepticon mapping (re-resolved to our `concept_id`) and/or pin a
`concept_id` directly.

## Quality model

`data/score_weights.yaml` defines per-block signal weights. Signals,
all in [0, 1]:

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

`src/arcaverborum/phonology.py` validates and re-segments via merkmal.

* Source segments are kept when present AND all tokens recognized.
* Otherwise, greedy longest-match resegmentation against the phoible
  inventory (3,142 graphemes).
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
build.py update [<av_id> ...] [--all] [--family X] [--macroarea Y] [--changed]
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
priority_score = form_density(n_forms) · (1 − forms_score)
```

so a variety with substantial data and a weak forms-block ranks highest;
tiny or already-good varieties sink. Code lives in `curation.py`; run
`aggregate` first.

**Tone is deferred.** A large share of `unclean` forms are blocked only by
tone marks (digits/superscripts/Chao letters) that the merkmal `phoible`
system does not yet tokenise. Tone handling is being added natively in
merkmal upstream — the build carries these forms as-is and does **not**
strip or rewrite them. The report's `pct_tone_blocked` column isolates the
cohort (a heuristic match on tone-like characters in `Segments`) so the
eventual recovery is measurable and tone-heavy varieties are excluded from
the manual-curation top.
