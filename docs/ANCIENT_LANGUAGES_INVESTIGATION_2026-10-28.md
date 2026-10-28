# Ancient languages worldwide — investigation, 2026-10-28

Planning only: no accepted lexical, identity, code or web-data changes. Accepted
baseline remains data commit `6009c09e58021f203beb920677418d9f7f51f805`:
7,329 constructions,2,069,214 forms and467,872 supported core slots.

[58-construction baseline](ancient_baseline_2026-10-28.csv),
[74 member opportunities](ancient_opportunities_2026-10-28.csv),
[qualified-reading screen](ancient_qualified_scope_screen_2026-10-28.json),
[missing-sample screen](ancient_missing_samples_2026-10-28.csv), and
[source pins/methods](ancient_investigation_2026-10-28.json) accompany this report.
This is an explicit research shortlist, not an exhaustive ancient-language census.
Twenty shortlisted constructions have zero supported core concepts. Existing
primary sources and new acquisition routes were examined separately from ranking.

## Scope and interpretation

“Ancient” follows regional attestation and periodization, not one global European
date cutoff. Include ancient/classical languages and clearly label adjacent late
antique or early historical records. Tocharian manuscript traditions and Old
Japanese require their own dating; Old Nubian, Tangut, Jurchen, Old Turkic and
medieval European stages are adjacent historical opportunities, not automatically
ancient. Colonial Classical Nahuatl/Quechua and Old Guarani evidence cannot be
redated to the precolonial period. Extinction alone does not establish antiquity.

Sanskrit's continuing learned use and Hebrew's historical continuity/revival do
not eliminate the need to distinguish stages. Vedic composition, surviving
manuscript date and recitation tradition are separate facts. Achaean/Mycenaean,
Attic and Koine samples likewise retain separate constructions and authorities.

An attested word can have a reconstructed pronunciation. Romanized spelling,
Egyptological reading, dictionary headword normalization, phonemic reconstruction
and recorded pronunciation must remain distinct. `Segments_Source=source` means
segments supplied by the input, not that an ancient speaker was recorded or that
the source's interpretation is certain. Do not erase stars, restoration brackets,
uncertain consonants or alternatives merely to obtain valid tokens.

## Recommended sequential batch

Each track is a bounded pilot or feasibility decision. Gains are unverified;
records/characters/tokens/signs are not automatically independent lexical lemmas.

| ID | Work and current baseline | First action, potential and tradeoff |
| --- | --- | --- |
| AN01 | Historical representation and source-identity audit | Establish reading basis, language stage, authority, attestation/witness dates and uncertainty separately from source/profile origin. Audit IDSsegmented conversions and Kogan identity matches before importing more of them. Improves quality rather than promising extra slots. |
| AN02 | Classical Sanskrit, Attic Greek and Latin qualified readings | Register exact source scopes, then review a bounded literal-sense/morphology subset. Sanskrit43/161:99 raw missing-concept ceiling; Attic128:26; Latin128:17. This is the fastest measured route, using already frozen data rather than a new dump. Sanskrit Devanagari profile only where scoped supplied readings are absent and a documented convention supports it. |
| AN03 | Existing-source supplements across regions | Review Gothic95, Tokharian A98/B118, Avestan113, Akkadian109, Ugaritic107 and Old Japanese145 core baselines. Candidate ceilings22/21/27/18/14/5/13 respectively, but some are automatic conversions or reconstructed readings. Choose a first literal subset per member; compare original authority before admission. Coverage-first, with substantial transcription gates. |
| AN04 | African lexical depth: Coptic and Egyptian | Coptic36 core/64 forms; Egyptian0/1,346. Start with a Sahidic-specific Coptic dictionary slice (roughly20–30 reviewed lemma/sense decisions), then a stage-specific TLA Egyptian slice. Preserve script/transliteration even where pronunciation remains unresolved. Strong licensed acquisition route; lexical gains need not increase phonetic support. |
| AN05 | Mesopotamia and Northwest Semitic | Pilot source-linked Sumerian/Akkadian glossary lemmas via ORACC/ePSD2 and an Ancient Hebrew BHSA/reading-convention feasibility slice. Current Sumerian119 core/245 forms, Akkadian109/905, Ancient Hebrew0/109. Pin actual project payload and terms; separate period/dialect and written lemma from reconstructed reading. Larger depth potential, unmeasured admissions. |
| AN06 | East Asian evidence and reconstruction scope | Old Chinese138/289 already relatively strong; existing Peiros member offers8 missing core candidates and Lee's Old Japanese13. Review named reconstruction systems and attested graph/word identity, then a small lexical-depth subset. Classical Chinese0/40 is not automatically interchangeable with Old Chinese. Do not synthesize a consensus reconstruction or silently strip uncertainty. |
| AN07 | South/Southeast Asian acquisition | Old Khmer and Old Cham have no accepted constructions or intake rows; Gandhari4 forms/0 core and Old Tamil4/0 are sparse. Start with a dated Old Khmer inscription/lexicon pilot, then Gandhari rights/export and Old Tamil source feasibility. Actual historical diversity, but inscriptions need lemma/sense work and period checks rather than token import. |
| AN08 | Americas: Classic/Epigraphic Mayan | Existing `may-epigraphic-mayan` has1 form/1 supported core concept. Begin with a small set of well-supported lexical readings and source attestations, preserving sign IDs, transcription/translation, site/date and certainty. TWKM notes/catalog offer evidence; a planned2026 API is not a verified released lexicon. High diversity value, unmeasured gains. |
| AN09 | Rare ancient-language acquisition | eDiAna pilot for Carian2/0, Lycian A9/0 and Lydian5/0; examine Palaic/Hieroglyphic Luwian as absent accepted samples. Bound the first review to about20 sourced lexical decisions across available languages. Etruscan70/9, Hurrian6/0, Urartian3/0, Hattic1/0, Meroitic4/0 remain discovery cases. Do not turn proper names, undeciphered signs or disputed readings into a basic wordlist. |

