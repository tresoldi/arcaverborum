# CORECOG Collection Implementation Plan

## Current State Analysis

**datasets.csv structure:**
- **CORECOG only:** 46 datasets (cognate-focused, not in pedagogical core)
- **CORE only:** 1 dataset (grollemundbantu - in pedagogical core but not corecog)
- **Both CORECOG and CORE:** 12 datasets (overlap)
- **Total CORECOG:** 58 datasets
- **Total CORE:** 13 datasets

**Current system:**
- Two collections: `full` (149 datasets) and `core` (13 datasets)
- Output structure: `output/full/` and `output/core/`
- Documentation moved to `docs/` directory
- README.md references "Two collections"

## Proposed: Three-Collection System

Add **CORECOG** as a third collection alongside full and core:

1. **Full** - All 149 datasets (unchanged)
2. **Core** - 13 curated datasets for teaching (unchanged)
3. **CORECOG** - 58 datasets with expert cognate judgments (NEW)

## Implementation Questions

### Q1: Directory Structure

How should we organize the three output directories?

**Option A: Flat structure (current pattern)**
```
output/
├── full/
├── core/
└── corecog/     # NEW
```

**Option B: Hierarchical structure**
```
output/
├── full/
└── collections/
    ├── core/
    └── corecog/
```

**Pros/Cons:**
- **Option A (Flat):**
  - ✅ Consistent with current structure
  - ✅ Simple, no breaking changes for full/core
  - ✅ Equal treatment of all collections
  - ❌ Could get crowded if more collections added later

- **Option B (Hierarchical):**
  - ✅ Clear separation: full vs specialized collections
  - ✅ Scalable for future collections
  - ❌ Breaking change for existing core collection paths
  - ❌ More complex

**My recommendation:** Option A (Flat) - maintains consistency, no breaking changes

### Q2: Build Strategy

How should merge_cldf_datasets.py handle three collections?

**Option A: Always build all three**
```python
# Single pass through all datasets
# Filter and write to: full/, core/, corecog/
```
- ✅ Consistent with current behavior (builds both full+core)
- ✅ Simple for users (no flags needed)
- ❌ Always processes all data even if only one collection needed

**Option B: Optional flags to select collections**
```bash
python merge_cldf_datasets.py                  # All three
python merge_cldf_datasets.py --only full      # Just full
python merge_cldf_datasets.py --only core,corecog  # Specific collections
```
- ✅ Flexible for testing/development
- ✅ Faster when only specific collection needed
- ❌ More complex command-line interface
- ❌ Breaking change (current script has no collection flags)

**My recommendation:** Option A - maintain "always build all" approach for simplicity

### Q3: Clone Script Flags

Should clone_lexibank.py support --corecog-only?

**Option A: Add --corecog-only flag**
```bash
python clone_lexibank.py --core-only      # 13 datasets
python clone_lexibank.py --corecog-only   # 58 datasets
```
- ✅ Consistent with existing --core-only
- ✅ Useful for testing CORECOG collection
- ❌ Three separate flags could be confusing

**Option B: Add --collection flag**
```bash
python clone_lexibank.py --collection core      # 13 datasets
python clone_lexibank.py --collection corecog   # 58 datasets
python clone_lexibank.py --collection core,corecog  # Combined
```
- ✅ More scalable (one flag for all collections)
- ✅ Supports multiple collections at once
- ❌ Breaking change (removes --core-only flag)

**Option C: Keep --core-only, add --corecog-only**
- ✅ Backward compatible
- ✅ Simple to understand
- ❌ Less scalable

**My recommendation:** Option C - backward compatible, simple

### Q4: Release Archives

How should prepare_release.py handle three collections?

**Option A: Three separate archives**
```
releases/
├── arcaverborum_YYYYMMDD.zip           # Full (149 datasets)
├── arcaverborum_core_YYYYMMDD.zip      # Core (13 datasets)
└── arcaverborum_corecog_YYYYMMDD.zip   # CORECOG (58 datasets)
```
- ✅ Users download only what they need
- ✅ Smaller downloads (core: ~6MB, corecog: ~30MB estimate)
- ✅ Consistent with current two-archive approach
- ❌ Three files to manage per release

