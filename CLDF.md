# CLDF Format Documentation

## Overview

This document describes the Cross-Linguistic Data Format (CLDF) structure as found in the 149 Lexibank repositories cloned for this project. All datasets are stored in `lexibank/<dataset_name>/cldf/` directories.

## CLDF Version

All 149 repositories conform to **CLDF v1.0** with the Wordlist module:
- `dc:conformsTo`: `http://cldf.clld.org/v1.0/terms.rdf#Wordlist`

However, there are variations in supporting reference data versions:
- **Glottolog**: Most use v5.0, some older datasets use v4.7
- **Concepticon**: Most use v3.2.0, some use v3.0.0
- **CLTS** (Cross-Linguistic Transcription Systems): Most use v2.3.0, some use v2.2.0

## File Structure

Each CLDF dataset directory contains:

### Core Files (all 149 datasets)

1. **cldf-metadata.json** - JSON-LD metadata describing the dataset structure
2. **forms.csv** - Primary lexical data (words/forms)
3. **languages.csv** - Language information
4. **parameters.csv** - Semantic concepts/meanings
5. **sources.bib** - BibTeX bibliography
6. **lingpy-rcParams.json** - LingPy configuration used for processing
7. **requirements.txt** - Python package dependencies

### Optional Files (frequency across datasets)

- **cognates.csv** - Cognate judgments (81/149 datasets)
- **media.csv** - Media file references (9/149 datasets)
- **cognatesets.csv** - Cognateset definitions (5/149 datasets)
- **contributions.csv** - Dataset contributors (3/149 datasets)
- **borrowings.csv** - Borrowing/loan information (3/149 datasets)
- **trees.csv** - Phylogenetic trees (3/149 datasets)
- **values.csv** - Feature values (3/149 datasets)
- **features.csv** - Feature definitions (3/149 datasets)
- **chapters.csv** - Semantic field chapters (1 dataset: ids)
- **etyma.csv** - Etymology data (1 dataset)
- **entries.csv** - Dictionary entries (1 dataset)
- **senses.csv** - Word senses (1 dataset)
- **clades.csv** - Phylogenetic clades (1 dataset)
- **authors.csv** - Author information (1 dataset)

## Core Table Schemas

### 1. forms.csv - FormTable

The primary data table containing lexical forms. All 149 datasets have this table.

#### Standard Columns (present in all/most datasets)

| Column | Description | Required | Example |
|--------|-------------|----------|---------|
| `ID` | Unique form identifier | Yes | `KusundaGM-1_above-1` |
| `Local_ID` | Source-specific identifier | No | varies |
| `Language_ID` | Foreign key to languages.csv | Yes | `KusundaGM` |
| `Parameter_ID` | Foreign key to parameters.csv | Yes | `1_above` |
| `Value` | Original form as written in source | Yes | `nɔŋ.ʣeː ɐŋ.ʣeː` |
| `Form` | Cleaned/normalized form | Yes | `ɐŋ.ʣeː` |
| `Segments` | Space-separated phoneme segments | No | `ɐ ŋ + dz eː` |
| `Comment` | Notes about the form | No | varies |
| `Source` | BibTeX citation keys (semicolon-separated) | No | `Bodt2019b` |
| `Loan` | Boolean indicating loanword | No | `true`/`false` |
| `Graphemes` | Graphemic representation | No | varies |
| `Profile` | Orthography profile used | No | `default` |

#### Common Optional Columns

- `Cognacy` - Cognate set membership (7/8 sampled datasets)
- `Transcriptions` - Alternative transcriptions
- `AlternativeValues` - Alternative form representations

#### Extended Columns (found in specialized datasets)

