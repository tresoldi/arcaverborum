# Curation Packet — Higaonon (`map-higaonon`)

## Decision: defer source replacement pending vowel/orthography review

Retain the current GLED construction. Wiktionary has substantial potential,
but a general letter-to-IPA substitution would overstate pronunciation
certainty. A deliberately incomplete proposal is stored outside the enforced
custom layer at `proposals/profile.tsv`; it is not an accepted transcription.
No pin or source change is requested at this stage.

| Metric | Current GLED | Wiktionary candidate |
|---|---:|---:|
| Forms | 40 | 449 |
| Mapped concepts | 39 | 322 |
| Core concepts | 37/161 | 98/161 |
| Forms with concept IDs | 40 | 332 |
| Forms with cognacy annotations | 40 | 106 |

The candidate gains 71 core concepts and loses ten: `bod-blood`, `bod-die`,
`bod-horn`, `bod-skin`, `bod-tooth`, `kin-i`, `kin-thou`, `mot-come`,
`phy-fire`, `sns-see`. Source identity is `wikt_mba`, Glottocode `higa1237`.
The earlier identifier `wikt_hig` was a documentation error: the cached source
and Glottolog tables identify it as Kamwe (kamw1239), a different language.
No accepted source switch or pronunciation profile uses that erroneous identifier.
These figures measure lexical availability, not validated pronunciations.

## Why a general profile is not yet adequate

The Wiktionary forms overwhelmingly use a/i/o/u, with only three occurrences
of e. The language includes central-vowel distinctions and glottal stops
whose realization and notation differ across documented varieties. A profile
mapping every a to /a/ and o to /o/ would conceal information missing from
these headwords. Unknown word stress and glottal stops cannot be recovered
by successfully matching every letter.

The proposal records stable consonant mappings including ng -> /ŋ/, y -> /j/
and r -> /ɾ/, with a/i/o/u as provisional spelling values. It intentionally
omits e, hyphens, and unknown foreign letters. Its successful outputs must
not be treated as phonologically complete or as accepted clean IPA.

## Evidence

- [Birkin/Munger Higaonon numeral observations](https://lingweb.eva.mpg.de/channumerals/Higaonon.htm),
  data supplied by field linguists in 1998/2009: central-vowel and local
  pronunciation distinctions.
- Abingosa et al. (2026), [Documentation and description of sounds and grammar
  of Higaonon spoken in Opol, Misamis Oriental](https://doi.org/10.21831/diksi.v34i1.79632):
  consonants, central vowels, word stress, and glottal stops; this is a
  particular documented variety, not an automatic match to all Wiktionary.
- [AsiaLex 2011 proceedings](https://www.asialex.org/pdf/Asialex-Proceedings-2011.pdf),
  Higaonon lexicography/orthography account: Tankulan spelling conventions,
  loan letters, and glottal notation.
- Local intake diagnostics, recomputed 2026-10-23.

## Concrete next work

Identify the source/dialect behind the Wiktionary headwords and obtain a
matched pronunciation dictionary or field transcription list. Validate
central vowels and glottal-stop notation against a sample including core
concepts before enabling a profile. Keep source etymology annotations
separate from expert comparative cognates. A source-specific concept and
transcription overlay can then recover the new vocabulary without guessing.
