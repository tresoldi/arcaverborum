# CLDF Data Merger - Detailed Specification

## Project Overview

This specification describes the process of merging 149 CLDF (Cross-Linguistic Data Format) v1.0 Wordlist datasets from the Lexibank project into a unified set of CSV files for analysis. All source datasets are located in `lexibank/<dataset_name>/cldf/` directories.

## Input Data

### Source Structure
- **Location**: `lexibank/` directory containing 149 subdirectories
- **Format**: Each dataset contains a `cldf/` subdirectory with:
  - `cldf-metadata.json` - JSON-LD metadata
  - `forms.csv` - Lexical data (present in all 149 datasets)
  - `languages.csv` - Language metadata (present in all 149 datasets)
  - `parameters.csv` - Semantic concepts (present in all 149 datasets)
  - `cognates.csv` - Cognate judgments (present in 81/149 datasets)
  - `borrowings.csv` - Borrowing data (present in 3/149 datasets)
  - `sources.bib` - BibTeX references
  - Other optional files (not used in this merger)

### CLDF Version Compatibility
- All datasets conform to CLDF v1.0 Wordlist module
- Reference data versions vary:
  - Glottolog: v4.7 to v5.0
  - Concepticon: v3.0.0 to v3.2.0
  - CLTS: v2.2.0 to v2.3.0

## Output Files

Generate the following files in output directories (output/full/, output/core/, output/corecog/):

1. **forms.csv** - Merged lexical data with cognate and metadata integration
2. **languages.csv** - Merged language metadata
3. **parameters.csv** - Merged semantic concepts
4. **metadata.csv** - Dataset-level metadata
5. **sources.bib** - Merged BibTeX references
6. **validation_report.json** - Data quality report

## Detailed Output Schemas

### 1. forms.csv (24 columns)

| Column | Type | Source | Description | Example |
|--------|------|--------|-------------|---------|
| `ID` | string | forms.csv | Unique form identifier, prefixed with dataset name | `aaleykusunda_KusundaGM-1_above-1` |
| `Dataset` | string | NEW | Source dataset name | `aaleykusunda` |
| `Local_ID` | string | forms.csv | Original source-specific identifier | varies |
| `Language_ID` | string | forms.csv | Foreign key to languages, prefixed with dataset | `aaleykusunda_KusundaGM` |
| `Parameter_ID` | string | forms.csv | Foreign key to parameters, prefixed with dataset | `aaleykusunda_1_above` |
| `Value` | string | forms.csv | Original form as written in source (may contain multiple forms) | `nɔŋ.ʣeː ɐŋ.ʣeː` |
| `Form` | string | forms.csv | Cleaned/normalized form | `ɐŋ.ʣeː` |
| `Segments` | string | forms.csv | Space-separated phoneme segments | `ɐ ŋ + dz eː` |
| `Comment` | string | forms.csv | Notes about the form | varies |
| `Source` | string | forms.csv | BibTeX citation keys (semicolon-separated), prefixed | `aaleykusunda_Bodt2019b` |
| `Loan` | boolean | forms.csv | Boolean indicating loanword status | true/false/`<NA>` |
| `Graphemes` | string | forms.csv | Graphemic representation | `^ɐ ŋ . ʣ eː$` |
| `Profile` | string | forms.csv | Orthography profile used | `default` |
| `Cognacy` | string | forms.csv + cognates.csv | Merged cognate set IDs (semicolon-separated), prefixed | `aaleykusunda_42;aaleykusunda_hand-1` |
| `Doubt` | boolean | cognates.csv | Uncertain cognacy judgment | false/`<NA>` |
| `Cognate_Detection_Method` | string | cognates.csv | Method used for cognate judgment | `expert`/`<NA>` |
| `Cognate_Source` | string | cognates.csv | Citation for cognate judgment, prefixed | `abvdoceanic_Greenhilletal2008` |
| `Alignment` | string | cognates.csv | Phonetic alignment | `n u m a`/`<NA>` |
| `Glottocode` | string | JOIN from languages.csv | Glottolog identifier via Language_ID | `kusu1250` |
| `Glottolog_Name` | string | JOIN from languages.csv | Glottolog language name via Language_ID | `Kusunda` |
| `Concepticon_ID` | string | JOIN from parameters.csv | Concepticon identifier via Parameter_ID | `1741` |
| `Concepticon_Gloss` | string | JOIN from parameters.csv | Concepticon standard gloss via Parameter_ID | `ABOVE` |
| `Morpheme_Index` | string | cognates.csv | Partial cognacy: which morpheme is judged (4 datasets) | `1`/`2`/`<NA>` |
| `Segment_Slice` | string | cognates.csv | Partial cognacy: segment indices (3 datasets) | `1`/`1:3`/`<NA>` |

