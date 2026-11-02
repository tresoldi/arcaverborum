# Codex adversarial review of the organization launch plan (2026-11-02)

Reviewed: `docs/planning/ORG_LAUNCH_PLAN_2026-11-02.md` at commit `87ff015c9`. Read-only sandbox, no network, no builds. Assessment: [2026-11-02-org-launch-assessment.md](2026-11-02-org-launch-assessment.md).

The plan is not ready to execute. Its release permissions, rebuild guarantee, review rules, and publication sequence contain unresolved blockers.

This is a read-only review. Repository behavior below is **verified** from the cited files. Legal consequences and GitHub/journal policy requirements are identified as **risks or external mechanics**, not as facts established by repository inspection. No network requests or full builds were run.

1. **[Blocker] The plan publishes material whose redistribution permission remains unresolved.**

   **Evidence — verified:** The plan explicitly retains 23,261 records without licence declarations on both sites and in `-full` (`docs/planning/ORG_LAUNCH_PLAN_2026-11-02.md:154`). The accepted status currently keeps the full bulk release private because of missing declarations and other unresolved terms (`docs/STATUS.md:40`; `docs/releases/README.md:18`). The RC4 datasheet says missing/restrictive terms require review before separate redistribution (`docs/releases/all-accepted-2026-11-02-rc4/RELEASE_README.txt:5`).

   **Failure scenario — legal risk:** “Good-faith inclusion pending clarification” and a `missing_declaration` flag do not themselves supply permission. Launch would turn a documented withholding decision into public redistribution without an intervening clearance gate. Existing website exposure does not establish permission for a new archive.

   **Remedy:** Make permission resolution or exclusion blocking for every public distribution surface, including the snapshot and sites. Keep unresolved material in a restricted internal baseline.

2. **[Blocker] The accepted-inputs snapshot is not a complete build-input specification.**

   **Evidence — verified:** The proposed snapshot primarily contains forms for accepted pairs, with parameters and pronunciation evidence still undecided (plan:60). Actual rebuilding also reads:

   - intake language tables and Glottolog when constructing the catalog (`src/arcaverborum/variety.py:849`);
   - parameter mappings (`src/arcaverborum/variety.py:857`);
   - intake metadata and bibliography for aggregation (`src/arcaverborum/aggregate.py:81`);
   - source language labels, parameter names and raw Glottolog fields for the site (`scripts/build_research_web.py:117`);
   - generated recordings, including recording-only constructions (`scripts/build_research_web.py:273`).

   **Failure scenario — inference:** A forms-only snapshot can produce missing attribution, altered names/geography, absent source senses, or lost recording-only entries while still producing lexical tables.

   **Remedy:** Specify a versioned snapshot schema covering forms, languages, parameters, metadata, bibliography, Glottolog, recording inputs and all required selectors. Prove its sufficiency in an empty workspace with source-network access disabled.

3. **[Major] “Accepted pairs” is underspecified for supplements, member unions, fallback data and future contributions.**

   **Evidence — verified:** Builders use `source_glottocodes`, exact source-member selectors, and supplementary input keys (`src/arcaverborum/variety.py:630`, `:878`). They also fingerprint GLED fallback slices (`:881`) and can switch to fallback data when the selected source is empty (`:677`).

   **Failure scenario — inference:** An exporter based only on each variety’s canonical Glottocode and configured primary source omits necessary inputs. A contributor changing source choice can also request data outside the frozen snapshot; the proposed PR workflow does not define how those inputs enter review.

   **Remedy:** Derive snapshot membership from the builder’s complete dependency closure. Record the accepted variety list separately, fail on unexpected fallback, and define reviewed snapshot extensions for new sources or varieties.

4. **[Blocker] A green update command can conceal failed variety builds.**

   **Evidence — verified:** `update_many` catches build exceptions and returns a failure count (`src/arcaverborum/variety.py:972`). `cmd_update` ignores that result and returns zero (`build.py:183`). Aggregation includes whatever generated files exist (`src/arcaverborum/aggregate.py:93`).

   **Failure scenario:** CI runs `python build.py update …`, receives success despite failures, and then aggregates incomplete output—or stale output in a reused workspace.

   **Remedy:** Return a nonzero status for any failed build. Require exact accepted-membership and per-variety output checks before aggregation or publication.