The recommended order first establishes representation safeguards, then realizes
measured recovery while reserving non-European acquisition. No GLED replacement
is justified by a raw row count alone. Tracks may end in explicit holds when
rights, semantics or interpretation do not support admission.

## Frozen qualified-reading screen

The previous generic Wiktionary matcher deliberately excludes qualified or
conflicting readings. The raw pronunciation index retains useful historical
scopes that the accepted intake therefore does not yet use. Frozen dump SHA256:
`a6a32d41e35990b79a886d9082ebb3459a16fbaed6d2995aaedf6ef46d3ee643`.

The read-only screen groups every raw homograph by exact language, NFC headword
and POS. Every matching entry must supply a valid reading in the specified scope;
all qualifying raw alternatives are retained. The counts then intersect mapped
core concepts missing source/profile support in accepted output. Existing shared
sense corrections are honored. No broad orthographic-to-phonetic conversion runs.

| Target | Exact raw scope | Complete raw entry groups | Missing-core form candidates | Distinct-concept ceiling |
| --- | --- | ---: | ---: | ---: |
| Sanskrit | tags exactly `Classical-Sanskrit`, no note/form/raw tags | 2,363 | 180 | 99 |
| Ionic-Attic Ancient Greek | note exactly `5ᵗʰ BCE Attic`, no other tags/form/raw tags | 6,661 | 58 | 26 |
| Latin | tags exactly `Classical-Latin`, no note/form/raw tags | 6,271 | 58 | 17 |

These are **not admissions**. The Greek note-based route is a research screen,
not implemented admission support. Scope registry/compiler changes require tests.
Latin's same-headword alternatives may mix grammatical quantities (for example
nominative/ablative-like readings); Sanskrit homographs and nominal stems need
form/sense checks. Bare unqualified Greek IPA must not substitute for an identified
Attic reading. Ecclesiastical Latin, modern Greek and Vedic alternatives remain
outside the selected scopes. Preserve pitch/raw accent even if downstream segment
normalization has a different convention.

## Existing-source quality and replacement findings

Current additive ceilings include Greek28 and Tokharian A21/B27 through
`idssegmented`, Gothic22 through `streitberggothic`, Latin25 through Northeuralex,
Avestan18 through IDSsegmented, Akkadian14/Ugaritic5 through Kitchen, and Old
Japanese13 through Lee. Members overlap; do not sum alternative rows as gains.