**Option B: Two archives (full + combined collection)**
```
releases/
├── arcaverborum_YYYYMMDD.zip              # Full
└── arcaverborum_collections_YYYYMMDD.zip  # Both core + corecog
```
- ✅ Simpler (only 2 files)
- ❌ Users who want only core get corecog too
- ❌ Breaks existing core-only downloads

**My recommendation:** Option A - three separate archives for user choice

### Q5: Zenodo Upload Strategy

How should Zenodo releases handle three archives?

**Option A: Single Zenodo record with three files**
```
Zenodo Record (one DOI):
├── arcaverborum_YYYYMMDD.zip
├── arcaverborum_core_YYYYMMDD.zip
└── arcaverborum_corecog_YYYYMMDD.zip
```
- ✅ One DOI for entire project
- ✅ Consistent with current approach
- ✅ Users choose which file to download
- ❌ All three count toward same download stats

**Option B: Separate Zenodo records**
```
Arca Verborum Full (DOI 1)
Arca Verborum Core (DOI 2)
Arca Verborum CORECOG (DOI 3)
```
- ✅ Separate DOIs for each collection
- ✅ Independent download stats
- ❌ More complex to maintain
- ❌ Users need to know which DOI to cite

**My recommendation:** Option A - single record, maintains project unity

### Q6: Documentation Updates

What needs updating in README.md?

**Required changes:**
1. Update "Two collections" → "Three collections"
2. Add CORECOG section describing:
   - 58 datasets with expert cognate judgments
   - Purpose: cognate detection, phylogenetic analysis
   - Link to download
3. Update download section with third archive
4. Update quick start examples (should mention all three)

**Question: How prominent should CORECOG be?**

**Option A: Equal prominence**
```markdown
## Collections

### Full Collection
- 149 datasets...

### Core Collection
- 13 datasets for teaching...

### CORECOG Collection
- 58 datasets for cognate analysis...
```

**Option B: Grouped by use case**
```markdown
## Collections

### For Research
- **Full** - All 149 datasets
- **CORECOG** - 58 datasets with cognate sets

### For Teaching
- **Core** - 13 curated datasets
```

**My recommendation:** Option A - equal prominence, clear structure

### Q7: Template Updates

How should DATASET_DESCRIPTION.md.j2 template handle three collections?

**Current:** Template uses `if collection == "core"` conditionals

**Option A: Add corecog conditionals**
```jinja
{% if collection == "core" %}
  Core Collection content...
{% elif collection == "corecog" %}
  CORECOG Collection content...
{% else %}
  Full Collection content...
{% endif %}
```

**Option B: Collection metadata dict**
```python
COLLECTION_INFO = {
    'full': {...},
    'core': {...},
    'corecog': {
        'name': 'CORECOG Collection',
        'description': '58 datasets with expert cognate judgments',
        'datasets': 58,
        ...
    }
}
```

**My recommendation:** Option A - simple conditionals, consistent with current approach

### Q8: CORECOG Collection Description

How should we describe the CORECOG collection?

**Purpose:** What is CORECOG for?

**Option A: Cognate detection focus**
- "For developing and testing cognate detection algorithms"
- "58 datasets with expert-curated cognate judgments"
- Emphasize methodological use

**Option B: Phylogenetic/historical linguistics focus**
- "For phylogenetic inference and historical linguistics"
- "58 datasets with complete cognate information"
- Emphasize research applications

**Option C: Comprehensive research focus**
- "For comprehensive cognate-based research"
- "58 high-quality datasets with expert cognacy"
- Broader appeal

**My recommendation:** Option C - broader appeal, includes both methodological and research uses

**Selection criteria to highlight:**
- All datasets have expert cognate judgments (CORECOG column in datasets.csv)
- Overlap with pedagogical core (12 datasets in both)
- Larger than core but smaller than full (middle ground)

### Q9: Backward Compatibility

