# Sub-Saharan Africa and Bantu: AF01–AF09 execution

The authorized nine-track batch follows the [investigation](SUBSAHARAN_AFRICA_INVESTIGATION_2026-10-28.md).
The [realized metrics](africa_expansion_summary_2026-10-28.json) distinguish lexical
records, supported concepts, written-only evidence and source changes. Raw ceilings
in the investigation are historical screens, not outstanding admissions.

Realized:619 records across19 constructions, +464 supported core slots and555
mapped slots. Narrow Bantu gains403 records and352 supported slots across the
same485 constructions. Totals:7,331 varieties,2,070,117 forms,468,501 supported
core slots and1,575 GLED primaries. All2,069,498 earlier rows/comments survive.

## Reviewed outcomes

| Track | Accepted action | Boundary retained |
| --- | --- | --- |
| AF01 | Source-scoped reading-origin disclosure for 302 Bantu constructions using Grollemund/TLS; eight identity/notation decisions | No automatic Kamba merger, Ndebele reassignment, RefLex family-to-language match or Ngoni geographic correction |
| AF02 | 249 supplied upstream readings: Ngoreme42, Nilamba40, Kamba Kitui42, Ikizu42, Nata46, Suba37 | Temi/Sonjo gloss–form alignment is suspicious; Shashi identity/notation needs separate review; alternatives, noun-class ambiguities and narrow senses held |
| AF03 | 31 Wiktionary records: Zulu22/21 concepts and Xhosa9/9 | Preserve supplied IPA, clicks, tone and all admitted alternatives; avoid possessive kinship and homonyms |
| AF04 | Ten exact non-ideophonic Tumbuka broad readings | No invented lexical H or length, ideophones, ambiguous clusters or general-purpose pronunciation rules |
| AF05 | 18 Ruruuli original dictionary entries, written-only | Source augment/classes/examples retained; no pronunciation invented from unmarked tone |
| AF06 | Fwe29 original entries (26 profiles, three written-only); Gyeli66 (64 profiles, two written-only) | Gyeli dictionary becomes primary, all36 old GLED rows retained. Fwe stays GLED-primary: reviewed26 phonetic concepts cannot safely replace36 |
| AF07 | Two previously unrepresented canonical languages: Konyagi/Wamey20 entries, Kam30, written-only | Exact RefLex sources39/3074, original authors/class forms/alternatives, CC BY-NC-SA4.0; no phonetic coverage claim |
| AF08 | 76 tone-preserving finite readings: Bambara12, Soninke30, Koyra Chiini34 | Original values retain tones dropped by upstream conversion. Toneless or uncertain nasal/creaky/compound cases held |
| AF09 | Hdi45 finite source readings; Sidaama45 written-only dictionary entries | Hdi dictionary becomes primary, all32 old GLED rows retained. Sidaama headword/official-orthography/prominence conventions need reconciliation before readings |

Authored decisions are the `africa_af01` through `africa_af09` CSV files alongside
this report. AF02 has499 reviewed rows, AF03 also records exclusions, and AF04
records20 candidates rather than claiming its whole raw ceiling. AF06 keeps five
prenasalized-unit cases as written evidence because the validation engine does not
support those units; splitting a source phoneme to force validation is not justified.
Two GLED primaries are replaced; their earlier evidence and original cognacy remain.
Konyagi's frozen identifier is `atl-wamey`, following the canonical Glottolog name;
the Konyagi source alias remains searchable. These are two languages, zero new
named dialect/sample constructions. Existing-language dictionary slices are not
new-language gains.

## Evidence and reading conventions

Original resources are pinned in [the execution manifest](africa_execution_sources_2026-10-28.json)
and [the lexical registry](../src/arcaverborum/data/african_lexical_sources.json).
Native records, exact headwords, senses/POS, class/prefix fields, author/publication,
license, version and record hashes remain in lexical comments. No new expert
cognacy is manufactured. RefLex attribution joins are independently hash-guarded.
Original source cognacy, where present, remains in its native record rather than
being promoted into an invented cross-source namespace.

