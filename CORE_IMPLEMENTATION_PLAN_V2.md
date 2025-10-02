# Core Dataset Implementation Plan - Version 2

**Date:** 2025-10-02
**Status:** DRAFT v2 - Incorporating user feedback
**Core Selection:** 9 datasets (robinsonap, bowernpny, gravinachadic, peirosaustroasiatic, iecor, bdpa, tuled, utoaztecan, grollemundbantu)

---

## Changes from V1 Based on Feedback

### Approved Decisions:
- ✓ Q1: Collection name = "core"
- ✓ Q2: CSV column = "CORE"
- ✓ Q6: Two archives per Zenodo release
- ✓ Q8: Filtered validation reports per collection
- ✓ Q9: Keep grollemundbantu
- ✓ Q10: Static core for now

### Modified Decisions:

**Q3: Directory structure (CHANGED)**
- **User decision:** Single `output/` directory with subdirectories or suffixes
- **Options to clarify:**

**Option A: Subdirectories**
```
output/
  full/
    forms.csv
    languages.csv
    parameters.csv
    metadata.csv
    references.csv
    sources.bib
    validation_report.json
  core/
    forms.csv
    languages.csv
    parameters.csv
    metadata.csv
    references.csv
    sources.bib
    validation_report.json
```
- Pros: Clean organization, clear separation
- Pros: Each subdirectory is self-contained
- Cons: Nested paths (output/full/forms.csv)

**Option B: Suffixes**
```
output/
  forms.full.csv
  languages.full.csv
  parameters.full.csv
  metadata.full.csv
  references.full.csv
  sources.full.bib
  validation_report.full.json
  forms.core.csv
  languages.core.csv
  parameters.core.csv
  metadata.core.csv
  references.core.csv
  sources.core.bib
  validation_report.core.json
```
- Pros: Flat structure, easy to see all files
- Pros: Alphabetical sorting groups collections
- Cons: 14 files in one directory (more clutter)

**Option C: Mixed (subdirs + legacy top-level for backward compat)**
```
output/
  forms.csv          ← Legacy full dataset (for backward compat)
  languages.csv
  ...
  full/              ← Same as top level (symlinks or copies)
    forms.csv
    ...
  core/              ← Core only
    forms.csv
    ...
```
- Pros: Doesn't break existing scripts expecting output/forms.csv
- Cons: Duplication or symlink complexity

**MY RECOMMENDATION: Option A (subdirectories)**
- Reason: Cleaner, more scalable, self-contained
- Reason: No ambiguity about which is which
- Reason: Matches prepare_release.py logic (needs to know which files to archive)
- Backward compat: Can symlink output/forms.csv → output/full/forms.csv if needed

**Q4/Q5: Merge script behavior (CHANGED)**
- **User decision:** Build BOTH collections every time (single run)
- **Implication:** No flags needed for merge script
- **New behavior:**
  ```bash
  python merge_cldf_datasets.py
  # Builds both:
  #   output/full/
  #   output/core/
  ```

**Q7: Documentation (CHANGED)**
- **User decision:** Single documentation file (not separate)
- **Implication:** DATASET_DESCRIPTION.md covers both collections
- **Structure:** Sections for "Full Dataset" and "Core Dataset" within one file

---

## New Questions for Clarification

### NEW Q11: Output directory structure - confirm choice

**Question:** Confirm subdirectories approach?

```
output/
  full/
    forms.csv
    languages.csv
    ...
  core/
    forms.csv
    languages.csv
    ...
```

**Alternative (if you prefer suffixes):**
```
output/
  forms.full.csv
  forms.core.csv
  languages.full.csv
  languages.core.csv
  ...
```

**My recommendation:** Subdirectories (cleaner, more extensible)

---

### NEW Q12: Backward compatibility for output/

**Question:** Should we maintain backward compatibility for scripts expecting `output/forms.csv`?

**Context:** Some users might have scripts like:
```python
df = pd.read_csv('output/forms.csv')  # Will break if moved to output/full/
```

**Options:**

**A. Clean break** (no backward compat)
- output/full/ and output/core/ only
- Update all documentation to use new paths
- Pros: Clean, no confusion
- Cons: Breaks existing user scripts

