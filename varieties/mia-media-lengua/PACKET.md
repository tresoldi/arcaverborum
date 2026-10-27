# Media Lengua — reviewed Dictionaria construction, 2026-10-27

This replaces a two-form, zero-supported-core Wiktionary construction with the
Media Lengua dictionary by Jesse Stewart with Gabriela Prado Ayala and Lucia
Gonza Inlago. The source describes Pijal and San Pablo communities in Ecuador;
its variation is retained, not presented as one uniform local pronunciation.

The source provides Phonological_Representation for all 3,216 entries. These are
used directly, with ASCII stress apostrophes interpreted as the source's stress
notation and removed in Arca's segmental canonicalization. Explicit word
boundaries are retained. No Spanish/Quichua spelling-to-IPA rules are inferred.
All 3,216 emitted forms have validated supplied segments; 177 reviewed sense
mappings cover 144 concepts, including 124/161 basic concepts. Other definitions
remain searchable with their original glosses and empty concept mappings.

Original entry and sense IDs, complete source fields, phonological strings,
variant forms, acquisition methods and etymology are preserved in evidence
comments. Spanish/Quichua etymological origin does not automatically become a
loan flag. No cognate judgments are inferred or transferred from Wiktionary.
Source-sense review is not independent native lexical certification.

Upstream dc:bibliographicCitation incorrectly names Eline Visser's Kalamang
resource. The local source manifest instead follows the named Media Lengua
compilers and contribution, without inventing a publication year. Original
metadata are retained in the raw repository, and their hash is recorded in the
bibliography. License: CC BY 4.0. The exact repository commit appears in source
metadata. This source has not been admitted to the Core release collection.

Primary contribution: https://dictionaria.clld.org/contributions/medialengua
Source: https://github.com/dictionaria/medialengua

Reproduce mappings with scripts/compile_dictionary_maps.py --write. Ingest new
sources into staging; do not run subset ingest over active intake. The source
adapter rejects drift in reviewed headwords, definitions and grammatical labels.

Follow-up sense review (same date): twenty additional explicit source senses,
checked with accompanying Spanish/Quichua translations, add eighteen supported
core slots. Generic day, verbal rain/thunder and the noun labelled “heavy” remain
unmapped to incompatible frozen concepts. See the dictionary-sense follow-up
ledger; the lexical records and supplied segment strings are unchanged.
