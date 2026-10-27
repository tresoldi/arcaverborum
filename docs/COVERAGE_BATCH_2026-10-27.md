# Coverage batch: dictionary senses, American supplements and source-scoped profiles

This follow-up to [the earlier Americas batch](AMERICAS_COVERAGE_FOLLOWUP_2026-10-27.md)
works through five tracks in order, then uses the new ranking to review two
additional South American pilots. It adds **256 forms and 215 supported core
slots**, keeping **7,312 accepted varieties**. No new language count is claimed
for overlapping sources, dialect codes or unqualified candidates.

## 1. Dictionary senses

Twenty additional Media Lengua source senses, checked with accompanying
Spanish/Quichua translations and frozen definitions, raise supported core coverage
**106 → 124/161**. The 3,216 supplied-segment records are unchanged; 177 guarded
sense mappings now cover 144 concepts. General day, verbal rain/thunder and the
noun labelled “heavy” remain outside incompatible frozen concepts.

The staged Iquito and Guarayu dictionaries gain 62 and 119 guarded sense decisions
respectively. `scripts/compile_dictionary_maps.py` now validates inactive sources
too, so source drift cannot remain unnoticed simply because a dictionary is not
the primary construction. Mapping a sense does not certify its pronunciation.

Authored decisions: [dictionary sense follow-up](dictionary_sense_followup_2026-10-27.csv)
and `src/arcaverborum/data/dictionary_senses.csv`.

## 2. American supplements

A scan of remaining South American GLED-primary constructions found no additional
missing core concepts with supplied IPA in current intake. Five North American
pilots therefore receive 54 source-supported Wiktionary forms, filling 53 slots.
The existing primary records remain intact.

| Variety | Supported core before | After | Added forms |
| --- | ---: | ---: | ---: |
| Rio Grande Tewa | 38 | 53 | 15 |
| Yucatec Maya | 38 | 50 | 12 |
| Taos / Northern Tiwa | 38 | 49 | 11 |
| Unami | 34 | 42 | 8 |
| Western Apache | 33 | 40 | 8 |

The review withholds a playing-card “heart”, a general biological egg sense that
does not explicitly establish the frozen food concept, and a redundant second
child sense. See [the authored review](americas_supplement_followup_2026-10-27.csv).

The ranking in track five also exposed opportunities outside GLED-primary
constructions. Reviewing exact Huber–Reed members adds:

| Variety | Supported core before | After | Added forms |
| --- | ---: | ---: | ---: |
| Sikuani / source Guahibo | 76 | 147 | 104 |
| Hitnu / source Jitnu | 79 | 148 | 72 |

These two South American pilots add 140 supported slots. The review rejects an
old-man noun mapped to the adjective “old”, a generic egg sense, and the Spanish
editorial note “al fin de la cita” mistakenly present as a word. Segment validity
alone cannot establish lexical authenticity. Raw source records remain intact.
See [the South American review](south_american_supplement_review_2026-10-27.csv).

The generalized `scripts/compile_supplements.py` accepts an explicit source per
review row, retaining Wiktionary as the legacy default. Partial compilation now
merges admissions rather than deleting unrelated existing sources or IPA
alternatives. Scoped/profile decisions require their own compiler. Source-form
hashes, exact member IDs and original concept IDs guard all additions.

## 3. Missing-language screening

Ten additional Lexibank repository names were screened for CLDF language tables,
with a separate check of Rutul Basic Lexicon. The resulting candidates are
recorded in [the identity/blocker ledger](new_language_screen_2026-10-27.csv).
No new variety was admitted in this track.

* Nepal Linguistic Survey offers apparent Belhariya and Chhulung coverage, but
  original citations use anonymous authors/year 0000 and project metadata remain
  placeholders. Ghale is a family-level identifier, not a standalone language.
* Wust phylogenies offers Tangam, Bangru and Dirang Tshangla candidates, but source
  segment fields are empty and no explicit distribution license was found in
  its repository/CLDF metadata. Transformed Form strings are not promoted to
  supplied IPA merely because they look phonetic.
