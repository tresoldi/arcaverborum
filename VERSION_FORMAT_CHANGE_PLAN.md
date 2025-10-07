# Version Format Change Implementation Plan

## Current State Analysis

### Current Version Format: `YYYYMMDD`
Example: `20251002` (October 2, 2025)

### Proposed Version Format: `V.YYYYMMDD`
Example: `A.20251002` (Version A, October 2, 2025)

**Where V is:**
- A letter indicating major version/data source type
- Starts with `A` for current Lexibank data
- Future: `B` for Wiktionary data, etc.
- Can have multiple types in release simultaneously

## Current Version Usage

The version string appears in **8 different contexts**:

1. **Archive filenames:**
   - Current: `arcaverborum.20251002.zip`, `arcaverborum.20251002.core.zip`
   - Proposed: `arcaverborum.A.20251002.zip`, `arcaverborum.A.20251002.core.zip`

2. **Archive internal directory names:**
   - Current: `arcaverborum.20251002/`, `arcaverborum.20251002.core/`
   - Proposed: `arcaverborum.A.20251002/`, `arcaverborum.A.20251002.core/`

3. **Git tags:**
   - Current: `v20251002`
   - Proposed: `vA.20251002` or `A.20251002`

4. **State file (`.zenodo_state.json`) keys:**
   ```json
   {
     "last_version": "20251002",
     "releases": {
       "20251002": { ... }
     }
   }
   ```
   - Proposed: `"A.20251002"` as keys

5. **Zenodo metadata version field:**
   - Current: `version: "20251002"`
   - Proposed: `version: "A.20251002"`

6. **Website display:**
   - Current: "Current version: 20251002"
   - Proposed: "Current version: A.20251002"

7. **Documentation templates:**
   - Current: "Version 20251002" in DATASET_DESCRIPTION.md
   - Proposed: "Version A.20251002"

8. **Code examples in templates:**
   - Current: `arcaverborum_20251002/forms.csv`
   - Proposed: `arcaverborum_A.20251002/forms.csv`

## Implementation Questions

### Q1: Version Generation Logic

**How should the major version letter be determined?**

**Option A: Hardcoded constant**
```python
MAJOR_VERSION = "A"
version = f"{MAJOR_VERSION}.{datetime.datetime.now().strftime('%Y%m%d')}"
```
- ✅ Simple, explicit
- ✅ Easy to change (edit constant)
- ❌ Need to remember to update manually for B, C, etc.

**Option B: Configuration file**
```yaml
# config.yml
current_major_version: A
```
- ✅ Centralized configuration
- ✅ Can document reasoning
- ❌ Extra file to manage
- ❌ More complex

**Option C: Command-line argument**
```bash
python prepare_release.py --major-version A
```
- ✅ Explicit per release
- ✅ Flexible
- ❌ Easy to forget/mistype
- ❌ Breaking change to CLI

**Option D: Hybrid (constant with CLI override)**
```python
MAJOR_VERSION = "A"  # Default
# Allow: python prepare_release.py --major-version B
```
- ✅ Safe default
- ✅ Override when needed
- ✅ Backward compatible (default)
- ❌ Slightly more complex

**My recommendation:** **Option A (Hardcoded constant)** - Simple and explicit. When moving to B, you make a conscious decision to update the constant. For multi-version releases (A and B simultaneously), we can revisit.

### Q2: Git Tag Format

**What should git tags look like?**

**Option A: `vV.YYYYMMDD`**
```
vA.20251002
vB.20251003
```
- ✅ Follows semantic versioning convention (`v` prefix)
- ✅ Sortable if same date
- ❌ Slightly longer

**Option B: `V.YYYYMMDD` (no `v` prefix)**
```
A.20251002
B.20251003
```
- ✅ Cleaner
- ✅ Matches version string exactly
- ❌ Breaks convention (most tags start with `v`)

**Option C: `v-V-YYYYMMDD`**
```
v-A-20251002
```
- ❌ More complex
- ❌ Less readable

