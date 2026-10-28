# Panará — curation packet

## South American depth review — 2026-10-28

Current construction: 70 forms / 54 supported core concepts
(previously 31 forms / 30 supported core).

Frozen CC BY4.0 study supplement: Ferraz Gerardi et al.2025,
doi:10.5281/zenodo.15041553, related article10.12688/openreseurope.19346.3.
Exact original row and SHA remain in provenance. All study readings stay
Segments_Source=profile; automatic COGID/COGIDS remain raw provenance only.
No expert/computed cognacy is emitted from those columns. Profiles are anchored
whole forms and cannot transcribe unknown forms or secondary sources.

39 new study forms cover38 core concepts. Panará j is a palatal approximant
(Lapierre2024, table2, printedp60/PDFp8); explicitly supplied ĭ retains extra-short
i. No unmarked echo vowels or surface-allophone detail is invented. Leading
diacritics, ambiguous c, stress conventions and unresolved notation stay held.
Reference: https://bpb-us-e1.wpmucdn.com/sites.uw.edu/dist/2/29962/files/2024/10/292-EnkeEtAl-2024-3-1.pdf
The study becomes primary; all earlier GLED forms remain separately attributed
supplements. Original catalog coordinates remain regional reference points.

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

Added 20 non-core study forms; current total 90. Existing core coverage and
primary selection remain unchanged. The frozen source is expanded371→463 forms
with `expand_source_intake.py --expected-old-forms 371`; all371 earlier forms and
all earlier languages, parameters, citations and source version remain intact.
Authored row hashes, senses and exact scoped readings remain in
`src/arcaverborum/data/je_original_review.csv`; profiles are compiled from it.
Unresolved road/path, brother, throat and other sense distinctions stay held.
A football-rattle definition is explicitly rejected for the Indigenous instrument.
Automatic cognacy is provenance only. See the source-led batch report.
