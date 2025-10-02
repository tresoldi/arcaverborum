# Migration Guide: Full and Core Collections

This document explains the changes introduced in the dual-collection system and how to migrate existing workflows.

## What Changed

Starting with this release, Arca Verborum builds **two collections** from the Lexibank datasets:

1. **Full Collection** - All 149 datasets (research use)
2. **Core Collection** - 9 curated datasets (pedagogical use)

## Directory Structure Changes

### Before
```
output/
├── forms.csv
├── languages.csv
├── parameters.csv
├── metadata.csv
├── sources.bib
└── validation_report.json
```

### After
```
output/
├── full/
│   ├── forms.csv
│   ├── languages.csv
│   ├── parameters.csv
│   ├── metadata.csv
│   ├── sources.bib
│   └── validation_report.json
└── core/
    ├── forms.csv
    ├── languages.csv
    ├── parameters.csv
    ├── metadata.csv
    ├── sources.bib
    └── validation_report.json
```

## Breaking Changes

### 1. Output File Paths

**Old:**
```python
import pandas as pd
forms = pd.read_csv('output/forms.csv')
```

**New:**
```python
import pandas as pd
# For full collection:
forms = pd.read_csv('output/full/forms.csv')

# For core collection:
forms = pd.read_csv('output/core/forms.csv')
```

### 2. Script Behavior

**Old:**
```bash
# Merge script produced single output
python merge_cldf_datasets.py
```

**New:**
```bash
# Merge script produces BOTH collections
python merge_cldf_datasets.py
# Writes to both output/full/ and output/core/
```

### 3. Release Archives

**Old:**
```
releases/arcaverborum_YYYYMMDD.zip
```

**New:**
```
releases/arcaverborum_YYYYMMDD.zip       # Full collection
releases/arcaverborum_core_YYYYMMDD.zip  # Core collection
```

## Updated Workflows

### Quick Start (Core Collection)

For teaching or rapid prototyping:

```bash
# Clone only core datasets (faster)
python clone_lexibank.py --core-only

# Build both collections (core will be complete, full will be partial)
python merge_cldf_datasets.py

# Use core collection data
python your_analysis.py --input output/core/forms.csv
```

### Full Research Workflow

For comprehensive analysis:

```bash
# Clone all datasets
python clone_lexibank.py

# Build both collections
python merge_cldf_datasets.py

# Use full collection data
python your_analysis.py --input output/full/forms.csv
```

### Release Workflow

```bash
# Clone all datasets
python clone_lexibank.py

# Build both collections
python merge_cldf_datasets.py

# Prepare both release archives
python prepare_release.py

# This creates:
#   - releases/arcaverborum_YYYYMMDD.zip (full)
#   - releases/arcaverborum_core_YYYYMMDD.zip (core)

# Publish to Zenodo (uploads both archives)
python zenodo_publish.py
```

## Core Collection Datasets

The core collection includes these 9 datasets:

1. **robinsonap** - Papunesia (Austronesian and Papuan)
2. **bowernpny** - Australia (Pama-Nyungan)
3. **gravinachadic** - Africa (Chadic)
4. **grollemundbantu** - Africa (Bantu)
5. **peirosaustroasiatic** - Eurasia (Austroasiatic)
6. **iecor** - Eurasia (Indo-European)
7. **bdpa** - Eurasia (Sino-Tibetan and others, with alignments)
8. **tuled** - South America (Tupían, with alignments)
9. **utoaztecan** - North America (Uto-Aztecan)

### Selection Criteria

Core datasets were selected for:
- **Geographic coverage:** All 6 macroareas represented
- **Concepticon coverage:** ≥75% Swadesh-100 where possible
- **Expert cognate sets:** All include manual cognate judgments
- **Minimal overlap:** Different language families per macroarea
- **Data quality:** Comprehensive metadata and segmentation

## Script Reference

### clone_lexibank.py

**New flag:**
```bash
--core-only   # Clone only the 9 core datasets
```

**Examples:**
```bash
# Clone only core datasets (fast setup)
python clone_lexibank.py --core-only

# Clone all datasets (research use)
python clone_lexibank.py

# Dry-run to see what would be cloned
python clone_lexibank.py --core-only --dry-run
```

### merge_cldf_datasets.py

**Behavior:**
- Always builds BOTH collections in a single run
- Processes each dataset once, filters on write
- No command-line flags needed

**Output:**
- `output/full/` - Full collection (all datasets in lexibank/)
- `output/core/` - Core collection (filtered to 9 core datasets)
- Separate validation reports for each collection

### prepare_release.py

**Behavior:**
- Always creates BOTH archives
- Generates separate documentation for each collection
- Updates zenodo.metadata.yml with both archives

**Output:**
- `releases/arcaverborum_YYYYMMDD.zip` - Full collection archive
- `releases/arcaverborum_core_YYYYMMDD.zip` - Core collection archive

## Updating Existing Code

### Python Scripts

**Before:**
```python
OUTPUT_DIR = Path('output')
forms = pd.read_csv(OUTPUT_DIR / 'forms.csv')
```

**After:**
```python
OUTPUT_DIR = Path('output')
# Choose collection:
COLLECTION = 'full'  # or 'core'
forms = pd.read_csv(OUTPUT_DIR / COLLECTION / 'forms.csv')
```

### R Scripts

**Before:**
```r
forms <- read.csv('output/forms.csv')
```

**After:**
```r
# Choose collection:
collection <- 'full'  # or 'core'
forms <- read.csv(file.path('output', collection, 'forms.csv'))
```

### Make/Shell Scripts

**Before:**
```bash
FORMS=output/forms.csv
```

**After:**
```bash
COLLECTION=${COLLECTION:-full}  # Default to full
FORMS=output/${COLLECTION}/forms.csv
```

## FAQ

**Q: Can I still work with the old single output/ directory structure?**
A: No, the new structure is required. Update your paths to use `output/full/` or `output/core/`.

**Q: Do I need to clone all datasets to use the core collection?**
A: No! Use `python clone_lexibank.py --core-only` for faster setup.

**Q: Will the merge script process datasets twice (once for each collection)?**
A: No, it processes each dataset once and filters on write for efficiency.

**Q: Can I build only one collection?**
A: No, the merge script always builds both. If you only cloned core datasets with `--core-only`, the full collection will only contain those 9 datasets.

**Q: How do I know which collection to use?**
A:
- **Use core** for: teaching, learning, prototyping, smaller memory footprint
- **Use full** for: comprehensive research, maximum language coverage

**Q: Can I add/remove datasets from the core collection?**
A: Yes, edit `datasets.csv` and set `CORE=TRUE` for your desired datasets.

## Backward Compatibility

This is a **breaking change**. There is no backward compatibility mode. You must update file paths in all scripts and workflows.

## Migration Checklist

- [ ] Update all hardcoded `output/` paths to `output/full/` or `output/core/`
- [ ] Review scripts for path assumptions (grep for `output/`)
- [ ] Update documentation and README files
- [ ] Test workflows with new directory structure
- [ ] Update CI/CD pipelines if applicable
- [ ] Inform collaborators about the changes

## Support

If you encounter issues during migration:
1. Check this guide for common patterns
2. Review example workflows in README.md
3. Open an issue: https://github.com/tresoldi/arcaverborum/issues
