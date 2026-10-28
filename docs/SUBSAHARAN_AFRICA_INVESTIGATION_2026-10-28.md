# Sub-Saharan Africa, especially Bantu — investigation, 2026-10-28

Planning only: no lexical admissions, source changes, active-intake modifications
or web-data rebuild. Accepted baseline remains data commit
`5d0981260945f7d90b827f8ade7ac9d603ca1f6d`:7,329 constructions,2,069,498 forms,
468,037 supported core slots. [Research manifest/pins](africa_investigation_2026-10-28.json).
Ancient AE, Romance and American proposals are parked rather than completed.

## What the accepted collection actually contains

The Africa-wide screen covers1,788 accepted constructions; this includes northern
Africa and is **not** a Sub-Saharan language count. Bantu is identified separately
through Glottolog classification ancestry at **Narrow Bantu `narr1281`**, pinned
commit`072ca0d0410039fb8b779be8fc165bac575d2cda`. Do not use every Atlantic-Congo
language or every member of a dataset named Bantu as a Bantu-language inventory.
Grollemund includes Bantoid outgroups: Fe'fe', Tiv and other outgroups remain
relevant African candidates, but are not included in the Narrow Bantu totals.
This operational boundary is explicit; it does not settle all classifications.
Tanzania-Mozambique Ngoni is classified within Bantu but has a blank accepted
Macroarea. The baseline file includes it through ancestry:1,789 rows in the union
of Africa-labelled and Narrow Bantu constructions; do not lose it by geography
filtering alone. Its geographic/sample metadata needs review.

| Narrow Bantu measure | Accepted value |
| --- | ---: |
| Constructions | 485 |
| Forms | 149,873 |
| Supported core slots | 34,732 |
| GLED primaries | 97 |
| Zero supported core | 23 |
| Fewer than80 of161 supported core concepts | 365 |

Primary sources:206 Grollemund,96 Tanzania Language Survey (TLS),97 GLED,
29 Polyglotta Africana,25 Wiktionary,13 Mitterhofer Bena,10 Bantu BVD,
8 Sawka Toka-Leya,1 WOLD. The local source-member additive ranking yields240
Bantu opportunities within577 Africa-wide member rows. Counts overlap; no sum
is a verified gain. [Accepted baseline](africa_baseline_2026-10-28.csv),
[member opportunities](africa_opportunities_2026-10-28.csv).

The separate GLED screen found38 Bantu candidate members for38 targets; **all38
lose supported core coverage in a direct swap**. Across the431 Africa-wide
candidate members there is no positive-net supplied-reading replacement.
This is a strong reason to acquire better sources and retain earlier evidence,
not replace97 primaries by mechanically selecting another intake dataset.
[Loss-aware screen](africa_gled_replacements_2026-10-28.csv).

## Recommended sequential work

These are proposals AF01–AF09, not an authorized lexical batch. Raw ceilings below
measure missing supported concepts before sense/identity/notation review.
Verified admissions in this investigation: **zero**.