5. **[Major] RC4 byte reproduction does not demonstrate the promised reconstruction.**

   **Evidence — verified:** RC4’s reproduction receipt verifies identical archive members (`docs/releases/all-accepted-2026-11-02-rc4/reproduction.json:4`). Its builder packages existing aggregate tables and the existing catalog (`scripts/build_collection_release.py:99`); it does not reconstruct them from intake.

   **Failure scenario:** Deterministic packaging is reported in the paper as independent reconstruction of the dataset. The two tests establish different things.

   **Remedy:** Keep separate evidence for archive reproducibility and end-to-end derivation. The latter must regenerate every accepted variety, aggregate, export and site product before comparing outputs.

6. **[Major] Runtime and output nondeterminism remain outside the guarantee.**

   **Evidence — verified:** Current CI installs merkmal from an unpinned GitHub default branch (`.github/workflows/ci.yml:24`). Core dependencies have lower bounds rather than exact versions (`pyproject.toml:16`). Missing Glottolog cache triggers a download from `master` (`src/arcaverborum/glottolog.py:11`, `:39`). Site manifests use today’s date (`scripts/build_research_web.py:300`).

   **Failure scenario:** The same snapshot produces different classifications, phonological results or manifest bytes later—or cannot build offline.

   **Remedy:** Pin the compiled dependency revision and runtime environment, freeze Glottolog, and define reproducibility precisely: identical bytes or specified semantic equivalence with explicitly excluded fields. Make missing frozen inputs fail closed.

7. **[Major] The promise does not distinguish lexical reconstruction from evidence and derived-product reconstruction.**

   **Evidence — verified:** The plan excludes `raw/curation/` (plan:49). Scripts use it for pronunciation caches, pinned source documents and profile verification—for example `scripts/verify_original_profiles.py:42` and `scripts/ancient_pronunciations.py:53`. The ordinary update input columns do not include a separate pronunciation ledger (`src/arcaverborum/variety.py:46`). The web entry point also invokes concept-row and colexification builders (`scripts/build_research_web.py:335`).

   **Failure scenario — inference:** Lexical outputs reconstruct, but their pronunciation evidence cannot be independently checked, or the published network/community products cannot be regenerated under the advertised command.

   **Remedy:** Publish a dependency matrix for lexical outputs, evidence audits, concept rows, networks and communities. Explicitly distinguish tracked WordNet/Concepticon-derived bundles from the original resources needed to regenerate those bundles. Decide which products Tier 1 guarantees.

8. **[Blocker] The blanket CC BY claim for Arca corrections conflicts with the existing adaptation policy.**

   **Evidence — verified:** The plan assigns curated corrections and derived products to Arca’s CC BY 4.0 layer (plan:160). Existing release documentation explicitly keeps Wiktionary-derived records **and Arca adaptations to those records** under CC BY-SA 4.0 (`scripts/build_reviewed_release.py:133`; `docs/releases/README.md:14`).

   **Failure scenario — legal risk:** A corrected or normalized SA-derived record is offered as reusable under CC BY alone. NC-SA-derived adaptations raise a corresponding problem. Conversely, treating a mixed collection as if every independent component automatically acquires SA would also overstate the restriction.

   **Remedy:** Separate independently authored annotations from adaptations and preserved source material. Document effective terms at the appropriate component level, including retained notices and modification statements. Do not promise unrestricted CC BY reuse of all corrections.

9. **[Major] The tiers filter lexical rows but do not define the rights of the whole payload.**

   **Evidence — verified:** `-open` and `-by` are described only by licence categories (plan:84). The existing full packager recursively includes all registry data and accepted custom files (`scripts/build_collection_release.py:103`, `:115`). WordNet sidecars include Princeton material under its own licence (`src/arcaverborum/data/wordnet/sources.json:4`).

   **Failure scenario — inference:** A supposedly CC BY/public-domain archive still contains excluded-source readings in preserved custom data, restrictive evidence quotations, incompatible derived products, or sidecars requiring additional notices. The shared accepted-inputs asset can bypass every output-tier filter.

   **Remedy:** Define and audit a complete file-level payload for each tier. Apply policy to recipes, retained alternatives, source evidence, recordings and derived products as well as forms. Tier the snapshot or state clearly why its permissions differ.

