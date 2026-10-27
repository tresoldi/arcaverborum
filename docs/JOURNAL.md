# Project journal and working memory

## 2026-10-27 — Next coverage batch completed

Current baseline: **7,312 varieties / 2,066,017 forms**, 1,742,698 supplied-source
forms, 13,234 profile-supported forms, **464,736 supported core slots** and
538,833 mapped core slots. Core-source collection remains 892 varieties;
GLED primary selections remain 1,582. This batch adds **256 forms and 215
supported core slots**, without manufacturing new varieties.

All five agreed tracks were handled sequentially. Twenty new Media Lengua
sense mappings raise supported core 106 → 124. Staged dictionary reviews add
62 Iquito and 119 Guarayu decisions. Five North American supplements add 54
forms / 53 core slots. A source-scoped Iquito profile adds 26 forms / four
slots (125 → 129); 36 ambiguous senses remain held. Guarayu's transcription
issues prevent an active profile.

The missing-language screen found candidates but held them on provenance,
license, modality, transcription or identity grounds. NLS citations are
placeholders; Wust phylogenies lacks supplied segments and an explicit repository
license; Borch is already represented through a parent-coded Rutul member.
No new source namespaces were appended to active intake in this batch.

The new additive opportunity ranking found larger South American gains outside
the GLED-only scan. Reviewed Huber–Reed supplements add 104 Sikuani forms and
72 Hitnu forms, filling 71 and 69 slots: **Sikuani 76 → 147**, **Hitnu 79 → 148**.
A Spanish editorial note masquerading as a word, a playing-card heart, an old-man
noun mapped to an adjective, and insufficiently specific egg senses were held.

Important implementation changes: supplemental profiles use separate exact-form
files and guarded SHA256, retain Segments_Source=profile, and cannot affect the
primary source or reinterpret supplied IPA. The supplement compiler now accepts
explicit sources and merges partial reviews without erasing prior admissions.
Staged dictionary senses are validated even when not selected as a primary source.

Verification: **370 pytest tests**, full Ruff and JavaScript checks passed; all
7,312 accepted builds succeeded. A final freshness run rebuilt zero varieties.
All 400 compressed artifact hashes, seven core-pilot audits and the Vakh repair
audit passed. All 1,268 original primary forms across eight supplemented
constructions match the pre-batch exported evidence. Local generic and mixed-source
browser checks passed, including profile status, scholarly supplements and Core
isolation. Web artifacts were regenerated from the accepted aggregate.

See [the complete report](COVERAGE_BATCH_2026-10-27.md),
[metrics](coverage_batch_summary_2026-10-27.json), and
[ranked opportunities](coverage_opportunities_2026-10-27.csv). The current report
contains 6,838 member opportunities, including **635 South American** candidates.
They overlap and remain unreviewed; do not sum them as accepted gains. Next strong
review targets include Amahuaca (blumpanotacana), Puinave (IDS/Huber), Paraguayan
Guarani (IDS), Apurinã (Walker), Resígaro (Huber), and Baré (Walker).

Persistent user priorities and operational rules remain below. Asturian is still
**82 supported core concepts**, not the superseded 92/100. Pages deploys tracked
web artifacts; new raw repositories remain ignored. Old numeric export IDs may
shift with aggregate order; existing browser links resolve unique legacy source
identities. Pronunciation alternatives retain their persistent IDs.

## 2026-10-27 — Coverage, provenance and Americas follow-up

Baseline at that earlier batch: **7,312 varieties, 2,065,761 forms**, 1,742,468
source-supported forms, 13,208 profile-supported forms, 464,521 supported core
slots and 538,618 mapped core slots. There are 892 Core-source collection
varieties and 1,582 GLED primary selections. Discovery counts are not admissions.

### Persistent decisions

The goal is more languages, more coverage and better quality, reducing dependence
on GLED through better evidence. Prioritize the Americas, especially South
America. Evidence-based orthographic profiles are welcome for suitable languages
without IPA. Choose routine implementation details autonomously and carry agreed
tracks through sequentially.

Do not inflate variety counts using overlapping sources or pronunciation variants.
Keep raw evidence, transcription uncertainty, source identity, and expert versus
computed judgments distinct. Never infer pronunciation from unsupported spelling
or transfer cognate judgments between sources.

Website choices: All accepted varieties by default, Core as a named preset,
staged loading, selection-first comparison, restrained scholarly styling, readable
map borders and continents, and maps plus linguistic metadata on variety pages.

### Completed and published

* `5622ff27`: validated lexical expansion, strict unqualified Wiktionary IPA
  recovery, reviewed ABVD2026 upgrades and scholarly-source additions.
