# Arca Verborum organization launch plan — 2026-11-02

Decisions agreed with Tiago on 2026-11-02 for moving Arca Verborum into the
`arcaverborum` GitHub organization, cutting the first schema-`A` release and
preparing the MDPI *Data* paper. Revised the same day after the
[Codex adversarial review](../reviews/2026-11-02-codex-org-launch.md) and its
[assessment](../reviews/2026-11-02-org-launch-assessment.md); Tiago accepted all
four resulting decisions.

Order of work: **working system in the org → show it to the invited authors →
Zenodo → paper.** This is an immediate task.

**Curation is frozen** until release `A` is published: no data batches (the NXT
queue, NXT-05, new expansion) start before then. The `A` baseline is data commit
`2ca6d8de2` (RC4 state) plus the licence-metadata fixes in §6.

## 1. What the project is (positioning for org, README and paper)

- A **curated selection and harmonization layer built on top of** Lexibank,
  GLED, Wiktionary and original sources. It is not an alternative to them.
  Lexibank's contribution is acknowledged as **foundational**: sources hosted
  under `github.com/lexibank/` supply 1,361,851 of 2,120,263 accepted records
  (64%, RC4 source terms). The rest come from GLED, Wiktionary, other CLDF
  datasets and original sources. The classification query is published with
  the paper.
- Origin: a way for students to access comparative lexical data without
  learning the CLDF toolchain or cloning many repositories. This motivates the
  explorer-first, static design.
- Design choices that distinguish it:
  1. one reviewed construction per variety. It may combine sources and Arca
     corrections, but the aim is the best available evidence for each variety;
  2. editors own decisions on their varieties and families (§5);
  3. continuous automated verification, and releases named by schema letter
     and date (§4);
  4. static, mirrorable infrastructure: everything in git and archives, with
     client-side computation;
  5. its own concept catalog linked to Concepticon and WordNet, and its own
     colexification products;
  6. tabular/text first, with a CLDF export;
  7. an explicit AI-assisted, human-owned policy (§5).

## 2. Repositories

| Repo | Visibility | Contents |
| --- | --- | --- |
| `arcaverborum/arcaverborum` | public | pipeline code, tests, curated data (`varieties/`, `src/arcaverborum/data/` incl. the concept catalog), current specs, `docs/evidence/` |
| `arcaverborum/site` | public | static explorer code; deploys the **latest release** to `arcaverborum.org` |
| `arcaverborum/live` | public | deploy-only; builds from the main repo's `master` → `live.arcaverborum.org` |
| `arcaverborum/paper` | **private** (Free plan) | MDPI *Data* manuscript |
| `arcaverborum/.github` | public | org profile, CONTRIBUTING, AI policy, code of conduct, PR/issue templates |

- New repos start **without history**: each gets a single initial commit of the
  current state, authored as Tiago, with **no AI trailers or markers of any
  kind** (this applies to all commits until Tiago decides otherwise).
- The concept catalog stays in the main repo; it gets split out only if someone
  outside wants to reuse it.
- **Evidence carried over:** 901 tracked files under `varieties/` reference 92
  distinct `docs/` paths. Those 92 files move into `docs/evidence/` in the new
  repo and the references are rewritten, so every accepted decision can be
  understood from the repo that holds it. CI checks that every `docs/` path
  referenced from `varieties/` exists.
- Also carried over: README, ONBOARDING, CONTEXT, `BESTOF_SPECIFICATION`,
  `CONCEPTS_SPECIFICATION`, `CURATION_WORKFLOW_SPECIFICATION`, `CONCEPT_ENTRIES`,
  `WORDNET`, `COLEXIFICATION`, a rewritten STATUS, and this plan as
  `docs/LAUNCH.md` (deleted once launch is done). Specs are cleaned of links to
  material that doesn't move.
- **Not carried over:** other dated reports, review CSVs and execution JSONs,
  root `*.log` files, `memory/`. They remain in the git history of
  `tresoldi/arcaverborum`.
- **The old repo** gets a deprecation notice **prepended** to its README (the
  rest is kept) and is archived only after the launch is verified.
- **`raw/curation/`** (11 GB, never tracked, partly copyrighted): Tiago makes a
  checksummed private archive on the NAS from the laptop. It is not published.

## 3. Replicability promise (two tiers)

