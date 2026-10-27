# Iquito — source-scoped dictionary supplements, 2026-10-27

The accepted primary transcription source remains huntergatherer; its original
forms, supplied segments and cognacy records are preserved. The Dictionaria
Iquito dictionary is an additional source, not a replacement or a new variety.
The construction gains 26 reviewed dictionary forms and four supported core
slots (125 → 129/161), reaching 382 forms.

Michael and Beier (2021), Dictionaria 14, provide source-specific spelling and
phoneme tables 1–4. The compiler uses only a conservative subset: vowel length,
j → h, r → ɾ, y → j, and documented palatal/labiovelar digraph contexts.
Source-marked high tone is retained; unspecified low/null tone is not inferred.
This is the dictionary's partial tonal representation, not surface phonetics.
Mixed-tone long vowels are withheld so the position of high tone is not lost.
Other ambiguous palatal/hiatus/glide cases, clitics, spaces and unreviewed
characters also remain outside this first profile.

Of 62 reviewed senses, 26 have admissible readings and 36 are held. The
whole-form profile under custom/supplement_profiles/dictiquito.tsv is restricted
to reviewed source headwords and guarded by SHA256 in custom/supplements.csv.
It cannot affect primary forms or another source. Derived output is explicitly
Segments_Source=profile, never source. Original dictionary entry/sense fields,
pronunciation notes, root and variant strings survive in evidence comments.
Source variants are not silently merged. No cognacy is inferred or transferred.

Reproduce: `.venv/bin/python scripts/iquito_profile.py --write`, followed by
`build.py update zap-iquito`. Dictionary-sense validation is independent of
pronunciation admission: `scripts/compile_dictionary_maps.py` checks staged
reviews too. See docs/iquito_profile_review_2026-10-27.csv for all holds.

Authority: https://dictionaria.clld.org/contributions/iquito
Source commit: 558c466271b546d00b48979f61a64c4a5a5392c2. CC BY 4.0.
Review status: draft; source-sense/profile review is not specialist certification.
