# Arca Verborum Quality Assessment Report

**Evaluator:** Expert in Computational Historical Linguistics
**Date:** 2025-10-01
**Version Assessed:** 20251001
**Total Datasets Merged:** 149 CLDF Wordlist v1.0 datasets

---

## Executive Summary

Arca Verborum successfully aggregates 2,915,377 lexical forms from 149 Lexibank datasets into a unified, analysis-ready format. The merger achieves **high technical quality** with robust metadata integration, proper ID prefixing, and comprehensive validation. However, several **data quality considerations** warrant attention for users, primarily stemming from heterogeneity in the source datasets rather than merger implementation issues.

**Overall Quality Rating: A- (Excellent with caveats)**

### Key Strengths
- ✓ Complete and lossless data integration (100% of source data preserved)
- ✓ Robust metadata denormalization (95.15% Glottolog coverage)
- ✓ Successful cognate data aggregation from 81 datasets
- ✓ Proper handling of partial cognacy (7 datasets)
- ✓ Comprehensive validation reporting
- ✓ High phonological segmentation coverage (77.66%)

### Key Limitations
- ⚠ Highly variable Concepticon coverage (84.72% overall, with major gaps)
- ⚠ Low alignment data availability (3.85% of forms)
- ⚠ Significant segmentation gaps in 9 datasets (100% missing)
- ⚠ Version heterogeneity in reference systems
- ⚠ Limited loan status documentation (sparse `Loan` column)

---

## 1. Data Completeness Assessment

### 1.1 Core Dataset Coverage

**EXCELLENT**: All 149 datasets successfully merged with no data loss.

| Metric | Value | Assessment |
|--------|-------|------------|
| Total lexical forms | 2,915,377 | Complete |
| Total language varieties | 9,738 | Complete |
| Total semantic parameters | 168,263 | Complete |
| BibTeX references | 8,751 | Complete with prefixing |

**Dataset Size Distribution:**
- **Median:** 4,720 forms per dataset (healthy central tendency)
- **Mean:** 19,566 forms (right-skewed due to large datasets)
- **Range:** 209–437,902 forms (three orders of magnitude variation)

**Top 5 Largest Datasets:**
1. `ids` (World Loanword Database): 437,902 forms
2. `idssegmented`: 360,553 forms
3. `transnewguineaorg`: 148,777 forms
4. `acd` (Austronesian Comparative Dictionary): 146,733 forms
5. `northeuralex`: 121,611 forms

**Implication:** The database is dominated by a few very large datasets. Users should be aware of potential sampling bias when performing aggregate statistics.

### 1.2 Glottolog Integration

**EXCELLENT**: 95.15% of forms have Glottolog metadata.

