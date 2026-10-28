# Project journal and working memory

## 2026-10-28 — Five South American coverage tracks completed

Current baseline: **7,314 accepted varieties / 2,067,154 forms**; 1,743,541
supplied-source forms, 13,528 profile forms, **465,590 supported core slots** and
539,683 mapped slots. This batch adds **700 forms / 472 supported slots**.
GLED primary selections **1,582 → 1,580**. Core-source collection membership
**892 → 896**, as four constructions now contain TuLeD rows; its row-level
source policy is unchanged. Frozen vocabulary remains 3,787 concepts.

All five agreed tracks completed in order:

1. Guaraní +72 forms / core102→153; Hoti +51 /103→148; Yurutí +52 /96→143.
   Exact IDS and Huber members reviewed. IDS remains provisional CLTS conversion;
   Hoti repeated four/five alternatives, generic day/egg and bare fear held.
2. Mandahuaca +45 /41→86; Yine +44 /71→115. Walker source identity, bound
   morphology and source-specific cognacy retained; generic egg held.
3. Sateré-Mawé +45 /92→136; Tocantins Asurini +45 /93→133; Guarayu +46
   /100→139; Karitiâna +49 /113→153. TuLeD supplied segments/cognacy retained.
   Three generic eggs and Mawé posture ambiguity held. No Guarayu dictionary
   profile activated.
4. **Xerénte and Xavánte replace GLED as primary** with the licensed 2025 Jê
   study supplement and exact-form phonemic profiles. Xerénte159 total forms,
   120 study-profile forms, core36→71; Xavánte154 forms, 107 study-profile,
   core35→61. All84 GLED forms and two Wiktionary records remain separately
   attributed. Primary profiles never apply to secondary sources.
5. **Ingain admitted as nub-ingain**, canonical language inga1254, no earlier
   accepted sample/alias found:24 profile forms /22 concepts /16 core. Other
   screened Jê source codes are dialect cases under accepted languages; no
   language-count inflation.

New namespace gerardije2025: author repository TGH-2020/Je_Phylogeny, commit
8f4f0a9a7b36ba4e3a9a15ba49b13056cfbbcf1e; explicit CC BY4.0; supplementary
data doi:10.5281/zenodo.15041553, related article10.12688/openreseurope.19346.3.
368 mapped source rows reviewed:251admitted /117held. Raw notation is NOT
silently supplied IPA: all251 readings are explicitly profile-derived broad
phonemic values. Nikulin2020§1.4 pp50–53 documents notation. Ambiguous
c/ĵ/j/r/y, circumflexes, shielding alternatives, leading diacritics, missing
values and unsplit compounds held; NFC preserves nasalization/length. Original
automatic COGID/COGIDS survives only in provenance, no accepted cognacy inferred.
Dataset citation does not invent individual fieldwork authorship. Xerénte CROSS
is corrected to traverse: original Nikulin2020p453 tbro glossed atravessar,
not the geometric noun. Source label and full raw row retained.

Source manifest/review under src/arcaverborum/data/je_original_*. Materializer
and scripts/stage_je_original.py --fetch --write-profiles verify frozen TSV,
README and license hashes; default stage outside intake. Only this new namespace
appended; existing namespaces preserved. Intake DB7,181,640rows. Never subset
ingest active intake or append an existing namespace; refresh requires guarded
migration. Generic source fetch materializes the frozen source, no moving pull.

Verification: **408 tests**, full Ruff/JS, seven core-pilot/Vakh audits pass.
All7,314 outputs fresh, zero failures. All1,922 earlier affected records preserve
lexical/transcription/concept/cognacy evidence; primary replacements have expected
annotation/score/tier changes. All400 compressed hashes verified. Local generic
and mixed-source browser tests pass, including Ingain and retained GLED exports.
Web artifacts rebuilt. Asturian remains82 supported core. NLS/Tangam blockers
remain. Independent specialist review of draft packets remains welcome.

See [batch report](SOUTH_AMERICA_COVERAGE_2026-10-28.md),
[metrics](south_america_coverage_summary_2026-10-28.json), and
[updated triage ranking](south_america_opportunities_2026-10-28.csv).

## 2026-10-27 — Amazonian expansion and original-source Bangru admission

