# Critical assessment of the independent colexification reviews

Review target: commit `9bc2ad28d8d64ba44530a74a696436aa0c92e78e`, analytical core
`d5c9b49da8851392bac2e2e0`. This is a methodological review, not a new analytical
publication. Accepted lexical records, graph weights and published clusters have
not been changed.

## Independent reviewers and assessment outcome

The requested reviews were carried out separately by a Codex subagent
(`gpt-6.1-terra`) and the local Claude CLI (`claude-opus-5-5`, verified from its
result metadata). Neither read the other's report. Their complete reports are
[Codex](2026-11-01-codex-adversarial.md) and
[Claude](2026-11-01-claude-adversarial.md). Claude completed 29 turns; its report
includes read-only production queries and bounded experiments. Agreement between
reviewers is not independent lexical validation: both examined the same code and
data. The parent assessment below checks consequential claims rather than voting.

The strongest outcome is that there are **current extraction/classification
defects**, beyond the latent semantic-approval defects. The sense corrections
and evidence-preservation work remain valuable, but the globally replicated
model should remain explicitly experimental. Its apparent robustness does not
remove source-parser, concept-inventory or classification artefacts.

## Independently checked findings

The [verification record](2026-11-01-adversarial-verification.json) records bounded
fixtures and read-only queries against the accepted SQLite database.

* **Truncated Ineseño forms are a demonstrated extraction defect.** Retained
  aggregate values `ʧ'ɨlɨ` (antelope) and `ʧ'ɨpɨk` (beaver) both have `Form=ʧ`
  and `Segments=tʃ`; BAG has `Value=č'ïlï`, `Form=č`, `Segments=tʃ`. The current
  apostrophe-prefix exclusion guards Huntergatherer member 30, not this member
  43. This is stronger evidence than simply observing an improbable one-segment
  word. It establishes false identity for the differing source readings;
  original orthography and the possible BAG/ANTELOPE relation still need their
  own interpretation. Audit the parser and all affected members, preserving the
  full source readings before admitting repaired phonetics.
* **Isolate language/dialect family keys split one lineage.** Abun, Burushaski,
  Berta and Mosetén-Chimané illustrate `isolate:<ID>` for a language versus
  `<ID>` for its dialects. Independently merging these keys changes five current
  backbone weights; all five edges remain eligible. Fix canonical lineage keys
  in both counts and resampling, with display labels separate.
