# Public Repository Preparation Plan - FINAL

## Decisions Made

1. ✅ MIGRATION.md: **Delete** (one-time transition, not needed long-term)
2. ✅ README style: **User-focused for historical linguists** (downloadable data, use cases)
3. ✅ Code examples: **Minimal** (basic usage only)
4. ✅ License: **MIT for code, CC-BY-4.0 for data** (standard practice)
5. ✅ .zenodo_state.json: **Keep tracked** in git
6. ✅ Directory structure: **Keep flat** (simple, accessible)
7. ✅ Examples: **Add later** based on demand
8. ✅ GitHub templates: **Wait** (not needed initially)
9. ✅ DOI badges: **Add placeholders** (update after first Zenodo release)

## Current State Analysis

The repository contains:
- ✅ Working code (3 Python scripts + 1 metadata CSV)
- ✅ Production release system (templates, Zenodo integration)
- ✅ Comprehensive technical documentation (MERGER_SPECIFICATION.md, RELEASE_WORKFLOW.md)
- ❌ No README.md (critical for GitHub landing page)
- ❌ No LICENSE file
- ❌ Historical/planning documents that are no longer needed
- ❌ datasets.csv is gitignored (needed for public use)

## Proposed Changes

### 1. Documentation Cleanup

#### Files to DELETE:
- `CORE_DATASET_PROPOSAL.md` (845 lines) - Initial proposal, superseded
- `CORE_DATASET_PROPOSAL_REVISED.md` (627 lines) - Revised proposal, superseded
- `CORE_IMPLEMENTATION_PLAN.md` (915 lines) - Planning document
- `CORE_IMPLEMENTATION_PLAN_V2.md` (1239 lines) - Planning document
- `IMPLEMENTATION_SUMMARY.md` (206 lines) - Implementation notes
- `QUALITY_ASSESSMENT.md` (783 lines) - Initial analysis (now in validation reports)
- `CLDF.md` (298 lines) - Format documentation (summarized in README)
- `MIGRATION.md` (296 lines) - One-time transition guide (no longer needed)

**Total to delete:** ~5,500 lines of historical documentation

**Rationale:** These were development artifacts. The implemented system is documented in MERGER_SPECIFICATION.md and RELEASE_WORKFLOW.md.

#### Files to KEEP:
- `MERGER_SPECIFICATION.md` - Technical specification for researchers
- `RELEASE_WORKFLOW.md` - Instructions for maintainers/reproducibility

### 2. Create README.md

**Style:** User-focused for historical linguists (not programmers)
**Tone:** Accessible, emphasize ready-to-use data over technical pipeline

**Proposed Structure:**

```markdown
# Arca Verborum: Global Lexical Database for Computational Historical Linguistics

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXX)
[![License: CC-BY-4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Code License: MIT](https://img.shields.io/badge/Code%20License-MIT-green.svg)](https://opensource.org/licenses/MIT)

A ready-to-use aggregation of comparative wordlist data from 149 Lexibank datasets,
designed for immediate use in computational historical linguistics research and education.

**Key Features:**
- **2.9M+ lexical forms** across 149 datasets and 6,000+ languages
- **Pre-joined metadata** (no CLDF wrangling needed)
- **Expert cognate judgments** from 81 datasets
- **Two collections:** Full (research) and Core (teaching/prototyping)
- **Analysis-ready CSV format** (pandas, R, Excel compatible)

## 🎯 For Historical Linguists

This dataset solves a common problem: CLDF's normalized structure is excellent for
data integrity but requires significant preprocessing before analysis. Arca Verborum
provides denormalized, analysis-ready files so you can start working immediately.

**Perfect for:**
- Rapid method development and prototyping
- Student projects and teaching computational linguistics
- Cross-linguistic statistical analysis
- Training machine learning models on linguistic data

## 📦 Download Data (Recommended)

Download pre-built archives from Zenodo:

- **[Full Collection](https://doi.org/10.5281/zenodo.XXXXXXX)** - All 149 datasets (~XX MB)
- **[Core Collection](https://doi.org/10.5281/zenodo.XXXXXXX)** - 9 curated datasets (~XX MB)

Each archive contains:
- `forms.csv` - Lexical forms with denormalized metadata
- `languages.csv` - Language information (Glottolog integration)
- `parameters.csv` - Semantic concepts (Concepticon integration)
- `metadata.csv` - Dataset-level information
- `sources.bib` - Merged bibliography
- `validation_report.json` - Quality metrics
- `DATASET_DESCRIPTION.md` - Complete documentation

### Quick Start (Python)

```python
import pandas as pd

