# Curation Packet — Northern Chiapas Zoque (`mix-northern-chiapas-zoque`)

## Construction and identity

Replace GLED: core coverage rises from 37 to 107; the chosen source has direct phonetic documentation.

Accepted source: **mixezoqueanvoices**; source member `mixezoqueanvoices_Franciscoleon` is explicitly
filtered in config. Glottocode `fran1266` matches the source and the
cached Glottolog entry. The existing av_id remains frozen despite the source member name Francisco León.
The source choice is recorded in `selection.csv`. Tier is conservatively bronze;
mechanical source scores do not establish specialist review. Curation date:
2026-10-23; specialist review pending.

## Built diagnostics

| Metric | Value |
|---|---:|
| Forms | 157 |
| Distinct mapped concepts | 157 |
| Core concepts | 107/161 |
| Core concepts with source-clean forms | 107 |
| Source-clean forms | 157 |
| Unclean forms | 0 |
| Forms with source cognacy | 0 |

The source contains primary recordings and phonetic transcriptions, but supplies no comparative cognacy annotations. No GLED cognate IDs are transferred onto its forms.

## Gains and losses

The previous GLED construction had 43 forms and 37 core concepts.
Core concepts gained: 79; lost: 9. Lost IDs: agr-tree, bod-blood, bod-die, bod-horn, bod-knee, phy-mountain, phy-sun, qua-full, sns-hear.

No unrelated sources are merged; custom corrections are absent. Source IPA,
original form IDs, language IDs, bibliography and cognacy metadata are preserved.
IPA validity measures symbol compatibility, not the correctness or completeness
of a pronunciation. The entire vocabulary and its sense mappings still need
specialist review before any tier upgrade.

## Provenance and next work

- [Source repository](https://github.com/lexibank/mixezoqueanvoices); local intake generated from that source.
- Local `raw/glottolog/languages.csv`, language/dialect identity and family metadata.
- Bibliographic keys used in output: `mixezoqueanvoices_Kondic2023`.

Recover the nine missing GLED core concepts through individually reviewed additions or a named derived construction; assess cognates independently.
