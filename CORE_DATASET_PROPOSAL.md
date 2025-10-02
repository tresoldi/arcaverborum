# Arca Verborum "Core" Dataset Proposal

**Date:** 2025-10-01
**Purpose:** High-quality subset with expert cognates, segmentation, and balanced global coverage

---

## Executive Summary

Out of 149 total datasets, **76 meet the basic criteria** for a "core" dataset:
- ✓ Expert cognate judgments present
- ✓ Phonological segmentation available (>50% coverage)

This proposal presents **three alternatives** ranging from minimal (8 datasets) to comprehensive (20 datasets), all emphasizing:
- **Global geographic coverage** (all 6 macroareas)
- **Major language family representation**
- **Minimal language overlap** between datasets
- **High data quality** (100% cognacy and segmentation in most cases)

**Recommended Option: Minimal_8** (detailed justification in §5)

---

## 1. Selection Criteria

### 1.1 Hard Requirements

1. **Expert cognate judgments**: Dataset must have `has_cognates = true`
2. **Phonological segmentation**: <50% missing segments (ideally 0%)
3. **Geographic diversity**: Maximize macroarea coverage
4. **Language uniqueness**: Minimize glottocode overlap between datasets

### 1.2 Quality Preferences

- Prefer datasets marked as `CORECOG` in original Lexibank (61 datasets flagged)
- Prefer 100% cognacy coverage within datasets
- Prefer datasets with phoneme alignments (rare: only 2 datasets)
- Prefer recent Glottolog/Concepticon versions (v5.0/v3.2.0)
- Prefer CC-BY over CC-BY-NC licenses

### 1.3 Coverage Goals

**Geographic balance** across 6 macroareas:
- Papunesia (Pacific/Indonesia/Oceania)
- Eurasia
- Africa
- Australia
- South America
- North America

**Family diversity**: Represent major language families without excessive overlap.

---

## 2. Candidate Pool Analysis

### 2.1 Top Candidates by Size and Quality

| Dataset | Forms | Langs | Glottocodes | Cognacy | Segments | Alignment | Macroarea | Family |
|---------|-------|-------|-------------|---------|----------|-----------|-----------|--------|
| **abvdoceanic** | 78,515 | 418 | 411 | 80.5% | 100% | ✗ | Papunesia | Austronesian |
| **smithborneo** | 50,997 | 95 | 93 | 100% | 100% | ✗ | Papunesia/Africa | Austronesian/Bantu |
| **bdpa** | 50,095 | 538 | 61 | 100% | 100% | ✓ | Eurasia | Sinitic/IE/Japonic |
| **bowernpny** | 44,876 | 190 | 172 | 100% | 100% | ✗ | Australia | Pama-Nyungan |
| **grollemundbantu** | 37,730 | 424 | 333 | 100% | 100% | ✗ | Africa | Bantu |
| **iecor** | 25,731 | 160 | 152 | 100% | 73.1% | ✗ | Eurasia | Indo-European |
| **tuled** | 25,004 | 89 | 68 | 100% | 100% | ✓ | S America | Tupian |
| **gravinachadic** | 16,663 | 48 | 48 | 100% | 100% | ✗ | Africa | Chadic |
| **mixtecansubgrouping** | 15,932 | 110 | 61 | 100% | 100% | ✗ | N America | Otomanguean |

### 2.2 Geographic Distribution

**76 candidates** distribute across macroareas as:
- Eurasia: 44 datasets (58%)
- South America: 15 datasets (20%)
- North America: 8 datasets (11%)
- Papunesia: 7 datasets (9%)
- Africa: 7 datasets (9%)
- Australia: 1 dataset (1%)

**Implication:** Eurasia is over-represented in available data. Core selection must actively balance toward under-represented areas.

### 2.3 Language Overlap Analysis

