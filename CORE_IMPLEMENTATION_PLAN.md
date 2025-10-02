# Core Dataset Implementation Plan

**Date:** 2025-10-02
**Status:** DRAFT - Awaiting approval before implementation
**Core Selection:** 9 datasets (robinsonap, bowernpny, gravinachadic, peirosaustroasiatic, iecor, bdpa, tuled, utoaztecan, grollemundbantu)

---

## Executive Summary

Add "core" dataset functionality to Arca Verborum, allowing users to:
1. Clone only core datasets (faster setup)
2. Merge core datasets separately from full dataset
3. Download core-only release from Zenodo (smaller, focused)

This requires changes to 5 components: datasets.csv, clone script, merge script, release script, and documentation.

---

## Questions for Decision

### Q1: Collection Naming

**Question:** What should we call this collection?

**Options:**

**A. "core"** (simple, lowercase)
- Pros: Simple, matches common convention (core/full)
- Cons: May seem diminutive vs. "full"
- File examples: `arcaverborum_core_20251001.zip`, `output_core/`

**B. "essential"** (emphasizes value)
- Pros: Sounds premium, emphasizes quality over quantity
- Cons: Longer name
- File examples: `arcaverborum_essential_20251001.zip`, `output_essential/`

**C. "focus"** (emphasizes purpose)
- Pros: Academic tone, indicates curated selection
- Cons: Less intuitive
- File examples: `arcaverborum_focus_20251001.zip`, `output_focus/`

**D. "swadesh"** (emphasizes content)
- Pros: Immediately clear what it contains
- Cons: Technically imprecise (not just Swadesh, also aligned datasets)
- File examples: `arcaverborum_swadesh_20251001.zip`, `output_swadesh/`

**RECOMMENDATION: Option A ("core")**
- Reason: Industry standard (many projects have core/full splits), simple, clear hierarchy
- Usage: "core" and "full" are parallel, easy to understand

---

### Q2: CSV Column Naming

**Question:** What column name in datasets.csv should flag core datasets?

**Options:**

**A. Add "CORE" column** (alongside existing "CORECOG")
```csv
NAME,TYPE,URL,VERSION,CORECOG,CORE
robinsonap,cldf,https://...,TRUE,TRUE
bowernpny,cldf,https://...,TRUE,TRUE
```
- Pros: Clear, parallel to CORECOG, easy to filter
- Cons: Another column (but CSV can handle it)

**B. Reuse "CORECOG" column as "COLLECTION"** (consolidate)
```csv
NAME,TYPE,URL,VERSION,COLLECTION
robinsonap,cldf,https://...,CORE
bowernpny,cldf,https://...,CORE
abvdoceanic,cldf,https://...,CORECOG
aaleykusunda,cldf,https://...,
```
- Pros: Single column for all collections
- Cons: Loses CORECOG information (unless we allow comma-separated: "CORE,CORECOG")

**C. Use "COLLECTION" column with multiple values possible**
```csv
NAME,TYPE,URL,VERSION,COLLECTION
robinsonap,cldf,https://...,CORE
bowernpny,cldf,https://...,CORE;CORECOG
```
- Pros: Flexible, can tag datasets with multiple collections
- Cons: More complex parsing

**RECOMMENDATION: Option A (add "CORE" column)**
- Reason: Simple, clear, doesn't break existing CORECOG logic
- Keep CORECOG for historical tracking, use CORE for active collection
- Easy to extend later (could add "EXTENDED" column for future expansions)

---

### Q3: Directory Structure

**Question:** How should output directories be organized?

**Options:**

**A. Separate parallel directories**
```
output/           # Full dataset (all 149)
output_core/      # Core dataset (9 only)
releases/
  arcaverborum_20251001.zip              # Full
  arcaverborum_core_20251001.zip         # Core
```
- Pros: Clean separation, no risk of overwriting
- Cons: Duplication if running both mergers