# Load the data
forms = pd.read_csv('arcaverborum_20241002/forms.csv')

# Example: Forms with expert cognate judgments
cognate_forms = forms[forms['Cognacy'].notna()]

# Example: Filter by language family
indo_european = forms[forms['Glottolog_Name'].str.contains('Indo-European', na=False)]
```

### Quick Start (R)

```r
library(tidyverse)

# Load the data
forms <- read_csv('arcaverborum_20241002/forms.csv')

# Example: Forms with Concepticon mapping
concepticon_forms <- forms %>% filter(!is.na(Concepticon_Gloss))
```

## 📚 Collections

### Full Collection
- **149 Lexibank datasets**
- **~2.9M lexical forms** across 6,000+ languages
- Complete coverage for comprehensive research

### Core Collection
- **9 curated datasets** selected for:
  - Global geographic coverage (all 6 macroareas)
  - High Concepticon/Swadesh-100 coverage
  - Expert cognate sets and phonological alignments
  - Minimal language overlap

**Core Datasets:**
1. robinsonap (Papunesia)
2. bowernpny (Australia)
3. gravinachadic (Africa - Chadic)
4. grollemundbantu (Africa - Bantu)
5. peirosaustroasiatic (Eurasia - Austroasiatic)
6. iecor (Eurasia - Indo-European)
7. bdpa (Eurasia - Sino-Tibetan)
8. tuled (South America - Tupían)
9. utoaztecan (North America - Uto-Aztecan)

## 🔧 Building from Source (Advanced)

For reproducibility or customization:

```bash
# 1. Clone repository
git clone https://github.com/tresoldi/arcaverborum.git
cd arcaverborum

# 2. Install dependencies
pip install -r requirements.txt

# 3. Clone source datasets (all or core-only)
python clone_lexibank.py              # All 149 datasets
python clone_lexibank.py --core-only  # Just 9 core datasets

# 4. Build collections
python merge_cldf_datasets.py         # Creates output/full/ and output/core/

