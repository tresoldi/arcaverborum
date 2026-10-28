# nub-xerente — source supplementation packet


## Reviewed additive IPA evidence — 2026-10-27

1 exact Wiktionary source forms add 1 core concepts without removing primary forms. Only supplied IPA is used; the primary profile is not applied to the secondary source. Full lexical/source evidence hashes and original source IDs are retained in custom/supplements.csv. English-sense decisions are in docs/supplement_pilot_review_2026-10-27.csv. Source etymology IDs retain their namespace; no GLED judgments are transferred. Specialist lexical review remains pending.

## South American coverage review — 2026-10-28

Current construction: **159 forms / 71 supported core concepts**
(previously 39 forms / 36 supported core).

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

The documented study becomes the pinned primary source. Every previously
accepted GLED form remains a separately attributed supplemental record, along
with existing Wiktionary supplements. The new profile never transcribes those
secondary sources. No GLED cognacy is transferred onto study forms. See
docs/south_america_coverage_2026-10-28_gled_preservation.csv. Primary-source
replacement is counted separately from retained GLED lexical evidence.

Semantic correction: the upstream CROSS label denotes the traverse verb.
Nikulin2020 printed p.453 (PDF p.477), Akwẽ-Xerénte tbro, glossed atravessar,
supports mot-traverse rather than the geometric cross noun. Raw source label
and row remain visible. See the authored Jê review, entry658.