**My recommendation:** **Option A (`vV.YYYYMMDD`)** - Maintains git convention of `v` prefix while being clear and sortable.

### Q3: Archive Naming

**How should archive names change?**

**Current:** `arcaverborum.20251002.zip`

**Option A: Insert major version after project name**
```
arcaverborum.A.20251002.zip
arcaverborum.A.20251002.core.zip
arcaverborum.A.20251002.corecog.zip
```
- ✅ Clear hierarchy: project → version type → date → collection
- ✅ Easy to parse
- ✅ Consistent with current pattern

**Option B: Major version at the end (before collection)**
```
arcaverborum.20251002.A.zip
arcaverborum.20251002.A.core.zip
```
- ❌ Awkward placement
- ❌ Less intuitive

**Option C: Major version prefix**
```
A-arcaverborum.20251002.zip
```
- ❌ Breaks alphabetical sorting
- ❌ Inconsistent with current pattern

**My recommendation:** **Option A** - Natural extension of current format, maintains readability.

### Q4: Internal Directory Naming

**What should the directory inside archives be called?**

**Current:** Archive `arcaverborum.20251002.zip` contains `arcaverborum.20251002/`

**Option A: Match archive name (without .zip)**
```
Archive: arcaverborum.A.20251002.zip
Directory: arcaverborum.A.20251002/
```
- ✅ Consistent with current behavior
- ✅ Predictable
- ✅ Easy to reference in docs

**Option B: Remove major version from directory**
```
Archive: arcaverborum.A.20251002.zip
Directory: arcaverborum.20251002/
```
- ❌ Inconsistent
- ❌ Could cause confusion with old releases

**My recommendation:** **Option A** - Maintain consistency between archive and directory names.

### Q5: Backward Compatibility

**How should we handle existing releases?**

**Option A: Keep old format, new format going forward**
```
Existing: 20251001, 20251002
New: A.20251003, A.20251004
```
- ✅ No migration needed
- ✅ Old releases still accessible
- ❌ Mixed formats in history
- ❌ May need special handling in code

**Option B: Migrate state file to interpret old versions as "A"**
```python
# Internally treat "20251002" as "A.20251002"
def normalize_version(v):
    return f"A.{v}" if not v.startswith(tuple("ABCDEFGHIJKLMNOPQRSTUVWXYZ")) else v
```
- ✅ Unified format internally
- ✅ Cleaner code
- ❌ More complex migration

**Option C: Leave old releases as-is, only new code references**
- ✅ Simple
- ✅ No code complexity
- ❌ Inconsistent history

**My recommendation:** **Option A** - Simplest approach. Document the format change, treat old versions as pre-A. Code should handle both formats for reading state, but only generate new format.

### Q6: Version Comparison/Sorting

**How should versions be compared?**

**Scenario:** If we have both A and B releases

**Option A: Sort by date only**
```
A.20251001 < A.20251002 < B.20251002 < A.20251003
(chronological)
```
- ✅ Simple
- ✅ Reflects actual release order
- ❌ Mixed versions

**Option B: Sort by major version first, then date**
```
A.20251001 < A.20251002 < A.20251003 < B.20251002
(grouped by type)
```
- ✅ Logical grouping
- ❌ Doesn't reflect release order

**Option C: Don't compare across major versions**
```
Each letter is separate lineage
A.20251001 < A.20251002
B.20251002 < B.20251003
But A.20251003 ≠ B.20251002 (not comparable)
```
- ✅ Treats them as separate products
- ✅ Clear semantics
- ❌ More complex

**My recommendation:** **Option C** - Treat major versions as separate lineages. When displaying "latest version" on website, show latest of each type if multiple exist.

### Q7: Code Examples in Templates

**How should code examples reference archives?**

**Current template code:**
```python
forms = pd.read_csv('arcaverborum_20251002/forms.csv')
```

**Option A: Use full version string**
```python
forms = pd.read_csv('arcaverborum_A.20251002/forms.csv')
```
- ✅ Accurate
- ❌ Changes with every release
- ❌ Makes examples harder to follow