* `e9bfa9da`: normalization fingerprint tests explicitly cover both UTF8PROC modes.
* `46813603`: five-track follow-up, adding 3,288 forms and 153 supported core slots.
  Reviewed supplements improve Yurok, Chickasaw, Xavante, Apinayé and Xerente;
  their primary GLED records remain unchanged. Brazilian Portuguese gains 34
  scoped IPA alternatives for 21 concepts: supported core 128 → 149 in All
  accepted, while Core-source coverage remains 128.
* Media Lengua switches from two unsupported Wiktionary forms to 3,216
  source-segmented dictionary forms and 106 supported core slots. Preserve the
  dictionary's community variation and correct the upstream misattributed
  citation; no publication year was invented.
* Asturian gains 856 newly supported profile rows, while 458 formerly supported
  rows are withheld after correcting word-final-r handling. Net profile gain is
  398; **current supported core is 82/161**, superseding 92 and preliminary 100.
* Shared-sense rules increase 30 → 40; seven conflicts remain held. Source-local
  cognacy collisions are repaired in Chacon Tukanoan, UraLex and ABVD Philippines:
  41,119 accepted records affected, without inventing expert judgments.
* Web exports retain raw IPA, pronunciation tags, stable alternative IDs and
  mixed-source provenance. Core filtering operates per lexical row. Brazilian
  Portuguese no longer inherits misleading Portugal coordinates.

The full evidence and regeneration instructions are in
[the latest report](AMERICAS_COVERAGE_FOLLOWUP_2026-10-27.md) and
[its metrics](coverage_followup_summary_2026-10-27.json), following
[the previous expansion](DATA_EXPANSION_2026-10-27.md).

Verification at `46813603`: 346 pytest tests passed, Ruff and JavaScript checks
passed, all 7,312 builds succeeded, and a freshness rerun rebuilt zero varieties.
Seven core-pilot audits and the Vakh repair audit passed. All 400 compressed
artifact hashes were verified. Local and live generic/mixed-source browser tests
passed. CI run 40514968062 and Pages deployment 40514967948 succeeded; the public
manifest matched local counts and hashes. No deployment or approval was pending.

### Next opportunities and held evidence

1. Expand reviewed South American supplements and dictionary senses using the
   guarded ledgers, prioritizing genuine missing supported core slots.
2. Review staged Iquito, Guarayu and Tseltal dictionaries independently. They are
   staged, not accepted source switches: Iquito's sparse pronunciation values
   are orthographic reductions; Guarayu needs nasal/glottal, historical and
   dialect distinctions; Tseltal has sparse, multidialectal phonetic fields.
3. Extend regional pronunciation scopes only with explicit variety identity and
   complete homograph evidence. The 24,075 Brazilian Portuguese discovery
   lexemes are not automatically accepted forms. Preserve phonemic and phonetic
   alternatives rather than selecting convenient readings.
4. Resolve held shared senses and remaining cognacy conventions with source
   documentation. ACD/Sagart conventions were not blindly stripped or merged.
5. Extend orthographic profiles only where references justify the contrasts.
   Asturian x/y, unspecified glides and rhotics remain withheld. Higaonon is
   `wikt_mba` / `higa1237`; `wikt_hig` / `kamw1239` is Kamwe. The inactive
   Higaonon profile remains blocked, and its accepted GLED source is unchanged.

These are opportunities, not an authorization to admit unsupported data.

### Operational handoff

* Never run subset ingestion over active intake: it replaces tables. Stage under
  ignored `raw/curation/`, validate, and append new namespaces with
  `scripts/append_source_intake.py`; existing namespaces need guarded migration.
* Supplement source slices, member selectors, ledgers and phonology mode belong
  in fingerprints. Source drift must fail closed. Never silently refresh authored
  evidence hashes during compilation.
* Build accepted directories with existing `generated/forms.csv`. Orphan configs
  `sig-turkish-sign-language`, `sig-valencian-sign-language` and
  `urj-old-hungarian` do not establish acceptance.
* Use `.venv/bin/python` or `uv run --no-sync` to preserve locally installed
  merkmal; no generated uv.lock. Avoid assuming a UTF8PROC compile mode.
* After builds: aggregate, run `scripts/build_research_web.py`, audit and browser
  test, commit source plus web artifacts, push, verify CI/deployment and the live
  manifest. Pages deploys committed files, not regenerated intake.
* `web/core.html` is the archived Core 0.1.0 viewer. The current research
  explorer's Core-source preset and its concept filter are separate concepts.
* Large raw/intake/per-variety generated outputs remain ignored. Tracked web
  artifacts include catalog, 399 family shards, manifest and bibliography.

This tracked journal is the portable handoff. Local `memory/` is ignored;
archived memories in `~/work/meta` are read-only and must not be edited.
