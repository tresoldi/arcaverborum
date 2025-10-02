# Arca Verborum: Global Lexical Database for Computational Historical Linguistics

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXX)
[![License: CC-BY-4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Code License: MIT](https://img.shields.io/badge/Code%20License-MIT-green.svg)](https://opensource.org/licenses/MIT)

A ready-to-use aggregation of comparative wordlist data from 149 Lexibank datasets, designed for immediate use in computational historical linguistics research and education.

**Key Features:**
- **2.9M+ lexical forms** across 149 datasets and 6,000+ languages
- **Pre-joined metadata** (no CLDF wrangling needed)
- **Expert cognate judgments** from 81 datasets
- **Two collections:** Full (research) and Core (teaching/prototyping)
- **Analysis-ready CSV format** (pandas, R, Excel compatible)

## For Historical Linguists

This dataset solves a common problem: CLDF's normalized structure is excellent for data integrity but requires significant preprocessing before analysis. Arca Verborum provides denormalized, analysis-ready files so you can start working immediately.

**Perfect for:**
- Rapid method development and prototyping
- Student projects and teaching computational linguistics
- Cross-linguistic statistical analysis
- Training machine learning models on linguistic data

## Download Data (Recommended)

Download pre-built archives from Zenodo:

- **[Full Collection](https://doi.org/10.5281/zenodo.XXXXXXX)** - All 149 datasets (~200 MB)
- **[Core Collection](https://doi.org/10.5281/zenodo.XXXXXXX)** - 9 curated datasets (~6 MB)

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
forms = pd.read_csv('arcaverborum_20251002/forms.csv')

# Example: Forms with expert cognate judgments
cognate_forms = forms[forms['Cognacy'].notna()]

# Example: Filter by language family
indo_european = forms[forms['Glottolog_Name'].str.contains('Indo-European', na=False)]
```

### Quick Start (R)

```r
library(tidyverse)

# Load the data
forms <- read_csv('arcaverborum_20251002/forms.csv')

# Example: Forms with Concepticon mapping
concepticon_forms <- forms %>% filter(!is.na(Concepticon_Gloss))
```

## Collections

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

## Building from Source (Advanced)

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

## Documentation

- **[MERGER_SPECIFICATION.md](MERGER_SPECIFICATION.md)** - Technical specification and data processing details
- **[RELEASE_WORKFLOW.md](RELEASE_WORKFLOW.md)** - Building releases and publishing to Zenodo
- **DATASET_DESCRIPTION.md** - In each archive, complete dataset documentation

## Data Quality

Full collection metrics:
- **Glottolog coverage:** 94%
- **Concepticon coverage:** 94%
- **Forms with cognate data:** 99.5%
- **Forms with segmentation:** 97%

See `validation_report.json` in each archive for detailed quality metrics per dataset.

## Citation

If you use this dataset, please cite both:

**This dataset:**
```bibtex
@dataset{tresoldi2025arca,
  author       = {Tresoldi, Tiago},
  title        = {Arca Verborum: A Global Lexical Database for
                  Computational Historical Linguistics},
  year         = {2025},
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

## License

- **Code and scripts:** [MIT License](LICENSE)
- **Generated data:** [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/) (following source Lexibank datasets)

Individual dataset licenses are documented in `metadata.csv`.

## Related Projects

- **[GLED](https://doi.org/10.5334/johd.96)** - Global Lexical Database (predecessor)
- **[Lexibank](https://lexibank.clld.org/)** - Source data repository
- **[CLDF](https://cldf.clld.org/)** - Cross-Linguistic Data Format

## Contact

**Tiago Tresoldi**
Department of Linguistics and Philology
Uppsala University
Email: tiago.tresoldi@lingfil.uu.se
GitHub: [@tresoldi](https://github.com/tresoldi)

**Issues & Contributions:**
Please use [GitHub Issues](https://github.com/tresoldi/arcaverborum/issues) for bug reports, feature requests, or questions.
