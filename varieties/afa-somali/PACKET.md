# Curation Packet — Somali (`afa-somali`)

## Accepted construction

Wiktionary intake (`wikt_so`, Glottocode `soma1255`) with the broad segmental
Latin-script profile in `custom/profile.tsv`. Selected as a coverage pilot
on 2026-10-23; specialist review remains pending. The durable source choice
is pinned in `src/arcaverborum/data/selection.csv`. Tier is conservatively
bronze despite a high mechanical forms score.

## Coverage and tradeoffs

| Metric | Previous GLED | Wiktionary + profile |
|---|---:|---:|
| Forms | 47 | 1,025 |
| Mapped concepts | 39 | 510 |
| Core concepts | 37/161 | 112/161 |
| Profile-derived forms | 0 | 1,011 |
| Unclean forms | 0 | 14 |
| Forms with cognacy annotations | 47 | 172 |

612 of the new forms have a frozen concept ID. All 112 covered core concepts
have at least one profile-derived form. Relative to GLED, this gains 79 core
concepts and loses four: `bod-die`, `bod-horn`, `foo-drink`, `kin-thou`.
Sources are not merged. The wider vocabulary includes names, phrases, and
unmapped entries; concept filtering remains necessary for comparison.

The 172 Wiktionary cognacy annotations retain their original
`wiktionary_etymology` method and `wiktionary_kaikki2026` provenance. They
are not expert comparative cognate judgments. GLED cognate identifiers are
not transferred onto unrelated Wiktionary forms.

## Transcription method and limits

Somali's standard Latin spelling makes a useful broad segmental profile:
`dh`, `kh`, `sh`, `c`, `x`, `j`, and `y` require language-specific mappings;
double vowels encode length. Doubled `b d g l m n r` map to long consonants.
Uppercase spellings and apostrophe variants are handled explicitly. Spaces
retain word boundaries. Every output token is validated by merkmal tests.

The five vowel letters map to broad `a e i o u` symbols, with long counterparts.
These are an orthographic abstraction: vowel-harmony qualities, tone/accent,
contextual allophony, and unwritten glottal onsets are not reconstructed.
Profile success means spelling coverage and valid segment symbols, not a
complete observed pronunciation. Existing source IPA always takes precedence.

The 14 unsupported entries include alternate scripts, hyphenated forms,
punctuation, and foreign spellings. They retain their forms and remain unclean;
no unknown letters are silently deleted or guessed. Hyphen interpretation
and alternate-script conversion need separate review.

## Evidence

- [PCGN Somalia Toponymic Factfile](https://assets.publishing.service.gov.uk/media/6717aabfd94d2c219a540573/Somalia_Toponymic_Factfile.pdf),
  pp. 3–5: alphabet, consonant correspondences, doubled vowels and consonants.
- Ahmed Mohamed (2013), [An Overview of the Interface Between Aspects of
  Somali Phonology and Morphology](https://orthographyclearinghouse.org/theses/mohamedAnOverviewtheInterfacebetweenAspectsofSomaliPhonologyandMorphology.pdf),
  chapter 2: orthography, phonology, and unwritten tone (p. 25).
- Local Wiktionary intake and its retained per-form source provenance;
  diagnostics recomputed on 2026-10-23.

## Follow-up

Review concept mappings and source senses, especially synonyms and phrases;
recover the four missing core concepts through reviewed corrections or a
named derived layer; seek a scholarly Somali lexical source with observed
IPA and comparative cognates. A specialist should review vowel conventions
before upgrading the construction's tier.
