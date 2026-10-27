# Coverage follow-up, with an Americas priority — 2026-10-27

All five tracks were completed in sequence. The accepted collection remains
7,312 varieties, with **2,065,761 forms (+3,288)** and **153 additional supported
core-concept slots**. Supplied-segment forms increase by 3,290, and profile-supported
forms by 398. No language counts were inflated by treating overlapping dictionary
sources or pronunciation alternatives as independent languages. See
`coverage_followup_summary_2026-10-27.json` for the before/after metrics.

## 1. Reviewed supplementation

The additive layer retains primary forms and appends only individually reviewed
source forms. Evidence hashes guard original IDs, spelling, supplied segments,
source member, cognacy, bibliography and notes; source concept IDs are separately
guarded. Missing, duplicate or changed evidence fails the build. Profiles belonging
to the primary source are not applied to supplements. Source-specific cognate IDs
are preserved without transferring primary judgments. Supplemental inputs and
reviewed member selectors participate in freshness checks.

| Construction | Supported core before | After | Added supplied-IPA forms |
| --- | ---: | ---: | ---: |
| Yurok | 38 | 58 | 23 |
| Chickasaw | 37 | 50 | 14 |
| Xavante | 34 | 35 | 1 |
| Apinayé | 35 | 36 | 1 |
| Xerente | 35 | 36 | 1 |

These five American pilots add 36 supported core slots. Primary GLED forms,
segments, cognate codes and concept mappings were compared against the committed
pre-batch research shards and remain unchanged. English measurement-foot, written
indication and other less explicit senses were not admitted as anatomical or
spoken concepts. These checks do not certify target lexical accuracy.

Authored decisions: `supplement_pilot_review_2026-10-27.csv` and each construction's
`custom/supplements.csv`. Compile/validate with `scripts/compile_supplements.py`;
`--write` is explicit and previously reviewed evidence cannot silently refresh.

## 2. Qualified pronunciations and alternatives

The new regenerable regional evidence index retains every valid raw reading for
an exact registered scope. The first scope maps precisely `wikt_pt` + `Brazil` to
Brazilian Portuguese (braz1246), a cached Glottolog dialect under Portuguese
(port1283). Finer regions, registers and unmatched qualifiers are excluded. Every
matched lemma/POS homograph must supply valid scope evidence. Phonemic and phonetic
representations remain separate; the process never chooses a convenient reading.

The regional index accepts 24,075 matched Portuguese lexemes with this evidence,
withholding 7,535 incomplete homograph groups and 6,018 unsupported groups. These
are discovery figures, not accepted lexical gains. After reviewing missing core
senses, **34 supplied IPA alternatives for 21 source forms/concepts** supplement
the existing Brazilian Portuguese construction: supported core **128 → 149**.
The primary IECOR block is retained. The browser exposes raw IPA, tags, original
form IDs and stable pronunciation IDs. Original entry lines and the frozen dump
hash remain in the authored ledger and evidence comments.

The cached IECOR record explicitly places Brazilian Portuguese off Portugal for
map framing. That artificial point and inherited catalog coordinates are now
suppressed; actual sample coordinates remain unrecorded. The construction is
classified geographically under South America and linked to its Portuguese parent.

Reproduce with `scripts/qualified_pronunciations.py --index --compile-reviewed
--write`, using the exact frozen Wiktextract snapshot. The accepted decisions are
in `qualified_pronunciation_review_2026-10-27.csv`; scope rules are separate from
language-wide pronunciation assumptions.

## 3. Profile extension and correction

The Asturian profile adds documented onset-cluster taps, post-l/n/s trills,
open-vowel hiatus and written stressed-weak-vowel hiatus from the Academia de la
Llingua Asturiana grammar, pp.42–43,51. Source IPA retains precedence; remaining
ambiguous x/y, glides and rhotics are withheld.

A new regression test exposed an older empty-string membership bug that allowed
word-final r into the intervocalic branch. The grammar permits tap/trill variation
in final position; those readings are now withheld. The net result is **398 more
profile-supported forms**, but a scientifically more conservative core count of
**92 → 82**. Current evidence: 166 supplied forms, 3,946 profile-supported and
5,603 unresolved. Preliminary higher counts were not published as a new result.
The packet records this correction and the gains/losses explicitly.