#### Special Processing Rules for forms.csv

**ID Prefixing:**
- Prefix all `ID`, `Language_ID`, `Parameter_ID` values with `<dataset>_`
- Example: `KusundaGM` → `aaleykusunda_KusundaGM`

**BibTeX Key Prefixing:**
- In `Source` and `Cognate_Source` columns, prefix all citation keys with `<dataset>_`
- Handle semicolon-separated lists: `Bodt2019b;Smith2020` → `aaleykusunda_Bodt2019b;aaleykusunda_Smith2020`

**Cognacy Merging:**
- If forms.csv contains a `Cognacy` column, prefix its values with dataset name
- If cognates.csv exists, aggregate all `Cognateset_ID` values for each form
- Merge both sources into single semicolon-separated string
- Example: forms.csv has `Cognacy="42"`, cognates.csv has cognatesets `["hand-1", "hand-66"]`
  - Result: `Cognacy = "aaleykusunda_42;aaleykusunda_hand-1;aaleykusunda_hand-66"`
- Prefix all cognateset IDs with dataset name

**Row Multiplication for Multiple Cognate Judgments:**
- When a form has multiple cognate judgments with DIFFERENT `Alignment` or `Morpheme_Index` values, create MULTIPLE rows
- Each row has the SAME `ID` but different alignment/morpheme-specific data
- The `Cognacy` column contains ALL cognatesets (semicolon-separated) in every row
- Example:
  ```
  Form ID: abvdoceanic_Banoni_hand-1
  Cognate judgments:
    - Cognateset: hand-1, Alignment: "n u m a", Morpheme_Index: <NA>
    - Cognateset: hand-66, Alignment: "n u - -", Morpheme_Index: <NA>

  Result: 2 rows
    Row 1: ID=abvdoceanic_Banoni_hand-1, Cognacy="abvdoceanic_hand-1;abvdoceanic_hand-66", Alignment="n u m a"
    Row 2: ID=abvdoceanic_Banoni_hand-1, Cognacy="abvdoceanic_hand-1;abvdoceanic_hand-66", Alignment="n u - -"
  ```

**Partial Cognacy Support:**
- `Morpheme_Index`: Found in 4 datasets (mannburmish, mixtecansubgrouping, bodtkhobwa, luangthongkumkaren)
  - Indicates which morpheme within a polymorphemic form is being judged
  - Example: Form "mau³⁴ kʰoŋ³²" may have judgments with Morpheme_Index=1 (first morpheme) and Morpheme_Index=2 (second morpheme)
  - Creates multiple rows per form when different morphemes belong to different cognatesets
- `Segment_Slice`: Found in 3 datasets (tuled, kahd, liusinitic)
  - Indicates which segment indices are part of the cognate judgment
  - Values like "1" or "1:3" indicate segment ranges

**Denormalized Metadata:**
- Join `Glottocode` and `Glottolog_Name` from languages.csv via `Language_ID`
- Join `Concepticon_ID` and `Concepticon_Gloss` from parameters.csv via `Parameter_ID`
- Use LEFT JOIN to preserve forms even if metadata is missing

**Borrowing/Loan Status:**
- The `Loan` column from forms.csv already contains boolean borrowing status
- borrowings.csv is NOT used (we ignore it entirely)
- No additional borrowing columns are added

**NULL Handling:**
- Distinguish three types of missing data:
  1. `<NA>` (pandas.NA): Column did not exist in source dataset
  2. `""` (empty string): Cell was empty in the CSV
  3. `None`/`null`: Missing value in an existing column
