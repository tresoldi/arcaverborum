# Curation Packet — Vach-Vasjugan (`urj-vach-vasjugan`)

## Construction and identity

Register an attested variety omitted from the frozen registry and existing configs; identity confirmed against the cached Glottolog language/dialect entry and the single named source language.

Accepted source: **uralex**; source member `uralex_khanty_vakh_vasyugan` is explicitly
filtered in config. Glottocode `fare1244` matches the source and the
cached Glottolog entry. The newly minted av_id is frozen in `src/arcaverborum/data/varieties.csv`.
The source choice is recorded in `selection.csv`. Tier is conservatively bronze;
mechanical source scores do not establish specialist review. Curation date:
2026-10-23; specialist review pending.

Identity cross-review compared this member with the existing accepted Khanty
construction, `urj-kazym-berezover-suryskarer-khanty`. That construction emits
Northern Khanty from `northeuralex_kca`; its reference dictionaries concern
Shuryshkar/Northern varieties. This member explicitly samples Vakh–Vasyugan.
Other Vakh/Vasjugan candidates exist in intake, but no existing accepted
configuration emits those samples. The new row therefore does not duplicate
an accepted source member merely because both belong to Khanty.

## Built diagnostics

| Metric | Value |
|---|---:|
| Forms | 377 |
| Distinct mapped concepts | 307 |
| Core concepts | 150/161 |
| Core concepts with source-clean forms | 121 |
| Source-clean forms | 292 |
| Unclean forms | 85 |
| Forms with source cognacy | 377 |

85 forms retain unclean source segments. These include transcription tokenization/diacritic issues that require separate review; the 292 validated forms cover 121 core concepts. UraLex source cognacy remains marked expert. This is the tresoldi IPA-conversion fork, not an unmodified upstream release.

## Gains and losses

This adds a separately identifiable variety rather than merging it into an existing language.
There is no replaced accepted construction, so no existing forms or concepts are removed.

No unrelated sources are merged; custom corrections are absent. Source IPA,
original form IDs, language IDs, bibliography and cognacy metadata are preserved.
IPA validity measures symbol compatibility, not the correctness or completeness
of a pronunciation. The entire vocabulary and its sense mappings still need
specialist review before any tier upgrade.

## Provenance and next work

- [Source repository](https://github.com/tresoldi/uralex); local intake generated from that source.
- Local `raw/glottolog/languages.csv`, language/dialect identity and family metadata.
- Bibliographic keys used in output: `uralex_DEWbOstj`.

Review unclean transcriptions and concept senses; retain the separate source-member filter when upstream language metadata changes.