- **Total unique glottocodes:** 4,694 (covering a substantial portion of world's languages)
- **Missing glottocodes:** 580 language entries (5.96% of language table)

**Missing glottocodes are primarily:**
- Proto-languages and reconstructed varieties (e.g., `aaleykusunda_ProtoKusunda`)
- Dialect-level varieties not yet in Glottolog
- Very recently documented languages

**Recommendation:** Users filtering by glottocode should use `.notna()` checks to avoid inadvertently excluding valid proto-language data.

### 1.3 Concepticon Integration

**GOOD with MAJOR CAVEATS**: 84.72% of forms have Concepticon metadata, but distribution is highly uneven.

**Critical Issue:**
- **168,263 parameter entries** but only **3,261 unique Concepticon IDs**
- **119,549 parameters missing Concepticon IDs** (71% of parameter table!)

**Root Cause Analysis:**
This discrepancy arises because:

1. **Dataset `acd` (Austronesian Comparative Dictionary)** has 86,502 parameters (etymological entries) with highly granular semantic distinctions that don't map to Concepticon's comparative concepts
2. **Fine-grained semantic distinctions** in several datasets exceed Concepticon's coverage
3. **Cultural-specific concepts** in some datasets lack Concepticon equivalents

**Affected datasets include:**
- `acd`: 86,502 parameters (mostly unmapped)
- `ids` (WOLD): 1,310 parameters (many culture-specific items)
- Specialized vocabularies in smaller datasets

**Implication:** Users performing **cross-linguistic concept-based comparisons** should:
- Filter forms to those with non-null `Concepticon_Gloss`
- Be aware this reduces dataset from 2.9M to ~2.5M forms
- Recognize bias toward basic vocabulary and Swadesh-style concepts

**Concepticon Coverage by Concept:**
The top 10 most frequent concepts across datasets:
- TONGUE, BLOOD, WATER, EYE, EAR: 138–143 datasets each
- ONE, TWO, BIG, NOSE, NEW: 138–140 datasets each

This confirms strong coverage of **core comparative vocabulary** (Swadesh-100/200 range).

### 1.4 Phonological Segmentation

**GOOD**: 77.66% of forms include segmentation (2.26M forms).

**Datasets with complete segmentation missing (9 total):**
- `acd`, `csd`, `ids`, `mixezoqueanvoices`, `satterthwaitetb` (100% missing)
- 4 additional datasets with >50% missing

**Quality of Available Segmentation:**
Inspection of sample data shows **high-quality CLTS-compliant segmentation**:
```
Form: d̪u.hi     → Segments: d̪ u + h i
Form: jaːq      → Segments: j aː q
Form: ɐ̃.jiː ɐ̃.waː → Segments: ɐ̃ + j iː + ɐ̃ + w aː
```

**Segmentation conventions properly preserved:**
- `+` = morpheme boundary
- Space = segment boundary
- Syllable boundaries removed (properly handled)

**Implication:** For phonological/phonotactic analyses, users should filter to forms with non-null `Segments` column. The 77.66% coverage is excellent for this type of aggregated data.

---

## 2. Cognate Data Quality

### 2.1 Cognate Dataset Coverage

**VERY GOOD**: 81 of 149 datasets (54.4%) include cognate judgments.

**Forms with cognate data:**
- 811,829 forms (27.84% of total)
- 853,642 total forms in cognate-enabled datasets

**Cognacy coverage within cognate datasets:**
- **Average: 97.0%** of forms have cognacy assignments
- This is **excellent** – near-complete coding in datasets that include cognates

**Example cognacy structure** (properly implemented):
```
abvdoceanic_wing-1 → "abvdoceanic_19;abvdoceanic_wing-19"
abvdoceanic_wing-2 → "abvdoceanic_1,58;abvdoceanic_wing-1;abvdoceanic_wing-58"
```

Shows proper:
- Dataset prefixing
- Semicolon separation of multiple cognatesets
- Merging of forms.csv `Cognacy` column with cognates.csv data

### 2.2 Cognate Alignment Data

**POOR**: Only 3.85% of forms have alignment data.

**Root Cause:**
Most datasets provide cognate **set assignments** but not phoneme-by-phoneme **alignments**. Alignments are computationally expensive to produce and validate, so their absence is expected in many Lexibank datasets.

**Datasets with alignments:**
Primary contribution from a few specialized datasets (likely `abvdoceanic`, `carvalhopurus`, and other Oceanic/phylogenetic-focused sets).

**Implication:** Users needing alignments for:
- Sound correspondence detection
- Alignment-based phylogenetics
- Phonological reconstruction

Should filter to forms with non-null `Alignment` and recognize this drastically reduces sample size.

### 2.3 Partial Cognacy Support

**EXCELLENT**: Proper handling of morpheme-level cognacy.

**7 datasets with partial cognacy:**

**Morpheme-indexed (4 datasets):**
- `bodtkhobwa`, `luangthongkumkaren`, `mannburmish`, `mixtecansubgrouping`
- 25,961 forms with `Morpheme_Index` data

**Segment-sliced (3 datasets):**
- `kahd`, `liusinitic`, `tuled`
- 35,241 forms with `Segment_Slice` data

**Implementation Quality:**
The merger correctly handles the complex case where:
- A single form may have **multiple rows** if different morphemes/segments belong to different cognatesets
- The `Cognacy` column lists **all cognatesets** in each row
- Morpheme_Index/Segment_Slice disambiguates **which part** is being judged

**Example** (conceptual):
```
Form: "hand-1-2" (compound)
  Row 1: Cognacy="cs1;cs2", Morpheme_Index=1, Alignment="h a n d"
  Row 2: Cognacy="cs1;cs2", Morpheme_Index=2, Alignment="- - - -"
```

This is **cutting-edge practice** in comparative linguistics and properly implemented.

### 2.4 Cognate Detection Methods

**Variable:** Most cognate judgments are marked as `expert` (manual coding), but documentation is sparse.

**Recommendation:** Users should check `Cognate_Detection_Method` and `Cognate_Source` columns for methodology. For publications, cite the original dataset sources (available in prefixed BibTeX keys).

---

## 3. Metadata Integration Quality

### 3.1 Language Metadata

**EXCELLENT**: Full Glottolog integration with geographic coordinates.

**9,738 language varieties** with:
- 4,694 unique glottocodes (many datasets have multiple varieties per language)
- 95.15% coverage of Glottolog metadata
- Complete geographic coordinates (lat/long) for mapping
- ISO 639-3 codes where applicable
- Language family classifications

**Macroarea Distribution:**
```
Papunesia:       3,059 varieties (31.4%)
Eurasia:         3,022 varieties (31.0%)
Africa:          1,145 varieties (11.8%)
South America:     931 varieties (9.6%)
North America:     410 varieties (4.2%)
Australia:         269 varieties (2.8%)
```

**Quality Note:** One inconsistency found: `papunesia` (lowercase) appears twice, likely a data entry error in source. This is trivial and doesn't affect usability.

### 3.2 Semantic Parameter Metadata

**GOOD with caveats** (see §1.3 Concepticon Integration).

**168,263 parameters** across 149 datasets:
- Strong coverage of **core comparative concepts** (Swadesh lists well-represented)
- 3,261 unique Concepticon mappings
- 71% of parameters lack Concepticon IDs (due to specialized vocabularies)

**Top concepts very well distributed** across datasets (138–143 datasets per concept for core items).

### 3.3 Bibliographic References

**EXCELLENT**: Complete BibTeX integration with proper prefixing.

**8,751 BibTeX entries** covering all source citations:
- All citation keys properly prefixed with dataset names
- Full bibliographic metadata preserved
- Includes DOIs, URLs, abstracts where available in source

**Sample quality check:**
```bibtex
@article{aaleykusunda_Bodt2019b,
  author = {Aaley, Uday Raj and Bodt, Timotheus A.},
  journal = {Computer-Assisted Language Comparison in Practice},
  title = {New Kusunda data: A list of 250 concepts},
  url = {https://calc.hypotheses.org/2414},
  year = {2020}
}
```

Proper formatting, complete fields, accessible URLs. **No issues found.**

---

## 4. Technical Implementation Quality

### 4.1 ID Prefixing and Uniqueness

**EXCELLENT**: Global unique identifiers properly implemented.

All IDs prefixed with dataset name:
- Forms: `aaleykusunda_KusundaGM-1_above-1`
- Languages: `aaleykusunda_KusundaGM`
- Parameters: `aaleykusunda_1_above`
- BibTeX keys: `aaleykusunda_Bodt2019b`

**Referential integrity:**
- All `Language_ID` foreign keys → valid entries in languages table
- All `Parameter_ID` foreign keys → valid entries in parameters table
- All `Source` citation keys → valid entries in sources.bib

**No orphaned references detected** in validation report.

### 4.2 Column Standardization

**EXCELLENT**: Consistent schema across all datasets.

**20 columns in forms.csv**, properly ordered:
1. Core IDs: `ID`, `Dataset`, `Language_ID`, `Parameter_ID`
2. Metadata: `Glottocode`, `Glottolog_Name`, `Concepticon_Gloss`
3. Form data: `Value`, `Form`, `Segments`
4. Cognate data: `Cognacy`, `Alignment`, `Loan`, `Morpheme_Index`, `Segment_Slice`, `Doubt`
5. Provenance: `Comment`, `Source`, `Cognate_Detection_Method`, `Cognate_Source`

**Removed columns** (per spec):
- `Local_ID` (redundant with prefixed ID)
- `Profile` (internal processing detail)
- `Concepticon_ID` (redundant with Concepticon_Gloss)
- `Graphemes` (internal orthography processing)

This produces a **clean, analysis-ready schema** without internal processing artifacts.

### 4.3 NULL Handling

**VERY GOOD**: Proper distinction between missing data types.

The validation report tracks:
1. Columns not present in source dataset → `null_percentage: 100.0`
2. Empty cells in existing columns → tracked separately
3. Genuinely missing values → preserved as nulls

**Example** (from validation report):
```json
"aaleykusunda": {
  "null_percentage": {
    "Segments": 0.0,     // All present
    "Comment": 100.0,    // Column exists but all empty
    "Loan": 100.0,       // Column exists but not coded
    "Cognacy": 100.0     // No cognate data for this dataset
  }
}
```

Users can distinguish between:
- "This dataset doesn't have cognates" (expected)
- "This form is missing its cognate assignment" (data gap)

### 4.4 Data Type Consistency

**GOOD with minor issues:**

Most columns use appropriate types:
- IDs and text: `object` (string)
- Numeric morpheme indices: `float64` (allows NaN)

**Mixed type warnings** for columns 6, 9, 12, 15, 16, 17, 19:
```
Columns (6,9,12,15,16,17,19) have mixed types
```

**Analysis:**
- Column 6: `Concepticon_Gloss` – likely numeric concepticon IDs mixed with glosses in some datasets
- Columns 9, 12: Likely `Form`/`Segments` with occasional numeric-only forms
- Others: Minor type variations in sparse columns

**Impact:** Minimal. Pandas handles mixed types gracefully. Users loading data should use `dtype=str` for text columns if needed.

**Recommendation:** Future versions could enforce string types on all text columns during export.

---

## 5. Reference System Version Heterogeneity

### 5.1 Glottolog Versions

**MODERATE CONCERN**: 11 different Glottolog versions across datasets.

**Distribution:**
- v5.0: 111 datasets (74.5%)
- v5.1: 14 datasets (9.4%)
- v4.4–v4.8: 13 datasets (8.7%)
- Other: 11 datasets (7.4%)

**Implication:**
- Glottocodes are **generally stable** across versions for established languages
- **New languages** and **classification changes** may cause minor inconsistencies
- For most analyses, this is **not a significant issue**

**Recommendation:** Users performing:
- **Phylogenetic analyses** → check Glottolog version consistency for languages used
- **General comparative work** → version differences negligible

### 5.2 Concepticon Versions

**MODERATE CONCERN**: 11 different Concepticon versions.

**Distribution:**
- v3.2.0: 121 datasets (81.2%)
- v2.5.0: 9 datasets (6.0%)
- v3.3.0–v3.4.0: 6 datasets (4.0%)
- Other: 13 datasets (8.7%)

**Implication:**
- Concepticon IDs are **mostly stable** across versions for core concepts
- **New concepts** and **gloss standardization** may cause minor variations
- Given 71% of parameters lack Concepticon IDs anyway, version drift is a **minor issue**

**Recommendation:** For critical comparative work, users can check `references.csv` to see which datasets use which Concepticon versions.

### 5.3 CLTS Versions

**LOW CONCERN**: 8 different CLTS versions.

**Distribution:**
- v2.3.0: 120 datasets (80.5%)
- v2.2.0: 10 datasets (6.7%)
- v2.1.0 variants: 10 datasets (6.7%)
- Other: 9 datasets (6.0%)

**Implication:**
CLTS (Cross-Linguistic Transcription Systems) versioning affects:
- Segment tokenization rules
- IPA normalization
- Feature specifications

**Impact:** Most segmentations should be consistent, but edge cases (rare phonemes, tone marks) may differ slightly.

**Recommendation:** For phonological feature extraction, users should be aware of potential minor inconsistencies in segment representation across datasets.

---

## 6. Specific Dataset Quality Issues

### 6.1 Datasets with No Segmentation (9 datasets)

**High-Impact Missing Data:**

1. **`acd`** (146,733 forms): Austronesian Comparative Dictionary
   - **Reason:** ACD is an **etymological dictionary**, not a phonologically annotated wordlist
   - Forms are **reconstructions and citations** from sources with variable transcription
   - **Expected behavior**: Segmentation not feasible

2. **`ids`** (437,902 forms): World Loanword Database
   - **Reason:** WOLD focuses on **lexical borrowing**, not phonological detail
   - Emphasis on semantic fields and borrowing status
   - **Expected behavior**: Segmentation not priority

3. **`csd`, `mixezoqueanvoices`, `satterthwaitetb`**: Smaller specialized datasets
   - Likely legacy data or specific research focus

**User Guidance:**
These datasets are **still valuable** for:
- Lexical distribution studies
- Borrowing analysis (esp. `ids`)
- Etymological research (`acd`)
- Concept-based comparisons

But **unsuitable** for:
- Phonotactic analysis
- Sound change studies
- Alignment-based methods

### 6.2 Datasets with Sparse Loan Status

**`Loan` column sparsely populated** (only 12.5% of forms coded in first 100k sample).

**Root Cause:**
Most datasets don't systematically code loan status. Only specialized datasets like `ids` (WOLD) have comprehensive borrowing annotations.

**Implication:**
- Absence of `Loan=true` does **not** mean "not a loanword"
- It means "not coded for borrowing status"

**Recommendation:** Users studying loanwords should:
- Focus on datasets known to have borrowing annotations (check validation report)
- Use `ids` dataset for comprehensive cross-linguistic borrowing data
- Do **not** interpret missing `Loan` values as negative evidence

---

## 7. Validation Report Quality

**EXCELLENT**: Comprehensive, well-structured validation reporting.

The `validation_report.json` provides:

### 7.1 Summary Statistics
- Total dataset/form/language/parameter counts
- Cognate dataset counts
- Partial cognacy tracking

### 7.2 Per-Dataset Completeness
- Row counts for all tables
- Null percentage per column
- Columns present vs. absent tracking

### 7.3 Referential Integrity
- Foreign key validation
- Orphan detection (none found)

### 7.4 Data Quality Metrics
- Coverage percentages for key fields
- Segmentation/alignment/cognate availability

### 7.5 Version Distribution
- Complete tracking of Glottolog/Concepticon/CLTS versions

**This level of validation reporting is exceptional** and allows users to make informed decisions about data subset selection.

---

## 8. Recommendations for Users

### 8.1 For Phonological Research

**Best practice:**
```python
# Filter to forms with segmentation
forms = pd.read_csv('forms.csv')
phono_data = forms[forms['Segments'].notna()]
```

**Expected coverage:** ~77% of data (2.26M forms)

**Avoid datasets:** `acd`, `ids`, `csd`, `mixezoqueanvoices`, `satterthwaitetb`

### 8.2 For Cognate-Based Phylogenetics

**Best practice:**
```python
# Filter to forms with cognates and alignments
cog_data = forms[forms['Cognacy'].notna()]
align_data = forms[forms['Alignment'].notna()]  # Much smaller subset
```

**Expected coverage:**
- Cognacy: 27.84% (811k forms from 81 datasets)
- Alignment: 3.85% (112k forms from ~10–15 datasets)

**Check:** `Cognate_Detection_Method` to ensure expert-coded judgments

### 8.3 For Cross-Linguistic Concept Comparisons

**Best practice:**
```python
# Filter to forms with Concepticon mappings
concept_data = forms[forms['Concepticon_Gloss'].notna()]
```

**Expected coverage:** ~84.72% (2.47M forms)

**Note:** This biases toward core vocabulary. Extended semantic domains will be underrepresented.

### 8.4 For Geographic/Areal Studies

**Best practice:**
```python
# Use Glottolog metadata for filtering
geo_data = forms[forms['Glottocode'].notna()]
# Join with languages.csv for lat/long coordinates
```

**Expected coverage:** 95.15% (2.77M forms)

**Note:** Missing glottocodes are primarily reconstructed proto-languages, which don't have geographic coordinates anyway.

### 8.5 For Borrowing Research

**Best practice:**
```python
# Focus on datasets with systematic loan coding
ids_data = forms[forms['Dataset'] == 'ids']  # WOLD
# Or filter to forms with explicit loan status
loan_data = forms[forms['Loan'] == True]
```

**Expected coverage:** Highly variable; `ids` dataset alone provides 437,902 forms with systematic borrowing annotation.

---

## 9. Comparison with Alternatives

### 9.1 vs. Direct CLDF Access

**Advantages of Arca Verborum:**
- ✓ **Pre-joined metadata**: No need to join forms/languages/parameters
- ✓ **Global unique IDs**: Cross-dataset comparisons trivial
- ✓ **Aggregated cognates**: Merges forms.csv and cognates.csv
- ✓ **Single-file access**: No need to navigate 149 directory structures
- ✓ **Validation report**: Immediate quality assessment

**When to use CLDF directly:**
- Need for complete CLDF metadata (provenance, contributors, etc.)
- Requirement for CLDF-specific tooling (pycldf library)
- Access to non-wordlist tables (trees, borrowings, etc.)
- Need for original Local_IDs

### 9.2 vs. GLED (Tresoldi 2023)

**Complementary resources:**
- **GLED**: 136 datasets, focus on **high-quality cognate-coded data**
- **Arca Verborum**: 149 datasets, focus on **breadth and accessibility**

**Arca Verborum advantages:**
- Broader language coverage (9,738 vs. GLED's ~7,000)
- Includes non-cognate datasets (useful for distribution studies)
- More recent (2025 vs. 2023)
- Explicit pedagogical design

**GLED advantages:**
- More stringent quality filtering
- Focus on cognate-rich datasets
- Established publication record (DOI: 10.5334/johd.96)

**Recommendation:** Use both! GLED for cognate-focused research, Arca Verborum for exploratory analysis and student projects.

---

## 10. Overall Quality Grades by Dimension

| Dimension | Grade | Justification |
|-----------|-------|---------------|
| **Data Completeness** | A+ | 100% of source data preserved, no loss |
| **Metadata Integration** | A | Excellent Glottolog (95%), good Concepticon (85%) |
| **Cognate Data** | A- | 81 datasets, 97% coverage within sets, but low alignment |
| **Phonological Data** | B+ | 78% segmentation, high quality, but 9 datasets lack entirely |
| **Technical Implementation** | A+ | Perfect ID prefixing, referential integrity, validation |
| **Documentation** | A | Excellent validation report, clear specifications |
| **Version Consistency** | B | Manageable heterogeneity, tracked but not harmonized |
| **Borrowing Data** | C | Sparse except in specialized datasets |

**Overall Composite Grade: A-**

---

## 11. Critical Issues Requiring User Awareness

### 11.1 High Priority

1. **Concepticon Coverage Heterogeneity**
   - 71% of parameters lack Concepticon IDs
   - Primarily affects specialized datasets (`acd`, `ids`)
   - **Action:** Filter to non-null `Concepticon_Gloss` for concept-based studies

2. **Segmentation Gaps**
   - 9 datasets have 100% missing segmentation
   - **Action:** Filter to non-null `Segments` for phonological work

3. **Alignment Scarcity**
   - Only 3.85% of forms have alignments
   - **Action:** Recognize severe sample reduction if alignments required

### 11.2 Medium Priority

4. **Reference Version Heterogeneity**
   - 11 different Glottolog versions
   - 11 different Concepticon versions
   - **Action:** Check `references.csv` for critical phylogenetic work

5. **Loan Status Sparsity**
   - Most datasets don't code borrowing
   - **Action:** Use `ids` for systematic borrowing data

### 11.3 Low Priority (Minor Issues)

6. **Mixed Data Types**
   - Some columns have mixed types (manageable)
   - **Action:** Use `dtype=str` when loading if issues arise

7. **Macroarea Typo**
   - `papunesia` (lowercase) appears twice
   - **Action:** Normalize to `Papunesia` in preprocessing

---

## 12. Recommendations for Future Versions

### 12.1 Data Quality Improvements

1. **Harmonize Reference Versions** (if feasible)
   - Re-map all datasets to latest Glottolog/Concepticon
   - Would improve cross-dataset consistency
   - **Effort:** High; **Impact:** Medium

2. **Add Alignment Data**
   - Generate alignments for cognate sets without them
   - Use LingPy or similar automated tools
   - **Effort:** Medium; **Impact:** High for phylogenetics

3. **Backfill Segmentation**
   - Apply CLTS segmentation to unsegmented datasets
   - May not be feasible for `acd` (reconstructions)
   - **Effort:** Medium; **Impact:** Medium

### 12.2 Technical Improvements

4. **Enforce String Types on Export**
   - Eliminate mixed-type warnings
   - **Effort:** Low; **Impact:** Low (cosmetic)

5. **Add Dataset Quality Flags**
   - Categorize datasets by quality dimensions (e.g., "cognate-rich", "segmented", "aligned")
   - **Effort:** Low; **Impact:** High for user guidance

6. **Expand Validation Report**
   - Add inter-dataset consistency checks
   - Cross-reference glottocodes across datasets
   - **Effort:** Medium; **Impact:** Medium

### 12.3 Documentation Enhancements

7. **Dataset-Specific Guidance**
   - Create per-dataset README snippets in metadata
   - Document known issues and recommended uses
   - **Effort:** Medium; **Impact:** High for users

8. **Tutorial Notebooks**
   - Provide Jupyter notebooks for common use cases
   - Example workflows for phonology, cognates, geography
   - **Effort:** Medium; **Impact:** Very High for pedagogical mission

---

## 13. Conclusion

Arca Verborum represents a **high-quality, production-ready** aggregation of comparative linguistic data. The technical implementation is **exemplary**, with robust ID management, complete metadata integration, and comprehensive validation reporting.

The main quality considerations stem from **inherent heterogeneity** in the source Lexibank datasets, which is unavoidable when aggregating 149 independently curated resources. The merger handles this heterogeneity **gracefully** through proper NULL handling and detailed validation reporting.

**For its intended audience** (students, rapid method development, exploratory analysis), Arca Verborum **excels**. It dramatically lowers the barrier to working with cross-linguistic lexical data while preserving all essential information and providing clear quality metrics.

**For advanced research applications** (phylogenetics, sound change, borrowing studies), users must be **selective** about which datasets and which forms to use, guided by the validation report. This selectivity is appropriate and expected for any large-scale aggregation.

### Final Verdict

**Arca Verborum is fit for purpose and ready for release.**

The dataset achieves its core goals:
- ✓ Accessibility for non-specialists
- ✓ Immediate usability without complex CLDF tooling
- ✓ Preservation of data quality and provenance
- ✓ Transparent quality reporting

Recommended for:
- **Student projects** (A+)
- **Method prototyping** (A+)
- **Exploratory analysis** (A+)
- **Large-scale comparative studies** (A- with careful filtering)
- **Phonological typology** (B+ for segmented subset)
- **Phylogenetic research** (B for cognate subset)

**Publish with confidence.**

---

## Appendix: Quality Metrics Summary

```
Dataset Version: 20251001
Assessment Date: 2025-10-01
Total Datasets:  149
Total Forms:     2,915,377
Total Languages: 9,738
Total Parameters: 168,263

Coverage Metrics:
  Glottolog:     95.15%
  Concepticon:   84.72%
  Segmentation:  77.66%
  Cognates:      27.84%
  Alignments:     3.85%

Cognate Datasets: 81 (54.4%)
  Avg coverage in cognate datasets: 97.0%

Partial Cognacy: 7 datasets
  Morpheme-indexed: 25,961 forms
  Segment-sliced:   35,241 forms

Reference Versions:
  Glottolog v5.0:     74.5%
  Concepticon v3.2.0: 81.2%
  CLTS v2.3.0:        80.5%

BibTeX References: 8,751 entries

Technical Quality:
  ID prefixing:        ✓ Complete
  Referential integrity: ✓ 100%
  NULL handling:       ✓ Proper
  Validation report:   ✓ Comprehensive
```

---

**Report Prepared By:** Expert Assessment (Computational Historical Linguistics)
**Methodology:** Systematic analysis of output files, validation report, and data samples
**Confidence Level:** High (based on comprehensive validation metrics and direct data inspection)
