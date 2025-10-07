# CORECOG → CoreCog Rename Review

## Summary

Renaming "CORECOG" to "CoreCog" for better readability and consistency with naming conventions.

## Naming Strategy

| Context | Current | Proposed | Rationale |
|---------|---------|----------|-----------|
| **User-facing display** | CORECOG Collection | CoreCog Collection | More readable, less "shouty" |
| **CSV column header** | CORECOG | CoreCog | Consistency with display name |
| **Python variables** | `corecog` | `corecog` | Keep lowercase (PEP 8) |
| **Directory names** | `corecog/` | `corecog/` | Keep lowercase (Unix convention) |
| **Archive filenames** | `.corecog.zip` | `.corecog.zip` | Keep lowercase (file naming) |
| **CLI flags** | `--corecog-only` | `--corecog-only` | Keep lowercase (CLI convention) |
| **Code string literals** | `"corecog"` | `"corecog"` | Internal identifier |

## Files Requiring Changes

### 1. datasets.csv (1 change)
- **Line 1**: Column header `CORECOG` → `CoreCog`
- **Impact**: Requires code update to read new column name

### 2. Python Scripts (Code reads CSV column)

#### merge_cldf_datasets.py
- **Line ~42**: Update CSV column reference from `'CORECOG'` to `'CoreCog'`
- **User-facing output**: Change "CORECOG COLLECTION SUMMARY" → "CoreCog Collection Summary"
- **Variable names**: Keep as `corecog_datasets`, `output_dir_corecog` (lowercase)

#### prepare_release.py
- **User-facing output**:
  - "CORECOG COLLECTION" → "CoreCog Collection"
  - "CORECOG Collection" → "CoreCog Collection"
  - "CORECOG archive created" → "CoreCog archive created"
- **Variable names**: Keep as `stats_corecog`, `OUTPUT_DIR_CORECOG` (constants/vars unchanged)

#### clone_lexibank.py
- **Help text**: "clone only corecog datasets" → "clone only CoreCog datasets"
- **CLI flag**: Keep as `--corecog-only` (CLI convention)
- **Variable names**: Keep as `corecog_only` (lowercase)

### 3. Documentation Files

#### README.md
- **Section headers**: "CORECOG Collection" → "CoreCog Collection"
- **Text references**: All mentions of "CORECOG" → "CoreCog"
- **Archive names**: Keep as `.corecog.zip` (lowercase in code examples)

#### docs/RELEASE_WORKFLOW.md
- **Text references**: "CORECOG collection" → "CoreCog collection"
- **Archive examples**: Keep as `.corecog.zip` (lowercase)
- **Directory paths**: Keep as `output/corecog/` (lowercase)

#### CORECOG_IMPLEMENTATION_PLAN.md
- **All references**: "CORECOG" → "CoreCog" (except in code blocks where lowercase)
- **File might be historical**: Consider renaming file to `CORECOG_IMPLEMENTATION_PLAN.md` (archive)

### 4. Website Templates

#### templates/website/index.html.j2
- **Table header**: "CORECOG" → "CoreCog"
- **Text**: "CORECOG Collection" → "CoreCog Collection"
- **Variable names**: Keep Jinja2 vars as `corecog_*` (lowercase)

#### templates/DATASET_DESCRIPTION.md.j2
- **Text**: "CORECOG Collection" → "CoreCog Collection"
- **Code checks**: `collection == "corecog"` stays lowercase

#### templates/RELEASE_NOTES.md.j2
- **Text**: Similar updates for display names

## Breaking Changes

### ⚠️ Critical: datasets.csv Column Name
Changing the CSV column header from `CORECOG` to `CoreCog` requires updating:
1. `merge_cldf_datasets.py` line ~42: `row.get('CORECOG', '')` → `row.get('CoreCog', '')`
2. Any external tools/scripts that read this CSV

**Recommendation**: Make this change atomically with code changes to avoid breakage.

### 🟢 Non-breaking Changes
- Directory names stay lowercase: `output/corecog/`
- Archive filenames stay lowercase: `.corecog.zip`
- CLI flags stay lowercase: `--corecog-only`
- Python variables stay lowercase: `corecog_datasets`, `OUTPUT_DIR_CORECOG`

## Implementation Steps

1. **datasets.csv**: Change column header `CORECOG` → `CoreCog`
2. **merge_cldf_datasets.py**: Update CSV column reference to `'CoreCog'`
3. **Python scripts**: Update user-facing output messages
4. **Documentation**: Update all markdown files
5. **Website templates**: Update display text
6. **Test**: Run merge_cldf_datasets.py to verify CSV reading works
7. **Commit**: Single atomic commit with all changes

## Estimated Changes
- **1 CSV header change**
- **1 critical code change** (CSV column reference)
- **~50 display text changes** (messages, docs, templates)
- **0 variable/function name changes**
- **0 file/directory name changes**

## Risk Assessment

**Low Risk** - Changes are primarily cosmetic display text with one critical CSV column reference that can be tested immediately.

## Questions for User

1. ✅ Confirm naming: "CoreCog" (not "Core-Cog" or "Core_Cog")
2. ✅ Keep file/directory names lowercase: `corecog/`, `.corecog.zip`
3. ✅ Keep CLI flags lowercase: `--corecog-only`
4. Do you want to rename `CORECOG_IMPLEMENTATION_PLAN.md` → `CoreCog_IMPLEMENTATION_PLAN.md`?