**Option B: Use placeholder variable**
```python
forms = pd.read_csv('arcaverborum_{{ version }}/forms.csv')
```
- ✅ Already what we do
- ✅ Updates automatically
- ✅ Users substitute actual version

**Option C: Generic placeholder**
```python
forms = pd.read_csv('arcaverborum_VERSION/forms.csv')
```
- ✅ Clear it's a placeholder
- ❌ Deviates from actual format

**My recommendation:** **Option B** - Current approach works well, will automatically include new format.

### Q8: Same-Day Revisions

**Current format supports:** `20251002.1`, `20251002.2`

**How should this work with new format?**

**Option A: After date**
```
A.20251002.1
A.20251002.2
```
- ✅ Logical extension
- ✅ Clear hierarchy: major → date → revision

**Option B: Before date**
```
A.1.20251002
```
- ❌ Confusing (looks like A.1 is a version)
- ❌ Breaks hierarchy

**My recommendation:** **Option A** - Extend after date, maintains hierarchy.

### Q9: Display Format

**How should versions be displayed to users?**

**Option A: As-is**
```
"Current version: A.20251002"
"Arca Verborum v A.20251002"
```
- ✅ Accurate
- ❌ Slightly awkward with "v" prefix

**Option B: With better spacing**
```
"Current version: A (20251002)"
"Arca Verborum A.20251002"
```
- ✅ More readable
- ❌ Inconsistent with internal format

**Option C: Full description**
```
"Current version: Type A, released 2025-10-02"
```
- ✅ Very clear
- ❌ Verbose

**My recommendation:** **Option A** - Use the version string as-is everywhere for consistency. Users will quickly understand "A" refers to data source.

### Q10: Migration Strategy

**How to implement the change?**

**Option A: Big bang (change everything at once)**
- ✅ Clean cut
- ✅ No mixed states
- ❌ Risky
- ❌ Hard to test

**Option B: Phased approach**
1. Phase 1: Update version generation only (prepare_release.py)
2. Phase 2: Update templates and documentation
3. Phase 3: Update website
4. Phase 4: Test full workflow
- ✅ Safer
- ✅ Can test incrementally
- ❌ Takes longer

**Option C: Feature flag**
```python
USE_NEW_VERSION_FORMAT = True  # Toggle while testing
```
- ✅ Can test without commitment
- ✅ Easy rollback
- ❌ Extra complexity

**My recommendation:** **Option B (Phased)** - Update code in logical phases, test at each step. Since all version generation is in one place (prepare_release.py), the change is localized.

## Proposed Implementation Order

### Phase 1: Core Version Generation (~30 min)
1. Add `MAJOR_VERSION = "A"` constant to prepare_release.py
2. Update version generation:
   ```python
   version = f"{MAJOR_VERSION}.{datetime.datetime.now().strftime('%Y%m%d')}"
   ```
3. Update git tag format: `vA.20251002`
4. Update archive naming in `create_archive()`
5. Test with `--dry-run`

### Phase 2: Templates and Documentation (~20 min)
1. Update all template files (no code changes needed, just pass new version)
2. Update RELEASE_WORKFLOW.md documentation
3. Update README.md examples
4. Update WEBSITE_IMPLEMENTATION_PLAN.md

### Phase 3: State File Compatibility (~15 min)
1. Update `load_state()` to handle both old and new formats
2. Ensure old releases still accessible
3. Document migration in code comments

### Phase 4: Testing (~30 min)
1. Run full release workflow with new version format
2. Check all generated files
3. Verify website displays correctly
4. Test archive extraction and directory names

### Phase 5: Documentation Updates (~15 min)
1. Add note about version format change to RELEASE_NOTES template
2. Update VERSION_SCHEME section in RELEASE_WORKFLOW.md
3. Add FAQ about version format

**Total estimated time: ~2 hours**

## Files to Modify