**WOLD (World Loanword Database) includes extensive borrowing information:**
- `Word_ID` - Word identifier
- `original_script` - Original orthography
- `Borrowed` - Borrowing status
- `Borrowed_score` - Borrowing probability score
- `comment_on_borrowed` - Notes on borrowing
- `borrowed_base` - Source of borrowing
- `loan_history` - History of borrowing
- `Analyzability` - Morphological analyzability
- `gloss` - English gloss
- `Simplicity_score` - Morphological simplicity
- `reference` - Cross-reference
- `relative_frequency` - Frequency ranking
- `numeric_frequency` - Absolute frequency
- `Age` - Age of word
- `Age_score` - Age score
- `integration` - Integration level
- `salience` - Cultural salience
- `effect` - Semantic effect
- `register` - Register/style
- `contact_situation` - Language contact context
- `calqued` - Whether calqued
- `grammatical_info` - Grammatical information
- `colonial_word` - Colonial-era word
- `etymological_note` - Etymology notes
- `lexical_stratum` - Lexical layer
- `word_source` - Source of word

### 2. languages.csv - LanguageTable

Language metadata with Glottolog integration. All 149 datasets have this table.

#### Standard Columns

| Column | Description | Example |
|--------|-------------|---------|
| `ID` | Unique language identifier | `KusundaGM` |
| `Name` | Language name | `Gyani Maiya` |
| `Glottocode` | Glottolog identifier | `kusu1250` |
| `Glottolog_Name` | Name from Glottolog | `Kusunda` |
| `ISO639P3code` | ISO 639-3 code | `kgg` |
| `Macroarea` | Geographic macro-area | `Eurasia` |
| `Latitude` | Decimal latitude | `28.0` |
| `Longitude` | Decimal longitude | `82.26` |
| `Family` | Language family | `Kusunda` |
| `Location` | Geographic location description | `Dang district` |
| `Remark` | Additional notes | varies |

### 3. parameters.csv - ParameterTable

Semantic concepts/meanings with Concepticon integration. All 149 datasets have this table.

#### Standard Columns

| Column | Description | Example |
|--------|-------------|---------|
| `ID` | Unique parameter identifier | `1_above` |
| `Name` | Concept name | `above` |
| `Concepticon_ID` | Concepticon identifier | `1741` |
| `Concepticon_Gloss` | Standard Concepticon gloss | `ABOVE` |

### 4. cognates.csv - CognateTable

Cognate judgments linking forms to cognate sets. Found in 81/149 datasets.

#### Standard Columns

| Column | Description | Example |
|--------|-------------|---------|
| `ID` | Unique cognate judgment ID | `Banoni_4-1_hand-1-1` |
| `Form_ID` | Foreign key to forms.csv | `Banoni_4-1_hand-1` |
| `Form` | The form being judged | `numa-` |
| `Cognateset_ID` | Cognate set identifier | `hand-1` |
| `Doubt` | Uncertain cognacy | `false` |
| `Cognate_Detection_Method` | How determined | `expert` |
| `Source` | Citation | `Greenhilletal2008` |
| `Alignment` | Phonetic alignment | varies |
| `Alignment_Method` | Alignment algorithm | varies |
| `Alignment_Source` | Source of alignment | varies |

### 5. borrowings.csv - BorrowingTable

Loanword/borrowing information. Found in 3 datasets (including WOLD).

#### Standard Columns

| Column | Description | Example |
|--------|-------------|---------|
| `ID` | Unique borrowing event ID | `1` |
| `Target_Form_ID` | Borrowed form (FK to forms.csv) | `Manange-1-28-1` |
| `Source_Form_ID` | Source form (optional FK) | varies |
| `Comment` | Notes | varies |
| `Source` | Citation | varies |
| `Source_relation` | Relationship type | `immediate` |
| `Source_word` | Source language word | `oɖhaar` |
| `Source_meaning` | Source word meaning | `cave` |
| `Source_certain` | Certainty | `yes` |
| `Source_languoid` | Source language name | `Nepali` |
| `Source_languoid_glottocode` | Source Glottocode | `nepa1252` |

### 6. contributions.csv - ContributionTable

Contribution/vocabulary metadata. Found in 3 datasets.