- **Tier 1, guaranteed and checked by CI:** git plus the **accepted-inputs
  snapshot** re-derive the release tables and the site data in an empty
  workspace, offline.
  - **Snapshot contents:** the builder's full dependency closure, not just
    configured picks:
    - intake form rows for every accepted `(glottocode, source)` pair:
      configured picks (8,380), `custom/` supplement keys (215 more),
      source-member selectors and GLED fallback slices;
    - matching language, parameter, metadata and bibliography rows;
    - a frozen Glottolog table;
    - recording metadata;
    - the snapshot schema version.
  - A test fails the build if it reads anything outside the snapshot, or if a
    variety falls back unexpectedly.
  - **Size:** measured 2026-11-02 for configured picks only (79 MB + 5 MB
    gzip). Re-measure with the full closure; expected to stay in the low
    hundreds of MB.
  - **Pinned runtime:** merkmal by commit, a locked dependency set, no
    network fallbacks (missing frozen inputs fail the build). The build date
    is taken from the release identifier, not the clock.
  - **Two kinds of evidence, kept separate:** archive byte reproduction
    (already shown for RC4) and **full re-derivation from the snapshot**
    (not yet shown; required before `A`).
  - **Coverage:** Tier 1 covers lexical tables, catalogs and site data.
    Colexification and WordNet bundles are tracked derived inputs; they are
    regenerated from documented sources under Tier 2.
- **Tier 2, documented, best-effort:** re-derivation from the original sources.
  Each construction names its source and extraction script; non-redistributable
  inputs are named but not shipped.
- PR CI downloads the snapshot and rebuilds every touched variety.
- **Prerequisite fix:** `build.py update` must exit non-zero when any variety
  fails (today `update_many` counts failures and `cmd_update` returns 0). The
  aggregate step must check exact accepted membership.
- **Contributor changes outside the snapshot:** a PR that adds a source or
  variety ships the new intake rows as a reviewed snapshot extension. The next
  release folds the extension into the snapshot.

## 4. Releases

- Identifier `A-YYYY-MM-DD` (same-day re-release `A-YYYY-MM-DD.2`). The same
  string is used for the git tag, the Zenodo version and the archive names.
- The letter starts at **A** in the org. It bumps only on a **breaking** change
  to published tables: a column removed or renamed, a column's meaning changed
  (including value vocabularies and null conventions), an ID scheme changed, or
  a file restructured. Added columns, records or corrections keep the letter.
  Consumers must read tables by header. The paper describes schema A.
- Tags and assets are **immutable**. Every release has a changelog; supersession
  or withdrawal is recorded in the release notes.
- No public release candidates: candidates are CI artifacts or untagged drafts.
- Releases are cut when decided, not on a calendar.
- **Assets per release**, each tier with an explicit licence allowlist and
  filtered at file level (forms, custom files, evidence, recordings, derived
  products):
  - `arcaverborum-A-…-full.tar.gz`: every accepted record, including sources
    without a declaration (`terms_status = missing_declaration`);
  - `arcaverborum-A-…-redistributable.tar.gz`: declared licences that allow
    redistribution (CC BY, BY-SA, BY-NC, BY-NC-SA, GPL, PD). The datasheet
    lists NC and SA as restrictions;
  - `arcaverborum-A-…-by.tar.gz`: CC BY and public domain only. A test asserts
    no other source appears;
  - the accepted-inputs snapshot (it follows `-full` terms and says so),
    manifest, checksums and datasheet.
- **One release path:** `build.py release` currently builds the historical Core
  product. It is replaced by the schema-A builder: native tables, CLDF export
  validated independently (foreign keys, sources, cognate namespaces), and the
  three tiers.
- **Site:** `arcaverborum.org` serves the latest release by default;
  `live.arcaverborum.org` serves `master` with a banner showing the data
  revision and the latest release. Each site links to the other. Older
  releases are archived on Zenodo, not hosted.
  - Two Pages sites are needed because the site data is 652 MB (`web/` 664 MB)
    against the 1 GB Pages limit.
  - **Deployment:** `site` and `live` *pull* verified artifacts (a release
    asset, or the CI artifact of a green `master` run). They use a
    fine-grained read token stored as a secret and are triggered by dispatch,
    so the main repo never writes to them.
  - Measure the assembled payload at each deploy and fail above a headroom
    threshold. Shrinking the data is a post-launch optimization.
- **Zenodo:** a new concept DOI, minted **after the authors' first look**, not
  at launch. Author corrections become a later release (`A-<later date>`), and
  that release gets the DOI. The deposit tooling is rewritten (it targets the
  old DOI, Core metadata and `other-open`). The old record
  `10.5281/zenodo.17294927` gets a pointer.

## 5. Governance and AI policy