| ID | Exact proposal and baseline | Evidence / potential | First gate and intended outcome | Recommendation / tradeoff |
| --- | --- | --- | --- | --- |
| AF01 | Bantu identity, notation and alternatives audit, starting with Kamba, Ndebele and shared TLS/RefLex samples. | Accepted Kamba296 forms/76 core pools three Grollemund members. GLED Zimbabwean Ndebele159/38 includes four source labels, including SOUTHERN_NDEBELE. Pinned Grollemund and TLS conversion recipes both set first_form_only=True. | Reconcile original sample labels before any reassignment; document upstream profile-derived segments, optional prefixes, tone, alternative readings and same-source genealogy. Review lexical alternatives rather than mechanically splitting punctuation. | First: protects later gains from dialect mixing and false phonetic certainty. Primarily quality/provenance work; no immediate gain promised. |
| AF02 | TLS supplements: Ngoreme76/161, Nilamba75, Temi76 first; then Kamba76, Ikizu76, Ikoma-Nata75 and Suba76. | Exact members tls_Ngoreme, tls_Nyiramba, tls_Sonjo each have raw59 missing-core ceilings; tls_KambaKitu59, tls_Ikizu57 / tls_ShashiSiz58, tls_Nata58, tls_Suba58. TLS v4.1.1, CC BY4.0. | Review native gloss/POS, source-specific transcription conversion, exact regional member and noun/verb morphology. Supplements retain Grollemund evidence and keep regional samples explicit. | Highest measured near-term depth. Kitui/Machakos, Shashi/Ikizu and Nata/Ikoma cannot be silently treated as interchangeable. Do not add57+58 for Ikizu. |
| AF03 | Zulu200 forms/76 core and Xhosa100/76: supplied Wiktionary IPA first. | wikt_zu raw21 missing-core supplied readings; wikt_xh9. Separate spelling ceilings21/10. Frozen pronunciation snapshot a6a32d41… already available. | Exact word/POS/sense and every pronunciation alternative; preserve tone, clicks, aspiration, breathiness and noun-class morphology. | Good low-acquisition-cost improvement;21+9 is prospective and source-local, not30 approved admissions. No general tone-reconstruction profile. |
| AF04 | Tumbuka68 forms/60 core: bounded Wiktionary profile pilot. | wikt_tum373 intake forms; raw20 missing-core spelling concepts. Downing2019 gives an empirical analysis of predictable non-ideophonic prosody. | Match exact source spelling/variety and segmental conventions (including ŵ, nasals, aspiration); exclude ideophones and borrowed/uncertain forms. State broad segmental versus isolation/phrase reading explicitly. | Best identified Bantu orthography candidate. Useful bounded gain; “no tone” would be an incorrect generalization. Lingala49, Ngazidja39, Maore24 and Shona12 spelling ceilings need separate tone/source authority. |
| AF05 | Original Ruruuli-Lunyala dictionary pilot for atl-ruuli:6 forms/0 supported core. | Namyalo et al.2021 dictionary about10,000 entries; CC BY4.0; actual TeX entries, guide and phonology downloaded at langsci/326 commit5c8dd129…. | Preserve root/headword, augmented citation, noun class, separate senses, examples and cross-references. Tone is contrastive and ordinary headword spelling does not recover it. Start with a bounded lexical slice; add only individually attested readings. | Largest qualitative improvement for a nearly empty Bantu construction. Strong written lexical coverage can precede supported phonetic gain; not a new language. |
| AF06 | Original-source Fwe and Gyeli depth/GLED-replacement pilots: Fwe47 forms/36 core, Gyele36/34. | Gunnink2022 Fwe wordlist about2,200 lexemes (langsci/351 @91344668…); Grimm2021 Gyeli lexicon about1,500 entries (langsci/298 fbcdc588…). Original sources CC BY4.0; actual lexical and phonology files inspected. | Preserve Namibian/Zambian Fwe labels, class prefixes, citation tones and separately marked underlying/floating H. Gyeli unmarked syllables are explicitly toneless, not automatically low. Keep original GLED rows and assess all losses before changing primary. | Strongest concrete route to reducing GLED dependence with richer phonological evidence. Extraction/profile review is more work than reusing intake; gains unmeasured. |
| AF07 | RefLex bounded acquisition for Bantu dictionaries and genuinely missing African languages. | Frozen archive contains932,836 records;239,769 Narrow Bantu records from280 source members/197 language samples.38 other canonical-language codes absent from accepted catalog are provisional candidates. | First two missing-language pilots: Konyagi/wame1240, Santos1996 source39 (4,044 rows), and Kam/kamm1249, Lesage2019 source3074 (1,694). Check aliases, original publication/notation, exact senses and inherited terms. Preserve source-specific records, comments and loan fields. | Best breadth opportunity. CC BY-NC-SA4.0 remains attached; no blanket IPA conversion or automatic mass import. Existing TLS/Polyglotta/BCCW data in RefLex are not independent sources. No missing Narrow Bantu canonical language confirmed in this export. |
| AF08 | Broader West African supplied-source review: Bambara317/78, Soninke296/78, Koyra Chiini384/78. | hantganbangime_Bambara raw36, baf2_Soninke38, hantganbangime_Songhai_Kiini44 missing-core ceilings. Pinned source versions/CC BY4.0 recorded in manifest. | Exact modern sample versus historical Koelle evidence, tone/length and native senses; preserve historical source rows rather than silently redating them. | Keeps this Sub-Saharan batch broader than Bantu. Measured alternatives exist, but overlap and historical-versus-modern scope need review. |
| AF09 | Original African dictionary complement: Hdi32 forms/31 core, Sidaama (accepted av_id afa-sidamo)49/38. | Dictionaria Hdi1,681 entries/1,704 senses, Sidaama3,578/3,992. Actual CLDF files pinned and inspected; CC BY4.0. Hdi has raw73 missing-core mappings, not73 verified readings. | Hdi source-specific phonology and bilingual sense/POS review; Sidaama official spelling versus phonemic analyses/tone. Prefer supplied original analyses over guessed profile readings; preserve GLED losses. | High-quality source-led geographic/family balance. Costs more sense/notation work; Hdi's English “run” can mean French “flow/spurt”, illustrating why Concepticon tags alone do not establish meaning. |

