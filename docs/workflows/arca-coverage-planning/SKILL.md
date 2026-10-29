---
name: arca-coverage-planning
description: Plan and close evidence-based Arca Verborum coverage batches when asked what could be next, how to improve language coverage or source quality, or to execute an agreed expansion batch. Distinguish recommendations from authorized data work.
---

# Plan the next Arca coverage batch

Repository-local, skill-style procedure, routed by [AGENTS.md](../../../AGENTS.md).
Resolve paths relative to this file or locate the repository root with Git.
This procedure is maintained with the project; it requires no global installation.

## Establish the current state

Read [STATUS](../../STATUS.md), [NEXT](../../NEXT.md), and
[held work](../../planning/HELD.md). Read the latest journal entry and only the
relevant dated reports/packets. Resolve disagreements against accepted configs,
guarded ledgers, generated forms and the committed web manifest/catalog. A dated
report's “current” means current for that recorded batch.

The standing objective is more languages, broader coverage and stronger evidence,
with the Americas, especially South America, first. Supplied transcriptions and
well-founded source-specific profiles are useful; valid tokens and larger raw
counts alone do not certify pronunciation or meaning.

## Source preference clarified by the user

Wiktionary is preferred over GLED when its reviewed variety-specific evidence
provides better coverage and trustworthy readings, whether supplied IPA or a
well-founded source-specific orthographic profile. GLED does not get a fixed
second-tier advantage: its ASJP-derived representations retain limitations that
normalization only partly addresses. Normalization cannot restore information
absent from the ASJP input. Compare original information, not just token
validity or the existing supported-core count. Record tone, quantity, phonation,
consonant contrasts, dialect/stage, exact senses and source provenance explicitly.
A larger GLED count or a zero-loss screen is not an automatic veto on a justified
quality-led primary change. Preserve earlier GLED evidence and document gaps,
superseded/uncertain readings and overlap without treating it as independent
confirmation. Generic Wiktionary spelling resegmentation alone does not establish
pronunciation. Source promotions remain reviewed config/custom changes, never a
blanket inversion of source-name rankings.

## Build a proposal

1. Remove completed tasks and check whether held cases have new reopening
   evidence. A repeated old candidate is not a fresh opportunity.
2. Inspect the latest member-level additive ranking. For changed intake/builds,
   regenerate locally with `python scripts/rank_coverage_opportunities.py
   --output output/report/coverage_opportunities.csv`. Inspect the CSV and JSON;
   do not sum overlapping members or promote a ranking directly into admissions.
3. Separately inspect sparse constructions, GLED primary replacements, primary-
   source profile recovery, unmapped/non-core vocabulary and genuinely missing
   languages. The additive ranking excludes the primary source and does not
   measure all these opportunities. Use `scripts/rank_gled_replacements.py` for
   replacement triage, then review accepted losses as well as gains. Also run `scripts/audit_reviewed_source_choices.py --output PATH` to inventory guarded alternatives across all accepted primaries; this includes authored profile/scoped evidence omitted by raw intake screens, but does not certify quality. The lossless
   supplied-reading screen is only a narrow diagnostic: profile-backed Wiktionary
   promotion and quality-led choices can be justified outside it.
4. Prefer concrete source/sense review with high-quality evidence and meaningful
   gaps, while reserving a bounded original-source acquisition task when language
   diversity is underserved. Compare family/geographic balance and research cost;
   batch size follows the evidence, not a fixed number of tracks.
5. For each proposed task state: exact variety/member, current baseline, evidence
   and source version, potential versus verified gain, first decision gate,
   next action and intended outcome. Give the recommendation and its material
   tradeoff. Mark unmeasured work as unmeasured.

Update NEXT with the proposal. A request for suggestions does not authorize a
new lexical batch. When asked to proceed, choose routine details autonomously
within the agreed scope and mark selected tasks reviewing.

## Evidence gates during execution

* **Identity:** reconcile exact source member, language/dialect/historical stage,
  accepted aliases and parent scopes. Keep separate counts for new languages,
  new named varieties and added evidence within existing constructions.
* **Provenance:** establish actual lexical attribution, immutable source snapshot
  and applicable redistribution terms. Metadata without lexical rows supplies no
  gain. Related literature cannot replace a missing original citation.
* **Transcription:** distinguish supplied readings, documented profile derivation,
  resegmented spelling and unresolved forms. Profile rules stay source/language
  scoped; exact-form profiles cannot generalize to unknown compounds. Preserve
  raw notation and unresolved tone, nasalization, glottals or alternatives.
* **Semantics:** compare original sense/POS/context against frozen definitions.
  Guard narrow meanings and homonyms; keep alternatives and bound forms visible.
* **Cognacy:** retain original namespaces, methods and uncertainty. Never transfer
  primary judgments to supplements or promote automatic IDs to expert judgments.
* **Admission:** author explicit admit/hold decisions and guarded evidence ledgers;
  update the variety's packet/recipe and enforced config/custom files together.

Use [ONBOARDING](../../../ONBOARDING.md), the build/concept specifications and
source-specific scripts for execution. Stage outside active intake. New namespaces
use `append_source_intake.py`; an additive existing-namespace expansion can use
`expand_source_intake.py` only if earlier rows/citations/license/version/bibliography
are unchanged and the actual old count is guarded. Other changes need a distinct
reviewed migration. Never subset-ingest over active tables or replay old counts.

## Verify, close and retain a useful next queue

Validate affected builds, preserved earlier evidence, source/profile scopes and
realized counts. Use accepted outputs rather than orphan configs for whole-
collection checks. Run checks appropriate to the change; CI uses the `pytest`
entry point. Regenerate aggregate and tracked web artifacts for data changes;
[web/README](../../../web/README.md) describes browser and publication checks.
A Pages success alone does not establish data freshness.

At closure:

* Record before/after forms, supported core slots, mapped slots, source/profile
  status, new languages/varieties and GLED replacements separately.
* Create a dated report/metrics/decision ledger and link it from the history index.
* Update STATUS's baseline/evidence/publication pointers, NEXT, relevant held
  cases, packets/recipes, journal and local memory. Keep dated evidence intact.
* Move completed tasks out of the active queue. A hold records its exact reason,
  next evidence required and source/version; reopen it only on relevant changes.
* Report zero gains/admissions honestly when the research gate fails. Explain the
  resulting evidence, then choose future work from the updated baseline.

A good next proposal can be understood from NEXT and STATUS without reconstructing
conversation history. Historical counts, prospective ceilings and realized gains
must remain distinguishable.