- **Roles:**
  - *Maintainer*: Tiago. Pipeline, schema, releases and policy.
  - *Editor*: an org member in the `editors` team with write access; may
    approve any PR.
  - *Language editor*: an editor with a scope over varieties and/or families
    (one or more), or a layer (`concepts`, `colexification`, `pipeline`).
- `editors.csv` (`github_login, name, orcid, scope`) is committed data.
  - A script generates `.github/CODEOWNERS` from it, listing individual logins.
    Family scopes become `av_id`-prefix rules (`/varieties/tup-*/`), since the
    family code is the ID prefix; sub-family scopes list varieties explicitly.
  - Shared registries (`varieties.csv`, `concepts.csv`, the rest of
    `src/arcaverborum/data/`) belong to the maintainer and layer editors.
    CODEOWNERS and `editors.csv` themselves are maintainer-owned.
  - `editors.csv` feeds Zenodo *contributors* (not creators), `CITATION.cff`,
    and the explorer's "editors of this variety".
- **Branch protection on `master`** applies to **everyone including Tiago**:
  changes go through PRs and **CI must pass**; no approving review is required
  (decided 2026-11-02). Authors may merge their own PRs once CI is green.
  GitHub cannot record a self-approval, so this is implemented as "PR + green
  CI", not as a required review.
  - CODEOWNERS still **auto-requests** the relevant language editors, so they
    see every change to their varieties and families.
  - Expected practice, not enforced: a change to a variety with a language
    editor waits for that editor; cross-cutting files (`src/`, the concept
    catalog, schema) go through the maintainer or a layer editor.
  - **Procedures, not automation:**
    - If a language editor doesn't respond for **30 days**, the maintainer may
      override with a reason stated in the PR.
    - The `bulk/mechanical` label covers pipeline-wide non-curatorial changes,
      which the maintainer may merge without waiting for language editors. Only the maintainer applies the
      label. Changes to a language's source choice or readings always need its
      language editor.
- **AI:** AI-assisted work is welcome; the PR author owns every changed record.
  - Disclosure is a **required PR-template field** (`none` /
    `search & suggestion` / `extraction or transformation` /
    `drafting & review`, plus the tool), checked by CI. There are no commit
    trailers and no per-variety data field. The initial-import PR fills in
    the field too.
  - Each release gets an AI-assistance summary harvested from the PR fields.
    The datasheet carries a baseline methods statement: the `A` baseline was
    built by the maintainer with extensive AI assistance.
  - Agents never approve. A model review never counts as expert review.
  - A bot account running scheduled agents is **post-launch**; non-AI
    scheduled CI checks run from day one.

## 6. Licensing for `A`

RC4 accepted records by declared licence (226 sources):

| Licence | Records | Sources |
| --- | ---: | ---: |
| CC BY 4.0 | 1,844,986 | 193 |
| missing declaration | 164,311 | 3 |
| CC BY-NC 4.0 | 72,005 | 13 |
| CC BY-NC-SA 4.0 | 34,822 | 8 |
| CC BY-SA 4.0 | 1,549 | 5 |
| CC BY-NC-ND 4.0 | 1,473 | 1 |
| GPL-3.0 | 1,108 | 2 |
| Public domain mark | 9 | 1 |

- Per-row `License` and `terms_status` columns; a per-source table in the datasheet.
- **Legacy Wiktionary (141,050 records):** declared CC BY-SA 4.0 with per-entry
  URLs. The declaration **states that the dump date was not recorded**; no
  snapshot date is invented.
- **`luangthongkumkaren`:** the ND in the CLDF metadata is an error; the
  authors approved Tiago's correction (fixed in their next release). Recorded
  as CC BY-NC 4.0 in a source-terms override that cites the approval.
- **`kogansemitic`, `williamsonbenuecongo` (23,261 records):** kept on both
  sites, in `-full` and in the snapshot, flagged `missing_declaration`. This
  is an accepted risk, decided knowingly. The letters to the rights holders
  go out **before the Zenodo mint**, so the record can state the date of the
  request.
- Re-audit the terms of the 20 largest sources before `A`; the rest stay
  `declared_not_reaudited`, as the datasheet states.
- **Arca's own work** is **CC BY 4.0**: IDs, variety and concept catalogs,
  concept/WordNet links, scores, code-generated products.
  **Adaptations of SA or NC-SA source records** (corrections, normalizations)
  **inherit the source's terms**, as the existing reviewed-sources release
  already states. WordNet sidecars keep their OEWN, CILI and Princeton notices.
  Code: MIT.