# 5. Prepare release archives
python prepare_release.py
```

See [RELEASE_WORKFLOW.md](RELEASE_WORKFLOW.md) for detailed build instructions.

## 📖 Documentation

- **[MERGER_SPECIFICATION.md](MERGER_SPECIFICATION.md)** - Technical specification and data processing details
- **[RELEASE_WORKFLOW.md](RELEASE_WORKFLOW.md)** - Building releases and publishing to Zenodo
- **DATASET_DESCRIPTION.md** - In each archive, complete dataset documentation

## 📊 Data Quality

Full collection metrics:
- **Glottolog coverage:** 95%+
- **Concepticon coverage:** 85%+
- **Forms with cognate data:** XX%
- **Forms with segmentation:** XX%

See `validation_report.json` in each archive for detailed quality metrics per dataset.

## 📄 Citation

If you use this dataset, please cite both:

**This dataset:**
```bibtex
@dataset{tresoldi2024arca,
  author       = {Tresoldi, Tiago},
  title        = {Arca Verborum: A Global Lexical Database for
                  Computational Historical Linguistics},
  year         = {2024},
  publisher    = {Zenodo},
  doi          = {10.5281/zenodo.XXXXXXX},
  url          = {https://doi.org/10.5281/zenodo.XXXXXXX}
}
```

**The Lexibank project:**
```bibtex
@article{list2022lexibank,
  title={Lexibank: A public repository of standardized wordlists with
         computed phonological and lexical features},
  author={List, Johann-Mattis and Forkel, Robert and Greenhill, Simon J and
          Rzymski, Christoph and Englisch, Johannes and Gray, Russell D},
  journal={Scientific Data},
  volume={9},
  number={1},
  pages={316},
  year={2022},
  doi={10.1038/s41597-022-01432-0}
}
```

## 📜 License

- **Code and scripts:** [MIT License](LICENSE)
- **Generated data:** [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/)
  (following source Lexibank datasets)

Individual dataset licenses are documented in `metadata.csv`.

## 🔗 Related Projects

- **[GLED](https://doi.org/10.5334/johd.96)** - Global Lexical Database (predecessor)
- **[Lexibank](https://lexibank.clld.org/)** - Source data repository
- **[CLDF](https://cldf.clld.org/)** - Cross-Linguistic Data Format

## 👤 Contact

**Tiago Tresoldi**
Department of Linguistics and Philology
Uppsala University
📧 tiago.tresoldi@lingfil.uu.se
🐙 [@tresoldi](https://github.com/tresoldi)

**Issues & Contributions:**
Please use [GitHub Issues](https://github.com/tresoldi/arcaverborum/issues)
for bug reports, feature requests, or questions.
```

### 3. Add LICENSE File (MIT)

Create standard MIT License for code:

```
MIT License

Copyright (c) 2024 Tiago Tresoldi

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

**Note:** Generated data remains CC-BY-4.0 (following Lexibank sources)

### 4. Fix datasets.csv in .gitignore

**Action:** Remove this line from `.gitignore`:
```
# CSV files (large datasets)
datasets.csv
```

datasets.csv (10KB) is essential metadata, not a large dataset file.

### 5. Final Repository Structure

```
arcaverborum/
├── .gitignore                 (cleaned: remove datasets.csv line)
├── .zenodo_state.json        (keep tracked)
├── README.md                  (NEW - user-focused for linguists)
├── LICENSE                    (NEW - MIT for code)
├── requirements.txt
├── datasets.csv              (UNIGNORE and commit)
├── zenodo.metadata.yml
├── clone_lexibank.py
├── merge_cldf_datasets.py
├── prepare_release.py
├── zenodo_publish.py
├── MERGER_SPECIFICATION.md   (keep - technical reference)
├── RELEASE_WORKFLOW.md       (keep - for maintainers)
└── templates/
    ├── DATASET_DESCRIPTION.md.j2
    └── RELEASE_NOTES.md.j2

DELETED (8 files, ~5,500 lines):
- CLDF.md
- CORE_DATASET_PROPOSAL.md
- CORE_DATASET_PROPOSAL_REVISED.md
- CORE_IMPLEMENTATION_PLAN.md
- CORE_IMPLEMENTATION_PLAN_V2.md
- IMPLEMENTATION_SUMMARY.md
- QUALITY_ASSESSMENT.md
- MIGRATION.md
```

**Result:** Clean, professional, user-focused repository.

## Implementation Checklist

1. **Delete historical documentation**
   - [ ] Delete 8 markdown files (CLDF.md, CORE_*.md, IMPLEMENTATION_SUMMARY.md, QUALITY_ASSESSMENT.md, MIGRATION.md)

2. **Create new files**
   - [ ] Create README.md with user-focused content (linguist audience)
   - [ ] Create LICENSE file (MIT license for code)

3. **Fix .gitignore**
   - [ ] Remove `datasets.csv` line from .gitignore
   - [ ] Review and clean up other entries if needed

4. **Git operations**
   - [ ] Commit datasets.csv to repository
   - [ ] Commit all new/modified files
   - [ ] Create annotated git tag (e.g., v1.0.0)

5. **Quality checks**
   - [ ] Verify all README code examples work
   - [ ] Check all internal documentation links
   - [ ] Test build commands from README
   - [ ] Spell check README

6. **Post-publication updates** (after first Zenodo release)
   - [ ] Replace DOI placeholders with actual DOIs
   - [ ] Update README badges
   - [ ] Update archive sizes (XX MB → actual)

## Additional Questions

**Q10: Year in LICENSE and citations**
The README draft uses "2024" - should this be:
- **Option A:** 2024 (current year)
- **Option B:** 2025 (anticipated publication year)
- **My recommendation:** Use actual publication year when finalizing

**Q11: Repository visibility**
When making repository public:
- **Option A:** Public immediately (with placeholders)
- **Option B:** Keep private until first Zenodo release with real DOIs
- **My recommendation:** Option B - cleaner first impression with real DOIs

**Q12: Archive file sizes in README**
README has "~XX MB" placeholders for archive sizes. Should I:
- **Option A:** Fill in approximate sizes from test build (~6 MB)
- **Option B:** Leave as XX MB until final release
- **My recommendation:** Option A - use test build sizes as estimates

**Q13: Quality metrics in README**
README has "XX%" placeholders for data quality. Should I:
- **Option A:** Fill from validation_report.json (if available)
- **Option B:** Leave as placeholders until first release
- **My recommendation:** Option A if we have the data

Do you want me to:
1. Fill in these placeholders now from existing data?
2. Make any other adjustments to the README draft?
3. Proceed with implementation once you approve?
