# South American lexical dataset assessment — JOHD555,2026-10-29

**Worth pursuing, chiefly as a lead to original HGN phonemic fields and separately scoped reconstructions. Do not bulk-import the combined table or count it as an independent corroborating source.** This assessment makes no lexical admissions and leaves the Q baseline unchanged.

[Article](https://doi.org/10.5334/johd.555): Arozarena Gómez, Verkerk and Tanti,2026, *A CLDF-Standardized Lexical Dataset for Quantitative Diachronic Research of South American Languages*. [Dataset concept DOI](https://doi.org/10.5281/zenodo.19458765) resolved to [record20330494](https://zenodo.org/records/20330494) at inspection. Downloaded all six files; every advertised MD5 verifies. The record/README declares CC BY4.0. [Repository](https://github.com/lumenauta/south-american-phylogenies), inspected commit `8d8b6358078dfbedc2df857cee48357d047cc09e`. Raw downloads, notebooks and checks are cached under `raw/curation/johd555/`.

## What the actual files provide

299 source members,25,203 forms and1,521 parameters. Fifteen named proto-languages account for4,842 forms; the284 other members account for20,361 forms. The final table has six fields: ID, Language_ID, Parameter_ID, Form, Segments and Source. Original glosses, source-row IDs, contextual notes, alternatives and uncertainty must be recovered from upstream material rather than assumed present in this derivative. All Concepticon identifiers have `.0` suffixes and need explicit integer-string normalization.

An NFC-trimmed exact `(Glottocode, Concepticon ID, Form)` screen matches17,807 rows to current intake. This establishes substantial overlap, not transcription certification or identical source ancestry in every matching row. Sources already held include TuLeD, Galucio Tupi, Chapacuran, Chaco, Arawakan/Tukanoan and Hunter-Gatherer material. The7,396 nonmatches include4,713 proto rows and2,683 other rows. There are786 nonmatching non-proto rows with HGN among their source references; these are candidates, not786 new usable readings. Code mismatches, transcription changes and versions can cause nonmatches.

Seven non-proto members lack an exact accepted Glottocode match: Roçado/Rio Negro Nadëb, Tanimuca, Akawaio, Andoke, Yavitero and Trinitario. Five have represented language/broader-identity counterparts under different codes: tani1257, akaw1239, ando1256, yavi1244 and trin1274. The two Nadëb dialect scopes require member-specific treatment within nade1244. These are not seven established new languages. Proto-Tucanoan's family code tuca1253 also occurs in accepted output; never infer modern-language equivalence from that match.

## Strongest discovery: omitted original HGN phonemic evidence

The cached Lexibank Hunter-Gatherer v2.0 builder (`lexibank_huntergatherer.py`, lines130–152) selects `Orthographic Form` and emits only nonempty values. It stores `Phonemicized Form` as an auxiliary field, so entries with only phonemic forms never enter that CLDF forms table. Original per-language JSON tables are already cached and contain those readings with source context.

Screening the original cached South American tables finds **11,962 phonemic-only rows across101 source members**. These are raw rows across basic/flora/cultural tables, not unique concepts, independent attestations or guaranteed coverage gains. Some readings contain notation requiring a profile, alternatives, bound forms or uncertain analyses.

**Nadëb/Roçado, source122, is the first recommendation:**341 phonemic-only rows (178 basic/114 flora/49 cultural), against only one accepted record in nad-nadeb. Rio Negro source121 has154 phonemic-only rows and must remain a separate dialect sample. I checked the [live original Roçado page](https://huntergatherer.la.utexas.edu/languages/language/122): its basic table contains original phonemic blood, bone, water and pronoun entries despite empty orthographic cells. This is stronger acquisition evidence than a renamed Glottocode or the derivative's small pronoun slice.

[Member-level leads](johd555_hgn_phonemic_leads_2026-10-29.csv) preserve source IDs, canonical-code suggestions, table counts and current accepted scope. Other large raw leads include Paraguayan Guaraní290, Cha'palaa289 and Nivaclé282; their existing richer sources mean raw counts alone do not establish priority. Earlier Bribri original-reading recovery concerns selected existing intake records; phonemic-only omitted rows are a separate gap.

## Reasons to retain originals

The repository notebooks are useful audit evidence, but require review before reuse:

* `strip_parentheses_spaces.ipynb` removes parentheses/spaces and digits1–9 from a form column. Depending on the source convention, those can encode alternatives, boundaries or tone. This does not establish that every final row lost tone, but prevents trusting the process without per-source comparison.
* `fix_proto.ipynb` splits alternatives and removes stars, hyphens and parentheses. Reconstructed status and morphological/uncertainty notation therefore cannot be inferred from the final spelling alone.
* The archived HGN scraper CSV has misaligned headers: in Mapudungun “above”, the column labelled Phonemicized Form contains Portuguese *acima*, while actual *wente* occurs under Proto-Language. The [original HGN table](https://huntergatherer.la.utexas.edu/languages/language/265) confirms the correct fields. This is a defect in that intermediate CSV, not evidence that final *wente* was replaced by Portuguese. Read the original JSON/HTML by actual headers.
* The combined Source field and BibTeX are useful pointers, but do not preserve all original row-level citations, notes or independent source genealogy. The original HGN page itself can contain questionable semantic/person labels, so correct extraction still requires sense review.

## Recommended bounded follow-up

1. Start with a20–50-concept original Roçado pilot after exact sense, notation, citation and alternative review; preserve its one existing record and the separate Rio Negro scope. Use a reviewed additive original-source namespace or another explicitly preserving mechanism, not a subset overwrite of the64,607-row Hunter-Gatherer intake.
2. Rank the other100 HGN member leads against accepted supported gaps and original phonological information. Review exact representations, including rows already present elsewhere, before counting gains or changing primary preference.
3. Treat the15 proto inventories as a distinct research workstream. Prioritize substantive Proto-Quechuan832, Proto-Aymaran743 and Proto-Guaicuruan733 inventories if reconstruction coverage is desired; check original editions, citations, historical scope, stars/uncertainty and reuse. Reconstructions must not appear as attested ancient languages or increase an extant-language count.
4. Use the aggregate's mappings and bibliography as comparison aids. Reconcile the seven apparent missing-code cases and sample the2,683 non-proto nonmatches; import only independently reviewed additions or corrections.

The CC BY declaration is encouraging, but original component attribution and terms still need reconciliation where relevant. No contact, lexical migration, primary promotion or reconstruction admission is authorized by this assessment request.

[Machine-readable assessment](johd555_assessment_2026-10-29.json) records pinned versions, hashes, screens and limits. Counts are measured against the Q accepted baseline:7,343 constructions/2,072,595 forms.