Reproduce with `scripts/asturian_profile.py --write`; exact spelling/profile
rosters are guarded against source drift. Stress and surface allophones are not
inferred. Other proposed profiles remain inactive where their evidence is inadequate.

## 4. South American scholarly sources

Four Dictionaria CLDF dictionaries were screened and staged: Media Lengua,
Iquito, Guarayu, and, secondarily in the wider Americas, Tseltal. Their exact
commits and admission decisions are in `americas_dictionary_admissions_2026-10-27.csv`.
The adapter preserves original entry/sense records and uses conservative authored
sense mappings; a field named Pronunciation is not automatically interpreted as IPA.

**Media Lengua**, from Ecuador, replaces a two-form, zero-supported-core
construction with **3,216 validated supplied-segment forms and 106 supported core
concepts**. It uses the dictionary's Phonological_Representation directly, not
Spanish/Quichua spelling guesses. The source describes community variation, which
is retained. Its 157 reviewed senses map 126 concepts. Remaining original glosses
stay visible without invented concept mappings. Lexical origin does not become
a loan flag or a comparative cognate judgment.

The source metadata's citation mistakenly names the Kalamang dictionary. The
local manifest follows the actual Media Lengua contribution and named compilers,
records the original metadata hash, and does not infer a publication year.
License and exact source commit are preserved. See the construction packet.

Iquito and Guarayu already have substantial accepted coverage. Iquito's sparse
Pronunciation values include orthographic reductions; Guarayu's documented nasal,
glottal, historical and dialect spelling variation prevents blanket phonemic
conversion. Tseltal likewise needs a source-specific, multidialectal review.
These sources remain available in intake without displacing better evidence.
No new av_ids are manufactured for the same source languages.

New source ingestion must target staging, followed by validated append. Ordinary
subset ingest replaces intake tables and must not be directed at active intake.
`scripts/compile_dictionary_maps.py --write` validates and compiles the active
construction's authored sense decisions.

## 5. Semantic and cognate quality audits

Additional independent source-sense ledgers extend the guarded Wiktionary rules
from **30 to 40**. Seven conflicting/unresolved cases remain held; derived shared
reviews do not count as fresh independent evidence. Relative/exclamative,
figurative, grammatical and literal meanings are not silently interchanged.
Local authored corrections retain precedence. See `shared_sense_followup_*` and
`shared_sense_conflicts_*`; reproduce with `scripts/compile_shared_senses.py`.

A raw/structured cognacy audit covered 44 sources. Reviewed repairs for
**Chacon Tukanoan, UraLex and Philippine ABVD** remove additional global memberships
created from meaning-local raw labels. The complete source CognateTable judgments
are retained. Raw labels, including uncertainty marks, survive in evidence notes.
The repairs affect 49,667 intake forms and **41,119 currently accepted forms**.
Unclear global-root conventions in other sources are reported rather than
reinterpreted. Rules are pinned to exact forms/cognate-table hashes and fail
closed on drift. A regression also prevents missing structured metadata from
erasing an existing uncertainty flag during future ingestion.

An older inactive Higaonon packet misidentified its Wiktionary member as wikt_hig
(Kamwe). It now correctly names wikt_mba / higa1237. The actual accepted source was
not changed, and the incomplete profile remains inactive.

## Research export and validation

Mixed-source constructions expose every lexical source and its attribution.
Core-source membership and metrics now apply per lexical row: non-Core additions
remain outside that collection and its exports. Brazilian Portuguese is 149-core
under All accepted, and remains 128-core under Core sources. Core membership stays
892 varieties. The old Core 0.1.0 viewer is explicitly marked as an archived
snapshot; current corrected data are in the research explorer.

Raw IPA/qualifiers and stable pronunciation IDs survive exports. Legacy form
links still resolve unique unchanged source-form identities. Aggregation aligns
older optional-field schemas by column name, preventing positional corruption
following a partial rebuild.

Validation: all 7,312 accepted builds succeeded; a freshness pass rebuilt none;
346 tests and full lint passed; the seven core-sense audits and 82-form Vakh
repair audit passed. All 400 compressed artifact hashes were verified. Browser
checks cover comparison, search, provenance, export, maps, mobile, legacy links,
separate pronunciation records, mixed-source attribution, and Core isolation.
