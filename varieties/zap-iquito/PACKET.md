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

## Profile and lexical follow-up, 2026-10-27

Current construction: 425 forms, including 69 dictionary profile forms (43 more
than the first pilot), with supported core unchanged at 129/161. There are 106
reviewed senses: 69 admitted and 37 held. Forty-four additional semantic reviews
include concrete nouns and explicitly distinguished old-man/old-woman concepts.
The documented ni+vowel digraph is distinguished from short n+i before a
consonant or word edge (ani → /ani/); this does not infer surface allophones.
Mixed-tone long vowels, remaining s/ʃ cases and other uncertainties stay held.
The original source's partial H-tone convention is retained; L/null is not guessed.

The first pilot's dated review CSV remains unchanged. Reproduce current output
with scripts/iquito_profile.py --write --review-output
 docs/amazonian_expansion_iquito_profile_2026-10-27.csv. Other sources and every
primary record remain unaffected by the source-scoped profile.

## WN02 — 2026-10-29

Five new exact Iquito partial-tone profiles and seven Media Lengua mappings reviewed in [WN02](../../docs/worldwide_wn02_review_2026-10-29.csv). Media Lengua sell is held for noun/verb conflict. Guarayu profile hold remains; no inconsistent genderlect/nasality system inferred.

Q2026-10-29 adds a separate finite profile file with guarded original sense/reading evidence. Earlier profile bytes and all native alternatives remain unchanged; see the Q execution report and Q03/Q04 reviews.
