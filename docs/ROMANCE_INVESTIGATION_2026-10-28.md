# Romance and Italian-area investigation — 2026-10-28

Planning only: zero accepted lexical changes. Baseline remains data commit
`7de14ecd8710ad399189cd12405d1a4afc50fc54`, 7,315 varieties and 466,443 supported
core slots. [Measured shortlist](romance_baseline_2026-10-28.csv),
[member opportunities](romance_opportunities_2026-10-28.csv) and
[snapshot metadata/hashes](romance_investigation_2026-10-28.json) accompany this report.
The explicit Italian-area shortlist is not a complete Romance census. It includes
cross-border and historical cases; neither country membership nor the everyday
word “dialect” determines language status. No distinct-new-language count is promised.

## Recommended sequence

| ID | Work and baseline | Potential, first gate and tradeoff |
| --- | --- | --- |
| R01 | Supplied-reading supplements: Corsican36, Lombard38, Sicilian99, Ligurian99, Venetian99, Romagnol98 supported core/161 | Frozen Wiktionary member ceilings respectively15,3,9,7,2,2 missing concepts. Review senses, pronunciation scope and exact member before admission. Italian128 has29 Wiktionary or25 Northeuralex candidates, overlapping; include as a secondary control. Fastest source-first gains, but limited new geographical diversity. |
| R02 | Bounded spelling-profile pilots: Lombard38, Venetian99, Gallurese0, Istriot4 | Lombard has67 missing spelling concepts and Venetian37 in the additive ranking. Gallurese254 total forms and Istriot399 are primary-source recovery cases, not measured core gains. Choose a documented spelling system and locality first; prefer small exact subsets over a language-wide conversion. Useful sparse recovery, with greater phonological research cost. |
| R03 | Sardinian and locality provenance audit | Logudorese200 and Nuorese198 forms currently have zero supported core; broad source spelling is not IPA. Saenko's member called Logudorese is assigned to Barbaricino, a dialect under Logudorese. Inspect the original sample before borrowing any evidence across these identities. Audit merged Piemontese, Emiliano, Venetian and Sicilian samples and expose exact locality provenance. Better identity precision may produce metadata improvements rather than new forms. |
| R04 | RVID acquisition pilot: start with Sassarese, Nuorese/Logudorese and one mainland locality after source comparison | New structured broad-IPA source, with small verb inventory per locality and rich paradigm coverage. Preserve cell/POS and lexical meanings; etymon is not a modern concept. Reconcile closest-code metadata manually. GPL redistribution/provenance requirements must accompany any admitted derivative. Strong locality diversity, but not155,029 new lexical concepts. |
| R05 | Alpine acquisition: VerbaAlpina, then digitALD/VinKo feasibility | Prioritize source-attested lexical tokens with locality and documented notation. API/type metadata and recordings alone are not supplied IPA. Unmeasured gains; resolve source-specific rights/export/notation before building adapters. Broadens vocabulary and localities beyond Swadesh, at higher acquisition cost. |
| R06 | Wider Romance follow-up | Occitan0 supported core has60 supplied-reading candidates and87 spelling candidates; broad Romansh0 has4 supplied and129 spelling candidates, with standard/locality scope especially important. Extremaduran4, Picard0, Fala17 and Arpitan31 merit a subsequent exact-source/profile screen. Preserve Italian-area priority; do not repeat completed Galician/Aragonese/Asturian pilots. |

Ceilings are discovery counts, not admissions. Members overlap; supplied-token
status is not phonetic certification. Preserve existing supported concepts.
The separate GLED replacement screen finds Lombard Wiktionary gains3/losses36
and Corsican gains15/losses25 before profiles: supplement first. Sassarese
Wiktionary gains1/losses38. Do not replace a primary simply to reduce GLED counts.

## Locality and source genealogy

Saenko intake is pinned at `v1.0-1-ga463ddc`, CC BY4.0, derived from Saenko's
2015 GLD/Starling wordlists. It is not independent non-GLD evidence merely because
its namespace differs from GLED. All43 Saenko members already match accepted
constructions by code: this is not a missing-language discovery. Genoese,
Messinese, Gardenese, Fassano, Rumantsch Grischun and Lower Engadine already exist.

