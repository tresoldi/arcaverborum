# Curation Workflow Specification

Arca Verborum's goal is a single accepted lexical dataset for
computational historical linguistics. The dataset should be broad enough to
support large-scale comparison, but each language should also be improvable
as an individual scholarly object. This document defines the planning model
for that work. It is intentionally descriptive for now; it does not by
itself change build behavior.

## Current Baseline

As of the latest local aggregate reviewed for this specification:

* The aggregate contains 7,308 varieties and 2,007,699 forms.
* Segment status is approximately 85.0% source/profile clean, with 105,410
  unclean forms remaining.
* Manual curation is still small: 160 pinned selections, 39 non-empty
  orthographic profiles, and 4 transcription override files.
* Concept mapping is a major remaining bottleneck: 236,246 forms lack
  `concept_id`, and 369 varieties currently have zero mapped concepts.
* 1,271 varieties have a selected cognate source different from the selected
  transcription source, but cross-source cognate reconciliation is not yet
  implemented.

These numbers are diagnostics, not policy. They show that transcription
cleanup, concept mapping, source review, and cognate strategy all need to be
handled as first-class curation dimensions.

## Canonical Dataset

Arca should keep one canonical accepted dataset. Once a datapoint is
accepted into Arca, it belongs to that dataset. Users should filter by
tier, scores, provenance, and metadata rather than by a hidden distinction
between "real" and "provisional" data.

The canonical product should remain conservative in its outward shape:
there is one default accepted construction per variety. Alternative sources
remain available as evidence and candidates for audit, replacement,
correction, or future derived layers. They should not be merged into the
canonical aggregate automatically just because they exist.

## Authority Recipes

Language curation is not just source selection. For each language, the
central question is:

> What is the best authoritative construction for this language?

An authority recipe describes that construction. It may include:

* lexical base source;
* transcription and phonological normalization strategy;
* orthographic profile or segment correction strategy;
* concept-map corrections;
* cognate source, computed cognates, manual cognates, or a hybrid;
* loan and commentary handling;
* bibliography and provenance;
* known losses and tradeoffs relative to other candidate sources.

The first version of authority recipes should be conservative and
descriptive. They should let humans and agents discuss what is intended
before every field is made build-enforced. Once stable patterns emerge from
real curation packets, selected recipe fields can become consumed directly
by the build.

## Source Policy

The current documented priority of Lexibank, then GLED, then Wiktionary is
outdated for the intended curation workflow.

The intended policy is:

1. Prefer curated or otherwise known high-quality lexical datasets.
2. Treat Wiktionary as an important fallback and research entry point,
   especially for languages where no dedicated curated source is available.
3. Use GLED only as last-resort scaffolding when no better information can
   be found.

Source replacement decisions should be reviewed and durable. The compact
source-of-truth for an intentional source choice should be a reviewed pin,
currently represented by `src/arcaverborum/data/selection.csv`. Per-variety
`config.yaml` files may reflect that choice, but should not become the only
place where source-choice policy is recorded.

## Curation Packets

Improving a language should produce a structured curation packet rather
than ad hoc edits. The durable packet should be file-based and live in the
repo. A project-level spec lives under `docs/`; per-language packets should
live in a tracked curation area to be decided.

Each packet should have a human-readable Markdown report as its entry
point. Optional machine-readable sidecar files may hold proposed changes:
source proposals, transcription overrides, concept-map fixes, added forms,
cognate corrections, computed-cognate outputs, and bibliography additions.

A language packet should report at least:

* current accepted construction;
* candidate lexical sources and their coverage;
* transcription quality and required normalization;
* concept coverage and unmapped concepts;
* cognate availability and quality;
* possible computed-cognate strategy;
* candidate bibliography and source provenance;
* recommended authority recipe;
* gains and losses versus the current construction;
* proposed pins, overrides, derived layers, or follow-up work.