- Track which columns were present/absent per dataset for validation report

### 2. languages.csv (12 columns)

| Column | Type | Source | Description | Example |
|--------|------|--------|-------------|---------|
| `ID` | string | languages.csv | Unique language identifier, prefixed | `aaleykusunda_KusundaGM` |
| `Dataset` | string | NEW | Source dataset name | `aaleykusunda` |
| `Name` | string | languages.csv | Language/variety name | `Gyani Maiya` |
| `Glottocode` | string | languages.csv | Glottolog identifier (standardized) | `kusu1250` |
| `Glottolog_Name` | string | languages.csv | Name from Glottolog | `Kusunda` |
| `ISO639P3code` | string | languages.csv | ISO 639-3 code | `kgg` |
| `Macroarea` | string | languages.csv | Geographic macro-area | `Eurasia` |
| `Latitude` | float | languages.csv | Decimal latitude | `28.0` |
| `Longitude` | float | languages.csv | Decimal longitude | `82.26` |
| `Family` | string | languages.csv | Language family | `Kusunda` |
| `Location` | string | languages.csv | Geographic location description | `Dang district` |
| `Remark` | string | languages.csv | Additional notes | varies |

#### Processing Rules
- Prefix all `ID` values with dataset name
- Keep all entries (no deduplication) - different datasets may have different metadata for same Glottocode
- Preserve all columns as-is after ID prefixing

### 3. parameters.csv (5 columns)

| Column | Type | Source | Description | Example |
|--------|------|--------|-------------|---------|
| `ID` | string | parameters.csv | Unique parameter identifier, prefixed | `aaleykusunda_1_above` |
| `Dataset` | string | NEW | Source dataset name | `aaleykusunda` |
| `Name` | string | parameters.csv | Concept name | `above` |
| `Concepticon_ID` | string | parameters.csv | Concepticon identifier (standardized) | `1741` |
| `Concepticon_Gloss` | string | parameters.csv | Standard Concepticon gloss | `ABOVE` |

#### Processing Rules
- Prefix all `ID` values with dataset name
- Keep all entries (no deduplication) - preserve per-dataset concept mappings
- `Concepticon_ID` should be consistent across datasets for same concept, but keep separate rows per dataset

### 4. References (included in metadata.csv)

Reference version information is included in the validation_report.json under the "version_distribution" key.

#### Extraction Logic
Parse `cldf-metadata.json` for each dataset and include in validation report:
```json
"prov:wasDerivedFrom": [
  {
    "rdf:about": "https://github.com/glottolog/glottolog",
    "dc:created": "v5.0",
    "dc:title": "Glottolog"
  },
  {
    "rdf:about": "https://github.com/concepticon/concepticon-data",
    "dc:created": "v3.2.0",
    "dc:title": "Concepticon"
  },
  {
    "rdf:about": "https://github.com/cldf-clts/clts",
    "dc:created": "v2.3.0",
    "dc:title": "CLTS"
  }
]
```

### 5. metadata.csv (11 columns)

| Column | Type | Source | Description | Example |
|--------|------|--------|-------------|---------|
| `Dataset` | string | rdf:ID | Dataset identifier | `aaleykusunda` |
| `Title` | string | dc:title | Dataset title | `CLDF dataset derived from...` |
| `Citation` | string | dc:bibliographicCitation | Full bibliographic citation | `Uday Raj Aaley...` |
| `URL` | string | dcat:accessURL | GitHub repository URL | `https://github.com/lexibank/aaleykusunda` |
| `License` | string | dc:license | License URL | `https://creativecommons.org/licenses/by/4.0/` |
| `CLDF_Module` | string | dc:conformsTo | CLDF module type | `Wordlist` |
| `Repository_Version` | string | prov:wasDerivedFrom | Git version of repository | `v2.0-3-g3bfaaf5` |
| `Python_Version` | string | prov:wasGeneratedBy | Python version used | `3.12.4` |
| `Form_Count` | int | tables[FormTable].dc:extent | Number of forms in dataset | `662` |
| `Language_Count` | int | tables[LanguageTable].dc:extent | Number of languages | `3` |
| `Parameter_Count` | int | tables[ParameterTable].dc:extent | Number of parameters | `230` |
| `Has_Cognates` | boolean | Computed | Whether cognates.csv exists | `false` |

