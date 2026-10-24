# Curation Packet — Somali (`afa-somali`)

## Current construction — core-sense audit, 2026-10-24

Accepted base: Wiktionary with the documented spelling/dictionary profile and
explicit concept corrections. Tier remains **bronze**. This audit checks
English source senses against frozen concept definitions; it does not certify
native translation accuracy, dialect identity, or inflection choices.

| Current metric | Value |
|---|---:|
| Forms (none deleted) | 1,025 |
| Forms with a concept ID | 613 |
| Distinct mapped concepts | 512 |
| Core concepts | 114/161 |
| Core concepts with supported IPA | 114/161 |
| Profile-derived forms | 1,011 |
| Unclean forms | 14 |
| Reviewed source parameters | 121 |
| Remapped parameters | 4 |
| Explicitly unmapped parameters | 1 |
| Provisional senses needing specialist review | 0 |

Before this audit the profile pilot covered 112 core concepts,
112 with supported IPA. Changes distinguish actual recovery
from removal of false coverage claims. Mechanical scores were recomputed on
the corrected construction; they do not confer specialist review.

## Applied decisions and pronunciation evidence

Animal horn (`gees`) and singular you (`adiga`) were already present in intake
but were not assigned their core concepts. Human/person senses are now mapped
to `kin-person`, while adult-male `nin` remains `kin-man`. The orange-brown
hair sense of red is no longer counted as the general red-colour slot.

One translation-specific error is corrected independently of its English
parameter: `waraabin` is irrigation/watering, not water as a substance.
[Zorc's Somali–English dictionary](https://zorc.net/RDZorc/SOMALI/SOMALI-ENGLISH%3DDICTIONARY.pdf),
revised 2019-06-05, p. 534, supports this distinction. Only source form
`wikt_2843349` is unmapped; `biyo` under the same parameter remains `phy-water`.
The correction has parameter and spelling guards against source-ID reuse.
See `custom/form_review.csv`.

Authored decisions are in `custom/core_review.csv`; `concept_map.csv` is their
compiled correction layer. `action=unmap` retains lexical rows and provenance
while blocking both concept identifiers and parameter-index fallback.

Run `python scripts/audit_core_pilots.py --write-maps` to reproduce corrections,
rebuild the pilots, then run `python scripts/audit_core_pilots.py` to validate
review completeness, source text/mapping drift and built concept assignments.
The checker writes `output/report/core_audit.json`.

## Remaining work

Missing concepts from the previous GLED construction: `bod-die`, `foo-drink`.
Missing with supported IPA: `bod-die`, `foo-drink`.
These are explicit recovery targets; related noun senses or GLED strings are
not silently substituted for missing verbs or independently verified sources.

Review the native translations and regional/grammatical forms against matched
lexical references before raising the tier. Spelling coverage and valid IPA
symbols alone do not establish correct meanings.

## Initial source review — 2026-10-23, historical

The following records the initial pilot. Its counts and follow-up lists are
superseded by the current audit above; transcription conventions and cited
references remain the basis unless explicitly amended.

### Accepted construction

Wiktionary intake (`wikt_so`, Glottocode `soma1255`) with the broad segmental
Latin-script profile in `custom/profile.tsv`. Selected as a coverage pilot
on 2026-10-23; specialist review remains pending. The durable source choice
is pinned in `src/arcaverborum/data/selection.csv`. Tier is conservatively
bronze despite a high mechanical forms score.

### Coverage and tradeoffs

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

### Transcription method and limits

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

### Evidence

- [PCGN Somalia Toponymic Factfile](https://assets.publishing.service.gov.uk/media/6717aabfd94d2c219a540573/Somalia_Toponymic_Factfile.pdf),
  pp. 3–5: alphabet, consonant correspondences, doubled vowels and consonants.
- Ahmed Mohamed (2013), [An Overview of the Interface Between Aspects of
  Somali Phonology and Morphology](https://orthographyclearinghouse.org/theses/mohamedAnOverviewtheInterfacebetweenAspectsofSomaliPhonologyandMorphology.pdf),
  chapter 2: orthography, phonology, and unwritten tone (p. 25).
- Local Wiktionary intake and its retained per-form source provenance;
  diagnostics recomputed on 2026-10-23.

### Follow-up

Review concept mappings and source senses, especially synonyms and phrases;
recover the four missing core concepts through reviewed corrections or a
named derived layer; seek a scholarly Somali lexical source with observed
IPA and comparative cognates. A specialist should review vowel conventions
before upgrading the construction's tier.
