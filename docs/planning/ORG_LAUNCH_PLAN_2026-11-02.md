# Arca Verborum organization launch plan — 2026-11-02

> Under revision after the [Codex adversarial review](../reviews/2026-11-02-codex-org-launch.md)
> and its [assessment](../reviews/2026-11-02-org-launch-assessment.md).

Decisions agreed with Tiago on 2026-11-02 for moving Arca Verborum into the
`arcaverborum` GitHub organization, cutting the first schema-`A` release and
preparing the MDPI *Data* paper. Order of work: **working system in the org →
show it to the invited authors → Zenodo → paper.** This is an immediate task.

**Curation is frozen** until release `A` is published: no data batches (the NXT
queue, NXT-05, new expansion) start before then. The `A` baseline is data commit
`2ca6d8de2` (RC4 state) plus the two licence-metadata fixes in §6.

## 1. What the project is (positioning for org, README and paper)

- A **curated selection and harmonization layer built on top of** Lexibank,
  GLED, Wiktionary and original sources. It is not an alternative to them.
  Lexibank's contribution is acknowledged as **foundational**: sources hosted
  under `github.com/lexibank/` supply 1,361,851 of 2,120,263 accepted records
  (64%, RC4 source terms); the rest come from GLED, Wiktionary, other CLDF
  datasets and original sources.
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
| `arcaverborum/arcaverborum` | public | pipeline code, tests, curated data (`varieties/`, `src/arcaverborum/data/` incl. the concept catalog), current specs |
| `arcaverborum/site` | public | static explorer code; deploys the **latest release** to `arcaverborum.org` |
| `arcaverborum/live` | public | deploy-only; CI from the main repo's `master` → `live.arcaverborum.org` |
| `arcaverborum/paper` | **private** (Free plan) | MDPI *Data* manuscript |
| `arcaverborum/.github` | public | org profile, CONTRIBUTING, AI policy, code of conduct, PR/issue templates |

- New repos start **without history**: each gets a single initial commit of the
  current state, authored as Tiago, with **no AI trailers or markers of any
  kind** (this applies to all commits until Tiago decides otherwise).
- The concept catalog stays in the main repo; it gets split out only if someone
  outside wants to reuse it.
- **Not carried over:** dated batch reports, review CSVs and execution JSONs in
  `docs/`, root `*.log` files, `memory/`, `raw/curation/`. They remain in
  `tresoldi/arcaverborum`, which gets a pointer README and is **archived**.
- Carried over: README, ONBOARDING, CONTEXT, `BESTOF_SPECIFICATION`,
  `CONCEPTS_SPECIFICATION`, `CURATION_WORKFLOW_SPECIFICATION`, `CONCEPT_ENTRIES`,
  `WORDNET`, `COLEXIFICATION`, a rewritten STATUS, and the launch plan as
  `docs/LAUNCH.md` (deleted once launch is done). Specs are cleaned of links to
  material that doesn't move.

## 3. Replicability promise (two tiers)

- **Tier 1, guaranteed and checked by CI:** git plus the **accepted-inputs
  snapshot** rebuild the release and the site data. The snapshot holds the
  intake rows of every accepted `(glottocode, source)` pair. Measured
  2026-11-02: 8,380 pairs; Lexibank-format slice 2,195,921 rows / 79 MB gz,
  Wiktionary slice 150,765 rows / 5 MB gz; curated `varieties/` 7.6 MB in git.
  Still to be added: filtered `parameters_raw` rows and the Wiktionary
  pronunciation table, if the build reads it. Expected total < 150 MB. The
  snapshot is published as a release asset and on Zenodo.
- **Tier 2, documented, best-effort:** re-derivation from the original sources.
  Each construction names its source and extraction script; non-redistributable
  inputs are named but not shipped.
- PR CI downloads the snapshot and rebuilds every touched variety.

## 4. Releases

- Identifier `A-YYYY-MM-DD` (same-day re-release `A-YYYY-MM-DD.2`). The same
  string is used for the git tag, the Zenodo version and the archive names.
- The letter starts at **A** in the org. It bumps only on a **breaking** change
  to published tables: a column removed or renamed, a column's meaning changed,
  an ID scheme changed, or a file restructured. Added columns, records or
  corrections keep the letter. The paper describes schema A.
- No public release candidates: candidates are CI artifacts or untagged drafts.
- Releases are cut when decided, not on a calendar.
- Assets per release:
  - `arcaverborum-A-…-full.tar.gz`: every accepted record, including sources
    without a declaration (`terms_status = missing_declaration`);
  - `arcaverborum-A-…-open.tar.gz`: declared redistributable licences only;
  - `arcaverborum-A-…-by.tar.gz`: CC BY and public domain only;
  - the accepted-inputs snapshot, manifest, checksums and datasheet.
- **Site:** `arcaverborum.org` serves the latest release by default;
  `live.arcaverborum.org` serves `master` with a banner showing the data
  revision and the latest release. Each site links to the other. Older
  releases are archived on Zenodo, not hosted. Two Pages sites are needed
  because the site data is 652 MB and Pages allows 1 GB per site. Shrinking
  the data (single compressed colexification DB, client-side concept rows) is
  a post-launch optimization.
