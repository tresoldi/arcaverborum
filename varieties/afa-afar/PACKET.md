# Curation Packet — Afar (`afa-afar`)

## Current construction — core-sense audit, 2026-10-24

Accepted base: Wiktionary with the documented spelling/dictionary profile and
explicit concept corrections. Tier remains **bronze**. This audit checks
English source senses against frozen concept definitions; it does not certify
native translation accuracy, dialect identity, or inflection choices.

| Current metric | Value |
|---|---:|
| Forms (none deleted) | 241 |
| Forms with a concept ID | 184 |
| Distinct mapped concepts | 171 |
| Core concepts | 63/161 |
| Core concepts with supported IPA | 63/161 |
| Profile-derived forms | 240 |
| Unclean forms | 1 |
| Reviewed source parameters | 65 |
| Remapped parameters | 3 |
| Explicitly unmapped parameters | 0 |
| Provisional senses needing specialist review | 1 |

Before this audit the profile pilot covered 62 core concepts,
62 with supported IPA. Changes distinguish actual recovery
from removal of false coverage claims. Mechanical scores were recomputed on
the corrected construction; they do not confer specialist review.

## Applied decisions and pronunciation evidence

Animal horn (`gaysa`) and singular you (`atu`) are recovered from existing
intake. The source sense for `soole` is rise to one's feet, so it is assigned
to `mot-stand-up` rather than falsely supplying the static `spa-stand` slot.
The form and its transcription remain in the dataset.

Authored decisions are in `custom/core_review.csv`; `concept_map.csv` is their
compiled correction layer. `action=unmap` retains lexical rows and provenance
while blocking both concept identifiers and parameter-index fallback.

Run `python scripts/audit_core_pilots.py --write-maps` to reproduce corrections,
rebuild the pilots, then run `python scripts/audit_core_pilots.py` to validate
review completeness, source text/mapping drift and built concept assignments.
The checker writes `output/report/core_audit.json`.

## Remaining work

Missing concepts from the previous GLED construction: `ani-louse`, `bod-die`, `bod-tongue`, `foo-drink`, `kin-person`, `mot-come`, `tim-new`.
Missing with supported IPA: `ani-louse`, `bod-die`, `bod-tongue`, `foo-drink`, `kin-person`, `mot-come`, `tim-new`.
These are explicit recovery targets; related noun senses or GLED strings are
not silently substituted for missing verbs or independently verified sources.

Retained provisionally, with scope/aspect or grammatical interpretation still
requiring specialist review:

- seed (noun): any small seed-like fruit

Review the native translations and regional/grammatical forms against matched
lexical references before raising the tier. Spelling coverage and valid IPA
symbols alone do not establish correct meanings.

## Initial source review — 2026-10-23, historical

The following records the initial pilot. Its counts and follow-up lists are
superseded by the current audit above; transcription conventions and cited
references remain the basis unless explicitly amended.

### Accepted construction

Wiktionary intake with `custom/profile.tsv`, selected as a coverage pilot on
2026-10-23. Specialist review remains pending; bronze is retained conservatively.
This is broad spelling-derived transcription, not observed source IPA.

### Coverage and tradeoffs

| Metric | Previous GLED | Wiktionary + profile |
|---|---:|---:|
| Forms | 71 | 241 |
| Mapped concepts | 39 | 169 |
| Core concepts | 37/161 | 62/161 |
| Profile-derived forms | 0 | 240 |
| Unclean forms | 0 | 1 |
| Forms with cognacy annotations | 71 | 50 |

183 forms have frozen concept IDs. Every covered core concept
has at least one successfully profiled form. This gains 34 core
concepts and loses 9: `ani-louse`, `bod-die`, `bod-horn`, `bod-tongue`, `foo-drink`, `kin-person`, `kin-thou`, `mot-come`, `tim-new`.
Sources are not merged. The losses need reviewed concept or lexical additions.
The wider vocabulary includes unmapped entries; spelling coverage does not
validate senses or concept mappings.

Cognacy remains the source's `wiktionary_etymology` annotations with
`wiktionary_kaikki2026` provenance. These are not expert comparative judgments;
GLED identifiers are not transferred onto the new forms. Mechanical quality
scores were recomputed from mapped intake after applying the profile. The high
forms score measures available structure and segment validity, not review depth.

### Transcription method and limits

The profile follows the standard Wiktionary/Qafar Feera convention confirmed
by CNRS: `c` → `ħ`, `q` → `ʕ`, `x` → `ɖ`. It must not reuse Somali's
letter values. Single `r` is a tap (`ɾ`); doubled `rr` is long `rː`.
Vowel and consonant doubles map to length; case variants are explicit.
Acutely accented vowels retain marked high pitch as `⁵`; marked long vowels
map to a long vowel with high pitch. This preserves the presence of marked
high pitch, not its precise mora alignment or phonetic contour. No high or
low tones are supplied for unmarked vowels. Spaces retain boundaries.

One Arabic-script form (`أَف`) remains unclean. The profile is for the Latin
orthography in this intake, not the differently assigned Eritrean conventions.
Word-final vowel reduction, stress realization, dialectal palatalization, and
other contextual allophones are outside this broad transcription.

### Evidence

- [CNRS LGIDF: Afar](https://lgidf.cnrs.fr/afar): the standard `c q x` sound values.
- Richard J. Hayward, [Qafar (East Cushitic)](https://www.blackwellpublishing.com/content/bpl_images/content_store/WWW_Content/9780631226949/31Chap29.pdf),
  note 1: doubled lengths and acute-marked high tone; its own segmental spelling
  differs from Qafar Feera and is not copied blindly.
- [Wiktionary's Afar entry guidelines](https://en.wiktionary.org/wiki/Wiktionary:Afar_entry_guidelines):
  the orthographic convention of this source, including pitch marks and the tap.

Local Wiktionary intake and retained per-form provenance were inspected on
2026-10-23. Tests check language-specific contrasts, marked pitch, length,
unsupported input, and precedence of existing source IPA.

### Follow-up

Verify senses and concept assignments, recover the lost core concepts through
reviewed corrections or a named derived layer, and seek scholarly lexical data
with observed IPA and expert cognates. Review pitch conventions and dialect
coverage before any tier upgrade. A high profile-coverage percentage alone is
not an accuracy estimate.
