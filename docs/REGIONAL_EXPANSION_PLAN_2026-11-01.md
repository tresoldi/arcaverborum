# Regional coverage and source-quality proposal — 2026-11-01

Historical proposal, subsequently authorized in full by the user.
[Execution and measured outcomes](REGIONAL_EXECUTION_2026-11-01.md) supersede
these prospective counts, retrieval failures and source-choice recommendations.
The planning baseline was7,365 constructions /2,119,754 records.

[Geographic triage](regional_gap_audit_2026-11-01.json) uses the committed web
catalog, overlapping rectangular windows, and original coordinates. Its counts
include historical and sign-language entries and do not measure modern spoken
language completeness. Do not sum overlapping regions or interpret zero supported
segments as absence of written evidence. A single representative coordinate does
not describe a language's geographic extent. Specific examples below were checked
against current accepted output; proposed yields remain unverified.

## Current intake triage and planning infrastructure

[Fresh scoped member screen](regional_source_triage_2026-11-01.csv) checks23
selected accepted constructions and finds31 member-level alternatives. It streams
the shared parameter catalogs, queries indexed intake by exact Glottocode, keeps
members separate and subtracts already supported concepts. Segment normalization
is only a triage screen; it does not certify original pronunciation or semantics.
Examples: Inoric/Zay58, Gyeta55, Argobba54 Kitchen candidate core slots; Harsusi43;
Hefei54; Suzhou/Wenzhou49 each; Southern Yukaghir32; Tofa30; and Yagnobi41 in
several overlapping CALS members. These are prospective ceilings, not admissions,
and cannot be summed across overlapping sources or members. Profile recovery in
the primary source and whole-construction quality improvements fall outside this
additive screen.

The existing worldwide ranking refresh was interrupted after its whole-parameter
materialization reached roughly4.24GiB RSS. No failed refresh is used as current
ranking evidence. Refactor that planning utility to stream/index parameters and
apply explicit memory budgets before the next routine worldwide refresh. The
scoped screen supplies current evidence for this proposal without materializing
the complete multilingual parameter catalog.

The exact-code missing-member audit finds737 leads, including421 language-level
labels,281 dialect labels,20 family nodes and15 unclassified rows. These are not
737 or421 verified missing languages: aliases, accepted parents, historical scopes
and original lexical payload must be checked individually before any new-language
claim. A geographic/identity audit should precede attempts to fill map gaps.

## Recommended sequence

### R01 — Southern Cone: original dictionaries and exact historical evidence

Current Yámana 715 records/138 supported core concepts, Qawasqar 634/138,
Selk'nam 864/137 and Tehuelche 868/144 are substantial existing constructions.
Charrúa 10, Chaná 16 and Güenoa 1 are accepted historical written records, not
missing languages. Do not repeat their completed pilots as new gains.