* **Glottolog pseudo-categories are not genealogical families.** The loader
  accepts every nonempty `Family_ID`. Removing the eight categories identified
  by Claude makes 28 backbone edges lose eligibility. This is a diagnostic
  count, not a proposed exclusion of their lexical evidence. Resolve known
  retired identities to reviewed classifications; retain genuinely unknown
  genealogy as unknown. Glottolog explicitly labels
  [Bookkeeping a pseudo-family](https://glottolog.org/resource/languoid/id/book1242)
  and [Laitu Chin a retired bookkeeping entry](https://glottolog.org/resource/languoid/id/lait1239).
  The current LAUNDER–SPIT edge uses Bookkeeping and Sino-Tibetan as its two
  family keys, so the supposedly known-family criterion is unsound here even
  before resolving the retired entry's replacement.
* **Catalog overlap reaches the backbone.** PATH–PATH OR ROAD has 17 eligible
  families and model weight 8.5. Two native IDs do not establish two distinct
  meanings when the catalog definitions overlap. Claude's other candidates
  warrant a reviewed relation table; labels containing `or` alone must not drive
  automatic removals or node merges. Keep these identities inspectable and
  distinguish catalog overlap from colexification between distinct senses.

* **Conflicting local approvals are an implementation defect.** Two local maps
  for one parameter accept the last target; reversing row order reverses the
  accepted target. Merely sorting files would make the bug deterministic rather
  than resolve the contradiction. Collect incompatible targets and fail closed.
  A scan of 2,144 current local approval keys found no distinct-target conflicts;
  this does not establish that the current published graph was affected.
* **Local parameter ambiguity needs the same guard as shared rules.** The Codex
  follow-up reproduced an ambiguous source ID obtaining approval through a local
  parameter map. My scan found no multi-name source IDs among the 220 distinct
  currently approved local parameter IDs. This remains a real API failure mode,
  rather than demonstrated current data corruption.
* **The current deletion criterion is weaker than surviving cross-family
  replication.** Of 5,551 backbone edges, 3,353 (60.4%) retain only one family in
  the worst resource-deletion case; 2,198 retain at least two. The implementation
  follows the documented criterion: two families before deletion, positive
  remaining mass afterwards. This is not an arithmetic bug, and the 3,353 edges
  are not thereby false positives. It does invalidate an interpretation that
  cross-family replication necessarily survives deletion.
* **Unit group mass is sensitive to recorded inventory.** Pipeline fixtures give
  an unchanged pair mass 1 with two reported concepts and 1/3 with three. The
  penalty applies to reported group size before semantic gating; unreviewed
  additional senses can therefore reduce eligible evidence. Family maxima favor
  a smaller recorded group when alternative witnesses exist. These are real
  consequences, but neither demonstrates that an unweighted or per-node
  alternative is universally better.

## Criticisms that require qualification

* Claude labels short forms and affix-marked strings collectively as data
  defects. The Ineseño case is verified, but shortness alone does not establish
  corruption, and `_`/`-` require source-specific notation review. I independently
  reproduce the 201-edge loss after removing every single-segment witness.
  That is a sensitivity diagnostic, **not 201 demonstrated false edges**. Do
  not blanket-exclude genuine short words or infer boundness from punctuation.
* Claude's maximum-versus-sample-size example is mathematically valid: more
  witnessing varieties give more chances to reach a maximum of 1. Its observed
  contribution differences do not isolate causal sampling bias from source and
  language composition. Means/medians are alternatives to compare, not proven
  fixes; means restricted to positive witnesses also have selection effects.
* The resource-block registry explicitly disclaims certified independence.
  Claude's heading that independence is "asserted" overstates the current
  claim. The substantive remaining issue is incomplete original-source
  genealogy and the effect of grouping or splitting compilation blocks.
* Treating dropped nodes as singletons does not automatically give a
  mathematical lower bound on adjusted Rand agreement. Report conditional
  agreement and retention separately; any union-aware comparison needs its own
  stated missing-node convention. Do not turn absent nodes into a shared class.
* The CLICS comparison currently describes raw reported evidence, not the new
  weighted backbone. This is a limitation of its coverage, not an incorrect raw
  comparison. Add staged comparisons on matched scope and inventories if useful;
  neither agreement nor disagreement supplies an independent gold standard.
* Claude's proposed prosody-unresolved layer may recover candidates, but source
  stress absence can mean unknown prosody or known absence depending on the
  convention. Such matches belong in a separate explicitly unresolved layer,
  not silently in exact phonetic identity.

* A `needs_review` row currently does not veto another positive approval. This
  requires an explicit policy for scope and precedence: a provisional
  parameter-level hold should not automatically cancel a separately justified
  exact-record review. The Codex scan found no current positive/hold overlaps.
* The potential bypass for differently named Wiktionary namespaces is worth
  preventing by tracking mapping mechanism, but current reading scopes with a
  `wikt` prefix use the gated `wiktionary` namespace. A current bypass has not
  been demonstrated. Other sources' upstream mappings still need semantic
  validation; their label `source_mapping` is not a quality certificate.
* Missingness and independence are already explicit limitations. No shared form
  observed is not lexical absence; resource blocks are not proven independent
  fieldwork. Improvements should measure these weaknesses, rather than describe
  existing caveats as newly discovered features.
* Conditional community diagnostics already export eligible-replicate counts,
  and the UI displays coassignment as `together/eligible`. Adjusted Rand exports
  include common-node counts. The stronger request is to add retention beside
  comparisons and count eligibility against all replicates, not claim the
  existing denominators are entirely absent.
* The 64/65-concept quarantine boundary is discontinuous, but the current two
  quarantined groups are both TLS Mbunga identities (151 written / 154 segmented
  concepts). No group close to that boundary was demonstrated in this snapshot;
  normal segmented multi-concept groups reach 15. Investigate their source
  readings before treating a higher threshold as an improvement.

## Decision criteria

Recommended order for a subsequent implementation batch:

1. Audit and guard demonstrated prefix truncation across source members; repair
   source-specific ingestion where justified. Fix isolate keys and the use of
   pseudo-categories as known families. Add conflict/collision fail-closed guards
   and tests through the actual production semantic and resampling paths.
2. Review concept containment/overlap against frozen definitions and source
   questions. Separate these relationships from distinct-sense colexification.
3. Compare weighting conventions and the stricter post-deletion criterion on
   identical eligible evidence; publish retention and regional consequences.
   Preserve rare/local observations and avoid asserting that stricter is truer.
4. Extend mapping-mechanism-based semantic review and original-resource
   genealogy; use an independently adjudicated stratified benchmark and justified
   null diagnostics before any general superiority claim.

These are review recommendations, not implemented changes or a new deployment.

Keep the verified sense corrections, original evidence, representation layers
and sparse pipeline. Do not claim general superiority over CLICS: the new weights
are bounded-support diagnostics, not calibrated significance, prevalence or a
validated account of semantic categories. The CLICS 4 paper itself documents
improved phonetic evidence and sampling: [Tjuka et al. 2025](https://aclanthology.org/2025.iwcs-main.1/).

Before changing the default model, compare matched inventories and eligible
witnesses under raw capped-family, unit-total-group, per-node and stricter
post-deletion family variants. Measure edge/node retention, regional losses and
cluster changes, including the Americas. A stricter graph is a sensitivity
model, not an automatic replacement for evidence from rare languages.

The targeted existing evidence/core tests pass (32 tests). This does not test
away the newly reproduced defects: the contradictory approval fixture lies
outside their current coverage.
