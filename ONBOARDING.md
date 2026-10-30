# Arca Verborum Onboarding

This guide is for a local checkout that already has the tracked repo state.
Generated products under `varieties/*/generated/`, `intake/`, `raw/`, and
`output/` are intentionally not part of the committed source of truth.

Read [STATUS](docs/STATUS.md) for the accepted baseline and [NEXT](docs/NEXT.md)
for proposed work. Use [the planning workflow](docs/workflows/arca-coverage-planning/SKILL.md)
when choosing an expansion batch, [the journal](docs/JOURNAL.md) for handoff
history, and [the documentation map](docs/README.md) for technical references.

## 1. Project Shape

Arca Verborum is a per-variety lexical database for computational
historical linguistics. Each variety has a stable `av_id`, selected source
configuration, optional curated extensions, and generated per-variety forms.
The aggregate product is built from those per-variety outputs.

The current goal is not just to pick a source mechanically. Arca builds one
accepted authoritative construction per language. That construction may use
a source as-is, use a source plus explicit corrections, or eventually use
Arca-derived layers and computed/curated cognates when they are reviewed.

## 2. Data Flow

```
fetch     -> raw/<source>/...                         downloaded; gitignored
ingest    -> intake/<source>/{forms,languages,...}    normalized intake; gitignored
register/curate -> varieties/<av_id>/config.yaml       tracked source choices
update    -> varieties/<av_id>/generated/forms.csv    generated; gitignored
aggregate -> output/aggregate/...                     generated; gitignored
report    -> output/report/curation.*                 generated; gitignored
explore   -> output/explore.sqlite                    generated; gitignored
```

Tracked source of truth:

* code under `src/arcaverborum/`;
* stable registries under `src/arcaverborum/data/`;
* `varieties/<av_id>/config.yaml`;
* hand-authored `varieties/<av_id>/custom/*` files when present;
* documentation and tests.

## 3. Environment

Python 3.12+ is expected (the phonology library `merkmal` requires ≥3.12). merkmal
(≥0.9.0) is an undeclared runtime dependency: it is not on PyPI and is built from
source, so it is installed out-of-band rather than via `arcaverborum`'s own
dependency list. Install it either from the sibling checkout at `../merkmal` or
straight from GitHub (as CI does):

```bash
pip install ../merkmal            # from the local sibling checkout, or
pip install "merkmal @ git+https://github.com/tresoldi/merkmal.git"
```

