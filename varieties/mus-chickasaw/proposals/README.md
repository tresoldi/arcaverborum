# Chickasaw dictionary/profile pilot — 2026-10-27

The accepted GLED construction remains 39 forms / 37 core concepts. The Wiktionary candidate has 549 forms, including 105 core rows covering 66 concepts. It mixes modern Munro–Willmond and Humes spelling without row-level orthography labels. A wholesale spelling profile would falsely certify ambiguous data.

`profile.tsv` is an **inactive advisory proposal**, not a custom profile. It covers 44 spellings / 34 core concepts with positive modern spelling diagnostics. `core_evidence.csv` records all 105 core rows, proposed readings, dates, dictionary query URLs and exact entry matches. Nineteen rows have exact native dictionary spelling matches; those establish lexical corroboration, not IPA certification or agreement on orthography. Source senses still require review.

The [Chickasaw Nation](https://www.chickasaw.net/our-nation/culture/language.aspx) documents the two spelling systems. The [native dictionary](https://www.achickasawdictionary.com/) supplies spellings, audio and English pronunciation respellings; the latter are not IPA. Bounded English-headword API query results are cached locally, not redistributed as a dictionary dump. Run `python scripts/chickasaw_pilot.py --fetch` to refresh queries, or omit `--fetch` to reproduce from cache.

The prototype handles explicit vowel length, nasal underlining, high accents, glottal stops and established consonant digraphs. It rejects unsupported legacy letters; plain unmarked spellings are not enough to identify a spelling system. It does not infer missing pitch, glottals or nasal vowel duration. Native/specialist review and a sense audit must precede activation. The proposed 34-concept subset currently falls below the accepted 37, so a source switch is unjustified.

Phonological references: [Joshua D. Hinson, OWPIL 2 (2016), pp. 6–7](https://www.ou.edu/content/dam/cas/anthropology/docs/OWPIL/OWPIL_Vol.2_2016.pdf); [Juliet Morgan (2017)](https://shareok.org/items/13670662-667a-4694-bdd9-629172da1477). These describe the modern system; they do not certify every Wiktionary spelling.
