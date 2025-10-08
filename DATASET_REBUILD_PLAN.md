# Dataset Rebuild Plan

## Current Problem

**Issue:** Only 9 datasets are cloned in `lexibank/`, causing incorrect statistics:
- Full collection shows 9 datasets instead of 149
- Core collection shows 9 datasets instead of 13 (missing 4)
- CoreCog collection shows 8 datasets instead of 58 (missing 50)
- Full and Core have identical statistics because they're both processing the same 9 datasets

**Currently cloned (9 datasets):**
- bdpa, bowernpny, gravinachadic, grollemundbantu, iecor, peirosaustroasiatic, robinsonap, tuled, utoaztecan

## Expected State

**datasets.csv contains:**
- **Total:** 149 datasets
- **CORE:** 13 datasets (marked with CORE=TRUE)
- **CoreCog:** 58 datasets (marked with CoreCog=TRUE)
- **Overlap:** 12 datasets in both CORE and CoreCog

**Expected collections:**
- **Full:** All 149 datasets (~2.9M forms, 6,000+ languages)
- **Core:** 13 curated datasets for teaching
- **CoreCog:** 58 datasets with expert cognate judgments

## Resource Estimates

**Current usage:**
- 9 datasets in lexibank/ = 163MB
- Output from 9 datasets = 131MB

**Estimated for 149 datasets:**
- lexibank/ ≈ 2.7GB (~18MB per dataset × 149)
- output/ ≈ 2.2GB (proportional to data)
- **Total needed:** ~5GB

**Available:** 9.7GB ✓ (sufficient)

## Implementation Plan

### Phase 1: Clone All Datasets
**Action:** Clone all 149 Lexibank datasets from GitHub

**Command:**
```bash
python clone_lexibank.py
```

**Time estimate:** 30-60 minutes (149 git clones)
**Disk usage:** +2.5GB

**Verification:**
```bash
ls -d lexibank/*/ | wc -l  # Should show 149
```

### Phase 2: Rebuild All Collections
**Action:** Run merge script to process all 149 datasets into 3 collections

**Command:**
```bash
python merge_cldf_datasets.py
```

**Time estimate:** 10-30 minutes (processing 149 datasets)
**Disk usage:** +2GB for output files

**What it does:**
1. Reads all 149 datasets from lexibank/
2. Filters into 3 collections based on CSV columns:
   - Full: All 149 datasets
   - Core: 13 datasets where CORE=TRUE
   - CoreCog: 58 datasets where CoreCog=TRUE
3. Writes to output/full/, output/core/, output/corecog/
4. Generates validation reports with statistics

**Verification:**
```bash
# Check validation reports
python3 -c "import json; print('Full:', json.load(open('output/full/validation_report.json'))['summary']['total_datasets'])"
python3 -c "import json; print('Core:', json.load(open('output/core/validation_report.json'))['summary']['total_datasets'])"
python3 -c "import json; print('CoreCog:', json.load(open('output/corecog/validation_report.json'))['summary']['total_datasets'])"
```

Should show:
- Full: 149 datasets
- Core: 13 datasets
- CoreCog: 58 datasets

### Phase 3: Regenerate Website
**Action:** Run prepare_release.py to build website with correct statistics

**Command:**
```bash
python prepare_release.py --force
```

**Time estimate:** 1-2 minutes
**Disk usage:** +10MB for archives

**What it does:**
1. Loads statistics from all 3 validation reports
2. Generates website (docs/index.html) with correct numbers
3. Creates release archives (for distribution)

**Verification:**
```bash
grep -E "(149|13|58)" docs/index.html
```

Should show correct dataset counts in the table.

### Phase 4: Commit and Push
**Action:** Commit regenerated output and website

**Files changed:**
- docs/index.html (updated statistics)
- .zenodo_state.json (updated state)
- zenodo.metadata.yml (updated)

**Command:**
```bash
git add docs/index.html .zenodo_state.json zenodo.metadata.yml
git commit -m "Regenerate website with correct statistics (149/13/58 datasets)"
git push origin master
```

## Questions for User

### Q1: Dataset Cloning Strategy
Which datasets should I clone?

**Options:**
- **A) All 149 datasets** (recommended for production)
  - Pros: Complete, accurate statistics, ready for release
  - Cons: ~60 minutes clone time, 2.7GB disk usage
  - Use: `python clone_lexibank.py`

- **B) Only Core + CoreCog (67 unique datasets)**
  - Pros: Faster (~20 min), less disk (1.2GB)
  - Cons: Full collection will be incomplete
  - Use: Clone core first, then corecog, merge outputs

- **C) Keep current 9, fix separately**
  - Pros: Quick fix for testing
  - Cons: Still incomplete, not production-ready

**Recommendation:** Option A (clone all 149)

### Q2: Timing
When should I run this?

**Options:**
- **A) Now (immediately)**
  - 60-90 minutes total for all phases
  - Can run in background while you work

- **B) Later (you decide when)**
  - I can prepare commands/scripts for you to run
  - You control timing

**Recommendation:** Option A if you have time, or I can run and report progress

### Q3: Cleanup
Should I clean up old data first?

**Options:**
- **A) Clean clone (remove lexibank/, output/, releases/)**
  - Pros: Fresh start, no conflicts
  - Cons: Deletes current data
  - Command: `rm -rf lexibank output releases`

- **B) Incremental (keep existing, add missing)**
  - Pros: Reuses what we have
  - Cons: Might have stale data
  - Command: clone_lexibank.py will update existing

**Recommendation:** Option B (incremental) - clone script handles updates

### Q4: Validation
How should I verify success?

**Options:**
- **A) Automated tests**
  - Run validation checks after each phase
  - Report any discrepancies

- **B) Manual review**
  - You review outputs at each step
  - I wait for confirmation to proceed

**Recommendation:** Option A (automated with summary report)

## Summary

**Recommended execution:**
1. Clone all 149 datasets (`python clone_lexibank.py`)
2. Rebuild collections (`python merge_cldf_datasets.py`)
3. Regenerate website (`python prepare_release.py --force`)
4. Verify statistics and commit

**Total time:** 60-90 minutes
**Disk usage:** +5GB
**Result:** Correct statistics (149/13/58) across all collections and website
