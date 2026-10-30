# Evidence-bundle export

`python build.py export-evidence [<av_id> ...]` writes the framework's lawful `D`
object (`evidence_bundle`, histling framework `interchange.md` §3.1–3.3) from the
committed research web snapshot, together with two deliberately separate
partitions. Code: `src/arcaverborum/evidence_bundle.py`; tests:
`tests/test_evidence_bundle.py`; source-class table:
`src/arcaverborum/data/evidence_source_classes.csv`.

```bash
python build.py export-evidence                         # default ancient/historical IE set
python build.py export-evidence --list-default          # show the default selection and why
python build.py export-evidence ine-hittite ine-latin --exclude-licence nc,sa,gpl
python build.py export-evidence mix-isthmus-mixe mix-coatlan-mixe --name mixe   # NC-licensed rows, flagged
```

Output goes to `output/evidence/<name>/` (gitignored, like all generated
output; nothing generated is committed):

| File | Role | Contents |
| --- | --- | --- |
| `evidence_bundle.json` | `D` | Evidence, FormObs, SenseObs, lect-state candidates, retained conflicts |
| `door2_cognacy.json` | Door-2 hypotheses | Source cognacy partitions, loan flags, free-text source notes |
| `sealed/sealed_gold_proto.json` | sealed gold | Reconstructions and starred forms, for hide-the-witness evaluation only |
| `export_report.json` | report | Counts, licence breakdown, missing reading rules, content ids |

## Input and reproducibility

`raw/`, `intake/` and `output/aggregate/` are absent from a clean checkout, so the
exporter reads `web/data/manifest.json`, `catalog.json.gz` and the family shards
it needs. Each file is checked against the manifest SHA-256 (the export fails on
a mismatch), and `bundle.snapshot` records the manifest hash, build date,
catalog hash, aggregate-input hashes and every shard hash read. The same commit
therefore reproduces byte-identical output. Profile files referenced by
`pipeline_steps` are read from the working tree; each profile row is replayed
against the snapshot segments and the result is recorded in
`FormObs.profile_check` (zero mismatches in the default export).

## Selection

Explicit `av_id`s are exported as given. The default is derived from tracked
data, not a hard-coded list: Indo-European catalog varieties that have a
reviewed `custom/historical_evidence.csv` rule, or catalog first/last
documentation at or before 1500, or a stage name (Old, Middle, Early but not
Early Modern, Ancient, Classical). Each variety's reasons are recorded in
`bundle.selection`. `custom/reading_evidence.csv` (modern readings) does not
qualify a variety.

## Partitions (binding)

* **Expert cognacy is never `D`.** `Cognacy`, `cognate_sets`,
  `canonical_cognate_id`, `Alignment`, `Morpheme_Index`, `Segment_Slice`,
  `Doubt` and `Loan` go only to `door2_cognacy.json`: one named hypothesis per
  (cognate source, detection method), keyed to `form_obs_id`, with
  `prior_mass: null`, a `taint_label` of `conditional_on:<hypothesis_id>` and the
  rule that conditioning on it taints every downstream output and cannot confirm
  it (CONSTITUTION §11.2). Sets are not closed over unexported varieties.
* **Free-text source comments** (IE-CoR etymological notes cite reconstructions
  such as `*h₂éh₁s-`) are withheld from `D` and kept in the package's
  `source_notes`; Arca's own reading-rule JSON is parsed out of the comment first
  and becomes `Evidence.meta.reading_basis` etc. A source gloss containing a
  starred token is likewise withheld (`SenseObs.gloss_withheld`).