Fwe uses Gunnink2022's phonology and tone chapters plus appendix C. Citation tone
is not an instruction to add phonemic length; quantity and floating/underlying H
remain distinct. Gyeli uses Grimm2021's reading guide, phonology and appendix III:
unmarked syllables are underlyingly toneless, bound stems retain their boundary,
and noun-class prefixes remain in the original evidence. Both are CC BY4.0
Language Science Press sources. The frozen repository versions are immutable.

Tumbuka follows [Hamann, Miatto and Downing2019](https://www.internationalphoneticassociation.org/icphs-proceedings/ICPhS2019/papers/ICPhS_3617.pdf)
for a bounded segmental reading; phrase realization is not lexical tone.
Hdi's [dictionary guide](https://github.com/dictionaria/hdi/tree/0a286be9392aade7007533f7de5e81e52ee636bb)
establishes gh/hl/zl/glottal notation. The bilingual source evidence remains visible.
The [Sidaama guide](https://dictionaria.clld.org/contributions/sidaama) distinguishes
official orthography, phonemic analyses and unmarked prominence; its CLDF Headword
and Official_Orthography fields differ. This batch keeps both, without guessing a
complete phonetic reading. Multisense entries retain all senses and the reviewed
frozen target; alternative meanings are not erased.

West African sources are frozen Hantgan/List and BAF2 wordlists, not independent
corroboration of the converted intake. Explicit original tone survives in derived
readings. Source vowel-mora sequences and geminate sequences remain visible;
no tonal pattern is collapsed or unmarked tone filled in. Koyra Chiini ñ maps to
palatal nasal ɲ; nasal-vowel/creaky cases outside this finite review remain held.

`Segments_Source=source` describes upstream segment origin. Grollemund/TLS values
were profile-converted upstream; the new `custom/reading_evidence.csv` metadata
makes this explicit and does not reclassify them as independent phonetic elicitation.
Derived dictionary readings have `profile` status. Written-only records keep blank
segments and `unclean` status and add no supported phonetic coverage.

## Reproduction and verification

Use the installed `.venv/bin/python`, preserving local merkmal. For each of the
seven registry datasets, `scripts/stage_african_lexica.py --dataset NAME --fetch`
verifies immutable bytes and stages outside active intake. Only a genuinely absent
namespace may be appended using `scripts/append_source_intake.py`. This batch's
seven namespaces have already been appended once; do not replay that append or
subset-ingest over active tables.

`scripts/compile_african_lexica.py` validates the original-source ledgers;
`--write` compiles authorized reviews. `scripts/compile_african_profiles.py --review
docs/africa_af04_review_2026-10-28.csv` checks Tumbuka. The original-source compiler
recognizes promoted primary ledgers and preserves unrelated written/GLED supplements.
Profiles use exact whole-form anchors, SHA guards and source/member/form/sense guards;
they cannot generalize to unknown compounds or reinterpret supplied segments.

Rebuild accepted constructions only, then aggregate, report and build the research
web artifacts. Verification compares all previous lexical rows, retaining multiplicity,
while allowing new reading/review comments, derived quality scores and current primary-selection metadata. The68 preserved GLED rows acquire explicit guarded concept mappings, which recompute their mechanical field-presence score; this is not a new phonetic-quality claim.
The summary records actual realized gains and hash checks. Browser checks exercise
written-only exports, tone/profile provenance, old GLED preservation and existing
research workflows. Publication evidence is recorded in STATUS after deployment.

Publication: data commit `a1f8e941692d5e1f6ec893e37edf916d5b40058e`;
[CI](https://github.com/tresoldi/arcaverborum/actions/runs/40760562984) and
[Pages](https://github.com/tresoldi/arcaverborum/actions/runs/40760563003) succeeded.
The canonical live manifest, catalog, recordings, bibliography and six family
shards match committed bytes. Live African browser exports pass.