#### Extraction Logic
- Parse each dataset's `cldf-metadata.json`
- Extract metadata fields from JSON-LD structure
- `CLDF_Module`: Extract simple name from URL (e.g., `http://cldf.clld.org/v1.0/terms.rdf#Wordlist` → `Wordlist`)
- `Repository_Version`: From `prov:wasDerivedFrom` where `dc:title` = "Repository"
- Counts: From `dc:extent` in each table definition

### 6. sources.bib

Merge all `sources.bib` files with prefixed citation keys.

#### Processing Rules
1. For each dataset, load `lexibank/<dataset>/cldf/sources.bib`
2. Parse BibTeX entries
3. Prefix each citation key with `<dataset>_`
4. Keep all entries, including duplicates (same reference cited by multiple datasets)
5. Output single merged BibTeX file

Example:
```bibtex
@article{aaleykusunda_Bodt2019b,
  author = {Bodt, Timotheus A.},
  title = {New Kusunda data},
  ...
}

@book{abvdoceanic_Greenhilletal2008,
  author = {Greenhill, S.J. and Blust, R. and Gray, R.D.},
  title = {The Austronesian Basic Vocabulary Database},
  ...
}
```

### 7. validation_report.json

Generate comprehensive data quality report in JSON format.

#### Structure

```json
{
  "summary": {
    "total_datasets": 149,
    "total_forms": 123456,
    "total_languages": 789,
    "total_parameters": 12345,
    "datasets_with_cognates": 81,
    "datasets_with_partial_cognacy": 7,
    "forms_with_multiple_cognatesets": 5432
  },
  "completeness": {
    "<dataset_name>": {
      "forms": 662,
      "languages": 3,
      "parameters": 230,
      "has_cognates": false,
      "columns_present": ["ID", "Form", "Segments", ...],
      "columns_absent": ["Borrowed", "Age", ...],
      "null_percentage": {
        "Segments": 0.0,
        "Comment": 95.3,
        "Loan": 100.0,
        ...
      },
      "empty_vs_missing": {
        "Comment": {
          "filled": 652,
          "empty_string": 10,
          "missing_na": 0
        },
        ...
      }
    },
    ...
  },
  "referential_integrity": {
    "orphan_language_ids": 0,
    "orphan_parameter_ids": 0,
    "invalid_bibtex_references": 12,
    "forms_without_glottocode": 45,
    "forms_without_concepticon_id": 23
  },
  "data_quality": {
    "glottocode_coverage_percent": 98.5,
    "concepticon_coverage_percent": 97.2,
    "forms_with_cognate_data_percent": 54.3,
    "forms_with_segments_percent": 99.8,
    "forms_with_alignment_percent": 45.2
  },
  "version_distribution": {
    "glottolog": {
      "v5.0": 140,
      "v4.7": 9
    },
    "concepticon": {
      "v3.2.0": 140,
      "v3.0.0": 9
    },
    "clts": {
      "v2.3.0": 140,
      "v2.2.0": 9
    }
  },
  "partial_cognacy": {
    "datasets_with_morpheme_index": [
      "mannburmish",
      "mixtecansubgrouping",
      "bodtkhobwa",
      "luangthongkumkaren"
    ],
    "datasets_with_segment_slice": [
      "tuled",
      "kahd",
      "liusinitic"
    ],
    "forms_with_morpheme_index": 4567,
    "forms_with_segment_slice": 2341
  },
  "row_multiplication": {
    "forms_with_multiple_alignments": 3456,
    "total_duplicate_ids_from_cognates": 8901
  }
}
```

#### Validation Checks

1. **Completeness per Dataset:**
   - Count rows in each table
   - Calculate NULL percentage per column
   - Distinguish: filled, empty string (""), missing (NA)
   - Track which columns were present vs. absent

2. **Referential Integrity:**
   - Verify all `Language_ID` in forms exist in languages table
   - Verify all `Parameter_ID` in forms exist in parameters table
   - Count orphaned references