**B. Subdirectories within output/**
```
output/
  full/           # Full dataset
  core/           # Core dataset
releases/
  arcaverborum_20251001.zip              # Full
  arcaverborum_core_20251001.zip         # Core
```
- Pros: Organized hierarchy, single output/ directory
- Cons: Longer paths

**C. Single output/ with flag files**
```
output/           # Could be full or core depending on last run
.last_build.txt   # Contains "full" or "core"
releases/
  arcaverborum_20251001.zip              # Full
  arcaverborum_core_20251001.zip         # Core
```
- Pros: No directory proliferation
- Cons: Confusing - user doesn't know which is in output/
- Cons: Risk of overwriting

**RECOMMENDATION: Option A (parallel directories)**
- Reason: Clearest for users, no ambiguity
- Users can have both full and core outputs simultaneously
- prepare_release.py can operate on either directory

---

### Q4: Merge Script Invocation

**Question:** How should users specify which dataset to build?

**Options:**

**A. Command-line flag** (one script, flag to select)
```bash
python merge_cldf_datasets.py                # Full (default)
python merge_cldf_datasets.py --core         # Core only
python merge_cldf_datasets.py --collection core  # Alternative syntax
```
- Pros: Single script, familiar pattern
- Cons: Need to handle collection selection logic

**B. Separate scripts**
```bash
python merge_cldf_datasets.py           # Full
python merge_cldf_datasets_core.py      # Core
```
- Pros: Very explicit, no ambiguity
- Cons: Code duplication (or one imports the other)

**C. Collection parameter with validation**
```bash
python merge_cldf_datasets.py --collection full   # Explicit full
python merge_cldf_datasets.py --collection core   # Explicit core
```
- Pros: Extensible (could add --collection extended later)
- Cons: More verbose than flag

**RECOMMENDATION: Option A (--core flag, with --collection for future)**
- Reason: Simple for common case, extensible
- Implementation:
  ```python
  parser.add_argument('--core', action='store_true',
                      help='Build core dataset only (9 datasets)')
  parser.add_argument('--collection', choices=['full', 'core'],
                      help='Specify collection to build (alternative to --core)')
  ```
- Default: full dataset (backward compatible)

---

### Q5: Clone Script Behavior

**Question:** How should clone_lexibank.py handle core datasets?

**Options:**

**A. Clone all by default, flag for core-only**
```bash
python clone_lexibank.py              # Clones all 149
python clone_lexibank.py --core-only  # Clones only 9 core
```
- Pros: Backward compatible, fast core setup
- Cons: "core-only" is limiting if we add more collections

**B. Collection-based cloning**
```bash
python clone_lexibank.py                    # All
python clone_lexibank.py --collection core  # Core only
python clone_lexibank.py --collection core --collection corecog  # Multiple
```
- Pros: Flexible, extensible
- Cons: More complex

**C. Clone all, merge selects subset**
```bash
python clone_lexibank.py   # Always clones all 149
# Merge script filters based on --core flag
```
- Pros: Simple clone logic
- Cons: Wastes time/bandwidth if user only wants core

**RECOMMENDATION: Option A (--core-only flag)**
- Reason: Users wanting core likely want fast setup (pedagogical use case)
- Implementation: Filter datasets.csv rows where CORE == TRUE before cloning
- Keep full clone as default for researchers

---

### Q6: Release Archive Strategy

**Question:** How should Zenodo releases be organized?

**Options:**

**A. Two separate archives per release**
```
Zenodo deposit (version 20251001):
  - arcaverborum_20251001.zip (542 MB) - Full dataset
  - arcaverborum_core_20251001.zip (85 MB) - Core dataset
```
- Pros: Users can download only what they need
- Cons: Two uploads per release

**B. Single archive with both**
```
Zenodo deposit (version 20251001):
  - arcaverborum_20251001.zip
    ├── full/
    │   ├── forms.csv
    │   └── ...
    └── core/
        ├── forms.csv
        └── ...
```
- Pros: Single upload, users get both
- Cons: Large download even for core users

**C. Core-only releases with full as separate deposition**
```
Zenodo deposit 1 (Core): arcaverborum_core (versioned)
Zenodo deposit 2 (Full): arcaverborum_full (versioned)
```
- Pros: Completely separate, different DOIs
- Cons: More complex to maintain, two DOI chains

**RECOMMENDATION: Option A (two archives per release)**
- Reason: Best user experience (download only what needed)
- Zenodo supports multiple files per deposition
- Release workflow:
  1. prepare_release.py builds both archives
  2. zenodo_publish.py uploads both to same deposition
  3. Users see two download options

---

### Q7: Documentation Strategy

**Question:** How should core dataset be documented?

**Options:**

**A. Separate CORE_DATASET_DESCRIPTION.md in each archive**
- Full archive: DATASET_DESCRIPTION.md (describes all 149)
- Core archive: CORE_DATASET_DESCRIPTION.md (describes 9, rationale)
- Pros: Tailored documentation per archive
- Cons: Duplication of common info

**B. Single description with sections**
- DATASET_DESCRIPTION.md (covers both, with "Core vs Full" section)
- Same file in both archives
- Pros: Single source of truth
- Cons: Full users see core info they don't need

**C. Modular documentation**
- DATASET_DESCRIPTION.md (general info)
- CORE_RATIONALE.md (why core exists, which datasets)
- Both archives get both files
- Pros: Composable, users can read what they want
- Cons: More files to manage

**RECOMMENDATION: Option A (separate descriptions)**
- Reason: Clearest for end users
- Each archive is self-contained with relevant docs
- Implementation: Two Jinja templates:
  - `templates/DATASET_DESCRIPTION.md.j2` (full)
  - `templates/CORE_DATASET_DESCRIPTION.md.j2` (core)

---

### Q8: Validation Report Filtering

**Question:** Should validation_report.json differ between core and full?

**Options:**

**A. Filter validation report to match collection**
- Core validation_report.json: only statistics for 9 datasets
- Full validation_report.json: all 149 datasets
- Pros: Focused, relevant metrics
- Cons: Need to regenerate report per collection

**B. Include all datasets, add "collection" tags**
```json
{
  "summary": {
    "total_datasets": 149,
    "core_datasets": 9,
    ...
  },
  "completeness": {
    "robinsonap": {"collection": "core", ...},
    "aaleykusunda": {"collection": null, ...}
  }
}
```
- Pros: Complete picture even in core
- Cons: Adds noise for core users

**C. Same report for both, users filter if needed**
- Pros: Simplest implementation
- Cons: Confusing for core users (why stats for 140 other datasets?)

**RECOMMENDATION: Option A (filtered reports)**
- Reason: Each collection is self-contained
- Core users only see core metrics (less confusion)
- Implementation: generate_validation_report() filters datasets based on collection

---

## Implementation Plan

### Phase 1: CSV and Data Infrastructure

**Files to modify:**
1. `datasets.csv`

**Changes:**
```csv
# Add CORE column (new column at end)
NAME,TYPE,URL,VERSION,CORECOG,CORE
robinsonap,cldf,https://github.com/lexibank/robinsonap,,TRUE,TRUE
bowernpny,cldf,https://github.com/lexibank/bowernpny,,TRUE,TRUE
gravinachadic,cldf,https://github.com/lexibank/gravinachadic,,TRUE,TRUE
peirosaustroasiatic,cldf,https://github.com/lexibank/peirosaustroasiatic,,TRUE,TRUE
iecor,cldf,https://github.com/lexibank/iecor,,TRUE,TRUE
bdpa,cldf,https://github.com/lexibank/bdpa,,TRUE,TRUE
tuled,cldf,https://github.com/tupian-language-resources/tuled,,TRUE,TRUE
utoaztecan,cldf,https://github.com/lexibank/utoaztecan,,TRUE,TRUE
grollemundbantu,cldf,https://github.com/lexibank/grollemundbantu,,,TRUE
# All other datasets have empty CORE column
```

**Validation:**
- Ensure 9 datasets have CORE=TRUE
- All other rows have CORE empty or FALSE

---

### Phase 2: Clone Script Updates

**File to modify:**
1. `clone_lexibank.py`

**Changes:**

```python
# Add argument
parser.add_argument(
    '--core-only',
    action='store_true',
    help='Clone only core datasets (9 datasets for pedagogical use)'
)

# Filter datasets
def load_datasets(csv_path: Path, core_only: bool = False) -> list:
    """Load dataset list from CSV, optionally filtering to core only."""
    datasets = []
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Filter if core_only
            if core_only and row.get('CORE') != 'TRUE':
                continue
            datasets.append(row)
    return datasets

# Update main
datasets = load_datasets(args.csv, core_only=args.core_only)
if args.core_only:
    logging.info(f"Core-only mode: cloning {len(datasets)} core datasets")
```

**Benefits:**
- Fast setup for pedagogical users
- Bandwidth savings (9 repos vs 149)

---

### Phase 3: Merge Script Updates

**File to modify:**
1. `merge_cldf_datasets.py`

**Changes:**

```python
# Add configuration
OUTPUT_DIR_FULL = Path('output')
OUTPUT_DIR_CORE = Path('output_core')

# Add arguments
parser.add_argument(
    '--core',
    action='store_true',
    help='Build core dataset only (9 datasets)'
)

parser.add_argument(
    '--output',
    type=str,
    help='Output directory (overrides default based on --core)'
)

# Dataset filtering
def load_datasets_to_process(lexibank_dir: Path, core_only: bool = False) -> list:
    """Discover datasets to process, optionally filtering to core."""
    # Read datasets.csv to get core list
    core_datasets = set()
    csv_path = Path('datasets.csv')
    if csv_path.exists() and core_only:
        with open(csv_path) as f:
            reader = csv.DictReader(f)
            core_datasets = {row['NAME'] for row in reader if row.get('CORE') == 'TRUE'}

    # Scan lexibank directory
    all_datasets = [d.name for d in lexibank_dir.iterdir()
                    if d.is_dir() and (d / 'cldf' / 'cldf-metadata.json').exists()]

    if core_only:
        datasets = [d for d in all_datasets if d in core_datasets]
        logger.info(f"Core mode: processing {len(datasets)} of {len(all_datasets)} datasets")
    else:
        datasets = all_datasets
        logger.info(f"Full mode: processing {len(datasets)} datasets")

    return sorted(datasets)

# Update main
output_dir = args.output if args.output else (OUTPUT_DIR_CORE if args.core else OUTPUT_DIR_FULL)
datasets = load_datasets_to_process(args.input, core_only=args.core)
```

**Benefits:**
- Same script handles both collections
- Clear output separation
- Easy to extend (add --collection extended later)

---

### Phase 4: Release Script Updates

**File to modify:**
1. `prepare_release.py`

**Changes:**

```python
# Add configuration
OUTPUT_DIR_FULL = Path("output")
OUTPUT_DIR_CORE = Path("output_core")
CORE_TEMPLATE = "CORE_DATASET_DESCRIPTION.md.j2"

# Add arguments
parser.add_argument(
    '--core',
    action='store_true',
    help='Prepare core dataset release instead of full'
)

parser.add_argument(
    '--both',
    action='store_true',
    help='Prepare both full and core releases'
)

# Helper to prepare one release
def prepare_release(version: str, is_core: bool, force: bool, git_tag: bool) -> Path:
    """Prepare a single release (core or full)."""
    output_dir = OUTPUT_DIR_CORE if is_core else OUTPUT_DIR_FULL
    collection_name = "core" if is_core else "full"
    archive_name = f"arcaverborum_core_{version}.zip" if is_core else f"arcaverborum_{version}.zip"

    # Check output exists
    if not output_dir.exists():
        die(f"{output_dir} does not exist. Run merge_cldf_datasets.py {'--core' if is_core else ''} first")

    # Load validation report
    validation_report = load_validation_report(output_dir)

    # Generate documentation
    template_name = CORE_TEMPLATE if is_core else "DATASET_DESCRIPTION.md.j2"
    docs = generate_documentation(version, validation_report, template_name, is_core=is_core)

    # Create archive
    output_files = [output_dir / f for f in RELEASE_FILES]
    archive_path = create_archive(archive_name, output_files, docs)

    logger.info(f"Created {collection_name} release: {archive_path}")
    return archive_path

# Update main
if args.both:
    # Prepare both releases
    archive_full = prepare_release(version, is_core=False, force=args.force, git_tag=False)
    archive_core = prepare_release(version, is_core=True, force=args.force, git_tag=False)

    # Update zenodo metadata with both files
    update_zenodo_metadata(version, [archive_full, archive_core])

    if args.git_tag:
        create_git_tag(version)
else:
    # Single release
    archive = prepare_release(version, is_core=args.core, force=args.force, git_tag=args.git_tag)
    update_zenodo_metadata(version, [archive])
```

**Benefits:**
- Can prepare core, full, or both
- Separate validation reports per collection
- Separate documentation

---

### Phase 5: Zenodo Metadata Updates

**File to modify:**
1. `zenodo.metadata.yml`

**Changes:**

```yaml
# Update files section to include both archives
files:
  - path: releases/arcaverborum_20251001.zip
    name: arcaverborum_20251001.zip
    description: "Full dataset (149 datasets, 2.9M forms)"
  - path: releases/arcaverborum_core_20251001.zip
    name: arcaverborum_core_20251001.zip
    description: "Core dataset (9 datasets, 184k forms, Concepticon-optimized)"
```

**Update description:**
```yaml
description: |
  Arca Verborum provides denormalized, analysis-ready comparative wordlist data.

  **Two versions available:**

  - **Full** (2.9M forms, 149 datasets): Complete Lexibank aggregation
  - **Core** (184k forms, 9 datasets): Curated subset optimized for cross-linguistic
    comparison via Swadesh-100 and Concepticon mapping. Ideal for pedagogy and
    method development.

  See DATASET_DESCRIPTION.md (full) or CORE_DATASET_DESCRIPTION.md (core) for details.
```

---

### Phase 6: Documentation Templates

**Files to create:**

1. `templates/CORE_DATASET_DESCRIPTION.md.j2`

**Content outline:**
```markdown
# Arca Verborum Core Dataset

## Overview
Curated subset of 9 high-quality datasets optimized for cross-linguistic comparison.

## Why Core?
- Swadesh-100 coverage: 80.6/100 average
- Concepticon mapping: 93.6% average
- All 6 macroareas represented
- Both alignment datasets included (bdpa, tuled)

## Datasets Included
1. robinsonap (Papunesia/Austronesian)
2. bowernpny (Australia/Pama-Nyungan)
3. gravinachadic (Africa/Chadic)
4. grollemundbantu (Africa/Bantu)
5. peirosaustroasiatic (Eurasia/Austroasiatic)
6. iecor (Eurasia/Indo-European)
7. bdpa (Eurasia/Multi-family, with alignments)
8. tuled (South America/Tupian, with alignments)
9. utoaztecan (North America/Uto-Aztecan)

## Statistics
- Total forms: {{ core_forms_count }}
- Total languages: {{ core_languages_count }}
- Unique glottocodes: {{ core_glottocodes }}
- Average Swadesh-100: {{ core_swadesh_avg }}/100
- Average Concepticon: {{ core_concepticon_avg }}%

## When to Use Core vs Full
- **Use Core**: Comparative linguistics, typology, pedagogy, prototyping
- **Use Full**: Specialized vocabulary, phylogenetics, large-scale statistics

[Rest of documentation...]
```

2. `templates/CORE_RELEASE_NOTES.md.j2` (separate release notes for core)

---

### Phase 7: Update Documentation

**Files to update:**

1. `README.md` (if exists, or create)
```markdown
# Arca Verborum

## Quick Start

### For Students and Pedagogical Use (Core Dataset)
```bash
# Clone core datasets only (9 datasets, ~5 min)
python clone_lexibank.py --core-only

# Build core dataset
python merge_cldf_datasets.py --core

# Output in output_core/ directory
```

### For Research and Full Access (Full Dataset)
```bash
# Clone all datasets (149 datasets, ~30 min)
python clone_lexibank.py

# Build full dataset
python merge_cldf_datasets.py

# Output in output/ directory
```

## Core vs Full

| Feature | Core | Full |
|---------|------|------|
| Datasets | 9 | 149 |
| Forms | ~184k | ~2.9M |
| Glottocodes | ~669 | ~4,694 |
| Swadesh-100 | 80.6/100 avg | 69.4/100 avg |
| Concepticon | 93.6% avg | 84.7% avg |
| Use case | Pedagogy, comparison | Research, specialized |
```

2. `RELEASE_WORKFLOW.md`
```markdown
# Release Workflow

## Preparing Both Releases

```bash
# Build both datasets
python merge_cldf_datasets.py           # Full
python merge_cldf_datasets.py --core    # Core

# Prepare both releases
python prepare_release.py --both

# This creates:
#   releases/arcaverborum_20251001.zip       (full)
#   releases/arcaverborum_core_20251001.zip  (core)
```

## Publishing to Zenodo

```bash
# Publishes both archives in single deposition
python zenodo_publish.py
```

Users will see two download options on Zenodo.
```

---

## File Summary

### Files to Modify
1. **datasets.csv**: Add CORE column
2. **clone_lexibank.py**: Add --core-only flag
3. **merge_cldf_datasets.py**: Add --core flag and output_core/ logic
4. **prepare_release.py**: Add --core and --both flags
5. **zenodo.metadata.yml**: Update description and files list
6. **README.md**: Add core vs full documentation
7. **RELEASE_WORKFLOW.md**: Update for dual releases

### Files to Create
1. **templates/CORE_DATASET_DESCRIPTION.md.j2**: Core-specific description
2. **templates/CORE_RELEASE_NOTES.md.j2**: Core-specific release notes

### Directories Created
1. **output_core/**: Core dataset output (gitignored)

---

## Testing Plan

### Test 1: Core-Only Workflow
```bash
# Fresh checkout
python clone_lexibank.py --core-only
# Verify: Only 9 repos in lexibank/

python merge_cldf_datasets.py --core
# Verify: output_core/ created with ~184k forms

python prepare_release.py --core
# Verify: arcaverborum_core_20251001.zip created
```

### Test 2: Full Workflow (backward compatibility)
```bash
python clone_lexibank.py
python merge_cldf_datasets.py
python prepare_release.py
# Verify: Same behavior as before
```

### Test 3: Both Releases
```bash
python clone_lexibank.py
python merge_cldf_datasets.py
python merge_cldf_datasets.py --core
python prepare_release.py --both
# Verify: Two archives created
```

### Test 4: Validation Report Accuracy
```bash
python merge_cldf_datasets.py --core
# Check output_core/validation_report.json
# Verify: total_datasets = 9, not 149
# Verify: Only core datasets in completeness section
```

---

## Migration Strategy

### Backward Compatibility
- All existing scripts work without changes (full dataset is default)
- datasets.csv: empty CORE column doesn't break existing parsers
- No breaking changes to existing workflows

### Gradual Rollout
1. Phase 1: datasets.csv + clone script (users can start testing)
2. Phase 2: merge script (users can build core)
3. Phase 3: release script (users can create core releases)
4. Phase 4: Zenodo integration (publish both)

Can deploy phases incrementally without breaking existing functionality.

---

## Risks and Mitigations

### Risk 1: User Confusion (core vs full)
**Mitigation:** Clear documentation at every entry point
- clone_lexibank.py --help explains --core-only
- merge_cldf_datasets.py --help explains --core
- README.md has prominent comparison table
- Release notes explain which to download

### Risk 2: Stale datasets.csv
**Mitigation:**
- Add validation in merge script (warns if CORE dataset missing)
- Document in datasets.csv header which 9 are core

### Risk 3: Directory confusion
**Mitigation:**
- Clear naming: output/ vs output_core/
- Scripts check which directory exists before proceeding
- prepare_release.py requires explicit --core flag (no guessing)

### Risk 4: Release archive size
**Mitigation:**
- Both archives still compress well
- Users can download only what they need from Zenodo
- Document sizes clearly in Zenodo description

---

## Open Questions for User

### Q9: Should grollemundbantu remain in core despite Swadesh coverage?

**Context:** grollemundbantu has only 53/100 Swadesh concepts (worst in core selection)

**Options:**
A. **Keep it** (your current selection)
- Pros: Excellent African coverage (424 languages, 333 glottocodes)
- Pros: Only 100 concepts total, all Concepticon-mapped
- Cons: Pulls down average Swadesh coverage

B. **Replace with smithborneo**
- smithborneo: 51k forms, 93 glottocodes, 70/100 Swadesh, 100% Concepticon
- Covers both Borneo (Austronesian) and some African languages
- Cons: Mixed macroarea (confusing)

C. **Add second African dataset** (keep grollemundbantu, add another)
- Could add kitchensemitic or felekesemitic for Swadesh balance
- Cons: 10 datasets instead of 9

**My recommendation:** Keep grollemundbantu
- Reason: Its 100 concepts are ALL Concepticon-mapped (100%)
- Reason: Excellent language coverage for Bantu
- Reason: Low Swadesh score is due to selective concept choice (phylogenetically motivated), not poor quality
- Note: Users filtering to Swadesh-only will naturally exclude it

### Q10: Should we version the core selection?

**Context:** Core membership might change over time (new datasets, reassessment)

**Options:**
A. **Static core** (these 9 forever)
- Pros: Simple, stable
- Cons: Can't improve later

B. **Versioned core** (core-v1, core-v2, etc.)
- Pros: Can refine selection as new datasets emerge
- Cons: More complex

**My recommendation:** Start static, allow evolution
- Mark these as "core-v1" internally
- If we change core membership later, document clearly in release notes
- Users citing core should cite specific release version anyway

---

## Timeline Estimate

**Phase 1 (CSV + clone):** 1 hour
- Modify datasets.csv: 10 min
- Update clone script: 30 min
- Test: 20 min

**Phase 2 (merge):** 2 hours
- Modify merge script: 60 min
- Test full workflow: 30 min
- Debug: 30 min

**Phase 3 (release):** 2 hours
- Modify prepare_release: 60 min
- Create templates: 30 min
- Test: 30 min

**Phase 4 (documentation):** 1 hour
- Update all docs: 40 min
- Review: 20 min

**Total: ~6 hours** (one work session)

---

## Approval Checklist

Before implementation, please confirm:

- [ ] Q1: Collection name: "core" (or alternative?)
- [ ] Q2: CSV column: Add "CORE" column (or alternative?)
- [ ] Q3: Directories: output/ and output_core/ (or alternative?)
- [ ] Q4: Merge flag: --core (or alternative?)
- [ ] Q5: Clone flag: --core-only (or alternative?)
- [ ] Q6: Release: Two archives per release (or alternative?)
- [ ] Q7: Docs: Separate CORE_DATASET_DESCRIPTION.md (or alternative?)
- [ ] Q8: Validation: Filtered per collection (or alternative?)
- [ ] Q9: Keep grollemundbantu despite low Swadesh? (Yes/No)
- [ ] Q10: Static core for now? (Yes/No)

---

## Next Steps After Approval

1. You review and answer questions above
2. I implement changes in order (CSV → clone → merge → release → docs)
3. Test each phase before proceeding
4. Create test release with both archives
5. Update gitignore for output_core/
6. Commit all changes with clear message

**Ready to proceed once you approve the plan and answer the questions!**
