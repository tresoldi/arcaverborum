# nub-apinaye — source supplementation packet


## Reviewed additive IPA evidence — 2026-10-27

1 exact Wiktionary source forms add 1 core concepts without removing primary forms. Only supplied IPA is used; the primary profile is not applied to the secondary source. Full lexical/source evidence hashes and original source IDs are retained in custom/supplements.csv. English-sense decisions are in docs/supplement_pilot_review_2026-10-27.csv. Source etymology IDs retain their namespace; no GLED judgments are transferred. Specialist lexical review remains pending.

## South American depth review — 2026-10-28

Current construction: 120 forms / 82 supported core concepts
(previously 41 forms / 36 supported core).

Frozen CC BY4.0 study supplement: Ferraz Gerardi et al.2025,
doi:10.5281/zenodo.15041553, related article10.12688/openreseurope.19346.3.
Exact original row and SHA remain in provenance. All study readings stay
Segments_Source=profile; automatic COGID/COGIDS remain raw provenance only.
No expert/computed cognacy is emitted from those columns. Profiles are anchored
whole forms and cannot transcribe unknown forms or secondary sources.

79 new study forms cover59 core concepts. Oliveira2005 pp34,57–58 supports
phonemic c→t͡ʃ, r→ɾ, j→j; surface allophones remain uninferred. Nikulin2020
pp50–51 documents ñ→ɲ, explicit mid-high circumflex vowels and unrounded y.
Plain e/o, high circumflex vowels, shielding alternatives and unsplit compound
tokens remain held. This is broad phonemic interpretation, not narrow IPA.
Reference: https://www.etnolinguistica.org/local--files/tese:oliveira-2005/oliveira_2005.pdf
The study becomes primary; all earlier GLED forms and the existing supplied-IPA
Wiktionary supplement remain separately attributed. No new profile touches them.

Authored review and manifest: src/arcaverborum/data/je_original_review.csv and
je_original_source.json. Frozen source commit unchanged; phonological reference
PDF hashes stored in the manifest. Reproduce profiles with
scripts/stage_je_original.py --write-profiles. This round expands the existing
gerardije2025 namespace251→371 forms using scripts/expand_source_intake.py,
which forbids changes/removals to earlier forms/languages/parameters, changes to
license/citation/version/bibliography, and checks the expected baseline count.
Only new rows and source count metadata are added; replacement failures roll back.
Never subset-ingest active intake or append an existing namespace as new.

## Non-core source-led expansion — 2026-10-28

Added 72 non-core study forms; current total 192. Existing core coverage and
primary selection remain unchanged. The frozen source is expanded371→463 forms
with `expand_source_intake.py --expected-old-forms371`; all371 earlier forms and
all earlier languages, parameters, citations and source version remain intact.
Authored row hashes, senses and exact scoped readings remain in
`src/arcaverborum/data/je_original_review.csv`; profiles are compiled from it.
Unresolved road/path, brother, throat and other sense distinctions stay held.
A football-rattle definition is explicitly rejected for the Indigenous instrument.
Automatic cognacy is provenance only. See the source-led batch report.
