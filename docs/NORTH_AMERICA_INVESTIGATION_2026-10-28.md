# Central and North American coverage investigation — 2026-10-28

**Recommendation:** begin with reviewed Mexican/Central American supplements,
then invest in Tseltal and Isthmus Zapotec dictionary profiles. Reserve a separate
US/Canada track for sparse profile pilots and community-source acquisition.
Research outcomes and ranked ceilings below are **not lexical admissions**.
No active intake, accepted configuration, profile or website data was changed.

Baseline: data commit `9b1a16c282e8dddc6f52d2a8e325d663505169d1`.
The catalog's North America macroarea includes Mexico, Central America, the
Caribbean and Greenland: **610 accepted varieties, 95,555 forms, 33,038 supported
core slots, 255 GLED primaries**. There are currently no accepted profile-derived
forms in that macroarea. This is a catalog scope, not a claim that all610 are
Indigenous languages or distinct language-level identities.
[Metrics and acquired-source hashes](north_america_planning_summary_2026-10-28.json).

## Recommended work, in order

| ID | Work | Accepted supported core | Unreviewed ceiling / intended outcome | First evidence gate and tradeoff |
| --- | --- | --- | --- | --- |
| NA01 | Tlahuitoltepec Mixe and Highland Popoluca supplements | 97;69 /161 | Up to51;39 missing concepts | Exact recorded Tlahuitoltepec sample and Soteapan Zoque identity/senses. Strong immediate coverage prospect; Voices terms are CC BY-NC. Include the audio-placeholder audit below. |
| NA02 | Bribri and Nawat/Pipil supplements | 86;89 | Up to33;22 | Preserve Bribri dialect labels/tone/optional glottals, and trace Nawat rows to their individual lexical authorities. Strong Central American focus; conversion conventions need review before admission. |
| NA03 | Rarámuri/Tarahumara and Mayo source comparison | 86;91 | Tarahumara up to42 or38, overlapping; Mayo up to29 | Reconcile exact regional samples and stress/normalization conventions, then prefer the best evidence per gap. Substantial northern-Mexican opportunity; comparing sources costs more than copying one list. |
| NA04 | A conservative Tseltal dictionary profile | 38; GLED primary | 116 mapped core concepts in staged dictionary;88 absent from accepted core | Use the dictionary's explicit orthographic/morphological account, dialect metadata and individual senses. Highest documented profile/GLED-reduction prospect; no automatic conversion of all9,616 staged form rows. |
| NA05 | Acquire and stage the two Isthmus Zapotec dictionaries | 38; GLED primary | 9,012 general entries/9,046 senses and952 botanical entries; mapped yield unmeasured | Establish notation, exact La Ventosa/Juchitán scope, attribution and concept mappings. Large lexical-depth prospect with CC BY data; entry counts are neither mapped gains nor new-language counts. |
| NA06 | Sparse US profile pilots: Alutiiq first, Grand Ronde Chinuk Wawa second | 0;2 | Alutiiq has10 mapped core concepts/86 accepted forms; Chinuk Wawa19/142 | Match actual spellings to a documented community/dialect system before defining rules. Smaller core return, but directly addresses unsupported US varieties. Hold mixed historical spelling and unresolved pronunciation. |
| NA07 | Identity recovery and missing-language acquisition, including US/Canada | No admission baseline | Review Nizaviguiti; pursue Miluk source access and Canadian lexical leads; gains unmeasured | Reconcile sample versus language identity and actual lexical reuse terms. Potential language diversity benefit; research may end in a precise hold rather than admission. |

Do not add ceilings across overlapping members, and do not treat token validation
as independent pronunciation certification. A successful reviewed subset is useful;
none of these tasks requires attaining its ceiling or admitting a new language.

## NA01–NA03: exact members and source evidence