**IDSsegmented is a conversion layer.** Its pinned v1.1 README explicitly describes
rough IPA mapping and possible errors, including orthographies previously mistaken
for transcription. Its valid segments are not independent historical phonology.
Audit original IDS lexical forms and language-specific conversions before using
these high rankings. [Primary dataset documentation](https://github.com/intercontinental-dictionary-series/idssegmented)
provides the relevant caveat. Gothic's source is a dictionary-derived CLDF dataset,
not an audio corpus; document its sound-mapping authority too.

The Kogan intake contains concrete identity-warning pairs: source `Hebrew` linked
to Modern Hebrew; `Official Aramaic` to Middle-Modern Aramaic; `Demotic Aramaic`
to Demotic Egyptian. Their intended samples require original-source review, not
automatic reassignment. Kogan metadata currently lacks a recorded citation,
licence and immutable version. Some ancient constructions already use it; this is
a quality audit priority, not authorization for a blanket destructive migration.

A separate GLED replacement screen for Coptic finds Wiktionary gains6/losses34
before profile work. Supplement first. The larger943-row Wiktionary member and
its26 missing spelling concepts do not alone justify replacing the64-row primary.
Primary recovery cases such as Sanskrit43, Ancient Hebrew0, Egyptian0 and
Sogdian23 are not adequately measured by an alternatives-only ranking.

## Original-source acquisition evidence

### Africa: verified structured data, cautious pronunciation

**Coptic:** [Comprehensive Coptic Lexicon v1.2](https://refubium.fu-berlin.de/handle/fub188/27813)
and [Coptic Dictionary Online source](https://github.com/CopticScriptorium/dictionary).
The latter is pinned at `d39e8a844779c8e7f89f88a78e21c1e92957f1f1`.
Downloaded README and `xml/01_Alpha.xml` verify TEI entries, English/German/French
senses, POS and form-specific geographic/dialect labels. This one alphabetical
file contains316 entry records, not316 admissible basic words. It includes bound
particles, multiple forms and dialects S/B/F/L/A/M/Ak/P; select an exact dialect
before any profile. Data are CC BY-SA4.0; software terms differ. A modern liturgical
pronunciation cannot silently stand for late-antique Sahidic.

**Egyptian:** [TLA's official data releases](https://aaew.bbaw.de/daten-veroeffentlichungen)
provide dated Earlier Egyptian, Late Egyptian and Demotic datasets, lemma resources
and a LexFCS service. Releases carry explicit data terms, commonly CC BY-SA4.0;
its Wikidata lemma release has its own CC0 route. Pin the chosen release and verify
actual lexical payload, stage and source references. In Arca, sample Wiktionary
forms are Manuel-de-Codage-like glyph encodings rather than pronounceable Latin
spelling. Do not read glyph IDs as phonemes or insert Egyptological vowels as
historical reconstruction. This route can improve lexical/semantic coverage
while leaving phonetic support honestly unresolved.

### South Asia: dictionary depth and explicit Sanskrit stages

[Cologne's canonical source](https://github.com/sanskrit-lexicon/csl-orig), pinned
at `e4742e12cde786b1a2d10e0507808620a4f2c8eb`, was sampled with README, LICENSE
and the complete `v02/mw/mw.txt`. The actual file has286,525 `<L>` source records,
uses SLP1 and is CC BY-SA4.0. These are source records, including homonyms and
microstructure, not an admission estimate. Preserve dictionary IDs, grammatical
labels and Vedic/Classical distinctions; a multi-sense Sanskrit headword cannot
be assigned a core concept from its first English word. A documented Devanagari
or IAST/SLP1 profile is more defensible here than in consonant-only writing,
but sandhi, vocalic liquids, anusvara/visarga and accent need explicit scope.

[Gandhari.org](https://gandhari.org/) is a primary dictionary/text source for a
language attested third century BCE–fifth century CE. Its dictionary and manuscript
context are valuable for a four-form Arca construction. Public access did not
establish a blanket redistributable dictionary export in this screen. Its linked
[Pali dictionary notice](https://gandhari.org/blog/?p=48) specifically retains
copyright and permission terms; do not transfer a website's access grant to every
embedded resource. CEToM is a relevant Tocharian manuscript authority, with separate
rights/export verification still needed: [project](https://cetom.univie.ac.at/).

### Southeast Asia: a verified missing-sample route

[DHARMA Khmer repository](https://github.com/erc-dharma/tfc-khmer-epigraphy), pinned
at `329c55f29e845260ade1eaef515193d569fae74d`, supplied an actual TEI inscription,
`texts/xml/DHARMA_INSCIK00001.xml`, with edition language `okz-Latn`, named editors
and attribution. The file explicitly states **CC BY-SA4.0**, despite repository
listings advertising CC BY4.0. Use the selected file's actual terms.
It records draft editorial history; publication dates2019–2026 are not ancient
attestation dates. Recover original dating/bibliography and preserve restorations,
gaps and bilingual passages. The sample establishes structured availability, not
a ready lemma inventory or a new accepted language.

Neither Old Khmer `oldk1249` nor Old Cham `oldc1255` has current accepted output or
intake rows. Kawi/Old Javanese already has2,260 forms/0 supported core via ACD and
is an adjacent source/profile opportunity rather than a missing language. Old
Tamil is already present with four forms. Keep source language/script labels and
attestation periods explicit across any DHARMA expansion.

### Near East: lexical data versus corpus tokens

[ORACC's own acquisition guide](https://oracc.museum.upenn.edu/compass/downloads/2_3_Data_Acquisition_ORACC.html)
describes project JSON, glossaries and metadata and states CC0 for its open JSON.
The live documentation/ePSD2 endpoints returned502/unavailable during this screen;
no new glossary payload was pinned or ingested. Verify the chosen project's
actual release terms rather than treating edition text, images and JSON as one
undifferentiated licence. Preserve `cf`/guideword/sense/POS, period/dialect, text IDs
and compound semantic units. A logogram, syllabic spelling and normalized lemma
are different objects. [CDLI terms](https://cdli.earth/terms-of-use) distinguish text
reuse from image restrictions; neither text tokens nor object images are a new
phonetic lexicon by themselves.

[ETCBC BHSA](https://github.com/ETCBC/bhsa/blob/master/docs/index.md) provides
morphologically annotated Hebrew text under CC BY-NC4.0.
[ETCBC phono](https://github.com/ETCBC/phono) provides algorithmic reading features;
its software licence does not relicense the underlying corpus. Establish exactly
which reading tradition the algorithm encodes and align pointed forms/lexemes
before a pilot. A medieval vocalization tradition must not be labelled a recording
or unqualified Iron-Age pronunciation. Current Ancient Hebrew109 forms/0 supported
core is a primary-recovery case, not a claim that the ancient language lacks words.

### East Asia: preserve reconstruction identity

Old Chinese's accepted Sagart source has289 forms/138 supported core. Its related
[scholarly reconstruction](https://academic.oup.com/book/26638) is a named hypothesis
about an attested ancient language, not a proto-language to pool with unrelated
reconstructions. The author-site spreadsheet endpoint was inaccessible during this
screen; no new full-table licence or snapshot was established. Prioritize provenance
and source-specific alternatives over counting every Chinese character as a new
word. Classical Chinese's literary scope is broader than one Old Chinese stage;
modern Mandarin readings are not substitutes. Old Japanese offers a bounded
Lee-source comparison; retain its Old Japanese sound-class/romanization conventions.

### Americas: a real priority, with a bounded evidence route

[TWKM's project](https://classicmayan.org/portal/doc/24),
[2025 sign-catalog description](https://classicmayan.org/portal/doc/246), and
[IDIOM+ announcement](https://classicmayan.org/portal/doc/247?lang=de) establish
Classic Mayan text/sign work and a planned2026 FCS interface. This investigation
did not verify a released complete dictionary/API payload. A sign catalog is not
a wordlist. Preserve readings and certainty rather than merging disputed signs.
Prager's standardized drawings are CC BY4.0; third-party images have different
restrictions. Selected project research notes explicitly license their text CC BY4.0
and offer a feasible small source-led lexical pilot; check each original item and
attestation. Long vowels/glottalization and logographic versus syllabic spellings
must not be inferred from a generic font conversion.

South American colonial dictionaries may support historical varieties but cannot
supply independently attested ancient Inca pronunciations. This screen found no
verified, deciphered precolonial South American phonetic wordlist route. That is
an acquisition result, not a claim of historical linguistic absence. Archaeological
labels, khipu interpretations and undeciphered scripts cannot fill vocabulary slots.
The same discipline applies to prehistoric Oceania/Australia: reconstructed
proto-languages and modern descendant forms are a separate evidence collection,
not ancient attested-language admissions.

### Anatolia and other sparsely attested languages

[eDiAna's own citation/export notice](https://www.ediana.gwi.uni-muenchen.de/assets/pdfs/citation.pdf)
states CC BY-SA4.0 and documents lexical modules for Cuneiform/Hieroglyphic Luwian,
Carian, Sidetic, Palaic, Lycian, Lydian and Pisidian. It is a credible original-source
pilot, but no lexical export was pinned here; current dictionary endpoint access
was inconsistent. Select attributable lemmas/senses and preserve attested forms
versus etymological reconstruction. Palaic and Hieroglyphic Luwian currently have
zero intake rows/accepted constructions; a Luwian script/sample split is not
necessarily a distinct-new-language claim. Carian/Lycian/Lydian already exist.
Etruscan, Hurrian, Urartian, Hattic and Meroitic require source-specific lexical and
reading confidence; proper-name abundance does not establish core coverage.

## Admission and closure gates

If authorized, execute AN01–AN09 in order, bounding acquisitions to small explicit
admit/hold ledgers. Use exact members, source versions/hashes, original senses,
source-specific profiles and guarded primary/supplement selection. Stage new data
outside active intake. Do not overwrite an active namespace with a subset.
Report lexical rows, supported core slots, reading basis, historical stages, new
named samples and distinct-language claims separately. Keep Romance RP01–RP03 and
American NB/P proposals parked, not completed or cancelled. No source contacts,
lexical admissions or live-data rebuild were performed for this planning request.