10. **[Major] “Open” is ambiguous about NC; GPL and ND obligations are unresolved.**

    **Evidence — verified:** The plan lists NC, NC-SA, ND and GPL sources (plan:141), but defines `-open` as “declared redistributable licences” (plan:86), without an allowlist or compliance rules.

    **Failure scenario — legal risk:** Users interpret `-open` as permitting unrestricted commercial reuse. A declaration is accepted without checking whether Arca’s transformations are permitted under ND. GPL-covered material is distributed without determining applicable licence, notice and corresponding-source obligations.

    **Remedy:** Publish an explicit allowlist and rationale. Rename an NC-inclusive tier to avoid implying unrestricted openness. Resolve ND transformation permission and GPL compliance individually; a per-row licence label is insufficient.

11. **[Major] The legacy Wiktionary fix can overstate what is known about the snapshot.**

    **Evidence — verified:** The plan proposes assigning CC BY-SA 4.0 with entry URLs (plan:149). The web fallback currently admits that the exact dump date and original citation metadata were not recorded (`scripts/build_research_web.py:80`).

    **Failure scenario — inference/legal risk:** Current entry URLs are treated as provenance for historical extracted readings, or a present-day licence assertion is substituted for evidence about the actual source snapshot and attribution requirements.

    **Remedy:** Recover the dump/version and applicable notices where possible. Preserve contributor/history attribution routes, extraction provenance and modification statements. If historical metadata cannot be recovered, disclose the specific uncertainty; do not fabricate snapshot precision.

12. **[Blocker] The review policy can deadlock the launch and sole-maintainer work.**

    **Evidence — verified:** Required owner review applies to Tiago (plan:110); maintainer approval is prescribed for bulk work (plan:118). Branch protection is enabled at step 7, while other editors are invited at step 11 (plan:173).

    **Failure scenario — GitHub mechanics:** A PR author cannot supply their own approving review. With only Tiago available, required approvals cannot be satisfied. The same problem recurs when a language editor changes their own data.

    **Remedy:** Establish accepted reviewers before enforcing protection. Define deputy reviewers, author-recusal behavior and a narrowly controlled bootstrap exception. Test these cases with distinct accounts.

13. **[Major] CODEOWNERS cannot express the complete governance policy.**

    **Evidence — verified:** The plan promises variety/family scopes, language-editor approval, fallback approval, layer approval, a timed override and a label-based exception (plan:103–120).

    **Failure scenario — GitHub mechanics:** CODEOWNERS is a path-matching mechanism. Later matching rules take precedence; multiple owners on a matching rule generally provide alternatives rather than requiring all of them. It cannot independently express a 30-day timer, a trusted bulk-change classification, semantic reading changes, or ownership of particular CSV rows. Shared registries can change a variety without touching its directory.

    **Remedy:** Define precedence and expand family scopes to actual paths. Add a policy check for semantic/shared-file changes, protect ownership configuration itself, and test overlapping scopes, author-owned changes and multi-family PRs. Specify who may apply `bulk/mechanical`.

14. **[Major] Access roles, Free-plan assumptions and override mechanics are incomplete.**

    **Evidence — verified:** “Editor” means anyone with write access (plan:103), but the plan does not distinguish organization members, outside collaborators, team membership or repository-specific access. Only the paper repository’s Free-plan status is explicit (plan:41).

    **Failure scenario — external mechanics to verify:** A generated owner is ineligible because access was not granted; a team scope excludes outside collaborators; or private-paper protections assumed to exist are unavailable on the chosen plan. A 30-day override either violates “everyone” protection or requires an undocumented administrator bypass. Administrators can also alter protection settings, so “everyone” needs a stated trust boundary.

    **Remedy:** Specify access and enforcement per repository. Verify the exact public/private Free-plan capabilities before launch. Define an auditable bypass procedure, its clock, notification requirements and limits.