| Target | Exact member | Pinned intake version | Terms |
| --- | --- | --- | --- |
| `mix-tlahuitoltepec-mixe` | `mixezoqueanvoices_Tlahuitoltepec` | v1.0.1-329-gc04bf4d | CC BY-NC4.0 |
| `mix-highland-popoluca` | `wichmannmixezoquean_SoteapanZoque` | v1.0 | CC BY4.0 |
| `chi-bribri` | `pachechibchan_Bribri` | d97d914 | CC BY4.0 |
| `uto-pipil` | `utoaztecan_Pipil` | v1.3-1-g33d3734 | CC BY4.0 |
| `uto-central-tarahumara` | `utoaztecan_Tarahumara`; `wheelerutoaztecan_Raramuri` | v1.3-1-g33d3734;v1.0 | CC BY4.0;CC BY-NC4.0 |
| `uto-mayo` | `lionnetyotonahua_Mayo` | 7475017 | CC BY4.0 |

The Tlahuitoltepec member has189 supplied-segment rows and no play-symbol rows.
Mixe-Zoquean Voices attributes primary recordings/transcriptions to Ana Kondić
and collaborators; retain individual source/recording attribution and terms.
[Source repository](https://github.com/lexibank/mixezoqueanvoices).
Highland Popoluca's selected alternative has107 supplied-segment rows. Its name
“Soteapan Zoque” must be reconciled with the accepted Highland Popoluca scope,
without confusing Zoquean language names with a distinct new variety.

Bribri's117 rows have normalized segments, but raw values retain such information
as `(A, C)`, optional `(ʔ)` and inclusive/exclusive alternatives, some of which are
simplified in converted forms. Original Chevrier2017 references and the conversion
must be examined. Preserve uncertainty rather than silently treating an optional
segment as absent. [Pache dataset](https://github.com/lexibank/pachechibchan).
Nawat/Pipil rows cite Miller1984, Aranz1960, Campbell1978 and Hale1964: do not
invent a single modern-dictionary authority for this mixed lexical base.

Uto-Aztecan token strings can contain source/normalized pairs such as `é/e`.
Tarahumara's original value and normalized reading differ in suprasegmental
representation. Review the conversion's treatment of accents and original
regional citations before labelling the reading an evidence upgrade.
[Transcription record](https://github.com/lexibank/utoaztecan/blob/main/TRANSCRIPTION.md).
The two Tarahumara ceilings42/38 overlap; Ópata's47-candidate historical opportunity
is a reserve requiring its own authority/sample review, rather than the first
northern-Mexican target.

## An important quality issue: recording placeholders

`mixezoqueanvoices_Totontepec` and `_Ocotepec` each have196 rows whose Form/Value
is `►`, with no supplied segments. They are recording links, not orthographic
words. The ranker's “orthographic potential” therefore needs a placeholder
exclusion before it is used to select profiles. Totontepec's apparent53-concept
profile opportunity is not ready to profile.

Across the frozen Voices source,1,097 rows in nine members contain this marker.
Among accepted Voices-primary constructions,747 rows across 4 varieties retain
it (see the summary for exact counts).

The accepted Ocotepec Mixe construction currently emits196 such placeholder
rows and has zero supported core. This is a concrete quality-cleanup task:
retain recording metadata/links separately, prevent play icons from being
presented as lexical forms, report any count reductions, and seek actual
transcriptions. This planning turn changes none of those accepted rows.
Do not convert the recording audio to authoritative IPA automatically.
[Row-level member audit](north_america_member_audit_2026-10-28.csv).

## NA04: Tseltal is a promising, bounded profile project

Existing staged `dicttseltal_tzh` uses Polian2020, repository
ca7582dbce9229966a2505d8dc228783255b2dec, CC BY4.0. It has9,616 materialized
form/sense rows,116 mapped core concepts and zero supplied-segment forms.
A wholesale replacement would lose10 currently mapped core concepts; preserve
existing evidence explicitly. The88 missing concepts are spelling/mapping
potential, not verified supported gains or a promised final coverage count.

The source documents practical symbols, apostrophes/hyphens, initial glottals,
inflection and dialect distributions. Those details make a conservative profile
more defensible than an English-letter substitution table. Begin with exact
simple stems with a clear dialect/reading, holding unresolved compounds,
possessive forms and dialect-dependent conventions. The dictionary's presentation
is multidialectal, not a dialect atlas or a single homogeneous speech sample.
[Original documentation](https://github.com/dictionaria/tseltal#the-orthography-used-in-the-dictionary).
Its updated online successor is a separate acquisition/version decision;
do not silently mix the live dictionary with the pinned2020 snapshot.

## NA05: substantial new dictionary sources, already represented language

Downloaded research copies outside active intake at immutable commits:

* `dictionaria/didxazageneral`76c22cf30c23d8f4bc5c83c11013a8cb24fe0f85:
  9,012 entries/9,046 senses, CC BY4.0. Headwords include phonetic-looking
  diacritics and a separate PDLMA field; neither is accepted as IPA merely because
  it tokenizes. Entry-level attribution must survive staging.
* `dictionaria/diidxaza`daf603b21dda05ac60ecc95081696c840e487356:
  La Ventosa lexico-botanical dictionary,952 entries/senses, CC BY4.0.
  Authored by Gabriela Pérez Báez and Terrence Kaufman with named collaborators.
  It documents practical versus PDLMA notation, tone and syllabic nuclei;
  the fields should be aligned rather than treating ordinary spelling as complete
  phonemic information.

Both link to isth1244, already accepted as `oto-isthmus-zapotec` (50 forms,
38 supported core, GLED primary). They supply new evidence, not two new languages.
Stage separately, keep dictionaries/sample scopes distinct, map reviewed bilingual
senses, then derive only defensible readings. Broad botanical species entries may
lack appropriate frozen concepts; propose concepts separately instead of forcing
species into generic “tree/flower” slots.
[General dictionary](https://github.com/dictionaria/didxazageneral),
[botanical dictionary and notation](https://github.com/dictionaria/diidxaza#typology-phonology-and-orthography).

## NA06–NA07: US and Canada need a different acquisition strategy

**Alutiiq/Pacific Gulf Yupik** (`esk-pacific-gulf-yupik`) is a small but useful
profile pilot. The Alutiiq Museum publishes an alphabet, pronunciation lessons,
orthography references and attributed recordings. Match Kodiak versus Chugach
sample and spelling conventions first, including Russian loan notation and
context-sensitive consonant rules. The museum's available learning material is
an authority to investigate, not an assumed bulk-dictionary reuse license.
[Community lessons](https://alutiiqmuseum.org/alutiiq-people/language/lessons/).

**Grand Ronde Chinuk Wawa** currently mixes modern phonemic-looking forms and
older respellings. An exact-form subset may help, but a universal profile would
repeat the Chickasaw mixed-system mistake. Use the tribal dictionary/alphabet
and distinguish Grand Ronde from older regional trade-jargon varieties.
[Tribal language program](https://www.grandronde.org/culture-history/chinuk-wawa-language/).
Keep the separate accepted legacy-source constructions out of this profile scope.

**Miluk** (milu1241) is absent from accepted catalog identities and active intake.
The community site identifies a1953 Laura Hodgkiss Metcalf recording collection,
with Swadesh recordings and Morgan's transcription/notes, and reports284 distinct
words in that interview. This is a concrete source lead, not a ready licensed
wordlist or284 promised admissions. Establish usable transcription, senses,
community/source attribution and redistribution terms before staging anything.
No contact, permission request or bulk lexical extraction has been made.
[Community source](https://miluk.org/).

**Canadian/Northwest lexical depth:** Northern Haida already has1,023 accepted
forms/133 supported core from IDS; a modern dictionary would add or corroborate
evidence, not create a new Haida language. GiellaLT's Northern Haida project is
a concrete lead, but its pinned LICENSE includes explicit original-dictionary
exclusions and Cree-related text. Resolve the actual Haida lexical terms and
authority rather than assuming a repository software license licenses all lexical
material. Do not replace well-supported IDS evidence with unreviewed FST stems.
[Project](https://giellalt.github.io/lang-hdn/),
[license at inspected commit](https://github.com/giellalt/lang-hdn/blob/3badb20987fbc2281103decf8412753f94991c9e/LICENSE).

Cherokee's52-concept spelling potential is a research alternative, not a profile
recommendation yet: first establish which pronunciation contrasts and dialects
are actually specified by each entry. Chickasaw's inactive proposal remains held
and its earlier19 spelling matches do not establish IPA. Yurok and Chickasaw
supplement pilots are completed work, not fresh unexecuted tasks.

## Missing identities: six Lexibank members, not six new languages

| Exact member | Actual lexical evidence | Decision / next gate |
| --- | --- | --- |
| `mixezoqueanvoices_Copainala` | 152 supplied rows; dialect code copa1239 | Reconcile under accepted Central-South Chiapas Zoque/copa1236; dialect/sample evidence, not automatically new language. |
| `mixezoqueanvoices_Nizaviguiti` | 196 rows,193 supplied; no code | Highest-priority identity investigation. COLMIX researchers explicitly discuss unresolved classification of this community cluster. Preserve named sample; do not guess an Ulterior-Mixe or neighbouring code. |
| `mixezoqueanvoices_Tapalapa` | 198 supplied rows; no code | Reconcile Northeast Chiapas Zoque/rayo1235 scope; primary classification evidence associates Tapalapa with that language. |
| `mixezoqueanvoices_Tutla` | 199 supplied rows; family code lowl1263 | Resolve Santiago Tutla versus accepted Mazatlán Mixe; never register the family as a language. |
| `pachechibchan_Huetar` | Language metadata,0 rows | Hold until attributable usable lexical rows are acquired. |
| `tolmiebritishcolumbia_Tinne-Nakoontloon` | 182 supplied-conversion rows; no code | Trace historical locality/speaker identity and notation; “Tinnē” alone cannot select an Athabaskan language. |

[COLMIX researchers' documentation account](https://ichan.ciesas.edu.mx/hacia-una-documentacion-linguistica-comunitaria-consideraciones-sobre-la-documentacion-de-dos-comunalectos-de-la-lengua-mixe/),
[Tapalapa classification reference](https://glottolog.org/resource/reference/id/317836).
The article's classification uncertainty supports retaining an exact community
identity; it does not authorize creating or merging a language automatically.

Four additional unused Wiktionary members contain just one water-related row
each: Central Puebla Nahuatl, Santa María La Alta Nahuatl, Aranama and Central
Mahuatlán Zapotec. Only Santa María La Alta currently has supplied segments.
Review source language identity and actual lexical attribution before any claim;
these are thin evidence leads, not a meaningful four-language coverage expansion.
A raw Glottolog difference list also includes retired identities, signs,
constructed languages and varieties; its233 unmatched codes are not233 viable
spoken-language additions.

The additive ranker's `lea-lenca-salvador` / `constenlachibchan_LencaHonduras`
17-concept opportunity is an identity alarm, not an admission recommendation.
Honduran and Salvadoran Lenca must not be merged through an inherited code.

## Evidence, reproducibility and planning boundary

* [Regional additive ranking](north_america_opportunities_2026-10-28.csv):306
  member alternatives, filtered from the current accepted-baseline ranking.
* [GLED screen](north_america_gled_screen_2026-10-28.csv):221 member alternatives,
  **zero net-positive supplied-segment replacements**. This is not proof that
  profiles or newly acquired sources cannot replace GLED.
* [Target/source-member audit](north_america_member_audit_2026-10-28.csv): exact
  IDs, row counts, supplied segments, recording placeholders, versions and terms.
* [Metrics/acquisition manifest](north_america_planning_summary_2026-10-28.json):
  source commits, acquired file hashes and explicit zero accepted-data changes.

Reproduce broad triage with `rank_coverage_opportunities.py` and
`rank_gled_replacements.py`, then filter against the committed catalog's North
America identities. Query intake by exact Glottocode+dataset+member; inspect raw
CLDF/authority as well as normalized segments. Compare all primary-source losses
when considering replacements. A ranking is discovery evidence only.

The preceding South American P01–P04 proposals are parked, not cancelled or
completed: Marinahua; compared Kokama sources; Yukpa/Camsá; Johansson convention
audit. This investigation changes the active proposed focus to NA01–NA07.
Execution requires a subsequent instruction to proceed.