* Power et al.'s sign-language material requires a modality-specific treatment;
  VALPAL valency data are not a reviewed basic-vocabulary wordlist.
* Borch's more specific Glottocode does not establish new coverage: the accepted
  Rutul construction already contains the parent-coded Borchino–Khnow member.
  The Borch language-table row itself has no lexical forms.

The ledger preserves exact source commits for cloned repositories and hashes
for screened language tables. Read-only raw clones were inspected; these new
sources were not appended to active intake or registered as accepted choices.

## 4. Source-scoped orthographic profiles

The first accepted pilot is Iquito. Its primary huntergatherer construction stays
unchanged; **26 dictionary forms** are added through a profile, raising supported
core **125 → 129/161**. Of 62 reviewed senses, 36 remain held.

The authority is Michael and Beier (2021), Dictionaria 14, source-specific tables
1–4 and the tone-marking discussion. Only unambiguous spellings enter this first
subset. Vowel length and marked high tone are preserved; mixed-tone long vowels
are withheld to avoid losing high-tone position. Unspecified low/null tone is
not inferred. Ambiguous palatalization, hiatus/glides and unreviewed characters
remain held. The result represents the source's partial tonal convention, not a
complete surface phonetic transcription.

Profiles for supplementary sources live separately under
`custom/supplement_profiles/`. Every admission names its profile and SHA256;
only reviewed whole-form keys are allowed. Changes participate in fingerprints
and fail the ledger guard until explicitly reviewed. Invalid profile IPA is
rejected. A source profile cannot reinterpret supplied IPA or affect the primary
source. Exports retain **Segments_Source=profile** and the original dictionary
entry/sense evidence; these are never relabelled supplied source segments.

Reproduce using `scripts/iquito_profile.py --write`. See
[all profile decisions](iquito_profile_review_2026-10-27.csv) and the Iquito packet.
Guarayu remains held: its documentation describes inconsistent nasal/glottal
marking and dialect/genderlect variation, preventing a reliable blanket profile.
No active Guarayu profile or unsupported pronunciation was added.

## 5. Ranked next opportunities

`scripts/rank_coverage_opportunities.py` compares individual alternative source
members against supported accepted core concepts, prioritizing South America,
then North America. It reports missing supported slots, candidate concept IDs,
supplied-segment potential separately from orthographic potential, citations,
licenses, source versions, and remaining review blockers.

The [ranked CSV](coverage_opportunities_2026-10-27.csv) and
[method/counts JSON](coverage_opportunities_2026-10-27.json) describe the current
post-batch baseline. Member opportunities overlap and must not be summed as
unique gains. Raw upstream senses still require review; sharing a Glottocode
does not itself certify sample identity. Primary-source profile recovery is
outside this alternatives report. No source selection or intake is modified.

## Reproduction and validation

Use `.venv/bin/python` (or `uv run --no-sync`) with the installed merkmal build.
Run the dictionary compiler, both new supplementation review files, and the
Iquito compiler, then rebuild accepted directories with existing generated forms.
Do not ingest subsets into active intake; these admissions require no new intake.
After rebuilding, aggregate and run `scripts/build_research_web.py` to regenerate
the tracked webpage artifacts. Pages deploys those artifacts rather than
rebuilding lexical sources. The old Core 0.1.0 snapshot remains historical.

The machine-readable [batch summary](coverage_batch_summary_2026-10-27.json)
records before/after totals and each pilot. Source IDs, supplied segments,
concepts and cognacy of all eight supplemented primary constructions were
compared against pre-batch committed web shards. Sense/profile review here is
not independent specialist certification of native lexical accuracy.

Validation completed: 370 pytest tests, full Ruff and JavaScript syntax checks;
all accepted builds and a zero-rebuild final freshness pass; seven core-pilot
audits and the 82-form Vakh repair audit; all 400 compressed artifact hashes;
and local generic/mixed-source browser checks, including source-scoped profile
exports and South American supplements. All 1,268 original primary records
across eight supplemented constructions match pre-batch exported evidence.
