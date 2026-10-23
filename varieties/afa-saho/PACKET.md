# Curation Packet — Saho (`afa-saho`)

## Accepted construction

Wiktionary intake with `custom/profile.tsv`, selected as a coverage pilot on
2026-10-23. Specialist review remains pending; bronze is retained conservatively.
This is broad spelling-derived transcription, not observed source IPA.

## Coverage and tradeoffs

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

## Transcription method and limits

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

## Evidence

- Giorgio Banti and Moreno Vergari (2005), [A Sketch of Saho Grammar](https://www.sahoarchive.org/wp-content/uploads/2014/08/Banti___Vergari_Sketch_of_Saho_grammar__ms_-libre.pdf),
  manuscript pp. 2–3: alphabet correspondences, length, retroflex spelling,
  diaeresis-marked feminine high pitch, and ambiguous hyphens.
- [Saho Archive: How to write and read the Saho language](https://www.sahoarchive.org/366/):
  Eritrean Latin versus Ethiopian and historical writing conventions.

Local Wiktionary intake and retained per-form provenance were inspected on
2026-10-23. Tests check language-specific contrasts, marked pitch, length,
unsupported input, and precedence of existing source IPA.

## Follow-up

Verify senses and concept assignments, recover the lost core concepts through
reviewed corrections or a named derived layer, and seek scholarly lexical data
with observed IPA and expert cognates. Review pitch conventions and dialect
coverage before any tier upgrade. A high profile-coverage percentage alone is
not an accuracy estimate.
