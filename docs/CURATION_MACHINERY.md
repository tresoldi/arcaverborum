# Curation Machinery: Authority Recipes and Packets

Status: **draft for review** (2026-08-22). This defines the concrete file
mechanism for the curation workflow in `CURATION_WORKFLOW_SPECIFICATION.md`.
It implements the "descriptive companion" binding model: recipes and packets
are hand/agent-authored records of the accepted construction; the build keeps
using `config.yaml` + `custom/*`, and selected recipe fields become
build-enforced incrementally.

## Two artifacts, per variety

```
varieties/<av_id>/
├── config.yaml        (existing) source picks, scoring, pins — some fields auto-managed
├── recipe.yaml        (NEW) authority recipe: the accepted construction, machine-readable
├── PACKET.md          (NEW) curation packet: human-readable report + rationale
└── custom/            (existing) the enforced correction layer
    ├── transcriptions.csv · forms.csv · cognates.csv · concept_map.csv · profile.tsv
```

* **`recipe.yaml`** — the durable, structured "best construction for this
  variety" record. Descriptive-first. Every field is either **ENFORCED**
  (it names a mechanism the build already consumes) or **advisory** (rationale,
  candidates, tradeoffs, provenance, review). The recipe never duplicates data
  that lives in `custom/*`; it *references* it and explains it.
* **`PACKET.md`** — the human-readable entry point a reviewer or agent reads
  first: current construction, candidate sources and coverage, transcription
  and concept quality, cognate availability, recommended recipe, gains/losses,
  and proposed follow-up. "Found another source" is not enough — the packet
  must say what it improves, what it loses, and whether the tradeoff justifies
  a change (per the workflow spec).

## `recipe.yaml` schema

```yaml
av_id: <str>                     # matches directory; identity only
name: <str>
review:
  status: draft|reviewed|accepted
  reviewer: <str>
  date: <YYYY-MM-DD>
construction:
  summary: <str>                 # one-paragraph statement of the accepted construction
  lexical_base:
    source: <dataset>            # ENFORCED  -> config.sources.transcription
    rationale: <str>             # advisory
  transcription:
    strategy: source|profile|override|mixed
    profile: none|custom/profile.tsv          # ENFORCED  (extensions.profile)
    overrides: none|custom/transcriptions.csv # ENFORCED  (extensions.transcriptions)
    notes: <str>                 # advisory (e.g. segment cleanliness)
  concepts:
    mapping: source|corrected    # ENFORCED via custom/concept_map.csv when corrected
    core_coverage: <n>/<N>       # basic-vocab core concepts present (advisory diagnostic)
    notes: <str>
  cognates:
    source: <dataset>            # ENFORCED  -> config.sources.cognates
    method: expert|computed|manual|hybrid
    computed: none|{algorithm,implementation,version,parameters,date,input}  # method metadata
    notes: <str>
  loans:
    handling: source|<str>       # advisory for now
candidates:                      # advisory: other sources considered
  - source: <dataset>
    coverage: full|partial|none
    verdict: used|not used|fallback
    reason: <str>
provenance:
  bibliography: [<bibtex_key>, ...]   # advisory; keys resolve in output sources.bib
tradeoffs:
  gains: <str>
  known_losses: <str>
```

### Enforced vs advisory (v1)

**Enforced now** (already consumed by the build, recipe just names them):
`lexical_base.source`, `cognates.source` (→ `config.sources`), and the
`custom/*` layer referenced by `transcription.*` and `concepts.mapping`.

**Advisory now** (descriptive; may become enforced later): `review`,
`rationale` fields, `candidates`, `provenance.bibliography`, `tradeoffs`,
`loans.handling`, `cognates.method`/`computed` (until the computed-cognate
evaluation gate exists).

A recipe therefore never changes build output on its own today — it records
*why* the current `config.yaml` + `custom/*` are what they are, and what a
future improvement would cost. Enforcement is added field-by-field, each with
a reviewed migration, so recipe, docs, and rebuild consequences move together.

## Rollout

One exemplar packet + recipe per CORE family first (13 varieties) to prove and
refine this schema; then scaffold the remaining CORE varieties (auto-filled
from `config.yaml` + build diagnostics) and fill in by hand. Beyond-CORE
varieties (Wiktionary/GLED fallbacks) get packets when they enter curation.

## Open (defer until the exemplars are reviewed)

* whether `PACKET.md` is generated-then-edited or authored-then-checked;
* a `build.py packet <av_id>` scaffolder that emits a stub recipe + packet
  from current config + diagnostics;
* when `cognates.method: computed` becomes enforceable (needs the evaluation
  gate from the workflow spec);
* how agent-driven online-source discovery writes into `candidates`.