Should we maintain any compatibility?

**Current situation:**
- Users may have scripts using `output/full/` and `output/core/`
- README already says "Two collections"

**Option A: Full backward compatibility**
- Keep output/full/ and output/core/ unchanged
- Add output/corecog/ as third directory
- No breaking changes

**Option B: Clean break with migration notice**
- Reorganize all three collections
- Add migration guide in docs/
- Update version to 2.0.0

**My recommendation:** Option A - adding corecog/ doesn't break anything existing

### Q10: Testing Strategy

How to test with 58 datasets?

**Option A: Use --corecog-only flag for testing**
```bash
python clone_lexibank.py --corecog-only  # Just 58
python merge_cldf_datasets.py             # Builds all three
```
- ✅ Faster than full 149 datasets
- ✅ Tests corecog-specific functionality
- ❌ Still processes 58 datasets (slower than core's 13)

**Option B: Test with full dataset**
```bash
python clone_lexibank.py                  # All 149
python merge_cldf_datasets.py             # Should work
```
- ✅ Complete test
- ❌ Slow (all 149 datasets)

**My recommendation:** Option A for development/testing, Option B before release

## Proposed Implementation Order

1. **Update datasets.csv** ✅ (Already done by user)

2. **Update merge_cldf_datasets.py**
   - Add `OUTPUT_DIR_CORECOG = OUTPUT_DIR / 'corecog'`
   - Update `load_core_datasets()` to also load CORECOG datasets
   - Add third ValidationAccumulator for corecog
   - Write to three directories in main loop

3. **Update clone_lexibank.py**
   - Add `--corecog-only` flag (backward compatible)
   - Update help text to mention three collections

4. **Update prepare_release.py**
   - Process corecog collection (validation report, stats)
   - Create third archive: `arcaverborum_corecog_YYYYMMDD.zip`
   - Update zenodo.metadata.yml with three files
   - Update state tracking for three archives

5. **Update templates/DATASET_DESCRIPTION.md.j2**
   - Add `{% elif collection == "corecog" %}` section
   - Describe CORECOG selection criteria
   - List all 58 datasets or summarize by family

6. **Update README.md**
   - Change "Two collections" to "Three collections"
   - Add CORECOG section
   - Add download link (placeholder DOI)
   - Update statistics

7. **Update docs/RELEASE_WORKFLOW.md**
   - Mention three collections in workflow
   - Update commands/output examples
   - Update file structure diagram

8. **Update docs/MERGER_SPECIFICATION.md** (if needed)
   - Document three-collection architecture
   - Update examples

## Summary of Recommendations

| Question | Recommendation | Rationale |
|----------|---------------|-----------|
| Q1: Directory structure | Flat (output/full/core/corecog/) | Consistent, no breaking changes |
| Q2: Build strategy | Always build all three | Simple, consistent with current |
| Q3: Clone flags | Add --corecog-only flag | Backward compatible |
| Q4: Archives | Three separate archives | User choice, flexible |
| Q5: Zenodo | Single record, three files | Project unity, one DOI |
| Q6: README prominence | Equal prominence | Clear structure |
| Q7: Template strategy | Conditional blocks | Simple, consistent |
| Q8: CORECOG description | Comprehensive research focus | Broad appeal |
| Q9: Compatibility | Full backward compatibility | No breaking changes |
| Q10: Testing | --corecog-only for dev | Fast iteration |

## Estimated Impact

**Code changes:**
- merge_cldf_datasets.py: ~50 lines (add third collection logic)
- clone_lexibank.py: ~20 lines (add --corecog-only flag)
- prepare_release.py: ~100 lines (process third collection)
- templates/DATASET_DESCRIPTION.md.j2: ~30 lines (corecog section)

**Documentation changes:**
- README.md: ~50 lines (three collections section)
- docs/RELEASE_WORKFLOW.md: ~20 lines (update examples)
- docs/MERGER_SPECIFICATION.md: ~20 lines (if needed)

**Total:** ~290 lines of changes across 6 files

**No breaking changes** - fully backward compatible