15. **[Major] Fresh history and omitted review artifacts sever active provenance links.**

    **Evidence — verified:** The plan discards history and dated review evidence (plan:44). Active recipes cite excluded reports: `varieties/afa-hdi/recipe.yaml:5` and `:17`; reading evidence cites a dated review CSV (`varieties/afa-hdi/custom/reading_evidence.csv:2`). Cleaning links in specifications alone does not address these.

    **Failure scenario:** A new clone contains a decision and hash but lacks its rationale, prior reading, reviewer context or referenced artifact. Local Git-based preservation checks cannot resolve old objects. The new initial author also does not preserve original contributor credit or necessarily satisfy attribution obligations.

    **Remedy:** Retain history where practicable. Otherwise publish an immutable legacy Git bundle and evidence archive, a path/commit crosswalk, and contributor attribution. Rewrite active evidence references to durable, versioned targets; retain all evidence necessary to interpret accepted decisions.

16. **[Major] Archiving the old repository preserves only part of the promised record.**

    **Evidence — verified:** Raw and intake products are gitignored (`ONBOARDING.md:3`). The plan says excluded `raw/curation/` material “remain[s]” in the old repository (plan:49). It also excludes issue migration and plans a pointer README followed by archiving (plan:176, `:181`).

    **Failure scenario:** Readers assume archiving GitHub preserves private caches that were never committed. Replacing the README removes historical documentation, and archiving closes the old collaboration channel before issue triage, rights-holder follow-up and redirects are settled.

    **Remedy:** Inventory tracked versus local-only evidence. Archive permitted local evidence separately with checksums and retention commitments. Add a deprecation notice while preserving the old README, and establish issue/security/contact routes before making the repository read-only.

17. **[Major] The existing release and DOI tools implement a different product.**

    **Evidence — verified:** `build.py release` invokes the historical Core builder (`build.py:207`), which filters CORE datasets (`src/arcaverborum/release.py:421`). The whole-collection builder packages native tables rather than producing the promised new all-accepted CLDF product. Zenodo tooling targets the old concept DOI, Core metadata and `other-open` (`scripts/zenodo_deposit.py:30`, `:64`, `:95`).

    **Failure scenario:** A launch command emits only Core, uploads misleading metadata, uses the wrong DOI lineage, or labels NC/undeclared content as open.

    **Remedy:** Implement and document one authoritative schema-A release path. Validate CLDF foreign keys, source references and cognate namespaces independently. Replace the deposit metadata and define an accurate mixed-terms record strategy before uploading.

18. **[Major] The letter/date scheme lacks compatibility and immutability rules.**

    **Evidence — verified:** Only selected table changes trigger a letter bump; added columns and all corrections retain the letter (plan:75). Three different tier payloads share one version family.

    **Failure scenario — inference:** Positional readers break on added columns; changed serialization, null conventions, value vocabularies, cognate scopes or CLDF metadata break consumers without a new letter. Corrected stable-ID meanings change scientific results without a clear migration record. A same-day suffix does not establish which release is superseded or whether assets may be replaced.

    **Remedy:** Define compatibility across native tables, CLDF, manifests and site APIs. Require immutable tags/assets, tier identifiers and checksums, explicit supersession/withdrawal records, changelogs and migration guidance. Separate schema compatibility from scientific-data changes.

19. **[Major] Splitting the sites leaves deployment integrity and GitHub dependencies unresolved.**

    **Evidence — verified:** Current Pages deployment simply copies committed `web/` and `docs/` (`.github/workflows/pages.yml:27`). It neither rebuilds data nor waits for the separate CI workflow. The proposed split introduces cross-repository deployment but specifies no credentials, promotion protocol or artifact verification (plan:38). Local `du -sh web` returned **664M**; the actual Pages payload also includes documentation.

    **Failure scenario — inference:** Code and data from different revisions are deployed together; main-repository CI cannot write or dispatch to another repository with its default token; a failed build still triggers publication; or future growth exceeds hosting limits. Two repositories solve neither release promotion nor retention in growing Git histories.

    **Remedy:** Promote a sealed, verified release artifact to the stable site. Deploy live only from successful workflows, with least-privilege cross-repository authorization and a displayed revision. Measure assembled site size, largest files and build/deployment limits; define rollback and headroom thresholds. The quoted Pages limit remains an external assumption requiring confirmation.