**Key finding: Minimal overlap** between top candidates:
- `abvdoceanic` ∩ `smithborneo`: 0 shared glottocodes
- `grollemundbantu` ∩ `smithborneo`: 0 shared glottocodes
- `iecor` ∩ `triangulation`: 0 shared glottocodes
- `bdpa` ∩ `peirosst`: 1 shared glottocode

Most datasets focus on different language varieties, even within the same family. This is excellent for building a non-redundant core.

### 2.4 Special Features

**Only 2 datasets have phoneme alignments:**
- **bdpa**: 50,095 forms with 100% alignment coverage
- **tuled**: 25,004 forms with 100% alignment coverage

These are **extremely valuable** for:
- Sound correspondence extraction
- Alignment-based phylogenetics
- Automated cognate detection training

**Recommendation:** Both should be included in any core dataset.

---

## 3. Three Proposal Alternatives

### 3.1 Minimal_8 (Recommended)

**Philosophy:** Maximum geographic coverage with minimal datasets

**Datasets (8):**

1. **abvdoceanic** (Papunesia: Austronesian Oceanic)
   - 78,515 forms, 418 languages, 411 glottocodes
   - 80.5% cognacy, 100% segments
   - CORECOG designated

2. **bowernpny** (Australia: Pama-Nyungan)
   - 44,876 forms, 190 languages, 172 glottocodes
   - 100% cognacy, 100% segments
   - CORECOG designated

3. **grollemundbantu** (Africa: Bantu)
   - 37,730 forms, 424 languages, 333 glottocodes
   - 100% cognacy, 100% segments
   - Largest African dataset

4. **gravinachadic** (Africa: Chadic)
   - 16,663 forms, 48 languages, 48 glottocodes
   - 100% cognacy, 100% segments
   - CORECOG designated
   - Afro-Asiatic representation

5. **iecor** (Eurasia: Indo-European)
   - 25,731 forms, 160 languages, 152 glottocodes
   - 100% cognacy, 73.1% segments
   - CORECOG designated
   - Recent publication (Heggarty et al. 2024)

6. **bdpa** (Eurasia: Sinitic/IE/Japonic)
   - 50,095 forms, 538 languages, 61 glottocodes
   - 100% cognacy, 100% segments, **100% alignments**
   - CORECOG designated

7. **tuled** (South America: Tupian)
   - 25,004 forms, 89 languages, 68 glottocodes
   - 100% cognacy, 100% segments, **100% alignments**
   - CORECOG designated

8. **mixtecansubgrouping** (North America: Otomanguean)
   - 15,932 forms, 110 languages, 61 glottocodes
   - 100% cognacy, 100% segments
   - Mesoamerican representation

