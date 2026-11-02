# Assessment of the Codex review of the organization launch plan (2026-11-02)

Source: [Codex review](2026-11-02-codex-org-launch.md) of
[the launch plan](../planning/ORG_LAUNCH_PLAN_2026-11-02.md). Each finding was
re-checked against the repository. Verdicts:

- **accept**: real; the plan changes;
- **partial**: real core, overstated or mis-scoped;
- **reject**: contradicts an informed decision or is out of scope.

Codex's severity labels are not adopted as-is.

## Verified independently

- `build.py update` returns 0 even when varieties fail. `update_many` counts
  failures (`src/arcaverborum/variety.py:972-984`) and `cmd_update` discards
  the result (`build.py:183-193`).
- The build also reads supplement pairs from `custom/`: **215 extra
  `(glottocode, source)` pairs** beyond the 8,380 config picks. The 85 MB
  snapshot measurement in the plan excluded them, and also excluded languages,
  parameters, metadata, bibliography and Glottolog.
- CI installs merkmal from an unpinned default branch
  (`.github/workflows/ci.yml:25`). Glottolog falls back to a download from
  `master` (`src/arcaverborum/glottolog.py:11`). The site manifest embeds
  `date.today()` (`scripts/build_research_web.py:300`).
- `build.py release` is the historical Core builder. The RC4 "byte
  reproduction" re-packages existing aggregate tables; it does not re-derive
  them from intake.
- **901 tracked files under `varieties/` reference 92 distinct `docs/` paths.**
  Most of them are dated evidence that the plan proposed not to carry over.
- Existing release policy keeps Wiktionary-derived records **and Arca's
  adaptations of them** under CC BY-SA 4.0 (`scripts/build_reviewed_release.py:133`).
- **The plan's "87% from Lexibank" figure was wrong.** It was derived from the
  CC BY record count. Sources hosted under `github.com/lexibank/` supply
  1,361,851 of 2,120,263 accepted records (**64%**); the rest come from GLED,
  Wiktionary, `tresoldi/*` CLDF datasets and original sources. Codex flagged
  the claim as unclassified but did not detect the error.
- Legacy Wiktionary has no recorded dump date
  (`scripts/build_research_web.py:80`).

## Findings