#### Standard Columns

| Column | Description |
|--------|-------------|
| `ID` | Contribution identifier |
| `Name` | Contribution name |
| `Description` | Description |
| `Contributor` | Contributor name |
| `Citation` | Full citation |
| `Number_of_words` | Word count |
| `Language_ID` | Foreign key to languages.csv |

### 7. chapters.csv

Semantic field organization (only in IDS dataset).

| Column | Description |
|--------|-------------|
| `ID` | Chapter ID |
| `Description` | Semantic field description |

## Data Model

### Primary Relationships

```
forms.csv
  ├─→ Language_ID ─→ languages.csv (ID)
  ├─→ Parameter_ID ─→ parameters.csv (ID)
  └─→ Source ─→ sources.bib

cognates.csv (when present)
  └─→ Form_ID ─→ forms.csv (ID)

borrowings.csv (when present)
  ├─→ Target_Form_ID ─→ forms.csv (ID)
  └─→ Source_Form_ID ─→ forms.csv (ID) [optional]

contributions.csv (when present)
  └─→ Language_ID ─→ languages.csv (ID)
```

### Key Concepts

1. **Form**: A lexical item (word) in a specific language for a specific concept
2. **Language**: A language variety with Glottolog metadata
3. **Parameter**: A semantic concept (e.g., "hand", "water") with Concepticon linking
4. **Cognateset**: A set of forms judged to be cognate (historically related)
5. **Borrowing**: A documented case of lexical borrowing between languages

## Data Characteristics

### Segmentation

The `Segments` column uses space-separated phonemes with special characters:
- `+` - morpheme boundary
- `.` - syllable boundary (in original Form, not in Segments)
- Space - separates individual segments/phonemes

Example: `ɐ ŋ + dz eː` represents /ɐŋ.ʣeː/ with morpheme boundary before /ʣeː/

### Transcription Systems

- Forms use IPA (International Phonetic Alphabet)
- Transcriptions are standardized using CLTS (Cross-Linguistic Transcription Systems)
- Each dataset may have a specific orthography profile

### Identifiers

- **Glottocodes**: Unique language identifiers from Glottolog (e.g., `kusu1250`)
- **Concepticon IDs**: Unique concept identifiers (e.g., `1741` for ABOVE)
- **ISO 639-3**: Three-letter language codes (e.g., `kgg` for Kusunda)

## Dataset Statistics

- Total repositories: 149
- Total conforming to CLDF Wordlist v1.0: 149 (100%)
- With cognate data: 81 (54%)
- With borrowing data: 3 (2%)
- With media files: 9 (6%)
- With cognateset definitions: 5 (3%)

## Processing Notes

### Metadata Format

The `cldf-metadata.json` file is a JSON-LD file following the W3C CSVW (CSV on the Web) standard. It contains:
1. Dataset citation and licensing
2. Provenance information (source repositories and versions)
3. Table schemas with column definitions
4. Foreign key relationships
5. Data types and validation rules

### LingPy Integration

All datasets include `lingpy-rcParams.json`, indicating they were processed with LingPy (a Python library for quantitative historical linguistics). This ensures:
- Consistent phoneme tokenization
- Standardized orthography profiles
- Validated transcriptions

### Common Caveats

1. **Missing values**: Many optional columns may be empty/null
2. **Version drift**: Different datasets may use different Glottolog/Concepticon versions
3. **Schema extensions**: Some datasets add custom columns not in the core CLDF spec
4. **Encoding**: All files use UTF-8 encoding for Unicode characters

## Compatibility Considerations

When merging datasets:

1. **Core columns are compatible**: All datasets share the same core FormTable schema
2. **Optional columns vary**: Handle missing columns gracefully
3. **Reference versions differ**: Glottolog/Concepticon IDs may need reconciliation
4. **Custom extensions**: WOLD and a few others have extensive custom columns
5. **Cognate data availability**: Only 54% have cognate judgments
