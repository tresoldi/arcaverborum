# Curation Packet — Aragonese (`ine-aragonese`)

## Accepted construction

Wiktionary `wikt_an`, Glottocode `arag1245`, with a conservative broad segmental
profile in `custom/profile.tsv`. Coverage pilot dated 2026-10-23; specialist
review remains pending. The source decision should be mirrored in the durable
selection registry. Tier remains bronze despite the mechanical forms score.

| Metric | GLED | Wiktionary + profile |
|---|---:|---:|
| Forms | 52 | 1,510 |
| Mapped concepts | 40 | 468 |
| Core concepts | 38/161 | 79/161 |
| Profile-derived forms | 0 | 1,414 |
| Unclean forms | 0 | 96 |
| Forms carrying cognacy annotations | 52 | 503 |

604 Wiktionary forms have frozen concept IDs. All 79 covered core concepts have
at least one profile-derived form. This gains 51 core concepts but loses ten:
`ani-louse`, `bod-bone`, `bod-breast`, `bod-die`, `bod-horn`, `kin-person`,
`mot-come`, `phy-stone`, `qua-one`, `sns-hear`. Sources are not automatically
merged. The broader intake includes names, phrases, and unmapped entries.

## Transcription and uncertainty

This profile uses a broad central/reference convention, not a dialect-specific
pronunciation. It handles palatal digraphs, contextual c/qu/gu, vowel accents,
and rhotic contrasts. Exact-form `^word$` rows handle current-intake initial r, with the article
forms ro/ra/ros/ras retaining the tap. Anchored entries are excluded from
greedy substring matching, so they cannot leak into compounds. Contextual
graphemes cover interior rhotics; no bare r fallback is supplied. Unknown
initial-r words remain unclean until reviewed. There are 72 anchored entries,
including phrases with initial rhotics after word boundaries.

Vowel letters i and u remain abstract vowel segments, including where surface
glides are expected. Stress, stop lenition, nasal assimilation, and regional
vowel and consonant realizations are not inferred. Final consonants follow
broad lexical representations rather than regional deletion. This is suitable
for broad segmental comparison with these limitations, not phonetic analysis.

Ambiguous bare x is deliberately unsupported: native and learned words have
different values. Clear vowel+ix sequences are supported with a palatal
fricative convention. Foreign ge/gi, bare j, unknown letters, apostrophes,
and hyphens also remain unclean. Existing source IPA takes precedence.
The 96 failures are preserved as forms, not silently simplified.

The 503 Wiktionary cognacy annotations retain source method/provenance and
are not expert comparative cognate judgments. GLED cognates are not copied.

## Evidence

- Academia Aragonesa de la Lengua (2023), [official orthography](https://academiaaragonesadelalengua.org/sites/default/files/ficheros-pdf/Ortograf%C3%ADa%20del%20aragon%C3%A9s_web_es.pdf),
  sections 1.1–1.2: phonemic spelling correspondences and regional variants.
- Academia de l'Aragonés, [reading guide](https://www.efaragonesa.org/comoleeresp.htm):
  spelling alternatives, variable x, rhotics, and dialect-specific deletion.
- Local intake/build diagnostics, recomputed 2026-10-23.

## Follow-up

Recover the ten missing concepts through reviewed curation; check source
senses and orthographic systems; review rhotic whole-word exceptions after
intake updates; add dictionary-backed x pronunciations. Upgrade the tier
only after a specialist reviews the broad conventions and cognacy quality.
