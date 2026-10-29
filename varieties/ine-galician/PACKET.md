# Curation Packet — Galician (`ine-galician`)

## Current construction — core-sense audit, 2026-10-24

Accepted base: Wiktionary with the documented spelling/dictionary profile and
explicit concept corrections. Tier remains **copper**. This audit checks
English source senses against frozen concept definitions; it does not certify
native translation accuracy, dialect identity, or inflection choices.

| Current metric | Value |
|---|---:|
| Forms (none deleted) | 36,368 |
| Forms with a concept ID | 7,116 |
| Distinct mapped concepts | 2,315 |
| Core concepts | 150/161 |
| Core concepts with supported IPA | 145/161 |
| Profile-derived forms | 889 |
| Unclean forms | 35,479 |
| Reviewed source parameters | 313 |
| Remapped parameters | 16 |
| Explicitly unmapped parameters | 99 |
| Provisional senses needing specialist review | 7 |

Before this audit the profile pilot covered 151 core concepts,
147 with supported IPA. Changes distinguish actual recovery
from removal of false coverage claims. Mechanical scores were recomputed on
the corrected construction; they do not confer specialist review.

## Applied decisions and pronunciation evidence

Animal horn (`corno`, `corna`, `hasta`) is recovered. New exact dictionary
lookups cover those three spellings and `vostede`; the tracked evidence now
contains 417 spellings and 318 supported exact-form mappings. Previous
pronunciation facts are retained even when a sense is no longer core.

The source-only sharp slot referred to a raised musical note, and thick
referred to density or viscosity. These did not establish the frozen cutting
edge or physical-thickness concepts. Their removal lowers the apparent core
count. Dictionary-supported right previously came from archaic straight;
correct right-side phrases remain mapped but lack supported pronunciation.
All 37 concepts in the previous GLED construction now have supported IPA.

Other explicit collisions include the World Health Organization versus who,
a barking sound versus tree bark, book leaves versus plant leaves, grain
ears versus hearing organs, needle eyes versus anatomical eyes, river mouths,
board-game men, metaphorical fruit and musical sharp. Each changed sense is
recorded with its original source text; no form is deleted. Concepts such as
chest, fishbone, fruit stone, temporal shortness and density use existing
non-core frozen slots where the definition matches. Coffee without milk is
not forced into a guessed alternative concept.

Authored decisions are in `custom/core_review.csv`; `concept_map.csv` is their
compiled correction layer. `action=unmap` retains lexical rows and provenance
while blocking both concept identifiers and parameter-index fallback.

Run `python scripts/audit_core_pilots.py --write-maps` to reproduce corrections,
rebuild the pilots, then run `python scripts/audit_core_pilots.py` to validate
review completeness, source text/mapping drift and built concept assignments.
The checker writes `output/report/core_audit.json`.

## Remaining work

Missing concepts from the previous GLED construction: none.
Missing with supported IPA: none.
These are explicit recovery targets; related noun senses or GLED strings are
not silently substituted for missing verbs or independently verified sources.

Retained provisionally, with scope/aspect or grammatical interpretation still
requiring specialist review:

- all (adv): wholly
- bite (verb): hold something by clamping one’s teeth
- come (verb): to arrive, to appear
- open (verb): to make accessible to customers
- seed (noun): any small seed-like fruit
- short (adj): of a person, of comparatively small height
- throw (verb): to eject or cause to fall off

Review the native translations and regional/grammatical forms against matched
lexical references before raising the tier. Spelling coverage and valid IPA
symbols alone do not establish correct meanings.

## Initial source review — 2026-10-23, historical

The following records the initial pilot. Its counts and follow-up lists are
superseded by the current audit above; transcription conventions and cited
references remain the basis unless explicitly amended.

### Accepted construction

Wiktionary intake (`wikt_gl`, Glottocode `gali1258`) with **dictionary-supported
exact-form pronunciations**, selected as a core-coverage pilot on 2026-10-23.
The authority recipe remains draft pending specialist review. This is not a
fully transcribed 36,368-form dictionary. Most of the non-core tail deliberately
remains unclean. The mechanical forms score is 0.3521 and the tier remains
**copper**; the much stronger core slice must not imply whole-variety quality.

`config.yaml` consumes `custom/profile.tsv`. Every rule is anchored `^form$`:
only that complete NFC-normalized spelling can use it. Unknown words and
unknown phrases cannot inherit pronunciations by concatenating known words.
There are no generic letter-to-IPA rules and no redundant transcription
column overrides. Explicit source IPA still takes precedence over the profile.

### Coverage and quality

| Metric | Previous GLED | Wiktionary + dictionary profile |
|---|---:|---:|
| Forms | 39 | 36,368 |
| Mapped concepts | 39 | 2,310 |
| Core concepts represented | 37/161 | 151/161 |
| Core concepts with supported IPA | 37/161 | 147/161 |
| Forms with profile-derived IPA | 0 | 874 |
| Forms deliberately left unclean | 0 | 35,494 |
| Forms with cognacy annotations | 39 | 13,867 |

