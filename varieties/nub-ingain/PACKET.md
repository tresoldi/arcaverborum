# Ingain — curation packet

## South American coverage review — 2026-10-28

Current construction: **24 forms / 16 supported core concepts**
(previously 0 forms / 0 supported core).

Authority: Ferraz Gerardi et al. (2025), A phylogenetic classification of the Je
language family: Supplementary data, doi:10.5281/zenodo.15041553; related article
doi:10.12688/openreseurope.19346.3. Explicit CC BY 4.0 author repository
https://github.com/TGH-2020/Je_Phylogeny, frozen commit
8f4f0a9a7b36ba4e3a9a15ba49b13056cfbbcf1e. Dataset-level attribution is retained;
individual fieldwork authorship is not invented. Every original row and automatic
COGID/COGIDS survives in provenance; no accepted expert/computed cognacy is emitted.

Raw notation is NOT treated as supplied IPA. Exact whole-form profiles emit only
reviewed broad phonemic readings from already explicit unambiguous symbols.
Nikulin (2020), section 1.4, pp.50–53 documents Macro-Jê notation. Ambiguous
c/ĵ/j/r/y, circumflex vowels, shielding alternatives such as m/b, leading
diacritics, missing values and unsplit compound tokens stay held. Nasal vowels
are NFC-normalized, retaining nasalization/length; nasal mid-vowel symbols have
no four-height contrast in the notation authority. No surface allophones or
predictable echo vowels are invented. Every output has Segments_Source=profile.

The authored source-review ledger and frozen source/file manifest are
src/arcaverborum/data/je_original_review.csv and je_original_source.json.
Held food-egg/daylight and other insufficiently specific source senses remain
explicit. Source files are hash-checked before materialization. Reproduce with
scripts/stage_je_original.py --fetch --write-profiles, validate/append the staged
new namespace only on first installation, rebuild intake-db, then update.
Never subset-ingest over active tables or append the same namespace twice.

Ingain (inga1254) is a distinct language-level catalog entry with no earlier
accepted sample, source alias or parent-coded construction found. This is one
new language, not a speaker/dialect split. The initial slice has 24 forms and
22 concepts, including 16 core concepts. Its modest scope and held readings are
intentional. Regional catalog coordinates are not speaker GPS. Other source
samples such as Tapayúna, Parkatêjê and Pykobjê are dialect-level cases under
already accepted languages, so this batch does not count them as new languages.

## South American depth review — 2026-10-28

Current construction: 26 forms / 18 supported core concepts
(previously 24 forms / 16 supported core).

Frozen CC BY4.0 study supplement: Ferraz Gerardi et al.2025,
doi:10.5281/zenodo.15041553, related article10.12688/openreseurope.19346.3.
Exact original row and SHA remain in provenance. All study readings stay
Segments_Source=profile; automatic COGID/COGIDS remain raw provenance only.
No expert/computed cognacy is emitted from those columns. Profiles are anchored
whole forms and cannot transcribe unknown forms or secondary sources.

Two earlier held numerals are admitted: TWO repairs the explicit unsplit ɾi
token to ɾ i; FOUR similarly splits kəɾ into k ə ɾ. Original vowel qualities
and source labels retained; no ambiguous alternatives selected. Ingain now has
26 forms /24 mapped concepts /18 core concepts. It remains one existing accepted
language. Other historical source notation is still held.

Authored review and manifest: src/arcaverborum/data/je_original_review.csv and
je_original_source.json. Frozen source commit unchanged; phonological reference
PDF hashes stored in the manifest. Reproduce profiles with
scripts/stage_je_original.py --write-profiles. This round expands the existing
gerardije2025 namespace251→371 forms using scripts/expand_source_intake.py,
which forbids changes/removals to earlier forms/languages/parameters, changes to
license/citation/version/bibliography, and checks the expected baseline count.
Only new rows and source count metadata are added; replacement failures roll back.
Never subset-ingest active intake or append an existing namespace as new.