3. **Data Quality:**
   - Calculate coverage percentages for key fields
   - Count forms with segments, alignments, cognate data
   - Identify missing Glottocodes and Concepticon IDs

4. **Version Distribution:**
   - Count datasets using each version of Glottolog/Concepticon/CLTS

5. **Partial Cognacy:**
   - List datasets with Morpheme_Index or Segment_Slice
   - Count forms with partial cognacy data

6. **Row Multiplication:**
   - Count forms that appear in multiple rows due to multiple cognate judgments
   - Report total duplicate IDs

### 8. Requirements

See requirements.txt in repository root for dependencies.

## Data Processing Pipeline

### Step 1: Dataset Discovery

```python
datasets = [d.name for d in Path('lexibank').iterdir()
            if d.is_dir() and (d / 'cldf' / 'cldf-metadata.json').exists()]
# Expected: 149 datasets
```

### Step 2: Metadata Extraction

For each dataset:
1. Load `cldf-metadata.json`
2. Extract metadata fields for metadata.parquet
3. Extract reference versions for references.parquet
4. Store for later concatenation

### Step 3: Per-Dataset Table Processing

For each dataset, process in this order:

#### 3.1 Load Core Tables

```python
# Load with proper encoding
forms = pd.read_csv(f'lexibank/{dataset}/cldf/forms.csv', encoding='utf-8')
languages = pd.read_csv(f'lexibank/{dataset}/cldf/languages.csv', encoding='utf-8')
parameters = pd.read_csv(f'lexibank/{dataset}/cldf/parameters.csv', encoding='utf-8')

# Add Dataset column
forms['Dataset'] = dataset
languages['Dataset'] = dataset
parameters['Dataset'] = dataset

# Prefix IDs
forms['ID'] = dataset + '_' + forms['ID'].astype(str)
forms['Language_ID'] = dataset + '_' + forms['Language_ID'].astype(str)
forms['Parameter_ID'] = dataset + '_' + forms['Parameter_ID'].astype(str)

languages['ID'] = dataset + '_' + languages['ID'].astype(str)
parameters['ID'] = dataset + '_' + parameters['ID'].astype(str)

# Prefix BibTeX keys in Source columns
forms['Source'] = prefix_bibtex_keys(forms['Source'], dataset)
```

#### 3.2 Process Cognates (if exists)

```python
if (Path(f'lexibank/{dataset}/cldf/cognates.csv').exists()):
    cognates = pd.read_csv(f'lexibank/{dataset}/cldf/cognates.csv', encoding='utf-8')

    # Prefix IDs
    cognates['Form_ID'] = dataset + '_' + cognates['Form_ID'].astype(str)
    cognates['Cognateset_ID'] = dataset + '_' + cognates['Cognateset_ID'].astype(str)

    # Prefix BibTeX keys
    if 'Source' in cognates.columns:
        cognates['Source'] = prefix_bibtex_keys(cognates['Source'], dataset)

    # Merge cognacy information
    forms = merge_cognate_data(forms, cognates, dataset)
else:
    # Add empty cognate columns
    for col in ['Cognateset_ID', 'Doubt', 'Cognate_Detection_Method',
                'Cognate_Source', 'Alignment', 'Morpheme_Index', 'Segment_Slice']:
        forms[col] = pd.NA
```

#### 3.3 Merge Cognacy Column