**B. Symlinks for compatibility**
```
output/
  forms.csv → full/forms.csv  (symlink)
  languages.csv → full/languages.csv
  ...
  full/
    forms.csv
    ...
  core/
    forms.csv
    ...
```
- Pros: Existing scripts still work
- Cons: Symlink complexity on Windows
- Cons: Duplicate-looking files

**C. Top-level copies**
```
output/
  forms.csv  (copy of full/forms.csv)
  ...
  full/
    forms.csv
    ...
  core/
    forms.csv
    ...
```
- Pros: Works on all platforms
- Cons: Actual duplication (disk space)

**D. Document migration, no compat**
- Add MIGRATION.md explaining new paths
- Update all docs/examples to new structure
- Pros: Clean, pushes users to new structure
- Cons: Requires user action

**MY RECOMMENDATION: Option D (clean break with migration doc)**
- Reason: Project is pre-1.0, no stable API promised
- Reason: Symlinks are problematic cross-platform
- Reason: Duplication wastes space
- Action: Create MIGRATION.md with clear before/after examples

---

### NEW Q13: Clone script behavior

**Question:** Should clone script have filtering, or always clone all?

**Context:** User said merge builds both collections, but clone could still benefit from filtering

**Options:**

**A. Always clone all 149 datasets** (no flags)
```bash
python clone_lexibank.py  # Always clones all 149
# Then merge decides which to use
```
- Pros: Simple, merge has full data
- Cons: Slow for users who only want core (pedagogical case)

**B. Keep --core-only flag for fast pedagogy setup**
```bash
python clone_lexibank.py --core-only  # Clones only 9
# Faster for students, but can't build full later
```
- Pros: Fast setup for core-only users
- Cons: User needs to know upfront if they want full

**C. Clone core by default, --all for full**
```bash
python clone_lexibank.py         # Clones 9 core (default)
python clone_lexibank.py --all   # Clones all 149
```
- Pros: Fast default, opt-in to full
- Cons: Flips default behavior (breaking change)