- **Zenodo:** a new concept DOI, minted **after the authors' first look**, not
  at launch. The old record `10.5281/zenodo.17294927` gets a pointer.

## 5. Governance and AI policy

- **Roles:**
  - *Maintainer*: Tiago. Pipeline, schema, releases and policy.
  - *Editor*: anyone with write access; may approve any PR.
  - *Language editor*: an editor with a scope over varieties and/or families
    (one or more), or a layer (`concepts`, `colexification`, `pipeline`).
- `editors.csv` (`github_login, name, orcid, scope`) is committed data. A
  script generates `.github/CODEOWNERS` from it; it feeds `CITATION.cff` and
  Zenodo contributors per release and the explorer's "editors of this
  variety".
- Branch protection on `master`, for **everyone including Tiago**: PRs only,
  CI green, code-owner review required.
  - A variety with a language editor needs their approval; otherwise any
    editor's approval is enough.
  - Cross-cutting files (`src/`, the concept catalog, schema) need the
    maintainer or a layer editor.
  - If a language editor doesn't respond for **30 days**, the maintainer may
    override with a stated reason.
  - A `bulk/mechanical` label covers pipeline-wide non-curatorial changes,
    which the maintainer may approve alone. Changes to a language's source
    choice or readings always need its language editor.
- **AI:** AI-assisted work is welcome; the PR author owns every changed record.
  - Disclosure is a **required PR-template field only** (`none` /
    `search & suggestion` / `extraction or transformation` /
    `drafting & review`, plus the tool). No commit trailers and no per-variety
    data field for now.
  - Agents never approve.
  - A model review never counts as expert review.
  - The datasheet and paper state that the `A` baseline was built by the
    maintainer with extensive AI assistance.
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
- **Legacy Wiktionary (141,050 records):** write the CC BY-SA 4.0 declaration
  with per-entry URLs before `A`.
- **`luangthongkumkaren`:** the ND in the CLDF metadata is an error; the
  authors approved Tiago's correction (fixed in their next release). Record it
  as CC BY-NC 4.0 in a source-terms override that cites the approval.
- **`kogansemitic`, `williamsonbenuecongo` (23,261 records):** kept on both
  sites and in `-full`, flagged `missing_declaration`. The Zenodo record states
  mixed per-row terms and good-faith inclusion pending clarification. Write to
  the rights holders now.
- Re-audit the terms of the 20 largest sources before `A`; the rest stay
  `declared_not_reaudited`, as the datasheet states.
- **Arca's own layer** (catalogs, IDs, WordNet links, colexifications, curated
  corrections): **CC BY 4.0**. Code: MIT.

## 7. Launch checklist

| # | Step | Owner |
| --- | --- | --- |
| 1 | Freeze curation; record it in NEXT | Claude |
| 2 | Licence fixes (Wiktionary declaration, luangthongkumkaren override); top-20 terms re-audit | Claude (Tiago supplies the approval reference) |
| 3 | Snapshot exporter and three-asset release builder; tier-1 rebuild check | Claude |
| 4 | Stage the clean main-repo tree; `site` and `live` trees and deploy workflows; `.github` repo (profile, CONTRIBUTING, AI policy, CoC, templates); `editors.csv` + CODEOWNERS generator; PR template | Claude |
| 5 | End-to-end contributor test from a clean clone on devbox (download snapshot → edit a variety → PR → CI rebuild) | Claude |
| 6 | Review the staged trees | Tiago |
| 7 | Create the repos in the org and push single initial commits (Tiago's `gh` login, no trailers); branch protection; Pages | Claude, after step 6 |
| 8 | DNS for `arcaverborum.org` and `live.arcaverborum.org`; switch off the old repo's Pages | Tiago |
| 9 | Cut `A-<date>` from CI; verify both sites and the assets | Claude |
| 10 | Pointer README on `tresoldi/arcaverborum`, then archive it; pointer on the old Zenodo record | Claude / Tiago |
| 11 | Invite and confirm authors; assign editor scopes in `editors.csv` | Tiago |
| 12 | Authors' first look → fixes as PRs → mint Zenodo | all |
| 13 | Paper draft in `arcaverborum/paper` | Tiago + Claude |

Excluded from launch: bot agents, site-data size work, full licence re-audit,
issue migration.

## 8. Paper (MDPI *Data*, Data Descriptor)

- **Authors:** Tiago Tresoldi first and corresponding, then all invited
  editors **alphabetically**. Currently: Sandra Auderset, Marwan Kilani,
  Bonnie McLean; the list is still open. Reviewing their own data before
  submission is sufficient contribution; roles are given as CRediT.
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
  9. Validation: rebuild evidence, CI checks, coverage by macroarea with the
     Americas and South America highlighted, the source-selection audit;
  10. Limitations: AI-assisted baseline, unaudited terms, GLED/ASJP limits,
      written-only records;
  11. Licensing and availability.
- No hard content must-haves before submission.

## 9. Open inputs from Tiago

- **Blocking step 11:** GitHub logins, ORCIDs and editor scopes
  (varieties/families) for each author.
- **Blocking step 2:** a reference for the luangthongkumkaren licence correction
  (e-mail date or issue link).
- **Blocking step 9:** DNS for both domains.
- **Non-blocking:** outreach to the Kogan Semitic and Williamson Benue-Congo
  rights holders; final author list.