## Original-source acquisition findings

### RefLex: a real payload, not just a directory

The [RefLex-CLLD site](https://reflex.clld.huma-num.fr/) links its downloadable
archive at [DOI10.34847/nkl.e3cbkjzm](https://nakala.fr/10.34847/nkl.e3cbkjzm).
The Nakala API supplied six files, all verified against advertised SHA1 and
recorded with SHA256: languages, countries, records, references, sources and README.
They are staged **outside intake**, under `raw/curation/africa-reflex/`.
The frozen export actually contains932,836 lexical records, rather than the
927,845 described by the live site. Preserve that snapshot distinction.

RefLex's records link exact original forms, POS, translation, author comment and
loan donor to a language–reference source. This supports transparent source-led
pilots. It supplies no universal ready-to-use IPA field and no universal frozen
concept mapping. Some FRM cells combine singular/plural forms or bound stems;
separating them requires grammatical interpretation. Some source notes refer to
additional fields absent from this export: do not claim that absent information
has been recovered. Repeated TLS/Koelle/BCCW references remain one genealogy.

[Full source/identity screen](africa_reflex_source_screen_2026-10-28.csv),
[missing-language candidates](africa_missing_language_candidates_2026-10-28.csv).
The source-screen CSV and candidate extract retain RefLex attribution and
**CC BY-NC-SA4.0**; software MIT terms do not replace these source terms.
Missing-code candidates include Konyagi, Kam, Gimnime, Momi and Kuwaa. These are
not all Bantu and not38 verified admissions. RefLex language labels and modern
Glottolog levels can disagree: Luyia/luyi1234 and Subi/subi1247 are identity cases,
not established new Bantu-language gains. The export also has unaccepted dialect
samples inside accepted languages; a named variety is not a distinct language.
An Ogaden-Arabic/Taizzi-Adeni code pairing requires specific identity review.

### Original Bantu books: structured lexical text and explicit notation

The published [Ruruuli-Lunyala dictionary](https://langsci-press.org/catalog/book/326)
and [its source repository](https://github.com/langsci/326) make roots/citation
forms, noun classes, meanings and examples available as structured TeX. The source
README has stale pre-publication wording; use the published2021 book metadata
and pin exact bytes. The phonology chapter explicitly documents lexical tone;
blank tone marks on headwords are not a license to invent readings. The source
can make Ruuli useful as a lexical construction even before broad phonetic recovery.

[Fwe's published2022 grammar](https://refubium.fu-berlin.de/handle/fub188/35830)
includes a substantial wordlist. The actual pinned appendix distinguishes surface
citation tones from underlying high tones that fail to surface in isolation.
[Gyeli's2021 grammar](https://refubium.fu-berlin.de/handle/fub188/37550) has an
explicitly tone-marked lexicon and distinguishes tonelessness from missing tone.
Earlier RefLex Fwe2018/Gyeli2015 records and the later books share source histories;
do not promote them as independent confirmations or mix editions silently.

### Other original dictionaries and empirical phonology

[Hdi](https://dictionaria.clld.org/contributions/hdi) supplies lexical headwords,
meanings, examples and a detailed guide to transcription; some conventional
spellings differ from IPA. [Sidaama](https://dictionaria.clld.org/contributions/sidaama)
explicitly distinguishes official headword orthography from phonemic examples and
analyses. Its tone/prominence information cannot simply be read from every
headword. Actual entry/sense tables are available in the pinned research stage.

[Downing2019, Tumbuka prosody](https://langsci-press.org/catalog/view/192/1154/1594-1)
bases its analysis on fieldwork. Non-ideophonic forms have predictable
phrase-conditioned prosody; ideophones are an important contrastive subsystem.
A bounded profile must specify which representation it derives and exclude
unlicensed extrapolation to ideophones or full connected-speech pronunciation.

## Quality and depth work beyond the core ranking

Within accepted Bantu output, TLS accounts for101,971 rows, including33,357
unmapped rows;9,268 Values contain a possible alternative separator and10,416
contain parentheses. Grollemund contributes22,264 rows, with66 separator-bearing
Values and185 parenthesis-bearing Values. These are **inspection counts**, not
proof of lost lexical alternatives: punctuation can encode morphology, remarks,
alternatives or segmentation. The pinned intake conversion recipes both keep
only the first form. Explicitly recover reviewed alternatives and optionality
without inventing new lexemes or carrying one cognacy judgment onto everything.

The33,357 unmapped TLS rows are also a non-core semantic-depth opportunity.
Review the bilingual source gloss against the frozen concept definitions; do not
map an entire list by English-string similarity. Recovering existing primary
mappings is distinct from adding forms or recovering phonetic readings.

Existing sparse Bantu Wiktionary primaries include Kituba (DRC)154 forms/42 mapped
core but0 supported; Kabwa17/5/0; Malawi Lomwe23/11/0; Tonga (Nyasa)25/8/0;
Mwali19/2/0; South Transvaal Ndebele18/1/0. Their Latin-looking spellings currently
supply no supported phonetic coverage. Source-specific broad profiles or written
lexical expansion may be useful, but their tone, orthography and member identity
have not been established by this screen. Ruruuli's original dictionary is a
stronger immediate source than guessing a generic “Bantu” profile for these.

## Sources to monitor, rather than promise as immediate intake

* [South Bantu Etymological Dictionary](https://www.bantuetymology.org/) has an
  actual public sample and historical notes, but its stated full13,000 modern
  forms are not all public: the site describes a sample of about200 reconstructions
  and broader access planned for2027. Modern forms use orthographies. Verify a
  reusable lexical export and terms before counting gains; reconstruction records
  and modern descendants require different identities.
* BLR3 is valuable reconstruction evidence, not thousands of new modern languages
  or uniformly Proto-Bantu reconstructions. Preserve status, regional/time depth,
  variants, rejected hypotheses and reconstructed meaning uncertainty. A detached
  third-party CSV cannot supply original authority or missing reliability fields.
* [BantuDArc](https://bantudarc.aa-ken.jp/about.html) has Bende, Rwa, Swahili,
  Rundi and Xitsonga recordings/text resources. Its published terms are
  **CC BY-NC-ND**, with academic audio access restrictions. Suitable metadata and
  links can aid research; transformed lexical redistribution is not automatically
  permitted by public visibility. No contact/permission request made.
* [The Bantu Historical Linguistic Database](https://africanmatrilinealhistories.bucknell.edu/database.php)
  advertises71 languages/2,162 English headwords. No pinned reusable lexical
  export/terms established here. CBOLD and BantUGent are important attribution
  routes; many underlying TLS/BVD dictionaries are already represented indirectly.

## Reproducibility and next decision

The [manifest](africa_investigation_2026-10-28.json) records accepted/catalog hashes,
full ranking hash, Glottolog ancestry pin, intake release versions and resolved
full commits, separately from newer raw-checkout HEADs. Twelve original book
files, four Dictionaria lexical/metadata tables per source plus README, and all
six RefLex resources were retrieved outside intake and hashed. GLED and additive
rankings are separate; no empirical-phonetic or semantic validity claim follows
from a successful tokenizer or a dataset's size.

Recommended order is AF01–AF09 above: establish notation/identity, capture measured
core improvements, introduce the best-supported profile, expand substantive
original lexica, then the broader diversity pilots. The goal is a balanced batch
with transparent counts for supplied readings, profiles, written lexical data,
new canonical languages, named varieties and actual GLED replacements. Execution
requires explicit authorization; this investigation changes documentation only.

Verification:38 pinned resource hashes and planning totals checked; the accepted
web manifest remains byte-identical. No implementation or data-change tests are
needed for this documentation-only investigation.