Four Piemontese members (Lanzo Torinese, Barbania, Carmagnola, Vercelli) share one
construction; three Emiliano (Ferrara, Carpi, Reggio), three Venetian (Venice,
Primiero, Belluno) and three non-Messinese Sicilian members also share constructions.
Retain original evidence on any future split, model parent relationships explicitly,
and report named varieties separately from languages. Upstream Saenko v1.1 is a
refresh candidate, not proof of new lexical content: compare versions first.

Meloni Romance intake has six standard/historical languages and no supplied
Glottocode/Concepticon links. Its reconstruction-oriented lexical alignment needs
semantic/transcription review; it is lower priority for Italian local varieties.

## New source evidence and decision gates

**RVID:** [primary publication](https://aclanthology.org/2020.lrec-1.370/) and
[repository](https://gitlab.com/sbeniamine/Romance_Verbal_Inflection_Dataset).
Research clone pinned at `eb1efef3ef02fbbf06f96f77637736d9cd27db8a` outside intake.
Actual tables:74 varieties,27 with Country=Italy,155,029 forms,2,410 lexeme records,
41 paradigm parameters. The source uses broad IPA and GPLv3. Language metadata
includes town, dating, bibliography and **Closest_Glottocode**, which is not an
assertion that the sample equals that language. Candidate localities include
Ascrea, Servigliano, Macerata, Travo, Lugo, Genova, Cremona, Cairo Montenotte,
Valle d'Istria, Alpago, Nova Siri, Papasidero, Calvello, Casacalenda, Lucera and
Mussomeli. Infinitives may support a bounded lexical pilot; full paradigms require
an explicit morphology-aware representation. Keep Latin inflection and cognate
namespaces separate from modern semantic mappings. Validate cleaned readings
against original cited authorities when uncertain.

**VerbaAlpina:** [project methods](https://www.verba-alpina.gwi.uni-muenchen.de/?p=10700),
[API](https://www.verba-alpina.gwi.uni-muenchen.de/?api=1),
[example data rights metadata](https://www.verba-alpina.gwi.uni-muenchen.de/?p=9038).
Versioned geographic lexical evidence and CC BY-SA4.0 data are promising.
Distinguish attested token, morphological type and phonetic representation; types
are not a pronunciation dictionary. Pin a release, verify the selected records'
rights and source notation, and preserve town rather than assigning a whole
continuum one language label. No bulk acquisition or gain measured here.

**digitALD:** [university publication record](https://uni-salzburg.elsevierpure.com/en/publications/digitale-version-digitald-der-zwei-teile-des-aldversione-digitale/).
217 localities/1,950 atlas maps offer Ladin and neighboring coverage. Public access
is not a redistribution grant; establish structured export, applicable rights and
the dialectological transcription key before conversion. No OCR-to-IPA shortcut.

**VinKo/AlpiLinK:** [project description](https://alpilink.it/en/vinko/) provides
Italian-area locality recordings. The project describes CC BY-NC-SA4.0, while
other catalog descriptions differ; resolve terms against the exact deposit/version.
The [repository](https://clarin.eurac.edu/repository/xmlui/handle/20.500.12124/74)
blocked this investigation's automated access. Treat audio and sentence/morphology
material separately from transcribed lexical evidence. No IPA gain established.

**Sound Comparisons Romance:** [2019 deposit](https://zenodo.org/records/3596165)
is cognate-based rather than meaning-based, with draft readings and some samples
without transcriptions. Its restricted CC BY-NC-ND4.0 deposit is not ready for
adapted redistribution. Reopen on an appropriately licensed release or explicit
permission; no contact or acquisition is authorized by this investigation.

## Execution and closure criteria

The next authorized batch should execute R01–R06 in order with bounded admit/hold
ledgers. Source/version/profile drift guards, exact source member, original sense,
locality, transcription status and preserved prior evidence are mandatory. Stage
new sources outside active intake; never overwrite active tables with a subset.
Measure new forms, supported core slots, named varieties, distinct languages and
GLED replacements independently. Existing American NB proposals are parked, not
completed. This investigation changes documentation only; no data rebuild required.