20. **[Blocker] The checklist orders prerequisites after the steps that depend on them.**

    **Evidence — verified:** Step 5 requires an actual PR/CI test before repositories exist at step 7. Stable DNS switches at step 8 before the release is cut and verified at step 9. Review protection precedes editor invitation. Zenodo follows release publication, while the snapshot is promised on both services (plan:165–179).

    **Failure scenario:** A staged local test is mistaken for the GitHub acceptance test; DNS exposes an incomplete site; required reviews halt the launch; author corrections alter an already released baseline without an explicit new release.

    **Remedy:** Create test repositories first, provision reviewers, run real fork/member PR tests, publish and verify immutable artifacts, stage both sites, then cut over DNS. Define how author-requested changes become a subsequent version and how that version binds to Zenodo. Add permissions, snapshot completeness, reviewer availability and deployment authorization to the blocking-input list.

21. **[Major] The paper has no minimum evidential gate for its strongest claims.**

    **Evidence — verified:** The outline promises source-selection validation, quality scoring and replicability, yet says there are no hard content must-haves before submission (plan:184–209). Current status explicitly identifies same-model review rather than independent expert gold (`docs/STATUS.md:12`). Quality scoring includes bonuses for populated segments, mappings and cognacy fields (`src/arcaverborum/forms_schema.py:35`).

    **Failure scenario — inference:** Tests and mechanical completeness scores are presented as evidence of linguistic correctness. Invited editors’ bounded reviews are generalized to 7,371 constructions and over two million records. A paper describes a frozen product that has not passed its own reproducibility and rights gates.

    **Remedy:** Require a final version-specific dataset, resolved availability statement, full rebuild evidence, documented selection methodology, stratified linguistic validation and explicit review coverage before submission. Describe scores as heuristics unless independently validated. Confirm the journal’s current Data Descriptor requirements separately.

22. **[Major] Authorship and editor attribution are conflated.**

    **Evidence — verified:** Every invited editor is proposed as an author, and reviewing their own data is declared sufficient (plan:186). `editors.csv` also feeds citation authorship and Zenodo contributors (plan:106).

    **Failure scenario — publication-policy risk:** Access permissions become automatic scholarly authorship, including inactive editors or people who neither approve the manuscript nor accept responsibility. CRediT labels document contributions but do not establish authorship eligibility by themselves.

    **Remedy:** Separate repository roles, dataset contributors, dataset creators and paper authors. Record actual contributions, manuscript approval and accountability; apply the journal’s authorship criteria rather than declaring a contribution sufficient in advance.

23. **[Major] PR-only AI disclosure leaves the baseline and archived releases without durable disclosure evidence.**

    **Evidence — verified:** Initial commits intentionally omit AI markers and history (plan:44); future disclosure exists only in a PR-template field (plan:121). The paper will state extensive baseline assistance, but historical review records are omitted.

    **Failure scenario — inference:** The initial import has no qualifying PR, later direct imports or administrative changes bypass the template, and downloaded release archives contain no record of which transformations were model-assisted. A mandatory template field is also not an enforcement mechanism.

    **Remedy:** Preserve a baseline methods/disclosure record and include a release-level disclosure summary with durable PR links or exported records. Enforce completion mechanically. Commit trailers are not necessary, but suppressing them cannot substitute for preserving methodological provenance.

24. **[Minor] Lexibank’s claimed contribution needs a reproducible classification.**

    **Evidence — verified:** The plan claims roughly 87% of accepted records come from Lexibank datasets (plan:14). Release source counts are grouped by `transcription_source` (`scripts/build_collection_release.py:70`), while intake also uses a shared “lexibank” transport directory (`build.py:48`).

    **Failure scenario — inference:** Transport format, hosting organization, original scholarly source and intellectual contribution are conflated. “Not an alternative” also obscures that Arca does provide an alternative selection and access product.

    **Remedy:** Publish the source classification and counting query. Distinguish Lexibank-hosted inputs, CLDF-format original sources, reused normalization and original lexical authorship. State what Arca changes and preserve dataset-specific citations.

Questions the author must answer:

- What exact permission authorizes each unresolved source’s public redistribution, including snapshot rows and website downloads?
- Does Tier 1 guarantee identical bytes, equivalent lexical tables, or the entire site including recordings and analytical products?
- Which immutable manifest defines accepted constructions and every required input?
- Who reviews Tiago’s PRs and editors’ own changes, and who can authorize exceptions?
- Which legacy evidence will be preserved outside GitHub, by whom, and for how long?
- Which release receives the paper’s version DOI after author corrections, and how are earlier assets superseded?
- What linguistic validation and authorship requirements must be satisfied before submission?