Diagnostics were recomputed from local intake/build on 2026-10-23. There are
7,251 mapped forms. The candidate gains 115 mapped core concepts and loses
one GLED concept, `bod-horn`; counting only dictionary-supported IPA, it gains
111 core concepts and still loses only `bod-horn`. The four additional mapped
core concepts lacking supported IPA are not counted as pronunciation gains.
Sources are not merged.

These are source-mapping counts, not a semantic review of every entry. The known letter-name false match is corrected in `custom/concept_map.csv`:
`i` / `i latino` maps to `lng-character`, preserving `eu` as first-person
`kin-i`. The exact source parameter definition is “i (noun): name of the
letter I, i” in `intake/wiktionary/parameters_raw.csv`; that parameter affects
only those two Galician forms. The frozen CHARACTER definition is a written
symbol, whereas the separate LETTER concept denotes a posted text.

The coffee-without-milk sense of `só` still has the upstream BLACK mapping;
its applicability to the general color concept needs sense review. It is
not remapped to ALONE merely because the spelling has another lexical use.
Other gloss matches, inflections, synonyms, names, and phrases likewise need
review before research use.
Concept filtering alone is not a guarantee that each sense is appropriate.

### Why a dictionary profile

Galician spelling does not determine all vowel qualities: even accented `é`
and `ó` can denote different mid-vowel qualities. A five-vowel transliteration
would therefore invent distinctions or erase them. Initial/intervocalic
rhotics, final nasals, diphthongs, and lexical `x` readings also make an
unqualified substring profile inappropriate for the full intake.

The [ILG Dicionario de pronuncia da lingua galega](https://ilg.usc.gal/pronuncia/)
provides a documented standard, formal-register pronunciation model. The
[project description](https://ilg.usc.gal/es/node/484) identifies Xosé Luís
Regueira as director and the printed RAG dictionary (2010) as its basis.
The [dictionary criteria](https://ilg.usc.gal/pronuncia/criterios.html) explain
that this model excludes gheada and seseo, retains palatal lateral
transcriptions, and may list preferred and alternative pronunciations.
The [Galician Council of Culture's phonology overview](https://consellodacultura.gal/especiais/loia/gramatica.php?idioma=2)
describes the orthographic vowel ambiguity.

### Dictionary reconciliation and provenance

`scripts/galician_dictionary.py` looks up the **413 distinct core spellings**
(545 intake rows), using two bounded workers and a local cache. Exact
headword matching excludes similarly spelled entries. Superscript homograph
numbers are ignored for spelling comparison but dictionary entry IDs remain
separate. A pronunciation is accepted only if a validated segmented reading
is shared by **every returned homograph**; when alternatives remain possible,
the first dictionary reading in that common set is used. This preserves an
attested reading rather than inferring vowel quality.

- 314 headwords yielded validated exact-form mappings.
- 94 had no exact dictionary match.
- Five (`corda`, `ese`, `que`, `testa`, `á`) had incompatible homograph
  pronunciations or unresolved alternatives and remain unsupported.

`custom/pronunciation_evidence.csv` records each spelling, exact query URL,
lookup date, entry IDs, original IPA readings, decision, and segmented
output. Original IPA, including stress and alternatives, remains in that
file. The profile removes primary/secondary stress before tokenization,
consistent with Arca's segment representation, while retaining attested
vowel-quality diacritics. All output tokens validate with merkmal.

The script can reproduce the profile offline directly from tracked evidence;
ignored query caches live under `raw/curation/galician-ilg/`. Running
`.venv/bin/python scripts/galician_dictionary.py --fetch` requests only
previously uncached/unrecorded core forms. It never guesses a missing reading.
Profile entries can also benefit repeated identical spellings elsewhere in
intake, explaining the 874 covered rows rather than only the 545 core rows.

### Cognates and limitations

Wiktionary cognacy retains its `wiktionary_etymology` method and
`wiktionary_kaikki2026` provenance. These are etymology annotations, not expert
comparative cognate judgments. GLED cognates were not transferred onto new
forms. Segment-profile success means the spelling has a supported dictionary
reading; it does not validate the Wiktionary sense, dialect attribution, or
etymology. Dictionary standard-register choices do not cover Galician's full
geographical variation. This is a partial core-focused construction.

### Follow-up

Disambiguate the five homograph conflicts against source sense/POS evidence;
review missing dictionary headwords and the four core slots still without
supported IPA; recover `bod-horn` through a reviewed lexical addition or named
derived layer; correct gloss-based concept mismatches. Extend pronunciations
only with exact attested evidence or a separately evaluated contextual
transcriber, rather than assigning unknown mid-vowel quality by default.

## Worldwide follow-up — 2026-10-29

Accepted 36368 records; 146/161 supported core concepts. Primary: `wiktionary`.
[Execution, sources, gains and holds](../../docs/WORLDWIDE_FOLLOWUP_EXECUTION_2026-10-29.md).
Earlier evidence and source-specific cognacy remain; six precise shared English-sense
rules correct older mappings where applicable. Source conversions are not independent
IPA elicitation, profiles are finite and source-specific, and written-only records
add no phonetic support. Config and guarded custom ledgers enforce acceptance.