For a fresh checkout, run from its root. On this workstation, preserve the
existing `.venv` and its local merkmal installation and use `.venv/bin/python`.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
pip install -e ../merkmal/python
pip install pytest
python -c "import merkmal; print(merkmal.list_systems())"
pytest -q
```

The project intentionally avoids the CLDF ecosystem as runtime machinery.
Do not add `pycldf`, `pylexibank`, or `cldfbench` unless there is a
specific reviewed reason.

## 4. Common Commands

Build or refresh the affected accepted constructions from available intake:

```bash
python build.py update <accepted-av-id> [<accepted-av-id> ...]
python build.py aggregate
python build.py report
python explore.py index
```

Build a single variety after editing its config or custom files:

```bash
python build.py update ine-latin
python build.py aggregate
python build.py report
```

Scaffold curation files for a variety:

```bash
python build.py extend ine-latin
```

Inspect the aggregate:

```bash
python explore.py stats
python explore.py langs --family Indo-European
python explore.py lang ine-latin
python explore.py concept phy-water
python explore.py sql "SELECT tier, COUNT(*) FROM varieties GROUP BY tier"
```

Export a framework `evidence_bundle` (plus the separate Door-2 cognacy package and
sealed reconstruction gold) from the committed web snapshot; see
[the evidence-bundle reference](docs/EVIDENCE_BUNDLE.md):

```bash
python build.py export-evidence                    # default ancient/historical IE set
python build.py export-evidence ine-hittite --exclude-licence nc,sa,gpl
```

Audit concept drift against Concepticon:

```bash
python build.py concepts
python build.py concepts --mint
```

## 5. Current Baseline and Planning

[STATUS](docs/STATUS.md) maintains the accepted counts, data commit, verification,
latest evidence pointers and publication state. [NEXT](docs/NEXT.md) maintains
proposed tasks; [HELD](docs/planning/HELD.md) records reopening evidence.
Update these when a batch closes rather than copying historical metrics here.

The [coverage-planning workflow](docs/workflows/arca-coverage-planning/SKILL.md)
connects discovery, identity/source/sense gates, execution and closure. Dated
reports are indexed in [history](docs/history/README.md).

Frozen Jê source reproduction uses scripts/stage_je_original.py --fetch
--write-profiles. Fresh intake can append the complete namespace once. An
existing namespace requires scripts/expand_source_intake.py with a complete
stage and the actual preceding form count. Earlier rows, citations, license,
version and bibliography remain unchanged. The earlier251→371 migration has
already succeeded; never replay its old count or subset-ingest active intake.

## 6. Source Policy

Prioritize better evidence and broader lexical coverage, with particular
attention to the Americas, especially South America. Suitable languages without
source IPA may receive documented orthographic profiles. Never treat spelling
as IPA merely because an upstream field is named “Pronunciation”.

An accepted construction may combine a primary source with individually reviewed
supplements. Keep original source identities, raw readings, semantic decisions
and cognacy scopes. Do not apply a primary source's profile or cognate judgments
to a secondary source. The guarded supplementation ledger fails closed on drift.

The explorer defaults to All accepted varieties. Its Core-source preset filters
individual lexical rows; it is distinct from the 161-concept vocabulary filter
and the archived Core 0.1.0 release.

## 7. Curation Rules

Per-language work should become a structured curation packet, not ad hoc
edits. A packet should document the current construction, candidate sources,
concept mapping, transcription quality, cognates, provenance, tradeoffs, and
recommended authority recipe.

Small fixes can live in `varieties/<av_id>/custom/*`:

Supplementary sources use guarded `custom/supplements.csv` admissions. Their
profiles live separately under `custom/supplement_profiles/`, with exact
whole-form keys and a SHA256 recorded per admission; they never affect the
primary source. See `scripts/iquito_profile.py` for the first pilot.


* `transcriptions.csv` overrides source transcription columns;
* `forms.csv` adds new forms;
* `cognates.csv` overrides cognate fields by form id;
* `concept_map.csv` fixes source parameter-to-concept mapping;
* `profile.tsv` maps orthographic graphemes to IPA.

Profiles use greedy longest-match grapheme rules. A key such as `^word$`
instead matches the entire form exactly and takes precedence over grapheme
rules. Exact keys are excluded from substring matching: a dictionary-backed
profile cannot accidentally pronounce unknown compounds by concatenating
known headwords. Store pronunciation evidence and unresolved cases alongside
the curation packet. Profile coverage validates the chosen transcription
convention; it does not recover contrasts the spelling leaves unspecified.

Heavy correction or newly authored data should graduate into a named
Arca-derived layer once the data's scholarly identity is effectively Arca's
construction rather than the upstream source alone.

## 8. Gotchas

* `av_id` is the primary key. It is a frozen Arca identifier of the form
  `<family_code>-<name_slug>`, not a Glottocode.
* `concept_id` is also an Arca-controlled frozen key. Concepticon remains a
  mapped external column.
* `build.py status` checks config/custom/recipe freshness, but intake
  changes are detected by `build.py update`.
* `build_one` accepts pre-loaded intake DataFrames so `update --all` does
  not re-read huge CSVs per variety.
* Phonology uses merkmal's `descriptive` system. Source segments are
  normalized, tone digits are merged onto their nucleus before validation,
  and invalid source segments are preserved as `unclean`.
* Intake and per-variety generated outputs are gitignored. The research web
  catalog, family shards, manifest and bibliography under `web/data/` are tracked.
  Pages deploys these committed artifacts; it does not rebuild lexical data.
* Never ingest a subset directly into the active intake: ingestion replaces
  tables. Stage first, then use `scripts/append_source_intake.py` for new source
  namespaces. Existing namespaces require an explicit guarded migration.
* For accepted-only rebuilds, select varieties with existing
  `generated/forms.csv`; orphan configs are not accepted varieties.
* Use `.venv/bin/python` or `uv run --no-sync` with the installed local merkmal
  build. Both UTF8PROC normalization modes must be tested; do not add uv.lock.

## 9. Documentation Map

Use `docs/README.md` as the index. The main specs are:

* `docs/BESTOF_SPECIFICATION.md` for current build mechanics;
* `docs/CONCEPTS_SPECIFICATION.md` for concept IDs and Concepticon mapping;
* `docs/CURATION_WORKFLOW_SPECIFICATION.md` for the next curation workflow.

Document-based sources can use explicit transport handlers: bodtbangru fetches
and verifies a frozen Zenodo PDF, then materializes its reviewed CSVW/CLDF slice.
Use scripts/stage_bangru_original.py --fetch --audit-pdf before validated append
of the new namespace; optional PyMuPDF 2.0 reproduces the PDF-span audit. Source
versions may be immutable DOI/document hashes rather than Git commits.

For bounded reviewed dictionary primaries, unlinked community-member selectors
and recording-only metadata, see [the evidence format](docs/GUARDED_PRIMARY_AND_RECORDINGS.md).

## Worldwide follow-up reproduction state

WF01–WF12 is closed; see docs/WORLDWIDE_FOLLOWUP_EXECUTION_2026-10-29.md. Verify
new original dictionaries with scripts/verify_worldwide_sources.py --manifest
docs/worldwide_followup_sources_2026-10-29.json. The optional Text-Fabric command
in scripts/stage_bhsa_lexical.py reproduces14 written lexemes from23 pinned features.
Coptic materialization now uses two independently hashed files (58 rows); RVID's
complete derivative is92 rows/seven samples. Existing namespace expansions already
succeeded: do not replay older expected counts or append a namespace twice.
Cumulative profile reviews retain earlier exact keys and identity-scope fields;
do not compile a new partial slice over an existing profile inventory.

For complete research-web rebuilds on this workstation, use disk-backed scratch
space if `/tmp` is full (its tmpfs is small):

```bash
mkdir -p raw/curation/web-tmp
TMPDIR="$PWD/raw/curation/web-tmp" .venv/bin/python scripts/build_research_web.py
```

## Original-source S reproduction

S01–S09 is closed; see docs/WORLDWIDE_S_EXECUTION_2026-10-30.md. The pinned
original-source manifest covers12 complete namespaces/161,344 intake rows.
Use scripts/stage_original_lexica.py --dataset NAME --fetch only outside active
intake; these namespaces are already appended. scripts/verify_original_lexica.py
reproduces complete source/parameter/language/metadata/bibliography evidence
without changing intake. scripts/verify_original_profiles.py checks finite
reading scopes and the ten pinned LexiRumah profile files. The optional
PyMuPDF page audit is scripts/audit_original_pdf_citations.py. Complete intake
is not accepted vocabulary; primary/supplement ledgers remain the admission gate.
The PDF transport pins original bytes and manually reviewed page quotations;
run the independent page audit when changing that reviewed slice.

Reviewed literal source quotations retain original whitespace; do not normalize
those CSV cells merely to satisfy diff whitespace checks. Their native hashes
and independent page audits depend on the exact quotation.

## Historical T source reproduction

T01–T08 is closed; see docs/SOUTHERN_T_EXECUTION_2026-10-30.md. Four additional
complete original-source namespaces add56 intake rows. Use
`scripts/verify_original_lexica.py --output docs/southern_t_source_verification_2026-10-30.json`
to reproduce all16 registered original namespaces without changing intake.
`reviewed_facsimile` stores independently authored historical image transcriptions
with exact PDF/page/xref/image hashes and locators. It does not pretend that PDF
OCR verifies handwriting. The optional PyMuPDF audit is
`scripts/audit_southern_t_citations.py`; source PDFs/images remain privately cached.
`audit_chirila_transport.py` stages the pinned full historical CSV privately,
never active intake; it does not clear public redistribution or source identity.