## 7. Launch checklist

| # | Step | Owner |
| --- | --- | --- |
| 1 | Freeze curation; record it in NEXT | Claude (done) |
| 2 | Make `update` fail on errors; pin merkmal/dependencies; freeze Glottolog; deterministic build date | Claude |
| 3 | Licence fixes (Wiktionary declaration, luangthongkumkaren override, SA/NC adaptation rule); top-20 terms re-audit | Claude (Tiago supplies the approval reference) |
| 4 | Snapshot exporter (dependency closure + read-outside test); full re-derivation proof; schema-A release builder with three tiers and CLDF validation; new Zenodo metadata | Claude |
| 5 | Stage trees: clean main repo with `docs/evidence/` and rewritten references; `site` and `live` with pull-based deploys; `.github` (profile, CONTRIBUTING, AI policy, CoC, templates); `editors.csv` + CODEOWNERS generator; PR template with CI check | Claude |
| 6 | Review the staged trees | Tiago |
| 7 | Create all repos **private**; push single initial commits (Tiago's `gh` login, no trailers); branch protection (PR + green CI); deploy secrets | Claude |
| 8 | Real acceptance test: a contributor PR from a second account (download snapshot → edit a variety → PR → CI rebuild) | Claude + Tiago (second account) |
| 9 | Cut `A-<date>`; verify assets, tiers and the re-derivation | Claude |
| 10 | Deploy both sites under their default Pages URLs; verify; make public repos public | Claude |
| 11 | DNS cutover for `arcaverborum.org` and `live.arcaverborum.org`; switch off the old repo's Pages | Tiago |
| 12 | Prepend the deprecation notice to the old README; archive `tresoldi/arcaverborum` | Claude |
| 13 | Private checksummed archive of `raw/curation/` on the NAS | Tiago (laptop) |
| 14 | Invite and confirm authors as org members; assign scopes in `editors.csv` (CODEOWNERS review requests) | Tiago + Claude |
| 15 | Letters to the Kogan Semitic and Williamson Benue-Congo rights holders | Tiago |
| 16 | Authors' first look → fixes as PRs → release `A-<later date>` → mint Zenodo; pointer on the old Zenodo record | all |
| 17 | Paper draft in `arcaverborum/paper` | Tiago + Claude |

Excluded from launch: bot agents, site-data size work, the full licence
re-audit, issue migration, a policy bot for governance procedures.

## 8. Paper (MDPI *Data*, Data Descriptor)

- **Authors:** Tiago Tresoldi first and corresponding, then all invited
  editors **alphabetically**. Currently: Sandra Auderset, Marwan Kilani,
  Bonnie McLean; the list is still open. Reviewing their own data before
  submission is sufficient contribution; roles are given as CRediT. Every
  author approves the manuscript and accepts accountability.
- **Scope:** the lexical dataset; the variety and concept catalogs (frozen IDs,
  Glottolog/Concepticon/WordNet mappings); quality scoring and provenance; the
  release, replicability and governance model; the AI policy.
  **Colexification is only briefly mentioned** as a derived product; methods
  and the CLICS comparison go into a separate later paper.
- **Outline:**
  1. Introduction: student-access origin; Lexibank as the foundation;
  2. Design principles (§1);
  3. Data sources and selection;
  4. Data model and identifiers;
  5. Phonological representation and provenance;
  6. Concepts, WordNet and derived products;
  7. Infrastructure, releases and replicability;
  8. Governance and AI policy;
  9. Validation: re-derivation evidence, CI checks, coverage by macroarea with
     the Americas and South America highlighted, the source-selection audit;
  10. Limitations: AI-assisted baseline, unaudited terms, GLED/ASJP limits,
      written-only records, no stratified linguistic validation;
  11. Licensing and availability.
- No coverage must-haves before submission. **Evidence gates** for the
  paper's claims:
  - the Tier-1 re-derivation proof for the cited release;
  - a resolved availability statement;
  - quality scores described as heuristics;
  - review coverage reported as it is.

## 9. Open inputs from Tiago

- **Blocking step 3:** a reference for the luangthongkumkaren licence correction
  (e-mail date or issue link).
- **Blocking step 8:** a second GitHub account (or an invited author) for the
  real PR test.
- **Blocking step 11:** DNS for both domains.
- **Blocking step 14:** GitHub logins, ORCIDs and editor scopes
  (varieties/families) for each author.
- **Blocking step 16:** letters to the two rights holders (step 15).
- **Non-blocking:** the `raw/curation/` NAS archive; the final author list.
