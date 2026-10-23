# Curation Packet — Jitotolteco (`mix-jitotolteco`)

## Construction and identity

Register an attested variety omitted from the frozen registry and existing configs; identity confirmed against the cached Glottolog language/dialect entry and the single named source language.

Accepted source: **mixezoqueanvoices**; source member `mixezoqueanvoices_Jitotol` is explicitly
filtered in config. Glottocode `jito1235` matches the source and the
cached Glottolog entry. The newly minted av_id is frozen in `src/arcaverborum/data/varieties.csv`.
The source choice is recorded in `selection.csv`. Tier is conservatively bronze;
mechanical source scores do not establish specialist review. Curation date:
2026-10-23; specialist review pending.

Identity cross-review found no other accepted source member sampling Jitotol.
The Glottocode is language-level, distinct from the Chiapas Zoque grouping.
This differs from the rejected Copainalá proposal, whose locality was already
represented by an existing accepted member.

## Built diagnostics

| Metric | Value |
|---|---:|
| Forms | 196 |
| Distinct mapped concepts | 196 |
| Core concepts | 134/161 |
| Core concepts with source-clean forms | 134 |
| Source-clean forms | 196 |
| Unclean forms | 0 |
| Forms with source cognacy | 0 |

The source contains primary recordings and phonetic transcriptions, but supplies no comparative cognacy annotations. No GLED cognate IDs are transferred onto its forms.

## Gains and losses

This adds a separately identifiable variety rather than merging it into an existing language.
There is no replaced accepted construction, so no existing forms or concepts are removed.

No unrelated sources are merged; custom corrections are absent. Source IPA,
original form IDs, language IDs, bibliography and cognacy metadata are preserved.
IPA validity measures symbol compatibility, not the correctness or completeness
of a pronunciation. The entire vocabulary and its sense mappings still need
specialist review before any tier upgrade.

## Provenance and next work

- [Source repository](https://github.com/lexibank/mixezoqueanvoices); local intake generated from that source.
- Local `raw/glottolog/languages.csv`, language/dialect identity and family metadata.
- Bibliographic keys used in output: `mixezoqueanvoices_Kondic2023`.

Review unclean transcriptions and concept senses; retain the separate source-member filter when upstream language metadata changes.