1. **prepare_release.py** (~20 lines)
   - Add MAJOR_VERSION constant
   - Update version generation
   - Update git tag format
   - Backward compatibility in state file loading

2. **docs/RELEASE_WORKFLOW.md** (~15 lines)
   - Update version scheme documentation
   - Update examples

3. **README.md** (~5 lines)
   - Update version references in examples

4. **templates/RELEASE_NOTES.md.j2** (~5 lines)
   - Add note about version format for first A-versioned release

## Testing Checklist

- [ ] Version string generated correctly (A.YYYYMMDD)
- [ ] Archives named correctly
- [ ] Archive internal directories named correctly
- [ ] Git tags created correctly (vA.YYYYMMDD)
- [ ] State file updated with new format
- [ ] Old releases still readable from state file
- [ ] Website displays new version correctly
- [ ] Templates render with new version
- [ ] Code examples use new format
- [ ] Documentation is consistent

## Edge Cases and Considerations

### Edge Case 1: Transition Release
**Problem:** First release with new format

**Solution:** Add note in RELEASE_NOTES explaining format change. No technical issue.

### Edge Case 2: Multiple Major Versions
**Scenario:** We release both A.20251005 (Lexibank) and B.20251005 (Wiktionary) on same day

**Solution:**
- State file can handle multiple major versions as separate keys
- Website should show "Latest releases" with both A and B
- Users choose which data source they want

**Future consideration:** May need website updates to show multiple latest versions clearly.

### Edge Case 3: Rollback
**Problem:** Need to rollback to old version format

**Solution:**
- Comment out `MAJOR_VERSION` constant
- Revert version generation line
- Old code will still work with old format

### Edge Case 4: Sorting
**Problem:** Git tags like `v20251001` vs `vA.20251002` sort oddly

**Solution:** This is cosmetic. Old tags stay as-is, new format going forward. Users use full tag name.

## Summary of Recommendations

| Question | Recommendation | Rationale |
|----------|---------------|-----------|
| Q1: Version generation | Hardcoded constant `MAJOR_VERSION = "A"` | Simple, explicit, easy to change |
| Q2: Git tag format | `vV.YYYYMMDD` (e.g., `vA.20251002`) | Follows git convention |
| Q3: Archive naming | `arcaverborum.A.20251002.{collection}.zip` | Clear hierarchy |
| Q4: Internal directory | Match archive name (no .zip) | Consistency |
| Q5: Backward compat | Keep old format, new going forward | Simple, no migration |
| Q6: Version comparison | Separate lineages per major version | Clear semantics |
| Q7: Code examples | Use `{{ version }}` template variable | Already works |
| Q8: Same-day revisions | `A.20251002.1` | Logical extension |
| Q9: Display format | As-is: "A.20251002" | Consistency |
| Q10: Migration | Phased approach | Safer, testable |

## Questions for User

1. **Do you want the major version letter to be uppercase (A, B, C) or lowercase (a, b, c)?**
   - Recommendation: Uppercase (more visible, clearer)

2. **What should happen when we eventually have B releases? Should we:**
   - Continue releasing A updates alongside B?
   - Deprecate A and only release B?
   - Let users decide which they want?
   - Recommendation: Support both if data sources are complementary

3. **Should the website show multiple "latest versions" if we have both A and B?**
   - Example: "Latest: A.20251010 (Lexibank) | B.20251008 (Wiktionary)"
   - Recommendation: Yes, but we can defer implementation until B exists

4. **For DOI/citation purposes, should major version affect citation?**
   - Different DOI concept per major version?
   - Same concept DOI for all?
   - Recommendation: Same concept DOI (it's still "Arca Verborum")

5. **Any concerns about:**
   - Breaking existing scripts that parse version numbers?
   - Impact on Zenodo version tracking?
   - Git tag conventions?

## Next Steps

Once you approve the recommendations above:
1. I'll implement the changes in phases
2. Test with a dry-run release
3. Generate first A.YYYYMMDD version
4. Update all documentation

Would you like me to proceed with this plan?
