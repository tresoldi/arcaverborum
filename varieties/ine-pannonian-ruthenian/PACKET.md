# Pannonian Ruthenian — orthographic pilot, 2026-10-27

The accepted source remains Wiktionary, named member `wikt_rsk`, Glottocode pann1240. A reviewed exact-spelling profile supplies **broad phonemic sequences**, distinguished as `Segments_Source=profile`. These are inferred readings, not recorded IPA or narrow surface transcriptions.

| Metric | Before | After |
|---|---:|---:|
| Forms retained | 2407 | 2407 |
| Profile-supported forms | 0 | 2028 |
| Unclean forms | 2407 | 379 |
| Supported strict core concepts | 0 | 95/161 |
| Mapped strict core concepts | 98 | 98/161 |

The primary spelling/phonology reference is [Julijan Ramač, Ґраматика руского язика (2002)](https://digitalna.ff.uns.ac.rs/sadrzaj/2002/86-17-09626-8), especially §§7–14 and21 (printed pp.14–21,26). It distinguishes five vowels, glottal consonants г/х, affricates, and the soft counterparts of д/т/л/н. Iotated vowels after those consonants mark softness plus the vowel; elsewhere the profile retains /j/. Soft signs outside those reviewed contexts are excluded. Native transcription examples independently establish the iotated-vowel treatment (§21).

The profile uses phonemic /i e a o u/, /ɦ h/, and hard /l r/ with explicit /lʲ nʲ dʲ tʲ/. It intentionally does not infer stress, vowel duration, final devoicing, /v/ vocalization, or other surface assimilation. Ramač discusses those in §§10,16–20; they are not additional lexical phonemes. Thus mechanical validity here certifies a supported broad phonemic reading, not complete phonetic realization. The simpler IPA table in Slemender (2025), pp.17–18, differs on vowel notation and does not by itself determine contextual readings; it is not used to override the native grammar.

The compiler excludes multiword expressions, affixes/punctuation, mixed Latin/Cyrillic spellings, explicit accents needing separate review, unsupported soft signs, and дз/дж clusters whose morpheme boundaries have not been checked. Unknown input stays unclean. Exact keys prevent the profile from automatically generalizing to new spellings.

All 102 raw core English senses were reviewed in `custom/core_review.csv`. Human-being “man” maps to person; complementizer “that” is unmapped from the demonstrative concept. Other senses are checked against frozen definitions. This is an English-sense audit, not native certification of each translation. Source etymology annotations are retained without relabeling them expert cognates.

Reproduce with `python scripts/pannonian_profile.py --write`; the default checks source snapshots and compiler output. Run `python scripts/audit_core_pilots.py` after rebuilding to check source senses and effective mappings. Specialist pronunciation and lexical review remain pending.

## Worldwide follow-up — 2026-10-29

Accepted 2407 records; 99/161 supported core concepts. Primary: `wiktionary`.
[Execution, sources, gains and holds](../../docs/WORLDWIDE_FOLLOWUP_EXECUTION_2026-10-29.md).
Earlier evidence and source-specific cognacy remain; six precise shared English-sense
rules correct older mappings where applicable. Source conversions are not independent
IPA elicitation, profiles are finite and source-specific, and written-only records
add no phonetic support. Config and guarded custom ledgers enforce acceptance.