| # | Codex finding | Verdict | Plan change |
| --- | --- | --- | --- |
| 1 | Undeclared sources published | **reject** (informed decision) | Tiago kept them knowingly in `-full` and on the sites. Recorded as an accepted risk. Rights-holder letters move before the Zenodo mint, so the record can say "requested on <date>". |
| 2, 3, 7 | Snapshot incomplete | **accept** | Snapshot membership is the **builder's dependency closure**: config picks, supplement keys, source-member selectors, GLED fallback slices, language/parameter/metadata/bib rows, frozen Glottolog, recording metadata. A test fails the build on any read outside the snapshot. Tier 1 explicitly covers lexical outputs and site data; colexification/WordNet bundles are tracked derived inputs, regenerable from documented sources (tier 2). |
| 4 | Silent build failures | **accept**, fix first | `update` exits non-zero on any failure; aggregate checks exact accepted membership. |
| 5 | Packaging ≠ derivation | **accept** | The plan overstated "mostly built already". Tier-1 evidence is a full re-derivation from the snapshot in an empty workspace, separate from archive byte reproduction. |
| 6 | Unpinned runtime | **accept** | Pin merkmal by commit, lock dependencies, freeze Glottolog inside the snapshot, fail closed if offline inputs are missing, and take the build date from the release identifier rather than the clock. |
| 8 | CC BY vs SA adaptations | **accept** | CC BY 4.0 covers Arca's *independent* work: IDs, catalogs, concept/WordNet links, scores, code-derived products. **Adaptations of SA/NC-SA records inherit those terms**, matching existing policy. |
| 9 | Tier payloads leak | **partial** | A builder requirement, not a policy change. Each tier is filtered at file level, including custom files, evidence and recordings; a test asserts no excluded source appears in `-by`. The snapshot follows `-full` terms and says so. Princeton WordNet's licence is permissive; it needs its notice, nothing more. |
| 10 | "open" implies commercial reuse | **accept** | The tier name and allowlist need to change (decision below). |
| 11 | Wiktionary provenance | **accept** (minor) | The declaration states the licence and per-entry URLs, and **says plainly that the legacy dump date is unknown**. It does not invent a snapshot date. |
| 12 | Self-approval deadlock | **accept** | Real GitHub mechanics: an author cannot approve their own PR. Decision needed (below). |
| 13 | CODEOWNERS limits | **partial** | Path rules use `av_id` prefixes (`/varieties/tup-*/`), since the family code is the ID prefix. Sub-family scopes are listed explicitly. Shared registries (`varieties.csv`, `concepts.csv`) belong to the maintainer and layer editors. The 30-day override and the `bulk/mechanical` label are **documented procedures**, not automation; only the maintainer applies the label. No policy bot at launch. |
| 14 | Access roles | **partial** | Invited authors are made org **members** in an `editors` team. CODEOWNERS lists individual logins, generated from `editors.csv`. Required code-owner review on public Free repos is supported; the private `paper` repo needs no protection. |
| 15 | Provenance links severed | **accept**, important | Decision needed (below). |
| 16 | Archiving wording | **accept** | The plan wrongly said `raw/curation/` "remains" in the old repo; it was never tracked. The old README gets a prepended notice rather than being replaced. The old repo is archived only after launch. |
| 17 | Release/Zenodo tooling is old | **accept** | A work item in step 3: one schema-A release path, new Zenodo metadata (new concept DOI, mixed terms), CLDF export validated. |
| 18 | Versioning edge cases | **partial** | Add: tags and assets are immutable; consumers must read tables by header; every release has a changelog; supersession is recorded in the release notes. Codex's other cases (vocabularies, null conventions) fall under "meaning changed", which already bumps the letter. |
| 19 | Cross-repo deploy | **accept** (detail) | `site` and `live` **pull** verified artifacts from the main repo's releases/CI on dispatch, using a fine-grained token stored as a secret, so the main repo needs no write access to them. Deploy only after a green run. Measure the assembled payload. |
| 20 | Checklist order | **accept** | Reordered: create repos **private** → push → real PR test with a second account → release → stage sites → make public → DNS cutover → archive old repo. |
| 21 | Paper evidence gate | **partial** | Tiago's "no must-haves" concerns *coverage content* and stands. **Evidential** gates for the paper's claims are adopted: tier-1 rebuild proof, availability statement, scores described as heuristics, review coverage reported honestly. A stratified linguistic validation study is out of scope; limitations state it. |
| 22 | Authorship vs editors | **reject** (decided) | Authorship was decided by Tiago. Procedurally every author approves the manuscript and accepts accountability, per MDPI policy. `editors.csv` feeds Zenodo *contributors*, not *creators*. |
| 23 | AI disclosure durability | **partial** | No commit trailers, as decided. Add a baseline methods statement in the datasheet, plus a release-level AI-assistance summary harvested from PR fields. The initial-import PR carries the field. |
| 24 | Lexibank attribution | **accept**, error | The figure is corrected to 64% Lexibank-hosted, with the classification query published. The positioning wording is unchanged. |

## Decisions (all four recommendations accepted by Tiago, 2026-11-02)

1. **Self-approval deadlock (12).** (a) Until a second editor exists,
   branch protection requires CI and PRs but no approving review; required
   code-owner review turns on when the first author joins. (b) Admin bypass
   always on, logged.
   Recommendation: **(a)**. It keeps "PRs for everyone" without a fake review.
   Once editors exist, Tiago's PRs need any one editor's approval.
2. **Tier naming (10).** Recommendation: `-full` / `-redistributable` /
   `-by`, with explicit allowlists. NC is listed as a restriction on
   `-redistributable` in the datasheet.
3. **Evidence carried into the fresh repo (15).** (a) Carry the 92
   referenced evidence files into `docs/evidence/`. (b) Rewrite references to
   commit-pinned URLs in the archived `tresoldi/arcaverborum`, plus a Software
   Heritage snapshot.
   Recommendation: **(a)**. Accepted decisions should stay interpretable from
   the repo that holds them; the files are small. Remaining history stays in
   the archived repo.
4. **`raw/curation/` (11 GB, untracked, partly copyrighted).** Recommendation:
   keep a checksummed private archive on the NAS, done by Tiago from the
   laptop. It is not published.
