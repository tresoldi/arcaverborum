# Documentation map

WordNet sense alignment: [versions, typed links, review queue and reproduction](WORDNET.md).

## Start here

| Need | Read |
| --- | --- |
| Current accepted dataset, metrics and publication evidence | [STATUS](STATUS.md) |
| What could be next, with evidence and first gates | [NEXT](NEXT.md) |
| Repeatable planning and batch closure | [Coverage-planning workflow](workflows/arca-coverage-planning/SKILL.md) |
| Why a candidate is held and what would reopen it | [Held-work register](planning/HELD.md) |
| Environment, build commands and operational constraints | [ONBOARDING](../ONBOARDING.md) |
| Domain vocabulary and architecture | [CONTEXT](../CONTEXT.md) |
| Completed batches and dated evidence | [History index](history/README.md) |
| Chronological decisions and handoffs | [Journal](JOURNAL.md) |
| Bounded primary admissions, unlinked samples and recordings | [Evidence format](GUARDED_PRIMARY_AND_RECORDINGS.md) |

STATUS and NEXT are maintained at batch closure. The planning workflow is a
repository-local skill-style procedure, routed from [AGENTS.md](../AGENTS.md).
Per-variety `PACKET.md` and `recipe.yaml` explain the accepted construction;
configs and guarded `custom/*` implement it. Dated reports retain their original
paths and observations; the history index gives them context.

## Technical references

| Reference | Scope |
| --- | --- |
| [Build specification](BESTOF_SPECIFICATION.md) | Per-variety build, source/config/custom mechanics; current supplementation note included |
| [RVID data component](RVID_DATA_LICENSE.md) | GPLv3 source, derivative scope and reproduction |
| [Concept specification](CONCEPTS_SPECIFICATION.md) | Frozen IDs, definitions and Concepticon mapping/drift |
| [Curation workflow specification](CURATION_WORKFLOW_SPECIFICATION.md) | Design direction; original diagnostic baseline is historical |
| [Curation machinery](CURATION_MACHINERY.md) | Descriptive recipes/packets and their relationship to enforced config/custom files |
| [Research explorer](RESEARCH_EXPLORER.md) and [web README](../web/README.md) | Current All-accepted explorer, provenance, exports, maps and publication checks |
| [Core v0.1.0 release specification](RELEASE_SPECIFICATION.md) | Archived release design, distinct from the live Core-source collection preset |

Use build/concept specifications alongside current code and source-specific
packets. Older design intentions and historical counts do not override accepted
configs, guarded ledgers or current generated evidence.

## Evidence and tools by task

* **Additive coverage:** latest ranking is linked from STATUS;
  `scripts/rank_coverage_opportunities.py` refreshes member-level discovery.
* **GLED primary replacement:** `scripts/rank_gled_replacements.py`, followed by
  exact-member, gain/loss and preservation review. Source additions alone do not
  count as primary replacements.
* **Dictionary/profile review:** source-specific scripts such as
  `galician_dictionary.py`, `iquito_profile.py` and `stage_je_original.py`;
  inspect their packets and authored ledgers before regenerating profiles.
* **Concept/source drift:** `build.py concepts`, `audit_core_pilots.py`,
  `audit_source_refresh.py` and source-specific guarded review compilers.
* **Pinned upstream CLDF:** `stage_reviewed_cldf.py --dataset NAME --fetch` stages native-preserving releases from `reviewed_cldf_sources.json`; `verify_reviewed_cldf.py` checks complete accepted namespaces. Original rows, village identity, plural forms and digital links remain in each record; upstream profiles remain attributed conversions.
* **Safe intake changes:** stage outside active intake. `append_source_intake.py`
  handles a new namespace; `expand_source_intake.py` handles strictly additive
  expansion with immutable earlier evidence. Other changes need reviewed migrations.
* **Publication:** rebuild accepted output, aggregate and `web/data/`, then use
  the checks in the web README. Pages publishes committed artifacts.

The held register routes to dated candidate decisions. Detailed per-form admit/
hold judgments stay in their original ledgers rather than being copied here.