* **Proto-forms are never `D`.** Rows go to the sealed gold file when the
  variety is a reconstruction (`construction_kinds.csv` kind `reconstruction`, a
  `Proto-`/`-proto-` name, or a majority of star-prefixed Values — this catches
  e.g. `ine-indo-european`, `ine-germanic`, `ine-old-frankish`), when the row's
  reading basis is `source_reported_reconstruction` (Streitberg Gothic,
  Wiktionary period-pronunciation scopes, Baxter–Sagart Old Chinese), or when
  the Value or Form contains `*` (attested forms never do). A requested proto
  variety is listed under `selection.excluded_proto_varieties`.
  `--gold-scope` controls which proto varieties are swept in: `selected`,
  `family` (default: every proto variety in the selection's families) or `all`.
* `validate_bundle` runs before anything is written and refuses forbidden keys
  anywhere in the bundle, star-containing raw strings/forms/raw IPA/segments,
  star-prefixed gloss tokens, the reconstruction reading basis, the excluded
  source class, proto-variety references and unresolved ids.

## Field mapping

| Framework field | Source |
| --- | --- |
| `Evidence.source_id` | `transcription_source` |
| `Evidence.source_class` | `evidence_source_classes.csv`, keyed on (source, Segments_Source, reading_basis); most specific match wins (reading basis 4 > source 2 > segments source 1), ambiguity fails |
| `Evidence.cite` | catalog source `Citation` |
| `Evidence.raw_string` | `Value` (the source string); `Form` is in `meta.source_form` |
| `Evidence.modality` | the table's modality; `by_documentation` = `written_document` if catalog `last_documented` ≤ 1900, else `spoken` |
| `Evidence.date`, `collector`, `script_or_orthography` | `null`: Arca records no per-form date/collector; catalog documentation bounds live on the lect-state candidate |
| `Evidence.meta` | source ids, source version/URL, licence, reading basis + language stage + authority + notes, evidence role, representation basis, `source_class_rule`, volatile Arca row id |
| `FormObs.segment_hypothesis` | `Segments` split on spaces, `null` when empty (`blank_type: segment_hypothesis_absent`) |
| `FormObs.pipeline_steps` | `source_segments:<source>@<version>` + `merkmal_canonicalize:descriptive@unpinned`; or `profile:<path>@sha256:<16>` + one `flag:<grapheme>→<ipa> (<note>)` per FLAG-annotated profile rule the form uses (e.g. Hittite `flag:ḫ→x (→x (FLAG))`); or `resegment:merkmal_descriptive@unpinned` |
| `FormObs.provisional_variety_ref` | `av_id` (`lect_state_ref` stays `null`: variety ≠ lect-state) |
| `SenseObs.gloss_raw` | `source_gloss` |
| `SenseObs.concepticon_link` | Arca concept mapping, `weight: 1.0`, `role: q`, with the Arca `concept_id` and mapping review |
| `lect_state_candidates` | one provisional candidate per (av_id, reading-rule language stage) |
| `conflicts` | (variety, concept) pairs where two sources give different strings; retained, unresolved |

### Sigma (`arca_coarse_ordinal_v0`)

An ordinal 1–5, the maximum of three components; larger is less certain.

| Level | Label | Typical cause |
| --- | --- | --- |
| 1 | `supplied_transcription` | validated source segments, no historical reading basis |
| 2 | `derived_by_reviewed_conversion` | reviewed orthographic profile; reviewed lemma sources |
| 3 | `historical_or_lemma_reading` | historical reading basis; IE-CoR/LSI lemmata; any ASJP dependence |
| 4 | `mechanical_or_unvalidated` | resegmented, unclean, automatic transcription conversion |
| 5 | `no_segment_hypothesis` | written-only rows, orthographic transcription only |

Components: Segments_Source (source 1, profile 2, resegmented/unclean 4, empty 5),
reading basis (none/supplied pronunciation 1, upstream conversion 2,
historical readings 3, automatic conversion 4, orthographic only 5) and the
source-class `sigma_floor` from the table. Normalized classical lemmata never
fall below 3 (CONSTITUTION §3.6). SenseObs use 2 for a recorded mapping review,
3 for an unreviewed source mapping. The scale is coarse and uncalibrated.

### Licences

Every Evidence carries `meta.licence = {raw, spdx, flags, note?}` with flags
`nc`, `sa`, `nd`, `gpl`, `unrecorded`, `presumed`. Wiktionary rows record no
licence in Arca; they are marked `CC-BY-SA-4.0` with `presumed: true` and a
note (English Wiktionary text is CC BY-SA 4.0). Mixe-Zoque Voices is
CC-BY-NC-4.0; RVID infinitives (and DAG loans) are GPL-3.0. The default export
includes everything; `--exclude-licence` takes flags or SPDX ids, repeatable or
comma-separated, and applies to all three partitions.

### Stable IDs

`stable_id(prefix, *parts)` = `<prefix>-` + the first 24 hex digits of
SHA-256 over `"arcaverborum" ␟ prefix ␟ parts…` (␟ = U+001F).

| Object | Prefix | Parts |
| --- | --- | --- |
| Evidence | `av-ev` | `v1`, source, `source_form_id`, `source_pronunciation_id`, `av_id` |
| Evidence without a source form id | `av-ev` | `v1-content`, source, `av_id`, Value, Form, raw IPA, source parameter (`meta.id_basis` says which) |
| FormObs | `av-fo` | evidence id, Segments_Source, Segments, pipeline steps |
| SenseObs | `av-so` | evidence id, source parameter, concept id, source gloss |
| Lect-state candidate | `av-lsc` | `av_id`, language stage |
| Conflict | `av-cf` | `av_id`, concept, sorted FormObs ids |
| Sealed gold entry | `av-gold` | the evidence key |
| Door-2 hypothesis | `av-h2` | cognate source, detection method |

The aggregate's row `ID` embeds a shifting global row number, so it is kept only
as `meta.arca_row_id_volatile`. Container ids are content hashes
(`evidence_bundle:sha256:…`) over canonical JSON (sorted keys, compact
separators, UTF-8); the bundle hash excludes the `producer` code pin.

## Proposals for the framework

The framework leaves these open (`interchange.md` §5); the versions here are
minimal and should be read as proposals, not settled contract:

1. `reading_basis` is not a framework field. It is carried as
   `Evidence.meta.reading_basis` (+ `language_stage`, `reading_authority`) using
   Arca's nine-value vocabulary; the framework may want it typed on Evidence or on
   the decode/edition plate (§3.6).
2. Stable Evidence/FormObs id generation (above).
3. A Door-2 hypothesis record: `{hypothesis_id, kind, door: 2, producer,
   source_id, source_version, cite, detection_method, prior_mass, taint_label,
   sets: [{set_id, members: [{form_obs_id, …}]}]}` in a package that references
   the bundle id.
4. A sealed-gold record for hide-the-witness evaluation, referencing the bundle id.
5. `blank_type: segment_hypothesis_absent` for written-only evidence; concept-
   level absences (`not_in_source`, `unelicited`) are not emitted, because the
   snapshot cannot distinguish them.
6. Extension fields used here (listed in `bundle.conventions.extension_fields`):
   `FormObs.provisional_variety_ref`/`lect_state_candidate_ref`/`segments_status`/
   `profile_check`, `SenseObs.gloss_withheld`, and the extra keys on
   `concepticon_link`.

## Known limitations

* No reviewed historical reading rule exists for many selected IE-CoR stages
  (Old Norse, Old English, OHG, Church Slavic, Old Prussian, Gaulish, …). They
  are exported with `reading_basis_missing: true` and listed in
  `export_report.json`. Rules are not inferred, because the existing rules came
  from the AN01 reviewed identity audit, not from source metadata alone.
* A row whose Value mixes attested and starred alternatives (`āšḫar- / *āšḫan-`)
  goes to sealed gold whole; its attested half is lost to `D` until split upstream.
* Reconstruction-basis rows (e.g. Wiktionary Classical Latin) also carry an
  attested spelling; the binding rule routes the whole row to sealed gold.
* merkmal's version is not recorded in the snapshot (`@unpinned` steps).
* Profile steps cite the working-tree profile; the replay check detects drift
  but cannot recover an older profile.