```python
def merge_cognate_data(forms, cognates, dataset):
    """
    Merge cognacy from forms.csv and cognates.csv.
    Handle multiple cognatesets and create multiple rows when needed.
    """
    # Preserve original Cognacy column from forms.csv
    forms_cognacy = forms['Cognacy'].copy() if 'Cognacy' in forms.columns else None

    # Prefix forms.csv Cognacy values
    if forms_cognacy is not None:
        forms_cognacy = forms_cognacy.apply(
            lambda x: f"{dataset}_{x}" if pd.notna(x) else pd.NA
        )

    # Aggregate cognatesets per form
    cognateset_list = cognates.groupby('Form_ID')['Cognateset_ID'].apply(
        lambda x: ';'.join(x)
    )

    # Check if multiple alignments/morpheme indices exist per form
    forms_with_multiple = cognates.groupby('Form_ID').filter(
        lambda x: x['Alignment'].nunique() > 1 or
                  (('Morpheme_Index' in x.columns) and x['Morpheme_Index'].nunique() > 1)
    )

    if not forms_with_multiple.empty:
        # Need to create multiple rows
        expanded_rows = []

        for form_id in forms_with_multiple['Form_ID'].unique():
            form_base = forms[forms['ID'] == form_id].iloc[0].copy()
            cognate_rows = cognates[cognates['Form_ID'] == form_id]

            # Get all cognatesets for this form
            all_cognatesets = ';'.join(cognate_rows['Cognateset_ID'])

            # Create one row per distinct alignment/morpheme combination
            for _, cog_row in cognate_rows.iterrows():
                new_row = form_base.copy()
                new_row['Cognacy'] = all_cognatesets  # ALL cognatesets
                new_row['Alignment'] = cog_row.get('Alignment', pd.NA)
                new_row['Doubt'] = cog_row.get('Doubt', pd.NA)
                new_row['Cognate_Detection_Method'] = cog_row.get('Cognate_Detection_Method', pd.NA)
                new_row['Cognate_Source'] = cog_row.get('Source', pd.NA)
                new_row['Morpheme_Index'] = cog_row.get('Morpheme_Index', pd.NA)
                new_row['Segment_Slice'] = cog_row.get('Segment_Slice', pd.NA)
                expanded_rows.append(new_row)

        # Remove original rows and add expanded rows
        forms = forms[~forms['ID'].isin(forms_with_multiple['Form_ID'].unique())]
        forms = pd.concat([forms, pd.DataFrame(expanded_rows)], ignore_index=True)

    # For forms with single cognate judgments, merge normally
    single_judgment_forms = cognates.groupby('Form_ID').filter(
        lambda x: x['Alignment'].nunique() <= 1 and
                  (('Morpheme_Index' not in x.columns) or x['Morpheme_Index'].nunique() <= 1)
    )

    if not single_judgment_forms.empty:
        cognate_agg = single_judgment_forms.groupby('Form_ID').agg({
            'Cognateset_ID': lambda x: ';'.join(x),
            'Alignment': 'first',
            'Doubt': 'first',
            'Cognate_Detection_Method': 'first',
            'Source': 'first',
            'Morpheme_Index': 'first' if 'Morpheme_Index' in single_judgment_forms.columns else lambda x: pd.NA,
            'Segment_Slice': 'first' if 'Segment_Slice' in single_judgment_forms.columns else lambda x: pd.NA
        }).reset_index()

        cognate_agg.columns = ['ID', 'Cognateset_ID_from_cog', 'Alignment', 'Doubt',
                                'Cognate_Detection_Method', 'Cognate_Source',
                                'Morpheme_Index', 'Segment_Slice']

        forms = forms.merge(cognate_agg, on='ID', how='left', suffixes=('', '_cog'))

    # Combine forms.csv Cognacy with cognates.csv Cognateset_IDs
    if forms_cognacy is not None:
        forms['Cognacy'] = forms.apply(
            lambda row: combine_cognacy_sources(row, forms_cognacy),
            axis=1
        )
    else:
        forms['Cognacy'] = forms.get('Cognateset_ID_from_cog', pd.NA)

    return forms

def combine_cognacy_sources(row, forms_cognacy):
    """Combine cognacy from forms.csv and cognates.csv"""
    parts = []

    # Add forms.csv cognacy
    if pd.notna(forms_cognacy.get(row.name)):
        parts.append(forms_cognacy.get(row.name))

    # Add cognates.csv cognatesets
    if 'Cognateset_ID_from_cog' in row and pd.notna(row['Cognateset_ID_from_cog']):
        parts.append(row['Cognateset_ID_from_cog'])

    return ';'.join(parts) if parts else pd.NA
```

#### 3.4 Join Metadata