Current baseline: **7,313 accepted varieties / 2,066,454 forms**; 1,743,092
supplied-source forms, 13,277 profile forms, **465,118 supported core slots** and
539,211 mapped core slots. This batch adds **437 forms / 382 supported slots**,
including one genuinely new accepted language. GLED primary selections remain
1,582 and Core-source membership remains 892.

All five agreed tracks were completed sequentially:

1. Amahuaca: 80 Blum-source supplements, supported core **79 → 147**; two
   chest/breast entries held. English/Spanish senses and original Hyde citations
   retained; no new genealogical claims inferred.
2. Puinave: 63 additions, **96 → 159**. Huber preferred for overlaps; six IDS
   records fill separate gaps. IDS conversion remains explicitly provisional.
3. Apurinã: 54 additions, **50 → 102**; Resígaro: 51, **97 → 146**; Baré: 47,
   **65 → 112**. Bound forms/source cognacy retained; old-man, egg and playa
   ambiguities held rather than forced into core meanings.
4. Media Lengua: 220 new selected sense decisions; 397 total mappings, 331
   mapped concepts, supported core **124 → 132**, with all lexical records
   preserved. Iquito: 44 new sense decisions, short n+i context clarified,
   profile forms **26 → 69** (43 added), 425 total forms, core still 129.
   There are 106 reviewed Iquito senses, 69 admitted / 37 held. Mixed-tone long
   vowels and s/ʃ uncertainty remain held. Earlier dated review CSV is preserved;
   default regenerable reports now go under ignored output/report/.
5. **Bangru admitted as sit-bangru**: 99 supplied-IPA forms, 95 core concepts,
   one consistently identified speaker A (Pisa Chachung), Sarli 2013 fieldwork.
   Original Bodt Zenodo deposit **1116263**, explicit CC BY 4.0, bypasses no
   restrictions and does not license the Wust derivative. All 119 reviewed PDF
   spans verified against frozen document hashes; 95 entries admitted / 24 held.
   Every supplied alternative retained. Comparative languages, tentative roots,
   optional readings and unreviewed notation are not admitted as Bangru data.

Bangru canonical code is bang1369; the source's Sarli dialect leva1238 belongs
to it and was not already accepted. Glottolog map coordinates are regional
reference points, not speaker GPS. Source manifest, authored entries, fetch
handler and staging/audit script are tracked. Document fetch never attempts Git;
source-version metadata supports Source document provenance. The original
source's tʃ/dʒ are tied for segmentation using the author's documented inventory;
raw IPA, tone, phonation, length and nasalization are retained. No cognacy inferred.

Only the new bodtbangru namespace was staged, validated and appended to active
intake, then intake-db rebuilt. Existing namespaces were not subset-ingested.
Full original PDF SHA256:
61760ad451c9594d7d82bb04fa24b392c592cb88f0d153cd8a90e813c816a9fa.
Optional PDF audit used PyMuPDF 2.0. Other candidates remain held: NLS attribution
is anonymous/year 0000 and related survey literature cannot be grafted onto the
rows; Chhulung sample/location labels need reconciliation; Tangam original
lexical evidence/redistribution remains unresolved.

Verification: **384 tests**, full Ruff and JS checks pass; 7,313 accepted outputs
are fresh (zero rebuilds/no failures); seven core-pilot and Vakh audits pass;
all 400 compressed hashes verified. All 1,719 original primary forms in six
supplemented constructions match prior exported evidence. Media Lengua's 3,216
lexical/transcription records and previous mappings are preserved. Local generic
and mixed-source browser checks pass, including Bangru source evidence and
69 Iquito profile records. Web artifacts regenerated from the accepted aggregate.

See [the full report](AMAZONIAN_EXPANSION_2026-10-27.md),
[metrics](amazonian_expansion_summary_2026-10-27.json),
[ranked follow-up](amazonian_expansion_opportunities_2026-10-27.csv), and
[remaining language blockers](amazonian_expansion_missing_languages_2026-10-27.csv).
The ranking has 6,831 member opportunities, including **628 South American**
candidates; these overlap and are not promised gains. Asturian remains 82 core.

## 2026-10-27 — Next coverage batch completed

Baseline at that earlier batch: **7,312 varieties / 2,066,017 forms**, 1,742,698 supplied-source
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