**MY RECOMMENDATION: Option B (--core-only flag remains)**
- Reason: Fast setup for students (key use case)
- Reason: Users cloning for development likely want full anyway
- Reason: Default to "clone all" is safer (doesn't limit future options)
- Note: merge script will warn if datasets missing

---

### NEW Q14: Merge script progress indication

**Question:** How should merge indicate it's building both collections?

**Options:**

**A. Sequential logging**
```
Processing 149 datasets for full collection...
[progress bar]
Completed full collection: output/full/

Processing 9 datasets for core collection...
[progress bar]
Completed core collection: output/core/
```
- Pros: Clear what's happening
- Cons: Makes merge take ~2x longer (sequential)

**B. Interleaved processing**
```
Processing 149 datasets (9 in core, 140 full-only)...
[single progress bar]
Writing full collection: output/full/
Writing core collection: output/core/
```
- Pros: Only process each dataset once
- Cons: More complex logic (track which collection each dataset belongs to)

**C. Parallel processing**
```
Processing datasets...
[progress bar]
Built full collection: output/full/ (149 datasets)
Built core collection: output/core/ (9 datasets, subset)
```
- Pros: Fastest (single pass, filter on write)
- Cons: Requires holding both in memory or smart streaming

**MY RECOMMENDATION: Option C (parallel - single pass, filter on write)**
- Reason: Most efficient (only reads each dataset once)
- Reason: Core is subset of full, so filter during final write
- Implementation:
  ```python
  # Process all 149 datasets
  all_forms = []
  for dataset in all_datasets:
      forms = process_dataset(dataset)
      all_forms.append(forms)

  # Write full
  write_collection(all_forms, 'output/full/', collection='full')

  # Write core (filter by dataset name)
  core_forms = [f for f in all_forms if f['Dataset'].iloc[0] in CORE_DATASETS]
  write_collection(core_forms, 'output/core/', collection='core')
  ```

---

### NEW Q15: prepare_release.py behavior

**Question:** How should release preparation work with both collections?

**Context:** User approved two archives per Zenodo release

**Options:**

**A. Explicit flag to choose collection**
```bash
python prepare_release.py --collection full  # Creates full archive
python prepare_release.py --collection core  # Creates core archive
python prepare_release.py --both             # Creates both archives
```
- Pros: Explicit control
- Cons: User must run twice for both (unless --both)

**B. Always prepare both** (no flags)
```bash
python prepare_release.py  # Always creates both archives
# Output:
#   releases/arcaverborum_20251001.zip
#   releases/arcaverborum_core_20251001.zip
```
- Pros: Consistent with merge behavior (always both)
- Pros: Simpler workflow
- Cons: User can't prepare just one (though why would they?)

**C. Default to both, allow --only**
```bash
python prepare_release.py                  # Both archives (default)
python prepare_release.py --only full      # Just full
python prepare_release.py --only core      # Just core
```
- Pros: Flexibility
- Cons: More complex

**MY RECOMMENDATION: Option B (always both)**
- Reason: Consistent with merge behavior
- Reason: Simpler workflow (one command for release)
- Reason: Hard to imagine case where you want only one archive
- Note: Users can always delete one archive manually if needed

---

### NEW Q16: Documentation structure in DATASET_DESCRIPTION.md

**Question:** How should single documentation file be organized?

**Options:**

**A. Sequential sections**
```markdown
# Arca Verborum Dataset

## Overview
[General intro to project]

## Full Dataset
- 149 datasets
- 2.9M forms
- [Full stats]

## Core Dataset
- 9 datasets
- 184k forms
- [Core stats]
- Why core exists
- When to use core vs full

## Data Structure
[Common to both]

## Usage
[Examples for both]
```
- Pros: Linear read, comprehensive
- Cons: Full users must scroll past core info

**B. Choice-based sections (early split)**
```markdown
# Arca Verborum Dataset

## Choose Your Collection

### Core Dataset (Recommended for Students)
- 9 datasets, 184k forms
- Swadesh-optimized
- [Quick start]
- → See "Core Dataset Details" below

### Full Dataset (Recommended for Research)
- 149 datasets, 2.9M forms
- Complete Lexibank
- [Quick start]
- → See "Full Dataset Details" below

## Core Dataset Details
[Detailed core info]

## Full Dataset Details
[Detailed full info]

## Common Information
[Shared sections]
```
- Pros: Users quickly find their path
- Cons: More fragmented

**C. Comparison-first approach**
```markdown
# Arca Verborum Dataset

## Core vs Full Comparison

| Feature | Core | Full |
|---------|------|------|
| Datasets | 9 | 149 |
| Forms | 184k | 2.9M |
| Use case | Pedagogy, comparison | Research, specialized |
| Swadesh-100 | 81/100 avg | 69/100 avg |

## When to Use Core
[Explanation]

## When to Use Full
[Explanation]

## Using Core
[Core details and examples]

## Using Full
[Full details and examples]

## Data Structure (Common)
[Shared info]
```
- Pros: Immediate comparison, clear decision
- Cons: Table might overwhelm some users

**MY RECOMMENDATION: Option C (comparison-first)**
- Reason: Users need to make choice, comparison helps
- Reason: Table format is scannable
- Reason: Sets expectations upfront
- Structure:
  1. Brief intro
  2. Comparison table
  3. When to use X sections
  4. Detailed sections per collection
  5. Common information

---

### NEW Q17: Validation report generation

**Question:** Should validation reports be generated separately or in single pass?

**Context:** User approved filtered reports (core shows only 9 datasets)

**Options:**

**A. Generate during merge (single pass)**
```python
# During merge, track stats for both collections
full_stats = validate(all_datasets)
core_stats = validate(core_datasets_only)

write_validation_report(full_stats, 'output/full/validation_report.json')
write_validation_report(core_stats, 'output/core/validation_report.json')
```
- Pros: Efficient, all in one run
- Cons: More complex merge logic

**B. Post-processing step**
```bash
python merge_cldf_datasets.py  # Creates both, validates
# Then internally:
#   filter validation_report.json for core → output/core/
#   keep full validation_report.json → output/full/
```
- Pros: Clean separation
- Cons: Extra step

**MY RECOMMENDATION: Option A (during merge)**
- Reason: All statistics collected during processing anyway
- Reason: Ensures reports stay in sync
- Implementation: Track two validation objects in parallel during merge

---

### NEW Q18: zenodo_publish.py modification needed?

**Question:** Does zenodo_publish.py need updates for two archives?

**Context:** Zenodo allows multiple files per deposition

**Current behavior:** Uploads files listed in zenodo.metadata.yml

**Options:**

**A. Manual metadata update** (current approach works)
- User updates zenodo.metadata.yml to list both archives
- zenodo_publish.py uploads both (no code change needed)
- Pros: No code change needed
- Cons: Manual step

**B. Auto-detect archives**
```python
# zenodo_publish.py automatically finds:
#   releases/arcaverborum_YYYYMMDD.zip
#   releases/arcaverborum_core_YYYYMMDD.zip
# and uploads both
```
- Pros: Automated
- Cons: Might upload wrong files if multiple versions present

**C. prepare_release.py updates zenodo.metadata.yml**
```python
# prepare_release.py writes both file paths to metadata
# zenodo_publish.py reads and uploads
```
- Pros: Consistent with current workflow
- Cons: Metadata file changes with each release (but it already does)

**MY RECOMMENDATION: Option C (prepare_release updates metadata)**
- Reason: Matches current pattern (prepare_release already updates metadata)
- Reason: Explicit control over what gets uploaded
- Implementation: prepare_release.py lists both archives in files section

---

## Revised Implementation Plan

### Phase 1: Data Infrastructure

**1.1 Update datasets.csv**
```csv
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
# All other 140 datasets: CORE column empty or FALSE
```

**1.2 Update .gitignore**
```
# Keep output/ ignored (now contains subdirs)
output/
```
(No change needed - output/ already ignored)

---

### Phase 2: Clone Script (Optional Enhancement)

**File:** clone_lexibank.py

**Changes:**
```python
# Add optional --core-only flag for fast pedagogy setup
parser.add_argument(
    '--core-only',
    action='store_true',
    help='Clone only 9 core datasets (fast setup for students/pedagogy)'
)

def load_datasets(csv_path: Path, core_only: bool = False) -> list:
    """Load dataset list, optionally filtering to core only."""
    datasets = []
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            if core_only and row.get('CORE') != 'TRUE':
                continue
            datasets.append(row)
    return datasets

# In main():
datasets = load_datasets(args.csv, core_only=args.core_only)
if args.core_only:
    logger.info(f"Core-only mode: cloning {len(datasets)} core datasets")
else:
    logger.info(f"Cloning {len(datasets)} datasets")
```

**Note:** This is OPTIONAL. Users can still clone all and merge will use appropriate subset.

---

### Phase 3: Merge Script (Major Update)

**File:** merge_cldf_datasets.py

**Changes:**

**3.1 Configuration**
```python
# Update output configuration
OUTPUT_DIR = Path('output')
OUTPUT_DIR_FULL = OUTPUT_DIR / 'full'
OUTPUT_DIR_CORE = OUTPUT_DIR / 'core'

# Core datasets list (read from datasets.csv)
CORE_DATASETS = set()  # Will be populated from CSV
```

**3.2 Load core dataset list**
```python
def load_core_datasets() -> set:
    """Load list of core datasets from datasets.csv."""
    core = set()
    csv_path = Path('datasets.csv')
    if csv_path.exists():
        with open(csv_path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('CORE') == 'TRUE':
                    core.add(row['NAME'])
    return core

# At start of main():
CORE_DATASETS = load_core_datasets()
logger.info(f"Core datasets: {len(CORE_DATASETS)} ({', '.join(sorted(CORE_DATASETS))})")
```

**3.3 Process all datasets once**
```python
# Single pass through all datasets
all_forms = []
all_languages = []
all_parameters = []
# ... etc for all tables

for dataset in datasets:
    # Process dataset (existing logic)
    forms = process_forms(dataset)
    languages = process_languages(dataset)
    # ... etc

    # Collect for both collections
    all_forms.append(forms)
    all_languages.append(languages)
    # ... etc

# Concatenate all
full_forms = pd.concat(all_forms, ignore_index=True)
full_languages = pd.concat(all_languages, ignore_index=True)
# ... etc
```

**3.4 Filter for core**
```python
# Filter to core datasets
core_forms = full_forms[full_forms['Dataset'].isin(CORE_DATASETS)]
core_languages = full_languages[full_languages['Dataset'].isin(CORE_DATASETS)]
# ... etc for all tables
```

**3.5 Generate validation reports for both**
```python
# Generate validation for full
full_validation = generate_validation_report(
    datasets=datasets,
    forms=full_forms,
    languages=full_languages,
    # ... etc
)

# Generate validation for core (only core datasets)
core_datasets_list = [d for d in datasets if d in CORE_DATASETS]
core_validation = generate_validation_report(
    datasets=core_datasets_list,
    forms=core_forms,
    languages=core_languages,
    # ... etc
)
```

**3.6 Write both collections**
```python
# Create directories
OUTPUT_DIR_FULL.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR_CORE.mkdir(parents=True, exist_ok=True)

# Write full collection
logger.info(f"Writing full collection to {OUTPUT_DIR_FULL}")
full_forms.to_csv(OUTPUT_DIR_FULL / 'forms.csv', index=False)
full_languages.to_csv(OUTPUT_DIR_FULL / 'languages.csv', index=False)
# ... etc for all files
with open(OUTPUT_DIR_FULL / 'validation_report.json', 'w') as f:
    json.dump(full_validation, f, indent=2)

# Write core collection
logger.info(f"Writing core collection to {OUTPUT_DIR_CORE}")
core_forms.to_csv(OUTPUT_DIR_CORE / 'forms.csv', index=False)
core_languages.to_csv(OUTPUT_DIR_CORE / 'languages.csv', index=False)
# ... etc for all files
with open(OUTPUT_DIR_CORE / 'validation_report.json', 'w') as f:
    json.dump(core_validation, f, indent=2)

logger.info(f"Full collection: {len(full_forms):,} forms from {len(datasets)} datasets")
logger.info(f"Core collection: {len(core_forms):,} forms from {len(CORE_DATASETS)} datasets")
```

**3.7 Remove command-line flags** (not needed since always builds both)
- No --core flag needed
- No --output override needed (always builds both to output/full/ and output/core/)

---

### Phase 4: Release Script Updates

**File:** prepare_release.py

**Changes:**

**4.1 Configuration**
```python
OUTPUT_DIR = Path("output")
OUTPUT_DIR_FULL = OUTPUT_DIR / "full"
OUTPUT_DIR_CORE = OUTPUT_DIR / "core"

# Files remain the same
RELEASE_FILES = [
    "forms.csv",
    "languages.csv",
    "parameters.csv",
    "metadata.csv",
    "references.csv",
    "sources.bib",
    "validation_report.json"
]
```

**4.2 Always prepare both releases** (no flags needed)
```python
def main():
    # ... argument parsing for version, force, git-tag ...

    # Check both output directories exist
    if not OUTPUT_DIR_FULL.exists():
        die(f"{OUTPUT_DIR_FULL} does not exist. Run merge_cldf_datasets.py first")
    if not OUTPUT_DIR_CORE.exists():
        die(f"{OUTPUT_DIR_CORE} does not exist. Run merge_cldf_datasets.py first")

    # Prepare full release
    logger.info("Preparing full collection release...")
    full_archive = prepare_single_release(
        version=version,
        collection='full',
        output_dir=OUTPUT_DIR_FULL,
        archive_name=f"arcaverborum_{version}.zip"
    )

    # Prepare core release
    logger.info("Preparing core collection release...")
    core_archive = prepare_single_release(
        version=version,
        collection='core',
        output_dir=OUTPUT_DIR_CORE,
        archive_name=f"arcaverborum_core_{version}.zip"
    )

    # Update zenodo metadata with both files
    update_zenodo_metadata(version, [full_archive, core_archive])

    logger.info(f"Created releases:")
    logger.info(f"  Full: {full_archive}")
    logger.info(f"  Core: {core_archive}")
```

**4.3 Refactor preparation logic**
```python
def prepare_single_release(version: str, collection: str, output_dir: Path, archive_name: str) -> Path:
    """Prepare a single release archive."""

    # Load validation report for this collection
    validation_report = load_validation_report(output_dir)

    # Generate documentation (single file, covers both collections)
    docs = generate_documentation(version, validation_report, collection=collection)

    # Compute checksums
    output_files = [output_dir / f for f in RELEASE_FILES]
    checksums = compute_checksums(output_files)

    # Create archive
    archive_path = RELEASES_DIR / archive_name
    with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add output files
        for file_path in output_files:
            arcname = f"{archive_name.replace('.zip', '')}/{file_path.name}"
            zf.write(file_path, arcname)

        # Add documentation
        for doc_name, doc_content in docs.items():
            arcname = f"{archive_name.replace('.zip', '')}/{doc_name}"
            zf.writestr(arcname, doc_content)

    return archive_path
```

**4.4 Update zenodo.metadata.yml writer**
```python
def update_zenodo_metadata(version: str, archive_paths: list[Path]):
    """Update zenodo.metadata.yml with release info."""

    # Load existing metadata
    with open(METADATA_FILE) as f:
        metadata = yaml.safe_load(f)

    # Update version
    metadata['version'] = version

    # Update files section
    metadata['files'] = []
    for archive_path in archive_paths:
        # Determine if core or full based on name
        is_core = 'core' in archive_path.name

        metadata['files'].append({
            'path': str(archive_path),
            'name': archive_path.name,
            'description': (
                f"Core collection (9 datasets, ~184k forms, Concepticon-optimized)"
                if is_core else
                f"Full collection (149 datasets, ~2.9M forms)"
            )
        })

    # Write back
    with open(METADATA_FILE, 'w') as f:
        yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)
```

---

### Phase 5: Documentation Template Updates

**File:** templates/DATASET_DESCRIPTION.md.j2

**Changes:** Restructure to cover both collections in single file

```jinja2
# Arca Verborum: Global Lexical Database

## Overview

Arca Verborum provides denormalized, analysis-ready comparative wordlist data
from Lexibank CLDF datasets. Available in two collections:

## Collection Comparison

| Feature | Core | Full |
|---------|------|------|
| **Datasets** | 9 | 149 |
| **Forms** | {{ core_forms_count }} | {{ full_forms_count }} |
| **Languages** | {{ core_languages_count }} | {{ full_languages_count }} |
| **Unique Glottocodes** | {{ core_glottocodes }} | {{ full_glottocodes }} |
| **Swadesh-100 Coverage** | {{ core_swadesh_avg }}/100 avg | {{ full_swadesh_avg }}/100 avg |
| **Concepticon Mapping** | {{ core_concepticon_pct }}% | {{ full_concepticon_pct }}% |
| **Forms with Cognates** | {{ core_cognate_pct }}% | {{ full_cognate_pct }}% |
| **Forms with Alignments** | {{ core_alignment_pct }}% | {{ full_alignment_pct }}% |

## When to Use Core

**Recommended for:**
- Pedagogical use (students, teaching)
- Cross-linguistic comparison studies
- Typological research requiring Swadesh/Concepticon comparability
- Method prototyping and development
- Projects prioritizing quality over quantity

**Key advantages:**
- High Swadesh-100 coverage (80.6/100 average)
- Excellent Concepticon mapping (93.6% average)
- All 6 macroareas represented
- Both alignment datasets included (bdpa, tuled)
- Faster to download and process

## When to Use Full

**Recommended for:**
- Large-scale statistical studies
- Specialized vocabulary research
- Phylogenetic analyses requiring specific families
- Projects needing maximum language coverage
- Research on rare or endangered languages

**Key advantages:**
- Maximum coverage (2.9M forms, 4,694 glottocodes)
- 149 diverse datasets across all families
- Specialized vocabularies (kinship, flora, fauna, etc.)
- Complete Lexibank aggregation

---

## Core Collection Details

### Included Datasets

1. **robinsonap** (Papunesia: Austronesian Admiralty)
   - {{ dataset_stats['robinsonap']['forms'] }} forms, {{ dataset_stats['robinsonap']['languages'] }} languages
   - Swadesh: {{ dataset_stats['robinsonap']['swadesh_100'] }}/100

2. **bowernpny** (Australia: Pama-Nyungan)
   - {{ dataset_stats['bowernpny']['forms'] }} forms, {{ dataset_stats['bowernpny']['languages'] }} languages
   - Swadesh: {{ dataset_stats['bowernpny']['swadesh_100'] }}/100

[... continue for all 9 ...]

### Geographic Coverage
- Papunesia: 1 dataset (robinsonap)
- Australia: 1 dataset (bowernpny)
- Africa: 2 datasets (gravinachadic, grollemundbantu)
- Eurasia: 3 datasets (peirosaustroasiatic, iecor, bdpa)
- South America: 1 dataset (tuled)
- North America: 1 dataset (utoaztecan)

### Data Quality
- Average Swadesh-100: {{ core_swadesh_avg }}/100
- Average Concepticon mapping: {{ core_concepticon_pct }}%
- Cognacy coverage: {{ core_cognate_pct }}%
- Segmentation coverage: {{ core_segment_pct }}%

---

## Full Collection Details

### Coverage
- {{ full_datasets_count }} datasets from Lexibank
- {{ full_forms_count }} lexical forms
- {{ full_glottocodes }} unique glottocodes ({{ full_glottocode_pct }}% of world's languages)
- {{ full_languages_count }} language varieties

### Quality Metrics
[... existing full dataset documentation ...]

---

## Data Structure

[... common sections about CSV schema, citations, etc. ...]

## Version Information

- **Version:** {{ version }}
- **Release Date:** {{ release_date }}
- **Glottolog versions:** {{ glottolog_versions }}
- **Concepticon versions:** {{ concepticon_versions }}

## Citation

[... citation info, updated to mention both collections ...]

```

**Note:** Template needs statistics for BOTH collections passed to it.

---

### Phase 6: Additional Documentation

**File to create:** MIGRATION.md (for backward compatibility)

```markdown
# Migration Guide: New Output Structure

## What Changed

Starting with version YYYYMMDD, output structure changed from:

```
output/
  forms.csv
  languages.csv
  ...
```

To:

```
output/
  full/
    forms.csv
    languages.csv
    ...
  core/
    forms.csv
    languages.csv
    ...
```

## Why?

Arca Verborum now generates TWO collections:
- **Full**: All 149 datasets (same as before)
- **Core**: 9 curated datasets optimized for cross-linguistic comparison

## Updating Your Scripts

**Before:**
```python
import pandas as pd
df = pd.read_csv('output/forms.csv')
```

**After:**
```python
import pandas as pd

# For full dataset (same as before):
df = pd.read_csv('output/full/forms.csv')

# Or for core dataset:
df = pd.read_csv('output/core/forms.csv')
```

## Quick Fix

If you have many scripts to update, you can create a symbolic link:

**Linux/Mac:**
```bash
cd output
ln -s full/forms.csv forms.csv
ln -s full/languages.csv languages.csv
# etc.
```

**Windows:**
```cmd
cd output
mklink forms.csv full\forms.csv
mklink languages.csv full\languages.csv
```

Then your old scripts will still work (reading from full collection).
```

**File to update:** README.md

Add section explaining both collections and new structure.

**File to update:** RELEASE_WORKFLOW.md

Update all examples to use new paths:
```bash
# Build both collections
python merge_cldf_datasets.py
# Creates:
#   output/full/
#   output/core/

# Prepare both releases
python prepare_release.py
# Creates:
#   releases/arcaverborum_20251001.zip
#   releases/arcaverborum_core_20251001.zip
```

---

## File Summary

### Files to Modify
1. **datasets.csv** - Add CORE column with TRUE for 9 datasets
2. **clone_lexibank.py** - Add --core-only flag (optional)
3. **merge_cldf_datasets.py** - Build both collections to output/full/ and output/core/
4. **prepare_release.py** - Always prepare both archives
5. **templates/DATASET_DESCRIPTION.md.j2** - Restructure for both collections
6. **zenodo.metadata.yml** - List both archives
7. **README.md** - Document both collections
8. **RELEASE_WORKFLOW.md** - Update for new structure
9. **.gitignore** - No change needed (output/ already ignored)

### Files to Create
1. **MIGRATION.md** - Guide for updating scripts to new structure

### Directories Created (by merge script)
1. **output/full/** - Full collection (149 datasets)
2. **output/core/** - Core collection (9 datasets)

---

## Testing Plan

### Test 1: Full Workflow from Scratch
```bash
# Clone all datasets
python clone_lexibank.py

# Merge (creates both collections)
python merge_cldf_datasets.py

# Verify output structure
ls output/full/    # Should have 7 files
ls output/core/    # Should have 7 files

# Check core has 9 datasets
python -c "import pandas as pd; print(pd.read_csv('output/core/metadata.csv')['Dataset'].nunique())"
# Should print: 9

# Check full has 149 datasets
python -c "import pandas as pd; print(pd.read_csv('output/full/metadata.csv')['Dataset'].nunique())"
# Should print: 149

# Prepare releases
python prepare_release.py

# Verify archives
ls releases/
# Should show:
#   arcaverborum_20251002.zip
#   arcaverborum_core_20251002.zip
```

### Test 2: Core-Only Clone (fast setup)
```bash
# Clone only core datasets
python clone_lexibank.py --core-only

# Verify only 9 repos
ls lexibank/ | wc -l
# Should print: 9

# Merge (will process 9, but try to create both collections)
python merge_cldf_datasets.py
# output/full/ will have only 9 datasets (subset)
# output/core/ will have same 9 datasets

# Note: This is a valid workflow for core-only users
```

### Test 3: Validation Report Differences
```bash
python merge_cldf_datasets.py

# Check full validation
python -c "import json; v=json.load(open('output/full/validation_report.json')); print(v['summary']['total_datasets'])"
# Should print: 149

# Check core validation
python -c "import json; v=json.load(open('output/core/validation_report.json')); print(v['summary']['total_datasets'])"
# Should print: 9
```

### Test 4: Archive Contents
```bash
python prepare_release.py

# Check full archive
unzip -l releases/arcaverborum_20251002.zip
# Should show files from output/full/

# Check core archive
unzip -l releases/arcaverborum_core_20251002.zip
# Should show files from output/core/

# Check documentation (same in both)
unzip -p releases/arcaverborum_20251002.zip '*/DATASET_DESCRIPTION.md' | grep "Core Collection"
unzip -p releases/arcaverborum_core_20251002.zip '*/DATASET_DESCRIPTION.md' | grep "Core Collection"
# Both should contain core/full information
```

---

## Timeline Estimate (Updated)

**Phase 1 (CSV):** 15 min
- Add CORE column to datasets.csv
- Test: verify 9 rows have TRUE

**Phase 2 (Clone - optional):** 30 min
- Add --core-only flag
- Test: clone with and without flag

**Phase 3 (Merge - major):** 3 hours
- Refactor to build both collections
- Test: verify both output dirs created
- Test: verify correct dataset counts
- Debug: ensure validation reports accurate

**Phase 4 (Release):** 2 hours
- Refactor to prepare both archives
- Update zenodo metadata handling
- Test: create both releases

**Phase 5 (Templates):** 1 hour
- Restructure DATASET_DESCRIPTION.md.j2
- Ensure statistics for both collections
- Test: verify generated docs readable

**Phase 6 (Docs):** 1 hour
- Create MIGRATION.md
- Update README.md
- Update RELEASE_WORKFLOW.md
- Test: verify all examples work

**Total: ~8 hours** (one full work day)

---

## Remaining Questions for Approval

Please confirm:

- [ ] **Q11:** Use subdirectories (output/full/ and output/core/)? **YES/NO**
- [ ] **Q12:** No backward compatibility (clean break, add MIGRATION.md)? **YES/NO**
- [ ] **Q13:** Keep --core-only flag in clone script for fast setup? **YES/NO**
- [ ] **Q14:** Single-pass merge (process once, filter on write)? **YES/NO**
- [ ] **Q15:** prepare_release.py always creates both archives? **YES/NO**
- [ ] **Q16:** Use comparison-first approach in documentation? **YES/NO**
- [ ] **Q17:** Generate validation reports during merge (parallel tracking)? **YES/NO**
- [ ] **Q18:** prepare_release.py updates zenodo.metadata.yml with both archives? **YES/NO**

---

## Ready to Implement

Once you approve answers to Q11-Q18, I will:

1. Implement changes in order (CSV → clone → merge → release → docs)
2. Test each phase before proceeding
3. Report progress and any issues
4. Create final test release

**No changes will be made until you explicitly approve this plan!**