```python
# Join language metadata
forms = forms.merge(
    languages[['ID', 'Glottocode', 'Glottolog_Name']],
    left_on='Language_ID',
    right_on='ID',
    how='left',
    suffixes=('', '_lang')
).drop(columns=['ID_lang'])

# Join parameter metadata
forms = forms.merge(
    parameters[['ID', 'Concepticon_ID', 'Concepticon_Gloss']],
    left_on='Parameter_ID',
    right_on='ID',
    how='left',
    suffixes=('', '_param')
).drop(columns=['ID_param'])
```

#### 3.5 Process BibTeX Sources

```python
sources_bib = load_bibtex(f'lexibank/{dataset}/cldf/sources.bib')
prefixed_sources = prefix_all_bibtex_keys(sources_bib, dataset)
all_sources.append(prefixed_sources)
```

### Step 4: Streaming Append to CSV

The implementation uses streaming CSV appends rather than in-memory concatenation to handle large datasets efficiently:

```python
# Append each dataset to CSV files as processed
for dataset in datasets:
    forms, languages, parameters, ... = process_dataset(dataset)

    # Append to CSV files (write header only on first append)
    append_to_csv(output_dir / 'forms.csv', forms, is_first_write)
    append_to_csv(output_dir / 'languages.csv', languages, is_first_write)
    append_to_csv(output_dir / 'parameters.csv', parameters, is_first_write)

    # Accumulate metadata and validation stats
    validator.update(dataset, forms, languages, parameters, ...)
```

### Step 5: Validation

Generate `validation_report.json` with all metrics described in section 7.

### Step 6: Output

CSV files are written incrementally during processing. Final outputs:

```python
# CSV files are already written via streaming append

# Write metadata and validation report
pd.DataFrame(validator.all_metadata).to_csv(
    output_dir / 'metadata.csv', index=False
)

with open(output_dir / 'validation_report.json', 'w', encoding='utf-8') as f:
    json.dump(validator.generate_report(), f, indent=2, ensure_ascii=False)

# Write merged BibTeX
with open(output_dir / 'sources.bib', 'w', encoding='utf-8') as f:
    f.write('\n\n'.join(validator.all_bibtex))
```

## Important Implementation Notes

### NULL Handling Strategy

Distinguish and preserve three types of missing data:

1. **Column did not exist** in source CSV → `pandas.NA`
2. **Empty string** in CSV cell → `""`
3. **Missing value** in existing column → `None` or `pandas.NA`

Track in validation report which columns existed in each dataset to distinguish case 1 from cases 2 and 3.

### BibTeX Key Prefixing

When prefixing BibTeX keys in `Source` columns:
- Handle semicolon-separated lists
- Handle empty/missing values
- Preserve original formatting

Example function:
```python
def prefix_bibtex_keys(source_str, dataset):
    if pd.isna(source_str) or source_str == '':
        return source_str
    keys = [k.strip() for k in str(source_str).split(';')]
    prefixed = [f"{dataset}_{k}" for k in keys if k]
    return ';'.join(prefixed)
```

### Encoding

- All CSV files use UTF-8 encoding
- BibTeX files use UTF-8

### Data Types

Ensure proper data types in CSV output:
- IDs: `string` (not object)
- Booleans: `boolean` (nullable) - represented as True/False/NA in CSV
- Floats: `float64`
- Integers: `int64`

### Performance Considerations

- Use streaming CSV appends to avoid loading all data in memory
- Process datasets one at a time and append incrementally
- Use efficient pandas operations (avoid iterrows when possible)
- Accumulate validation statistics incrementally using ValidationAccumulator

## Expected Output Sizes

Approximate row counts and file sizes:
- **forms.csv**: ~2.9M rows, ~500 MB (depending on cognate row multiplication)
- **languages.csv**: ~10,000 rows, ~1 MB
- **parameters.csv**: ~170,000 rows, ~12 MB
- **metadata.csv**: 149 rows (one per dataset)
- **sources.bib**: ~2 MB
- **validation_report.json**: ~100 KB

## Success Criteria

1. All 149 datasets successfully processed
2. No data loss (all rows from source CSVs present in output)
3. All IDs properly prefixed and unique
4. Referential integrity maintained (all foreign keys valid)
5. NULL values properly distinguished and documented
6. Validation report generated with complete metrics
7. All output files created successfully