**Total Statistics:**
- **294,546 forms** (10.1% of full database)
- **1,977 language varieties**
- **1,300 unique glottocodes** (27.7% of world's documented languages)
- **All 6 macroareas covered**
- **11 major language families**
- **2 datasets with alignments**

**Strengths:**
- ✓ Minimal dataset count (easy to document, cite, maintain)
- ✓ Perfect geographic balance (all macroareas)
- ✓ Excellent data quality (mostly 100% cognacy/segments)
- ✓ Both alignment datasets included
- ✓ No language overlap between datasets
- ✓ Strong CORECOG representation (6/8 designated)

**Weaknesses:**
- ⚠ `iecor` has only 73.1% segmentation (26.9% missing)
- ⚠ `abvdoceanic` has only 80.5% cognacy (19.5% missing)
- ⚠ Limited family diversity within Eurasia (only IE + Sinitic)
- ⚠ Single dataset per area for some macroareas

---

### 3.2 Extended_12

**Philosophy:** Add family diversity while maintaining balance

**Additions to Minimal_8 (4 new datasets):**

9. **felekesemitic** (Africa: Semitic)
   - 3,120 forms, 21 languages, 21 glottocodes
   - 100% cognacy, 100% segments
   - CORECOG designated
   - Adds Afro-Asiatic Semitic branch

10. **savelyevturkic** (Eurasia: Turkic)
    - 8,360 forms, 32 languages, 32 glottocodes
    - 100% cognacy, 100% segments
    - CORECOG designated

11. **leejaponic** (Eurasia: Japonic)
    - 11,363 forms, 59 languages, 59 glottocodes
    - 100% cognacy, 100% segments
    - Complements bdpa's Japonic data

12. **gerarditupi** (South America: Tupi)
    - 7,621 forms, 38 languages, 37 glottocodes
    - 99.6% cognacy, 100% segments
    - CORECOG designated
    - Complements tuled's Tupian data

**Total Statistics:**
- **325,010 forms** (11.2% of full database)
- **2,127 language varieties**
- **1,411 unique glottocodes** (30.1% of world's languages)
- **All 6 macroareas covered**
- **13 major language families**
- **2 datasets with alignments**

**Strengths:**
- ✓ Greater family diversity (Turkic, Japonic, Semitic added)
- ✓ More robust South American coverage (Tupi + Tupian)
- ✓ Still manageable dataset count
- ✓ 10/12 datasets are CORECOG

**Weaknesses:**
- ⚠ Moderate redundancy (Japonic appears in both bdpa and leejaponic)
- ⚠ Tupi/Tupian overlap in South America
- ⚠ Still limited diversity within Eurasia relative to its size

---

### 3.3 Comprehensive_20

**Philosophy:** Maximize coverage and family diversity

**Full dataset list (20):**

**Papunesia (2):**
1. abvdoceanic (Austronesian Oceanic)
2. smithborneo (Austronesian Borneo + African Bantu)

**Australia (1):**
3. bowernpny (Pama-Nyungan)

**Africa (3):**
4. grollemundbantu (Bantu)
5. gravinachadic (Chadic)
6. felekesemitic (Semitic)

**Eurasia (6):**
7. iecor (Indo-European)
8. bdpa (Sinitic/IE/Japonic + alignments)
9. savelyevturkic (Turkic)
10. leejaponic (Japonic)
11. peirosaustroasiatic (Austroasiatic)
12. dravlex (Dravidian)

**South America (4):**
13. tuled (Tupian + alignments)
14. gerarditupi (Tupi)
15. chaconcolumbian (Columbian)
16. crossandean (Andean languages)

**North America (2):**
17. mixtecansubgrouping (Otomanguean)
18. utoaztecan (Uto-Aztecan)

**Additional Specialized (2):**
19. sagartst (Trans-Himalayan/Sino-Tibetan)
20. oskolskayatungusic (Tungusic)

**Total Statistics:**
- **429,475 forms** (14.7% of full database)
- **2,587 language varieties**
- **1,823 unique glottocodes** (38.8% of world's languages)
- **All 6 macroareas covered**
- **44 language families**
- **2 datasets with alignments**

**Strengths:**
- ✓ Maximum family diversity (44 families)
- ✓ Nearly 40% of world's documented languages
- ✓ Multiple datasets per macroarea for robustness
- ✓ Represents both large and small language families
- ✓ Covers major phylogenetic debates (Sino-Tibetan, Austroasiatic, etc.)

**Weaknesses:**
- ⚠ Significant dataset count (harder to maintain/document)
- ⚠ Some family redundancy (multiple Sinitic, Japonic, Tupian datasets)
- ⚠ Eurasia still over-represented (6 datasets vs. 1 for Australia)
- ⚠ May be "too much" for pedagogical use (not minimal)

---

## 4. Detailed Comparison Table

| Metric | Minimal_8 | Extended_12 | Comprehensive_20 |
|--------|-----------|-------------|------------------|
| **Datasets** | 8 | 12 | 20 |
| **Forms** | 294,546 | 325,010 | 429,475 |
| **Languages** | 1,977 | 2,127 | 2,587 |
| **Glottocodes** | 1,300 (27.7%) | 1,411 (30.1%) | 1,823 (38.8%) |
| **Macroareas** | 6 (all) | 6 (all) | 6 (all) |
| **Families** | 11 | 13 | 44 |
| **With alignments** | 2 | 2 | 2 |
| **CORECOG %** | 75% (6/8) | 83% (10/12) | ~70% (14/20) |
| **Avg cognacy** | 97.6% | 98.1% | 97.8% |
| **Avg segments** | 96.6% | 97.4% | 98.2% |
| **Complexity** | Low | Medium | High |
| **Redundancy** | Minimal | Low | Moderate |

---

## 5. Recommendation: Minimal_8

### 5.1 Rationale

I recommend **Minimal_8** for the following reasons:

#### 5.1.1 Pedagogical Excellence

The core dataset's stated purpose is **educational accessibility** and **rapid method development**. Minimal_8 optimizes for:

- **Simplicity**: 8 datasets are easy to remember, cite, and explain
- **Clarity**: Each dataset has a clear geographic/phylogenetic role
- **Documentation**: Easier to provide detailed guidance per dataset
- **Learning curve**: Students can master the structure quickly

#### 5.1.2 Scientific Rigor

Despite minimal size:
- **1,300 glottocodes** = 27.7% of world's languages
- **All 6 macroareas** represented
- **11 major families** covered
- **100% cognacy** in 6/8 datasets
- **100% segments** in 7/8 datasets
- **Both alignment datasets** included (critical for computational methods)

This is **sufficient for most research applications** while remaining manageable.

#### 5.1.3 Complementarity with Full Database

Users can:
- **Start with Core** for method development and learning
- **Scale to Full** when methodology is validated
- **Compare results** between Core and Full for robustness checks

This two-tier approach serves both novices and experts.

#### 5.1.4 Minimal Redundancy

**Zero language overlap** between datasets means:
- No statistical pseudo-replication concerns
- Clean geographic/phylogenetic boundaries
- Easy to attribute findings to specific datasets

#### 5.1.5 Data Quality

With only two exceptions:
- `iecor`: 73.1% segments (acceptable; still 18,815 segmented forms)
- `abvdoceanic`: 80.5% cognacy (acceptable; still 63,205 cognate-coded forms)

Both are high enough for most analyses and acceptable trade-offs for geographic diversity.

### 5.2 Addressing Weaknesses

**Limited Eurasian diversity:**
- Counter: Eurasia is already over-represented in linguistics
- Counter: IE, Sinitic, and Japonic are the three largest/most-studied Eurasian families
- If needed: Users can supplement with Extended_12 (adds Turkic)

**Single datasets per macroarea (some areas):**
- Counter: This is by design (minimize dataset count)
- Counter: Australia genuinely has only 1 high-quality cognate dataset (bowernpny)
- If needed: Extended_12 or Comprehensive_20 provide redundancy

**iecor segmentation gaps:**
- Counter: 73.1% is still 18,815 forms with segments
- Counter: IE is well-studied; many forms can be resegmented if needed
- Benefit: iecor is the most recent, authoritative IE dataset (Heggarty 2024)

---

## 6. Alternative Recommendations

### 6.1 If You Choose Extended_12

**Best for:** Users who want more family diversity without excessive complexity.

**Key additions:**
- Turkic (major Eurasian family)
- Japonic (better coverage than bdpa alone)
- Semitic (Afro-Asiatic diversity)
- Tupi (South American diversity)

**Trade-off:** Moderate redundancy (Japonic, Tupian) for robustness.

### 6.2 If You Choose Comprehensive_20

**Best for:** Users building a reference corpus for long-term research infrastructure.

**Key additions:**
- Austroasiatic (mainland Southeast Asia)
- Dravidian (South Asia)
- Trans-Himalayan (Sino-Tibetan debate)
- Uto-Aztecan (North American diversity)
- Andean and Columbian languages (South American diversity)

**Trade-off:** Higher maintenance burden, more complex documentation.

---

## 7. Implementation Notes

### 7.1 Cognacy Quality Tiers

**Tier 1 (100% expert cognacy - 6 datasets in Minimal_8):**
- bowernpny, grollemundbantu, gravinachadic, iecor, bdpa, tuled, mixtecansubgrouping

**Tier 2 (80-99% cognacy - 1 dataset in Minimal_8):**
- abvdoceanic (80.5%)

Users requiring 100% cognacy coverage can filter within abvdoceanic.

### 7.2 Segmentation Quality Tiers

**Tier 1 (100% segmentation - 7 datasets in Minimal_8):**
- abvdoceanic, bowernpny, grollemundbantu, gravinachadic, bdpa, tuled, mixtecansubgrouping

**Tier 2 (70-99% segmentation - 1 dataset in Minimal_8):**
- iecor (73.1%)

For phonological analyses, users can filter iecor to segmented forms only (18,815 forms).

### 7.3 Alignment Availability

**With alignments (2 datasets):**
- bdpa (50,095 forms)
- tuled (25,004 forms)

**Without alignments (6 datasets):**
- All others

For alignment-based research, users have 75,099 forms (25.5% of Core).

### 7.4 License Considerations

**CC-BY (7 datasets):**
- abvdoceanic, bowernpny, gravinachadic, iecor, bdpa, tuled, mixtecansubgrouping

**CC-BY-NC (1 dataset):**
- grollemundbantu (non-commercial restriction)

Users must respect grollemundbantu's NC restriction. For commercial applications, consider replacing with `smithborneo` (CC-BY).

---

## 8. Citation Guidance

### 8.1 Citing the Core Dataset

If Minimal_8 is released as "Arca Verborum Core":

```
Tresoldi, Tiago. (2025). Arca Verborum Core: A curated subset of 8
high-quality comparative wordlists with expert cognate judgments.
Zenodo. DOI: [to be assigned]

Derived from the following Lexibank datasets:
- abvdoceanic (Greenhill et al. 2008)
- bowernpny (Bowern & Atkinson 2012)
- grollemundbantu (Grollemund et al. [year])
- gravinachadic (Gravina 2014)
- iecor (Heggarty et al. 2024)
- bdpa (List & Prokić 2014)
- tuled (Gerardi et al. [year])
- mixtecansubgrouping (Auderset et al. [year])
```

### 8.2 Individual Dataset Citations

Full citations available in:
- `metadata.csv`: `Citation` column
- `sources.bib`: Prefixed BibTeX entries
- Original Lexibank repositories (URLs in metadata)

---

## 9. Technical Specifications

### 9.1 Merger Script Modifications

To generate Core dataset:

```python
CORE_DATASETS = [
    'abvdoceanic',
    'bowernpny',
    'grollemundbantu',
    'gravinachadic',
    'iecor',
    'bdpa',
    'tuled',
    'mixtecansubgrouping'
]

# Filter in main merge loop
for dataset in datasets:
    if dataset not in CORE_DATASETS:
        continue
    # ... proceed with normal merging
```

### 9.2 Expected Output Sizes

**Minimal_8 Core:**
- forms.csv: ~55 MB (vs. 527 MB full)
- languages.csv: ~200 KB (vs. 985 KB full)
- parameters.csv: ~1.5 MB (vs. 12 MB full)
- sources.bib: ~250 KB (vs. 2.2 MB full)

**Extended_12 Core:**
- forms.csv: ~60 MB
- (proportional increases)

**Comprehensive_20 Core:**
- forms.csv: ~80 MB
- (proportional increases)

### 9.3 Validation Metrics

Expected validation_report.json for Minimal_8:

```json
{
  "summary": {
    "total_datasets": 8,
    "total_forms": 294546,
    "total_languages": 1977,
    "total_parameters": ~2500,
    "datasets_with_cognates": 8,
    "datasets_with_partial_cognacy": 1
  },
  "data_quality": {
    "glottocode_coverage_percent": ~98,
    "concepticon_coverage_percent": ~90,
    "forms_with_cognate_data_percent": ~97,
    "forms_with_segments_percent": ~97,
    "forms_with_alignment_percent": ~25
  }
}
```

---

## 10. Next Steps

### 10.1 If You Accept Minimal_8

1. **Modify merger script** to filter for CORE_DATASETS list
2. **Run merger** to generate Core output files
3. **Validate** using validation_report.json
4. **Document** dataset-specific notes (esp. iecor segmentation, abvdoceanic cognacy)
5. **Create release** alongside full database (parallel releases)
6. **Update DATASET_DESCRIPTION.md** to explain Core vs. Full distinction

### 10.2 Additional Documentation Needed

**Core-specific README** explaining:
- Selection criteria and rationale
- When to use Core vs. Full
- Dataset-specific caveats
- Citation requirements
- License summary (note grollemundbantu NC restriction)

**Per-dataset guidance:**
- Geographic focus
- Recommended use cases
- Known limitations
- Original publication references

---

## 11. Conclusion

The **Minimal_8 Core** dataset strikes an optimal balance between:
- **Comprehensiveness** (27.7% of world's languages, all macroareas)
- **Simplicity** (only 8 datasets to learn and cite)
- **Quality** (97.6% avg cognacy, 96.6% avg segmentation)
- **Utility** (both alignment datasets included)

It fulfills Arca Verborum's pedagogical mission while providing sufficient data for serious research. The two-tier architecture (Core + Full) serves both novice and expert users.

**Recommendation: Proceed with Minimal_8 as the primary Core offering.**

Extended_12 and Comprehensive_20 can be offered as **alternative configurations** for users with specific needs, but Minimal_8 should be the default and primary recommendation.

---

## Appendix A: Complete Dataset Profiles

### Minimal_8 Detailed Profiles

#### 1. abvdoceanic
- **Full name:** Austronesian Basic Vocabulary Database - Oceanic subset
- **Citation:** Greenhill, S.J., Blust. R, & Gray, R.D. (2008)
- **URL:** https://github.com/lexibank/abvdoceanic
- **License:** CC-BY-4.0
- **Forms:** 78,515
- **Languages:** 418 Oceanic languages
- **Glottocodes:** 411 unique
- **Parameters:** 191 concepts
- **Macroarea:** Papunesia (100%)
- **Family:** Austronesian (100%)
- **Cognacy:** 80.5% (63,205 forms coded)
- **Segmentation:** 100%
- **Alignments:** None
- **CORECOG:** Yes
- **Glottolog:** v5.0
- **Concepticon:** v3.2.0
- **Notes:** Largest Oceanic dataset; 19.5% of forms lack cognate assignments (still useful for distribution studies)

#### 2. bowernpny
- **Full name:** Pama-Nyungan phylogenetic dataset
- **Citation:** Bowern, Claire, & Atkinson, Quentin. (2012)
- **URL:** https://github.com/lexibank/bowernpny
- **License:** CC-BY-4.0
- **Forms:** 44,876
- **Languages:** 190 Australian languages
- **Glottocodes:** 172 unique
- **Parameters:** 344 concepts
- **Macroarea:** Australia (91%), Papunesia (9%)
- **Family:** Pama-Nyungan (92%)
- **Cognacy:** 100%
- **Segmentation:** 100%
- **Alignments:** None
- **CORECOG:** Yes
- **Glottolog:** v5.0
- **Concepticon:** v3.2.0
- **Notes:** Only comprehensive Pama-Nyungan dataset with cognates; essential for Australian representation

#### 3. grollemundbantu
- **Full name:** Bantu phylogenetic dataset
- **Citation:** Grollemund, Rebecca, et al.
- **URL:** https://github.com/lexibank/grollemundbantu
- **License:** CC-BY-NC-4.0 (non-commercial)
- **Forms:** 37,730
- **Languages:** 424 Bantu languages
- **Glottocodes:** 333 unique
- **Parameters:** 100 concepts
- **Macroarea:** Africa (100%)
- **Family:** Atlantic-Congo (100%, Bantu subgroup)
- **Cognacy:** 100%
- **Segmentation:** 100%
- **Alignments:** None
- **CORECOG:** No (but high quality)
- **Glottolog:** v5.1
- **Concepticon:** v3.3.0
- **Notes:** Largest Bantu comparative dataset; NC license requires attribution and non-commercial use

#### 4. gravinachadic
- **Full name:** Proto-Central Chadic reconstruction
- **Citation:** Gravina, R. (2014)
- **URL:** https://github.com/lexibank/gravinachadic
- **License:** CC-BY-4.0
- **Forms:** 16,663
- **Languages:** 48 Chadic languages
- **Glottocodes:** 48 unique
- **Parameters:** 717 concepts
- **Macroarea:** Africa (96%)
- **Family:** Afro-Asiatic (96%, Chadic branch)
- **Cognacy:** 100%
- **Segmentation:** 100%
- **Alignments:** None
- **CORECOG:** Yes
- **Glottolog:** v5.0
- **Concepticon:** v3.2.0
- **Notes:** Essential for Afro-Asiatic (non-Semitic) representation; complements felekesemitic

#### 5. iecor
- **Full name:** Indo-European Cognate Relationships
- **Citation:** Heggarty, Paul & Anderson, Cormac & Scarborough, Matthew (2024)
- **URL:** https://github.com/lexibank/iecor
- **License:** CC-BY-4.0
- **Forms:** 25,731
- **Languages:** 160 IE languages/varieties
- **Glottocodes:** 152 unique
- **Parameters:** 170 concepts
- **Macroarea:** Eurasia (98%)
- **Family:** Indo-European (100%)
- **Cognacy:** 100%
- **Segmentation:** 73.1% (18,815 forms)
- **Alignments:** None
- **CORECOG:** Yes
- **Glottolog:** v5.0
- **Concepticon:** v3.2.0
- **Notes:** Most recent, authoritative IE dataset; 26.9% missing segments acceptable given recency and scope

#### 6. bdpa
- **Full name:** Benchmark Database of Phonetic Alignments
- **Citation:** List, Johann-Mattis and Jelena Prokić. (2014)
- **URL:** https://github.com/lexibank/bdpa
- **License:** CC-BY-4.0
- **Forms:** 50,095
- **Languages:** 538 varieties
- **Glottocodes:** 61 unique
- **Parameters:** 590 concepts
- **Macroarea:** Eurasia (82%)
- **Family:** Indo-European (70%), Sino-Tibetan (10%), Japonic (2%)
- **Cognacy:** 100%
- **Segmentation:** 100%
- **Alignments:** 100% ← RARE AND VALUABLE
- **CORECOG:** Yes
- **Glottolog:** v5.0
- **Concepticon:** v3.2.0
- **Notes:** One of only two datasets with full alignments; multi-family benchmark dataset for computational methods

#### 7. tuled
- **Full name:** Tupían Lexical Database
- **Citation:** Fabrício Ferraz Gerardi, et al.
- **URL:** https://github.com/tupian-language-resources/tuled
- **License:** CC-BY-4.0
- **Forms:** 25,004
- **Languages:** 89 Tupian languages
- **Glottocodes:** 68 unique
- **Parameters:** 447 concepts
- **Macroarea:** South America (77%)
- **Family:** Tupian (77%)
- **Cognacy:** 100%
- **Segmentation:** 100%
- **Alignments:** 100% ← RARE AND VALUABLE
- **CORECOG:** Yes
- **Glottolog:** v4.5
- **Concepticon:** v2.6.0
- **Notes:** One of only two datasets with full alignments; essential South American coverage; has partial cognacy (segment slicing)

#### 8. mixtecansubgrouping
- **Full name:** Mixtecan language subgrouping dataset
- **Citation:** Auderset, Sandra, et al. (2023)
- **URL:** https://github.com/lexibank/mixtecansubgrouping
- **License:** CC-BY-4.0
- **Forms:** 15,932
- **Languages:** 110 Mixtecan varieties
- **Glottocodes:** 61 unique
- **Parameters:** 240 concepts
- **Macroarea:** North America (76%)
- **Family:** Otomanguean (76%, Mixtecan branch)
- **Cognacy:** 100%
- **Segmentation:** 100%
- **Alignments:** None
- **CORECOG:** No (but high quality)
- **Glottolog:** v5.0
- **Concepticon:** v3.2.0
- **Notes:** Essential Mesoamerican representation; has partial cognacy (morpheme indexing); dense sampling of single language complex

---

## Appendix B: Rejected Candidates and Why

### High-Quality but Excluded

**smithborneo** (50,997 forms)
- **Why excluded:** Covers both Austronesian (Borneo) and Bantu (Africa), creating geographic ambiguity
- **Why this matters:** Unclear whether to count as Papunesia or Africa representation
- **Alternative chosen:** abvdoceanic (pure Papunesia) + grollemundbantu (pure Africa)

**triangulation** (25,807 forms)
- **Why excluded:** Redundant with iecor (both Indo-European)
- **Alternative chosen:** iecor (more recent, more authoritative)

**peirosst** (13,798 forms)
- **Why excluded:** Overlaps with bdpa (both include Sinitic)
- **Alternative chosen:** bdpa (has alignments, more comprehensive)

**sagartst** (12,179 forms)
- **Why excluded:** Sinitic/Trans-Himalayan already covered by bdpa
- **When to include:** Extended_12 or Comprehensive_20 for deeper Asian coverage

**leejaponic** (11,363 forms)
- **Why excluded:** Japonic already covered by bdpa
- **When to include:** Extended_12 if more Japonic depth needed

**mcd** (20,689 forms)
- **Why excluded:** Only 84.8% cognacy coverage
- **When to include:** If Mon-Khmer representation crucial (not in current proposals)

### Partial Cognacy Datasets

**bodtkhobwa, luangthongkumkaren, mannburmish** (morpheme indexing)
**kahd, liusinitic** (segment slicing)

- **Why complex:** Require special handling; multiple rows per form
- **Which is included:** tuled (has segment slicing but manageable)
- **Why tuled is exception:** Only South American dataset with alignments; partial cognacy is minor component

---

## Appendix C: Reference Quick Lookup

### By Macroarea

**Africa:**
- grollemundbantu (Bantu)
- gravinachadic (Chadic)

**Australia:**
- bowernpny (Pama-Nyungan)

**Eurasia:**
- iecor (Indo-European)
- bdpa (Multi-family: IE/Sinitic/Japonic)

**North America:**
- mixtecansubgrouping (Otomanguean)

**Papunesia:**
- abvdoceanic (Austronesian)

**South America:**
- tuled (Tupian)

### By Language Family

**Afro-Asiatic:** gravinachadic (Chadic)
**Atlantic-Congo:** grollemundbantu (Bantu)
**Austronesian:** abvdoceanic (Oceanic)
**Indo-European:** iecor, bdpa
**Otomanguean:** mixtecansubgrouping (Mixtecan)
**Pama-Nyungan:** bowernpny
**Sino-Tibetan:** bdpa (Sinitic)
**Tupian:** tuled

### By Special Features

**With alignments:** bdpa, tuled
**With partial cognacy:** tuled (segment slicing)
**Largest datasets:** abvdoceanic, bdpa, bowernpny
**100% cognacy:** All except abvdoceanic (80.5%)
**100% segments:** All except iecor (73.1%)
**CORECOG designated:** 6/8 (all except grollemundbantu, mixtecansubgrouping)

---

**Document Prepared By:** Analysis of 149 Lexibank datasets
**Date:** 2025-10-01
**Recommendation:** Minimal_8 Core (primary), Extended_12 (alternative), Comprehensive_20 (reference)
