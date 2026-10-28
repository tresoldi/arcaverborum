# Guarded primary subsets and recording metadata

A dictionary can become primary without emitting its entire unreviewed inventory.
`custom/primary.csv` uses the guarded source-form ledger schema: exact dataset,
member, Glottocode, full lexical evidence hash, source concept guard, frozen
concept, explicit admission/rationale, and optional anchored source-specific
profile with SHA256. Builds select only these rows and fail on missing, duplicate
or changed evidence. A primary ledger must use the configured source and one
profile scope. `custom/profile.tsv` cannot silently override that guarded scope.

Earlier primary evidence can be preserved through ordinary source-separated
`custom/supplements.csv`. Admission there retains original cognacy namespaces;
it does not transfer the new primary's judgments. Both ledgers and source-scoped
profile files participate in freshness checks. Tseltal is the first bounded
primary profile: see its packet and `scripts/tseltal_profile.py`.

An unlinked named community sample may use `sources.member_only: true` only when
its exact source_language_id is provided and canonical Glottocode is blank.
This selects that member within the blank-code dataset slice. It fails if the
member disappears and never uses a generic GLED fallback. A shared blank code
is not evidence for alternative-source identity, so these samples are excluded
from automatic cross-source coverage ranking. Nizaviguiti is a named-variety
admission without a distinct-language or guessed parent/code claim.

Mixe-Zoquean Voices' `►` denotes a recording placeholder, not a spelling.
The emitter excludes it from lexical rows while retaining exact source IDs,
member, parameter, citation and raw marker in generated/recordings.csv. The web
build publishes the combined recording metadata CSV, counts it separately in
catalog/manifest, and links it from affected variety pages. Raw source recording
links/files remain upstream. The opportunity ranker excludes the marker from
orthographic/profile potential. No IPA is inferred from audio.

[NA01–NA07 report](NORTH_AMERICA_EXPANSION_2026-10-28.md),
[standing workflow](workflows/arca-coverage-planning/SKILL.md).
