# Curation Packet — Saho (`afa-saho`)

## Current construction — core-sense audit, 2026-10-24

Accepted base: Wiktionary with the documented spelling/dictionary profile and
explicit concept corrections. Tier remains **bronze**. This audit checks
English source senses against frozen concept definitions; it does not certify
native translation accuracy, dialect identity, or inflection choices.

| Current metric | Value |
|---|---:|
| Forms (none deleted) | 143 |
| Forms with a concept ID | 124 |
| Distinct mapped concepts | 118 |
| Core concepts | 54/161 |
| Core concepts with supported IPA | 54/161 |
| Profile-derived forms | 143 |
| Unclean forms | 0 |
| Reviewed source parameters | 57 |
| Remapped parameters | 4 |
| Explicitly unmapped parameters | 0 |
| Provisional senses needing specialist review | 0 |

Before this audit the profile pilot covered 54 core concepts,
54 with supported IPA. Changes distinguish actual recovery
from removal of false coverage claims. Mechanical scores were recomputed on
the corrected construction; they do not confer specialist review.

## Applied decisions and pronunciation evidence

Animal horn (`gashsha`) is recovered from an unmapped source sense. Human
and generic-human man senses are assigned to `kin-person`; that evidence
does not establish the adult-male `kin-man` slot. Rise to one's feet is
mapped to `mot-stand-up`, not static standing. The two recovered core slots
are balanced by removal of these two false coverage claims.

Authored decisions are in `custom/core_review.csv`; `concept_map.csv` is their
compiled correction layer. `action=unmap` retains lexical rows and provenance
while blocking both concept identifiers and parameter-index fallback.

Run `python scripts/audit_core_pilots.py --write-maps` to reproduce corrections,
rebuild the pilots, then run `python scripts/audit_core_pilots.py` to validate
review completeness, source text/mapping drift and built concept assignments.
The checker writes `output/report/core_audit.json`.

## Remaining work

Missing concepts from the previous GLED construction: `ani-louse`, `bod-blood`, `bod-breast`, `bod-die`, `foo-drink`, `kin-i`, `kin-thou`, `mot-come`, `phy-mountain`, `tim-new`.
Missing with supported IPA: `ani-louse`, `bod-blood`, `bod-breast`, `bod-die`, `foo-drink`, `kin-i`, `kin-thou`, `mot-come`, `phy-mountain`, `tim-new`.
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

Wiktionary intake with `custom/profile.tsv`, selected as a coverage pilot on
2026-10-23. Specialist review remains pending; bronze is retained conservatively.
This is broad spelling-derived transcription, not observed source IPA.

### Coverage and tradeoffs

| Metric | Previous GLED | Wiktionary + profile |
|---|---:|---:|
| Forms | 71 | 143 |
| Mapped concepts | 39 | 117 |
| Core concepts | 37/161 | 54/161 |
| Profile-derived forms | 0 | 143 |
| Unclean forms | 0 | 0 |
| Forms with cognacy annotations | 71 | 12 |

122 forms have frozen concept IDs. Every covered core concept
has at least one successfully profiled form. This gains 29 core
concepts and loses 12: `ani-louse`, `bod-blood`, `bod-breast`, `bod-die`, `bod-horn`, `foo-drink`, `kin-i`, `kin-person`, `kin-thou`, `mot-come`, `phy-mountain`, `tim-new`.
Sources are not merged. The losses need reviewed concept or lexical additions.
The wider vocabulary includes unmapped entries; spelling coverage does not
validate senses or concept mappings.

Cognacy remains the source's `wiktionary_etymology` annotations with
`wiktionary_kaikki2026` provenance. These are not expert comparative judgments;
GLED identifiers are not transferred onto the new forms. Mechanical quality
scores were recomputed from mapped intake after applying the profile. The high
forms score measures available structure and segment validity, not review depth.

### Transcription method and limits

The profile follows Banti and Vergari's Eritrean Latin alphabet. In particular,
`c` → `ʕ`, `x` → `ħ`, `dh` → `ɖ`, `rh` → `ɽ`; ejective `q`, `qh`, `ch`,
`th`, and `ts` are distinct from plain consonants. Long vowels and consonants
are retained, including `shsh` → `ʃː`. This profile is distinct from Afar's
`c q x` convention. Letter case variants are explicit.

Diaeresis marks feminine final high pitch, not vowel fronting: `barhä` becomes
`b a ɽ a ⁵`, distinct from unmarked `barha`. Only explicitly marked high pitch
is represented; unmarked pitch patterns are not reconstructed. Hyphens may
separate digraph letters, express a glottal boundary, or join compounds. They
are deliberately unsupported rather than assigned one false universal value.
The current intake has none, and all 143 forms are covered. Dialect identity,
contextual phonetics, and completeness of tone marking remain unreviewed.

### Evidence

- Giorgio Banti and Moreno Vergari (2005), [A Sketch of Saho Grammar](https://www.sahoarchive.org/wp-content/uploads/2014/08/Banti___Vergari_Sketch_of_Saho_grammar__ms_-libre.pdf),
  manuscript pp. 2–3: alphabet correspondences, length, retroflex spelling,
  diaeresis-marked feminine high pitch, and ambiguous hyphens.
- [Saho Archive: How to write and read the Saho language](https://www.sahoarchive.org/366/):
  Eritrean Latin versus Ethiopian and historical writing conventions.

Local Wiktionary intake and retained per-form provenance were inspected on
2026-10-23. Tests check language-specific contrasts, marked pitch, length,
unsupported input, and precedence of existing source IPA.

### Follow-up

Verify senses and concept assignments, recover the lost core concepts through
reviewed corrections or a named derived layer, and seek scholarly lexical data
with observed IPA and expert cognates. Review pitch conventions and dialect
coverage before any tier upgrade. A high profile-coverage percentage alone is
not an accuracy estimate.