Agents looking for sources online should produce packets in this form.
"Found another source" is not enough. The packet must say what it improves,
what it loses, and whether the tradeoff justifies changing the accepted
construction.

## Arca-Derived Layers

Some language improvements will be too large to treat as ordinary custom
overrides. Arca may effectively create a new dataset itself, either by
authoring new data or by applying many explicit corrections to an upstream
source.

When corrections change the scholarly identity of the data, cover a
substantial share of forms or concepts, add newly computed or curated
cognates, or make the result better cited as Arca's construction than as
the upstream source alone, the work should graduate into a named
Arca-derived source layer.

An Arca-derived layer should be durable and exportable. It should have:

* a name and version;
* base source or sources;
* explicit correction lists mapping old values to new values;
* added or removed forms, if any;
* concept-map changes;
* transcription/profile changes;
* cognate judgments or computed-cognate outputs;
* method and parameter metadata for computed material;
* bibliography, notes, and review status;
* generated normalized output that can be inspected and tested.

The point is not to hide heavy correction behind anonymous overrides. The
canonical dataset should be honest about cases where Arca has become the
authoritative derived source.

## Computed Cognates

Computed cognates should be represented first as candidate layers, not as
silent overwrites of source cognates. Each computed layer should carry
method metadata: algorithm, implementation, version, parameters, date,
input data, and any preprocessing assumptions.

Before computed cognates become authoritative for a language, they need an
evaluation gate. The evaluation should compare against expert cognates
where available, include language- or family-specific spot checks, and
report diagnostics that favor precision over plausible-looking coverage.
The language packet then decides whether source cognates, computed
cognates, manual cognates, or a hybrid are accepted.

## Tier Model

The existing simple tier names should remain user-facing. Do not encode
construction type into compound tier labels such as `silver+profiled` or
`bronze+wiktionary`.

Tiers should, however, describe the whole authoritative construction for a
language, not only lexical-source quality. The supporting metadata and
reports should explain the components:

* lexical source quality;
* transcription cleanliness;
* concept mapping;
* cognate quality;
* provenance and bibliography;
* review depth;
* whether Arca-derived material is involved.

This lets users filter the canonical dataset by simple tiers while still
auditing why a variety received its tier.

## Curation Queue

The next curation queue should be broader than the current
unclean-transcription report. Ranking should combine:

* transcription cleanliness;
* concept coverage gaps;
* source-quality uncertainty;
* historical and comparative importance;
* cognate availability and reliability;
* data volume;
* family or macroarea priorities.

`output/report/curation.csv` remains useful, but it mainly surfaces
hand-fixable segment problems. It should not be the only driver for
language-review priority.

## Pilot Scope

The workflow should be tested on a small pilot set before broad
agent-driven source discovery.

The pilot should include:

* Indo-European / IECOR as a high-value curated baseline;
* Chinese varieties, where source selection, transcription, and concept
  mapping are likely to be difficult;
* Benue-Congo, where current coverage and quality issues can test the
  workflow outside Indo-European;
* at least one Wiktionary-heavy case, because Wiktionary is an important
  fallback and research entry point.

GLED-only cases should be included only when they represent the
last-resort problem the project must handle.

## Open Decisions

These decisions are not settled yet:

* exact per-language packet directory layout;
* exact authority-recipe schema;
* when and how recipe fields become build-enforced;
* file layout and naming for Arca-derived layers;
* tier thresholds and component metadata fields;
* computed-cognate benchmark metrics and required review gates;
* first concrete pilot language list;
* how online-source agents should cite, cache, and summarize external
  evidence;
* how to revise source-priority code and documentation without disrupting
  the current aggregate unexpectedly.

## Immediate Next Actions

1. Review and revise this specification until the curation model is shared.
2. Choose the first pilot languages.
3. Define the file layout for a per-language curation packet.
4. Draft the packet template.
5. Draft the descriptive authority-recipe schema.
6. Decide which current reports need expansion to produce the broader
   curation queue.
7. Only then change build behavior.