Begin with the [DILA Mataguayan comparison](https://dila-ling.github.io/pict-glotales/resultados/)
and [DIWICA](https://lenguawichi.com.ar/diccionario/) for Wichí, Chorote, Nivaĉle
and Maká; compare current accepted senses and primary source genealogy before
claiming gains. The DILA table supplies row-specific textual references and
adapted phonetic readings, while expressly retaining ambiguous doubled vowels.
DIWICA is a living pluridialectal dictionary; dialect attribution and original
entry authorship must survive transport. Neither public display nor a repository's
software licence establishes redistribution terms for every dictionary source.

For Fuegian depth, inspect the [official Yagán materials](https://www.pueblosoriginarios.gob.cl/lenguas-indigenas-en-chile/lengua-yagan)
and original dictionaries against the accepted IDS evidence. Modern revised
orthography is a different source/stage from historical Bridges or Bove citations.
Charrúa Silva1841, modern Chaná, Haush and Teushen retain their existing original-
page/identity/notation gates in HELD; no new reopening evidence was established
here. Benefit: original meanings and regional depth. Cost: historical attribution
and transcription review; large gains for the smallest historical languages
cannot be promised.

### R02 — Horn: replace weak evidence and broaden Cushitic/Ethiosemitic coverage

Afar 241/63 and Saho 143/54 use Wiktionary; several Oromo constructions retain
GLED. Inoric 199/37, Gyeta 199/39, Zay 171/40 and Argobba 167/43 use Kogan.
Somali already has 1,025/114, so basic-language presence is not the principal gap.

First review member-specific Kitchen alternatives for the named Ethiosemitic
constructions, and existing RefLex/other intake for exact Cushitic members. Full
frozen RefLex transport is already complete; do not propose importing it again.
Then acquire original Afar/Saho/Oromo and other Ethiopian/Eritrean dictionaries
or lexical appendices, with their exact locality and phonological conventions.
Finite source-specific Latin-orthography profiles may recover useful readings;
quantity, glottal/ejective contrasts and lexical tone/stress require independent
notation evidence. Keep wider Eritrean, Somali and Djiboutian coverage visible
rather than treating Amharic as a proxy for the region. Benefit: strong reduction
of weak-source dependence. Cost: dialect identity, source conventions and uneven
available dictionary depth.

### R03 — Western Iran: recover thin varieties and distinguish local lects

Northern Luri is 12 records/0 supported core concepts; Gurani 29/0. Southern Luri
has 104/35 with a GLED primary. Bakhtiari already has 178/112 with IECoR.

Investigate the [Atlas of the Languages of Iran materials](https://carleton.ca/iran/)
and [Bamberg lexical project](https://www.uni-bamberg.de/orientalistik/allgemeine-sprachwissenschaft/forschung/projekte/bamberg-lexical-database-for-contemporary-iranian-languages-bldcil/)
for actual lexical tables, transcription guides, samples and redistribution basis.
These are discovery leads; a complete licensed lexical export has not been
verified. Target Luri, Gurani/Hawrami, Laki and local Kurdish/Zagros samples after
reconciling accepted identities. Compare [VejînLex](https://lex.vejin.net/en/)
at the original dictionary/edition level; it aggregates resources whose evidence
and rights should not be flattened. Arabic-script spelling does not determine
short vowels. Benefit: potentially large gains in genuinely thin constructions.
Cost: access, exact locality and interpretation of original transcription.

### R04 — Arabia: South Arabian minorities plus geographically precise Arabic

Bathari is 1/1, Hobyót 47/38 with GLED, Harsusi 206/51, Mehri 716/100 and
Soqotri 452/86. Prioritize Bathari/Hobyot/Harsusi original lexical material before
another general Arabic list. [Castagna's Kuria Muria study](https://etheses.whiterose.ac.uk/id/eprint/22573/1/Castagna_G_LanguagesCulturesAndSocieties_PhD_2018.pdf)
provides an original scholarly source lead; exact lexical scope, notation and
reuse still need review. Preserve lateral/pharyngeal contrasts, quantity and
morphological citation conventions instead of normalizing them away.

For Omani, Yemeni, Najdi, Hijazi and Gulf Arabic, inspect variety-specific original
lexicons and the [NYU CAMeL resources](https://nyuad.nyu.edu/en/research/faculty-labs-and-projects/computational-approaches-to-modeling-language-lab/resources.html).
MADAR's equivalent words/phrases and CAPHI's phonetic convention are distinct
resources; do not assume every MADAR entry supplies CAPHI or IPA. MSA cannot stand
in for local lects, and phrases do not automatically supply independently elicited
core words. Benefit: neglected diversity and stronger pronunciation evidence.
Cost: vowel information, locality, clitics and source-specific terms.

### R05 — Eastern China: lexical comparisons, with tone and register intact

Hefei Mandarin has 150 records/37 supported core concepts. Suzhou 583/102,
Wenzhou 546/102 and Shanghainese 530/102 are already present. Review exact
Beida/Liu/Hou source members in intake for additive depth and source fidelity.
Expand Wu, Min, Gan, Hakka and Jianghuai samples on genuine vernacular word
lists, retaining locality, citation tone, sandhi context and literary/colloquial
readings. Character pronunciation inventories are not automatically lexical
translations; do not construct local words from Mandarin or character readings.

The [community Fuzhounese dictionary](https://fuzhounese.org/) is an additional
source lead, not a ready authority: it explicitly lacks recordings for many
words, and source editions, transcription and terms need examination. Benefit:
substantial depth and local variation. Cost: tone conventions, mixed sources and
character-versus-word distinctions; one generic pinyin profile is inappropriate.

### R06 — Mongolia/Mongolic: quality-led Buryat work and original comparisons

Mongolia Buriat is 30/28 and Russia Buriat 45/37, both GLED primaries. Bonan
already has 178 written records with no supported core readings; it is a reading-
recovery lead, not a new-language absence. Review existing Robbeets and other
original member evidence, then source-specific dictionaries/profiles for the two
Buryat constructions and further Mongolic lects.

[ILCAA's comparative Mongolic vocabulary](https://mongolicbv.aa-ken.jp/) surfaced
as a promising primary-project lead, but direct page retrieval timed out here;
no payload, version, member inventory or reuse entitlement is asserted. Keep
written/classical Mongolian separate from modern readings, and disambiguate
Khamnigan Mongolic versus Evenki when such labels occur. Benefit: clear quality
opportunities. Cost: exact sample identity, original access and script/stage
conventions; a Khalkha profile cannot automatically serve Buryat or Bonan.

### R07 — Kazakhstan and neighbours: local samples and dictionary depth

Kazakh already has 268 records/142 supported core concepts. A map with one
Kazakh point is not evidence of an absent Kazakh lexicon. Prefer local variety
attribution, dictionary depth and weaker neighbouring constructions over another
short standard-language basic list.

The already ingested [Central Asian Language Survey](https://github.com/lexibank/cals)
has 15,826 raw rows/88 members in its recorded metadata (v1.1); these are intake
counts, not new accepted coverage. Audit member-specific complements, including
Yagnobi's accepted 198/94 construction, and exact Kyrgyz, Uzbek/Karakalpak,
Tajik/Pamiri and neighbouring minority scopes. Do not sum several source members
sharing one Glottocode as distinct additive gains. Review original dictionaries
for full vocabulary and feasible source-specific Cyrillic/Latin profiles.
Benefit: geographic and lexical depth. Cost: sample identity, borrowing, quantity,
script reform and substantial existing overlap.

### R08 — Siberia: original dictionaries, weaker small varieties and corpus lemmas

Kerek is 2/0, Lower Chulym Turkic 9/0 and Mednyj Aleut 1/0. These are thin written
constructions. In contrast, Northern Yukaghir 929/141, Amur Nivkh 982/127 and
Nanai 689/147 already have substantial evidence. Southern Yukaghir 249/117 and
Tofa 256/115 have additional-source review leads in existing intake.

Inspect [INEL's dictionaries and corpora](https://inel.corpora.uni-hamburg.de/portal/),
particularly its Forest Enets and Ket dictionary routes and exact smaller lects.
Per-resource download and reuse conditions require checking; one corpus's
NC-SA terms do not establish the status of every other resource. Corpus lemma,
root, inflected word and gloss fields need distinct treatment. Historical Kamas,
Assan and other attestation slices must retain dates and uncertain notation.
Benefit: original evidence and small-variety recovery. Cost: dialect/stage scope,
annotation interpretation, quantity and original transcription conventions.

## Worldwide balance and first gates

Before admissions, audit geographic display against all accepted varieties,
missing/representative coordinates, collection filters and language/dialect/stage
identity. Produce separate measures of presence, lexical depth, usable reading
coverage and source fidelity. Do not invent distribution polygons or extra
language counts to fill map space.

Keep Amazonia, New Guinea/Torricelli and underserved African families in the
worldwide reserve queue using the already established U/S source and identity
holds. This regional batch should not consume every future acquisition slot.
For every region, preserve complete original editions, native sense IDs and
source genealogy; admit only reviewed source meanings and readings, retaining
unmapped dictionary depth when exact core equivalence is unavailable. New named
varieties, new canonical languages, added records and pronunciation recovery are
separate outcomes. All newly imported formal identities need the extraction-loss
and large-identity-group checks established in the colexification repair.

The first execution packet should combine R01/R02's existing-evidence review
with a bounded original-source acquisition for R03/R04. R05–R08 follow one at a
time. Candidate transport, entry counts, member-level potential, licensed usable
rows and realized accepted gain must remain separate. Every admission starts with
identity/edition, reuse, transcription and exact-sense gates. No numerical total
gain is promised for this plan.


## Worldwide reserve: existing quality opportunities remain active

Busoa641/62, Kaimbulawa341/60 and Wotu313/59 still have GLED primaries despite
substantial accepted alternative evidence; Lepcha1,335/80 still uses Peiros.
These remain whole-construction authority/contrast reviews already recorded in
NEXT, not unperformed imports or new language additions. Reserve a small parallel
quality track for them and evidence-ready Amazonian/New Guinea/African cases while
the requested regional tracks proceed. Etruscan and Elamite remain protected
ancient-language priorities under the existing source and historical-stage gates.
