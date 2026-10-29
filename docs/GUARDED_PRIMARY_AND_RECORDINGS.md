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

Missing bounded-primary input fails before generic fallback, including an entirely
absent primary slice. Empty non-guarded sources clear stale generated recording
sidecars. Profile readers normalize derived output to Unicode NFC; portable tests
use tracked authored ledgers/profiles rather than ignored local intake.

Historical lexical evidence can use `transcription_policy=orthographic_only` in a
reviewed ledger. It requires empty supplied Segments, no profile and no raw IPA;
the emitter preserves blank segments even for a tokenizable Latin spelling.
These rows remain unsupported in phonetic coverage. This is an explicit lexical
admission, not a fallback that reinterprets source pronunciations. Source/member
historical reading rules in `custom/historical_evidence.csv` annotate exported
comments independently of segment origin and participate in freshness checks.
[Ancient batch](ANCIENT_EXPANSION_2026-10-28.md).

A dictionary whose inherited source code is too coarse may use an exact registered
source/target scope after primary identity review. Sanzhi's `dictsanzhi_dar` source
code darg1241 maps only to target sanz1248 through its guarded rule; other Dargwa
members are not covered. The finite-profile compiler preserves all scope fields.
Explicit original dictionary noun/verb conflicts now fail profile compilation;
unknown labels and other semantic/POS relations still need manual review.

## Verbatim native evidence across a primary change

`custom/preserved_forms.csv` retains previously emitted native rows, including
unmapped evidence. It carries every `FORMS_OUT_FIELDS` column plus
`evidence_sha256`, `expected_source_concepticon_id`, `previous_output_sha256` and
`preservation_rationale`. The prior-output digest covers the complete prior row;
raw evidence, member/parameter, mapping, bibliography, native cognacy and the
unchanged normalizer result are independently checked. Unmapped rows stay
unmapped. This path cannot upgrade spelling, introduce a profile, carry qualified
IPA outside its original guard, or emit a duplicate already admitted elsewhere.
Both raw source slices and the preservation ledger participate in freshness.

Use this for an audited migration, with a preceding accepted-output comparison.
New lexical admissions still require the normal guarded primary/supplement route.
The Q07 Ruruuli and Chintang packets are bounded examples; the prior evidence
remains attributable and does not become independent confirmation of the new source.
