#!/usr/bin/env python3

"""
CLDF Dataset Merger

Merges Lexibank CLDF datasets into unified CSV files.
See MERGER_SPECIFICATION.md for details.

Usage:
    python merge_cldf_datasets.py [--input lexibank/] [--output output/] [--verbose]
"""

import pandas as pd
import json
from pathlib import Path
import re
import logging
from typing import Dict, List, Optional, Tuple
import argparse
import sys
import gc
import os

try:
    import bibtexparser
except ImportError:
    print("Error: bibtexparser not installed. Run: pip install bibtexparser>=1.4.0")
    sys.exit(1)

# === CONFIGURATION ===
LEXIBANK_DIR = Path('lexibank')
OUTPUT_DIR = Path('output')

# Expected columns for forms.csv (ensures consistent schema)
FORMS_COLUMNS = [
    'ID', 'Dataset', 'Local_ID', 'Language_ID', 'Parameter_ID',
    'Value', 'Form', 'Segments', 'Comment', 'Source', 'Loan',
    'Graphemes', 'Profile', 'Cognacy', 'Doubt', 'Cognate_Detection_Method',
    'Cognate_Source', 'Alignment', 'Glottocode', 'Glottolog_Name',
    'Concepticon_ID', 'Concepticon_Gloss', 'Morpheme_Index', 'Segment_Slice'
]

LANGUAGES_COLUMNS = [
    'ID', 'Dataset', 'Name', 'Glottocode', 'Glottolog_Name',
    'ISO639P3code', 'Macroarea', 'Latitude', 'Longitude',
    'Family', 'Location', 'Remark'
]

PARAMETERS_COLUMNS = [
    'ID', 'Dataset', 'Name', 'Concepticon_ID', 'Concepticon_Gloss'
]

# === LOGGING SETUP ===
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# === HELPER FUNCTIONS ===

def prefix_bibtex_keys(source_str: str, dataset: str) -> str:
    """
    Prefix BibTeX citation keys with dataset name.

    @param source_str: Semicolon-separated citation keys
    @param dataset: Dataset name to use as prefix
    @return: Prefixed citation keys
    """
    if pd.isna(source_str) or source_str == '':
        return source_str

    keys = [k.strip() for k in str(source_str).split(';')]
    prefixed = [f"{dataset}_{k}" for k in keys if k]
    return ';'.join(prefixed)


def prefix_bibtex_file(bibtex_content: str, dataset: str) -> str:
    """
    Prefix all BibTeX entry keys in a BibTeX file.

    @param bibtex_content: BibTeX file content
    @param dataset: Dataset name to use as prefix
    @return: BibTeX content with prefixed keys
    """
    try:
        # Configure parser to accept all entry types (including non-standard ones)
        parser = bibtexparser.bparser.BibTexParser()
        parser.ignore_nonstandard_types = False  # Accept thesis, webpage, online, software, etc.
        parser.homogenize_fields = False  # Preserve original field names

        bib_db = bibtexparser.loads(bibtex_content, parser=parser)

        # Prefix all entry IDs
        for entry in bib_db.entries:
            entry['ID'] = f"{dataset}_{entry['ID']}"

        return bibtexparser.dumps(bib_db)
    except Exception as e:
        logger.warning(f"Failed to parse BibTeX for {dataset}: {e}")
        # Fallback to regex-based approach
        return re.sub(
            r'@(\w+)\{([^,]+),',
            lambda m: f"@{m.group(1)}{{{dataset}_{m.group(2)},",
            bibtex_content
        )


def load_bibtex(path: Path) -> str:
    """Load BibTeX file content."""
    if not path.exists():
        return ""

    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.warning(f"Failed to load BibTeX from {path}: {e}")
        return ""


def prefix_ids_column(series: pd.Series, dataset: str) -> pd.Series:
    """Prefix all values in a series with dataset name."""
    return series.apply(lambda x: f"{dataset}_{x}" if pd.notna(x) else pd.NA)


def ensure_columns(df: pd.DataFrame, expected_columns: List[str]) -> pd.DataFrame:
    """
    Ensure dataframe has all expected columns, adding missing ones as NA.

    @param df: Input dataframe
    @param expected_columns: List of expected column names
    @return: Dataframe with all expected columns
    """
    for col in expected_columns:
        if col not in df.columns:
            df[col] = pd.NA

    # Reorder to match expected order
    return df[expected_columns]


def track_column_presence(df: pd.DataFrame, original_columns: List[str]) -> Dict[str, bool]:
    """
    Track which columns were originally present in the CSV.

    @param df: Dataframe after loading
    @param original_columns: Original column names from CSV
    @return: Dictionary mapping column names to presence
    """
    return {col: col in original_columns for col in df.columns}


def append_to_csv(filepath: Path, df: pd.DataFrame, is_first_write: bool):
    """
    Append dataframe to CSV file.

    @param filepath: Path to output CSV file
    @param df: Dataframe to write
    @param is_first_write: If True, write header; otherwise append without header
    """
    mode = 'w' if is_first_write else 'a'
    header = is_first_write
    df.to_csv(filepath, mode=mode, header=header, index=False, encoding='utf-8')


def initialize_output_files(output_dir: Path):
    """
    Initialize output directory and remove old files/partitions.

    @param output_dir: Output directory path
    """
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Remove old CSV files
    for csv_file in ['forms.csv', 'languages.csv', 'parameters.csv']:
        csv_path = output_dir / csv_file
        if csv_path.exists():
            csv_path.unlink()
            logger.debug(f"Removed old file: {csv_path}")

    # Remove old partition directories (from previous parquet-based runs)
    for parts_dir_name in ['forms_parts', 'languages_parts', 'parameters_parts']:
        parts_dir = output_dir / parts_dir_name
        if parts_dir.exists():
            import shutil
            shutil.rmtree(parts_dir)
            logger.debug(f"Removed old partition directory: {parts_dir}")


class ValidationAccumulator:
    """
    Accumulate validation statistics as datasets are processed.
    Uses minimal memory by storing only counters and summaries.
    """

    def __init__(self):
        self.total_forms = 0
        self.total_languages = 0
        self.total_parameters = 0
        self.datasets_processed = 0
        self.datasets_with_cognates = 0

        # Quality metrics counters
        self.forms_with_glottocode = 0
        self.forms_with_concepticon = 0
        self.forms_with_cognacy = 0
        self.forms_with_segments = 0
        self.forms_with_alignment = 0
        self.forms_with_morpheme_index = 0
        self.forms_with_segment_slice = 0

        # Collect small tables in memory
        self.all_metadata = []
        self.all_references = []
        self.all_bibtex = []
        self.all_column_tracking = []

        # Track datasets by feature
        self.datasets_with_morpheme_index = []
        self.datasets_with_segment_slice = []

        # Per-dataset completeness
        self.completeness = {}

    def update(self, dataset: str, forms: pd.DataFrame, languages: pd.DataFrame,
               parameters: pd.DataFrame, metadata: dict, references: dict,
               bibtex: str, column_tracking: dict):
        """
        Update statistics from one dataset.

        @param dataset: Dataset name
        @param forms: Forms dataframe
        @param languages: Languages dataframe
        @param parameters: Parameters dataframe
        @param metadata: Metadata dict
        @param references: References dict
        @param bibtex: BibTeX content
        @param column_tracking: Column presence tracking
        """
        # Update counters
        self.total_forms += len(forms)
        self.total_languages += len(languages)
        self.total_parameters += len(parameters)
        self.datasets_processed += 1

        if metadata['Has_Cognates']:
            self.datasets_with_cognates += 1

        # Quality metrics
        self.forms_with_glottocode += forms['Glottocode'].notna().sum()
        self.forms_with_concepticon += forms['Concepticon_ID'].notna().sum()
        self.forms_with_cognacy += forms['Cognacy'].notna().sum()
        self.forms_with_segments += forms['Segments'].notna().sum()
        self.forms_with_alignment += forms['Alignment'].notna().sum()

        # Partial cognacy tracking
        if forms['Morpheme_Index'].notna().any():
            self.datasets_with_morpheme_index.append(dataset)
            self.forms_with_morpheme_index += forms['Morpheme_Index'].notna().sum()

        if forms['Segment_Slice'].notna().any():
            self.datasets_with_segment_slice.append(dataset)
            self.forms_with_segment_slice += forms['Segment_Slice'].notna().sum()

        # Calculate null percentages for this dataset
        null_pct = {}
        for col in ['Segments', 'Comment', 'Loan', 'Cognacy', 'Alignment']:
            if col in forms.columns:
                total = len(forms)
                null_count = forms[col].isna().sum()
                null_pct[col] = round(100 * null_count / total, 1) if total > 0 else 0

        # Store completeness info
        self.completeness[dataset] = {
            'forms': len(forms),
            'languages': len(languages),
            'parameters': len(parameters),
            'has_cognates': metadata['Has_Cognates'],
            'columns_present': column_tracking['forms_columns_present'],
            'null_percentage': null_pct
        }

        # Accumulate small tables
        self.all_metadata.append(metadata)
        self.all_references.append(references)
        self.all_bibtex.append(bibtex)
        self.all_column_tracking.append(column_tracking)

    def generate_report(self) -> dict:
        """
        Generate validation report from accumulated statistics.

        @return: Validation report dictionary
        """
        # Version distribution
        version_dist = {
            'glottolog': {},
            'concepticon': {},
            'clts': {}
        }

        for ref in self.all_references:
            for key in ['Glottolog_Version', 'Concepticon_Version', 'CLTS_Version']:
                version = ref.get(key)
                if version:
                    dist_key = key.replace('_Version', '').lower()
                    version_dist[dist_key][version] = version_dist[dist_key].get(version, 0) + 1

        # Calculate percentages
        quality = {}
        if self.total_forms > 0:
            quality = {
                'glottocode_coverage_percent': round(100 * self.forms_with_glottocode / self.total_forms, 2),
                'concepticon_coverage_percent': round(100 * self.forms_with_concepticon / self.total_forms, 2),
                'forms_with_cognate_data_percent': round(100 * self.forms_with_cognacy / self.total_forms, 2),
                'forms_with_segments_percent': round(100 * self.forms_with_segments / self.total_forms, 2),
                'forms_with_alignment_percent': round(100 * self.forms_with_alignment / self.total_forms, 2)
            }

        return {
            'summary': {
                'total_datasets': self.datasets_processed,
                'total_forms': int(self.total_forms),
                'total_languages': int(self.total_languages),
                'total_parameters': int(self.total_parameters),
                'datasets_with_cognates': self.datasets_with_cognates,
                'datasets_with_partial_cognacy': len(self.datasets_with_morpheme_index) + len(self.datasets_with_segment_slice)
            },
            'completeness': self.completeness,
            'referential_integrity': {
                'note': 'Referential integrity not validated in streaming mode'
            },
            'data_quality': quality,
            'version_distribution': version_dist,
            'partial_cognacy': {
                'datasets_with_morpheme_index': self.datasets_with_morpheme_index,
                'datasets_with_segment_slice': self.datasets_with_segment_slice,
                'forms_with_morpheme_index': int(self.forms_with_morpheme_index),
                'forms_with_segment_slice': int(self.forms_with_segment_slice)
            }
        }


# === METADATA EXTRACTION ===

def extract_metadata(metadata_json: dict, dataset: str) -> dict:
    """
    Extract dataset metadata from cldf-metadata.json.

    @param metadata_json: Parsed JSON metadata
    @param dataset: Dataset name
    @return: Dictionary of metadata fields
    """
    # Find table extents
    form_count = 0
    language_count = 0
    parameter_count = 0

    for table in metadata_json.get('tables', []):
        if 'FormTable' in table.get('dc:conformsTo', ''):
            form_count = table.get('dc:extent', 0)
        elif 'LanguageTable' in table.get('dc:conformsTo', ''):
            language_count = table.get('dc:extent', 0)
        elif 'ParameterTable' in table.get('dc:conformsTo', ''):
            parameter_count = table.get('dc:extent', 0)

    # Extract repository version
    repo_version = None
    python_version = None

    for item in metadata_json.get('prov:wasDerivedFrom', []):
        if item.get('dc:title') == 'Repository':
            repo_version = item.get('dc:created')

    for item in metadata_json.get('prov:wasGeneratedBy', []):
        if item.get('dc:title') == 'python':
            python_version = item.get('dc:description')

    # Extract CLDF module type
    cldf_module = metadata_json.get('dc:conformsTo', '')
    if '#' in cldf_module:
        cldf_module = cldf_module.split('#')[-1]

    return {
        'Dataset': dataset,
        'Title': metadata_json.get('dc:title', ''),
        'Citation': metadata_json.get('dc:bibliographicCitation', ''),
        'URL': metadata_json.get('dcat:accessURL', ''),
        'License': metadata_json.get('dc:license', ''),
        'CLDF_Module': cldf_module,
        'Repository_Version': repo_version,
        'Python_Version': python_version,
        'Form_Count': form_count,
        'Language_Count': language_count,
        'Parameter_Count': parameter_count,
        'Has_Cognates': False  # Will be set during processing
    }


def extract_references(metadata_json: dict, dataset: str) -> dict:
    """
    Extract reference system versions from cldf-metadata.json.

    @param metadata_json: Parsed JSON metadata
    @param dataset: Dataset name
    @return: Dictionary of reference versions
    """
    glottolog_version = None
    concepticon_version = None
    clts_version = None

    for item in metadata_json.get('prov:wasDerivedFrom', []):
        title = item.get('dc:title', '')
        if title == 'Glottolog':
            glottolog_version = item.get('dc:created')
        elif title == 'Concepticon':
            concepticon_version = item.get('dc:created')
        elif title == 'CLTS':
            clts_version = item.get('dc:created')

    return {
        'Dataset': dataset,
        'Glottolog_Version': glottolog_version,
        'Concepticon_Version': concepticon_version,
        'CLTS_Version': clts_version
    }


# === CORE LOADING FUNCTIONS ===

def load_dataset_forms(dataset_path: Path, dataset: str) -> Tuple[pd.DataFrame, List[str]]:
    """
    Load forms.csv for a dataset.

    @param dataset_path: Path to dataset cldf directory
    @param dataset: Dataset name
    @return: Tuple of (forms dataframe, original column names)
    """
    forms_path = dataset_path / 'forms.csv'

    if not forms_path.exists():
        raise FileNotFoundError(f"forms.csv not found for {dataset}")

    df = pd.read_csv(forms_path, encoding='utf-8', dtype=str, keep_default_na=False)
    original_columns = df.columns.tolist()

    # Add Dataset column
    df['Dataset'] = dataset

    # Prefix IDs
    if 'ID' in df.columns:
        df['ID'] = prefix_ids_column(df['ID'], dataset)
    if 'Language_ID' in df.columns:
        df['Language_ID'] = prefix_ids_column(df['Language_ID'], dataset)
    if 'Parameter_ID' in df.columns:
        df['Parameter_ID'] = prefix_ids_column(df['Parameter_ID'], dataset)

    # Prefix BibTeX keys in Source column
    if 'Source' in df.columns:
        df['Source'] = df['Source'].apply(lambda x: prefix_bibtex_keys(x, dataset) if x else '')

    # Convert Loan to boolean
    if 'Loan' in df.columns:
        df['Loan'] = df['Loan'].map({'true': True, 'false': False}).astype('boolean')

    # Replace empty strings with pd.NA for appropriate columns
    for col in df.columns:
        if col not in ['Dataset']:
            df[col] = df[col].replace('', pd.NA)

    return df, original_columns


def load_dataset_languages(dataset_path: Path, dataset: str) -> pd.DataFrame:
    """Load languages.csv for a dataset."""
    languages_path = dataset_path / 'languages.csv'

    if not languages_path.exists():
        raise FileNotFoundError(f"languages.csv not found for {dataset}")

    df = pd.read_csv(languages_path, encoding='utf-8', dtype=str, keep_default_na=False)

    # Add Dataset column
    df['Dataset'] = dataset

    # Prefix IDs
    if 'ID' in df.columns:
        df['ID'] = prefix_ids_column(df['ID'], dataset)

    # Convert numeric columns
    if 'Latitude' in df.columns:
        df['Latitude'] = pd.to_numeric(df['Latitude'].replace('', pd.NA), errors='coerce')
    if 'Longitude' in df.columns:
        df['Longitude'] = pd.to_numeric(df['Longitude'].replace('', pd.NA), errors='coerce')

    # Replace empty strings with pd.NA
    for col in df.columns:
        if col not in ['Dataset'] and df[col].dtype == 'object':
            df[col] = df[col].replace('', pd.NA)

    return df


def load_dataset_parameters(dataset_path: Path, dataset: str) -> pd.DataFrame:
    """Load parameters.csv for a dataset."""
    parameters_path = dataset_path / 'parameters.csv'

    if not parameters_path.exists():
        raise FileNotFoundError(f"parameters.csv not found for {dataset}")

    df = pd.read_csv(parameters_path, encoding='utf-8', dtype=str, keep_default_na=False)

    # Add Dataset column
    df['Dataset'] = dataset

    # Prefix IDs
    if 'ID' in df.columns:
        df['ID'] = prefix_ids_column(df['ID'], dataset)

    # Replace empty strings with pd.NA
    for col in df.columns:
        if col not in ['Dataset']:
            df[col] = df[col].replace('', pd.NA)

    return df


def load_dataset_cognates(dataset_path: Path, dataset: str) -> Optional[pd.DataFrame]:
    """
    Load cognates.csv for a dataset if it exists.

    @param dataset_path: Path to dataset cldf directory
    @param dataset: Dataset name
    @return: Cognates dataframe or None if file doesn't exist
    """
    cognates_path = dataset_path / 'cognates.csv'

    if not cognates_path.exists():
        return None

    df = pd.read_csv(cognates_path, encoding='utf-8', dtype=str, keep_default_na=False)

    # Prefix IDs
    if 'Form_ID' in df.columns:
        df['Form_ID'] = prefix_ids_column(df['Form_ID'], dataset)
    if 'Cognateset_ID' in df.columns:
        df['Cognateset_ID'] = prefix_ids_column(df['Cognateset_ID'], dataset)

    # Prefix BibTeX keys in Source column
    if 'Source' in df.columns:
        df['Source'] = df['Source'].apply(lambda x: prefix_bibtex_keys(x, dataset) if x else '')

    # Convert Doubt to boolean
    if 'Doubt' in df.columns:
        df['Doubt'] = df['Doubt'].map({'true': True, 'false': False}).astype('boolean')

    # Replace empty strings with pd.NA
    for col in df.columns:
        df[col] = df[col].replace('', pd.NA)

    return df


# === COGNATE MERGING ===

def merge_cognate_data(forms: pd.DataFrame, cognates: Optional[pd.DataFrame], dataset: str) -> pd.DataFrame:
    """
    Merge cognacy information from forms.csv and cognates.csv.
    Simplified version: takes first alignment when multiple exist.

    @param forms: Forms dataframe
    @param cognates: Cognates dataframe (or None)
    @param dataset: Dataset name
    @return: Forms with cognate columns populated
    """
    # Preserve original Cognacy column from forms.csv
    forms_cognacy = forms['Cognacy'].copy() if 'Cognacy' in forms.columns else None

    # Prefix forms.csv Cognacy values
    if forms_cognacy is not None:
        forms_cognacy = forms_cognacy.apply(
            lambda x: f"{dataset}_{x}" if pd.notna(x) else pd.NA
        )

    if cognates is None:
        # No cognates.csv - use only forms.csv Cognacy
        if forms_cognacy is not None:
            forms['Cognacy'] = forms_cognacy
        return forms

    # Aggregate cognates data per form
    # Take first value for each field (simplified - no row multiplication)
    # Build aggregation dict dynamically based on available columns
    agg_dict = {
        'Cognateset_ID': lambda x: ';'.join(x.dropna()),  # All cognatesets
    }

    # Add optional columns if they exist
    if 'Alignment' in cognates.columns:
        agg_dict['Alignment'] = 'first'
    if 'Doubt' in cognates.columns:
        agg_dict['Doubt'] = 'first'
    if 'Cognate_Detection_Method' in cognates.columns:
        agg_dict['Cognate_Detection_Method'] = 'first'
    if 'Source' in cognates.columns:
        agg_dict['Source'] = 'first'
    if 'Morpheme_Index' in cognates.columns:
        agg_dict['Morpheme_Index'] = 'first'
    if 'Segment_Slice' in cognates.columns:
        agg_dict['Segment_Slice'] = 'first'

    cognate_agg = cognates.groupby('Form_ID').agg(agg_dict).reset_index()

    # Rename columns
    column_rename = {'Form_ID': 'ID', 'Cognateset_ID': 'Cognateset_ID_from_cognates'}
    if 'Source' in cognate_agg.columns:
        column_rename['Source'] = 'Cognate_Source'

    cognate_agg = cognate_agg.rename(columns=column_rename)

    # Merge with forms
    forms = forms.merge(cognate_agg, on='ID', how='left', suffixes=('', '_drop'))

    # Drop duplicate columns from merge
    forms = forms[[c for c in forms.columns if not c.endswith('_drop')]]

    # Combine Cognacy from forms.csv and cognates.csv
    if forms_cognacy is not None:
        # Merge both sources
        forms['Cognacy'] = forms.apply(
            lambda row: combine_cognacy(
                forms_cognacy.get(row.name) if row.name < len(forms_cognacy) else pd.NA,
                row.get('Cognateset_ID_from_cognates', pd.NA)
            ),
            axis=1
        )
    else:
        forms['Cognacy'] = forms['Cognateset_ID_from_cognates']

    # Remove temporary column
    if 'Cognateset_ID_from_cognates' in forms.columns:
        forms = forms.drop(columns=['Cognateset_ID_from_cognates'])

    return forms


def combine_cognacy(forms_cog, cognates_cog):
    """Combine cognacy values from two sources."""
    parts = []

    if pd.notna(forms_cog):
        parts.append(str(forms_cog))
    if pd.notna(cognates_cog):
        parts.append(str(cognates_cog))

    return ';'.join(parts) if parts else pd.NA


# === METADATA JOINING ===

def join_language_metadata(forms: pd.DataFrame, languages: pd.DataFrame) -> pd.DataFrame:
    """
    Join language metadata (Glottocode, Glottolog_Name) to forms.

    @param forms: Forms dataframe
    @param languages: Languages dataframe
    @return: Forms with language metadata
    """
    # Select columns to join
    lang_cols = ['ID', 'Glottocode', 'Glottolog_Name']
    available_cols = ['ID'] + [c for c in ['Glottocode', 'Glottolog_Name'] if c in languages.columns]

    forms = forms.merge(
        languages[available_cols],
        left_on='Language_ID',
        right_on='ID',
        how='left',
        suffixes=('', '_lang')
    )

    # Drop the extra ID column from join
    if 'ID_lang' in forms.columns:
        forms = forms.drop(columns=['ID_lang'])

    return forms


def join_parameter_metadata(forms: pd.DataFrame, parameters: pd.DataFrame) -> pd.DataFrame:
    """
    Join parameter metadata (Concepticon_ID, Concepticon_Gloss) to forms.

    @param forms: Forms dataframe
    @param parameters: Parameters dataframe
    @return: Forms with parameter metadata
    """
    # Select columns to join
    param_cols = ['ID'] + [c for c in ['Concepticon_ID', 'Concepticon_Gloss'] if c in parameters.columns]

    forms = forms.merge(
        parameters[param_cols],
        left_on='Parameter_ID',
        right_on='ID',
        how='left',
        suffixes=('', '_param')
    )

    # Drop the extra ID column from join
    if 'ID_param' in forms.columns:
        forms = forms.drop(columns=['ID_param'])

    return forms


# === DATASET PROCESSING ORCHESTRATION ===

def process_dataset(dataset: str, lexibank_dir: Path) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict, dict, str, dict]:
    """
    Process a single dataset.

    @param dataset: Dataset name
    @param lexibank_dir: Path to lexibank directory
    @return: Tuple of (forms, languages, parameters, metadata, references, bibtex, column_tracking)
    """
    dataset_path = lexibank_dir / dataset / 'cldf'

    # Load metadata
    metadata_path = dataset_path / 'cldf-metadata.json'
    if not metadata_path.exists():
        raise FileNotFoundError(f"cldf-metadata.json not found for {dataset}")

    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata_json = json.load(f)

    metadata = extract_metadata(metadata_json, dataset)
    references = extract_references(metadata_json, dataset)

    # Load core tables
    forms, forms_original_cols = load_dataset_forms(dataset_path, dataset)
    languages = load_dataset_languages(dataset_path, dataset)
    parameters = load_dataset_parameters(dataset_path, dataset)

    # Load cognates if available
    cognates = load_dataset_cognates(dataset_path, dataset)
    metadata['Has_Cognates'] = cognates is not None

    # Track column presence for validation
    column_tracking = {
        'dataset': dataset,
        'forms_columns_present': forms_original_cols,
        'has_cognates': cognates is not None
    }

    # Merge cognate data
    forms = merge_cognate_data(forms, cognates, dataset)

    # Join language and parameter metadata
    forms = join_language_metadata(forms, languages)
    forms = join_parameter_metadata(forms, parameters)

    # Ensure all expected columns exist
    forms = ensure_columns(forms, FORMS_COLUMNS)
    languages = ensure_columns(languages, LANGUAGES_COLUMNS)
    parameters = ensure_columns(parameters, PARAMETERS_COLUMNS)

    # Load BibTeX sources
    bibtex_path = dataset_path / 'sources.bib'
    bibtex_content = load_bibtex(bibtex_path)
    prefixed_bibtex = prefix_bibtex_file(bibtex_content, dataset)

    return forms, languages, parameters, metadata, references, prefixed_bibtex, column_tracking


# === VALIDATION ===

def validate_referential_integrity(
    forms: pd.DataFrame,
    languages: pd.DataFrame,
    parameters: pd.DataFrame
) -> dict:
    """
    Validate referential integrity across tables.

    @param forms: All forms
    @param languages: All languages
    @param parameters: All parameters
    @return: Dictionary of validation results
    """
    logger.info("Validating referential integrity...")

    # Get unique IDs
    language_ids = set(languages['ID'].dropna())
    parameter_ids = set(parameters['ID'].dropna())

    # Check orphans
    forms_language_ids = set(forms['Language_ID'].dropna())
    forms_parameter_ids = set(forms['Parameter_ID'].dropna())

    orphan_language_ids = forms_language_ids - language_ids
    orphan_parameter_ids = forms_parameter_ids - parameter_ids

    # Check missing metadata
    forms_without_glottocode = forms['Glottocode'].isna().sum()
    forms_without_concepticon = forms['Concepticon_ID'].isna().sum()

    return {
        'orphan_language_ids': len(orphan_language_ids),
        'orphan_parameter_ids': len(orphan_parameter_ids),
        'forms_without_glottocode': int(forms_without_glottocode),
        'forms_without_concepticon_id': int(forms_without_concepticon)
    }


def calculate_quality_metrics(
    forms: pd.DataFrame,
    all_metadata: List[dict]
) -> dict:
    """
    Calculate data quality metrics.

    @param forms: All forms
    @param all_metadata: List of metadata dicts for all datasets
    @return: Dictionary of quality metrics
    """
    logger.info("Calculating quality metrics...")

    total_forms = len(forms)

    return {
        'glottocode_coverage_percent': round(100 * forms['Glottocode'].notna().sum() / total_forms, 2) if total_forms > 0 else 0,
        'concepticon_coverage_percent': round(100 * forms['Concepticon_ID'].notna().sum() / total_forms, 2) if total_forms > 0 else 0,
        'forms_with_cognate_data_percent': round(100 * forms['Cognacy'].notna().sum() / total_forms, 2) if total_forms > 0 else 0,
        'forms_with_segments_percent': round(100 * forms['Segments'].notna().sum() / total_forms, 2) if total_forms > 0 else 0,
        'forms_with_alignment_percent': round(100 * forms['Alignment'].notna().sum() / total_forms, 2) if total_forms > 0 else 0
    }


def generate_validation_report(
    forms: pd.DataFrame,
    languages: pd.DataFrame,
    parameters: pd.DataFrame,
    all_metadata: List[dict],
    all_references: List[dict],
    all_column_tracking: List[dict]
) -> dict:
    """Generate comprehensive validation report."""
    logger.info("Generating validation report...")

    # Summary statistics
    datasets_with_cognates = sum(1 for m in all_metadata if m['Has_Cognates'])

    # Partial cognacy datasets
    datasets_with_morpheme_index = []
    datasets_with_segment_slice = []
    forms_with_morpheme_index = 0
    forms_with_segment_slice = 0

    for track in all_column_tracking:
        dataset = track['dataset']
        if track['has_cognates']:
            # Check if these columns appear in the final forms for this dataset
            dataset_forms = forms[forms['Dataset'] == dataset]
            if dataset_forms['Morpheme_Index'].notna().any():
                datasets_with_morpheme_index.append(dataset)
                forms_with_morpheme_index += dataset_forms['Morpheme_Index'].notna().sum()
            if dataset_forms['Segment_Slice'].notna().any():
                datasets_with_segment_slice.append(dataset)
                forms_with_segment_slice += dataset_forms['Segment_Slice'].notna().sum()

    # Version distribution
    version_dist = {
        'glottolog': {},
        'concepticon': {},
        'clts': {}
    }

    for ref in all_references:
        for key in ['Glottolog_Version', 'Concepticon_Version', 'CLTS_Version']:
            version = ref.get(key)
            if version:
                dist_key = key.replace('_Version', '').lower()
                version_dist[dist_key][version] = version_dist[dist_key].get(version, 0) + 1

    # Completeness per dataset
    completeness = {}
    for meta in all_metadata:
        dataset = meta['Dataset']
        dataset_forms = forms[forms['Dataset'] == dataset]

        # Calculate null percentages for key columns
        null_pct = {}
        for col in ['Segments', 'Comment', 'Loan', 'Cognacy', 'Alignment']:
            if col in dataset_forms.columns:
                total = len(dataset_forms)
                null_count = dataset_forms[col].isna().sum()
                null_pct[col] = round(100 * null_count / total, 1) if total > 0 else 0

        # Track column presence
        track = next((t for t in all_column_tracking if t['dataset'] == dataset), None)
        columns_present = track['forms_columns_present'] if track else []

        completeness[dataset] = {
            'forms': meta['Form_Count'],
            'languages': meta['Language_Count'],
            'parameters': meta['Parameter_Count'],
            'has_cognates': meta['Has_Cognates'],
            'columns_present': columns_present,
            'null_percentage': null_pct
        }

    # Referential integrity
    ref_integrity = validate_referential_integrity(forms, languages, parameters)

    # Quality metrics
    quality = calculate_quality_metrics(forms, all_metadata)

    return {
        'summary': {
            'total_datasets': len(all_metadata),
            'total_forms': len(forms),
            'total_languages': len(languages),
            'total_parameters': len(parameters),
            'datasets_with_cognates': datasets_with_cognates,
            'datasets_with_partial_cognacy': len(datasets_with_morpheme_index) + len(datasets_with_segment_slice)
        },
        'completeness': completeness,
        'referential_integrity': ref_integrity,
        'data_quality': quality,
        'version_distribution': version_dist,
        'partial_cognacy': {
            'datasets_with_morpheme_index': datasets_with_morpheme_index,
            'datasets_with_segment_slice': datasets_with_segment_slice,
            'forms_with_morpheme_index': int(forms_with_morpheme_index),
            'forms_with_segment_slice': int(forms_with_segment_slice)
        }
    }


# === OUTPUT ===

# Removed write_parquet_files - no longer needed (streaming CSV appends instead)


def write_bibtex_file(all_bibtex: List[str], output_dir: Path):
    """Write merged BibTeX file."""
    logger.info("Writing BibTeX file...")

    output_dir.mkdir(parents=True, exist_ok=True)

    merged_content = '\n\n'.join(bib for bib in all_bibtex if bib.strip())

    with open(output_dir / 'sources.bib', 'w', encoding='utf-8') as f:
        f.write(merged_content)

    logger.info(f"Wrote merged BibTeX to {output_dir / 'sources.bib'}")


def write_validation_report(report: dict, output_dir: Path):
    """Write validation report as JSON."""
    logger.info("Writing validation report...")

    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_dir / 'validation_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    logger.info(f"Wrote validation report to {output_dir / 'validation_report.json'}")


# Removed write_requirements_txt - requirements.txt is in repo root


# === MAIN ===

def main():
    """Main entry point - streaming CSV version."""
    parser = argparse.ArgumentParser(
        description='Merge CLDF datasets into unified CSV files (streaming mode)',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--input',
        type=Path,
        default=LEXIBANK_DIR,
        help=f'Input lexibank directory (default: {LEXIBANK_DIR})'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=OUTPUT_DIR,
        help=f'Output directory (default: {OUTPUT_DIR})'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Process data but do not write output files'
    )

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    lexibank_dir = args.input
    output_dir = args.output

    # Discover datasets
    if not lexibank_dir.exists():
        logger.error(f"Input directory does not exist: {lexibank_dir}")
        sys.exit(1)

    datasets = [
        d.name for d in lexibank_dir.iterdir()
        if d.is_dir() and (d / 'cldf' / 'cldf-metadata.json').exists()
    ]

    if not datasets:
        logger.error(f"No datasets found in {lexibank_dir}")
        sys.exit(1)

    logger.info(f"Found {len(datasets)} datasets")
    logger.info("Using streaming CSV mode - low memory footprint")

    # Initialize output directory (remove old files)
    if not args.dry_run:
        initialize_output_files(output_dir)

    # Initialize validation accumulator
    validator = ValidationAccumulator()

    # Process datasets one at a time with streaming append
    skipped = []

    for i, dataset in enumerate(sorted(datasets), 1):
        try:
            logger.info(f"Processing dataset {i}/{len(datasets)}: {dataset}")

            # Process dataset
            forms, languages, parameters, metadata, references, bibtex, column_tracking = process_dataset(
                dataset, lexibank_dir
            )

            # Update validation statistics (before we lose the dataframes)
            validator.update(dataset, forms, languages, parameters, metadata,
                           references, bibtex, column_tracking)

            # Append to CSV files immediately (unless dry-run)
            if not args.dry_run:
                is_first = (i == 1)
                append_to_csv(output_dir / 'forms.csv', forms, is_first)
                append_to_csv(output_dir / 'languages.csv', languages, is_first)
                append_to_csv(output_dir / 'parameters.csv', parameters, is_first)

            # Free memory immediately
            del forms, languages, parameters
            gc.collect()

        except Exception as e:
            logger.error(f"Failed to process {dataset}: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            skipped.append(dataset)
            continue

    if skipped:
        logger.warning(f"Skipped {len(skipped)} datasets due to errors: {', '.join(skipped)}")

    logger.info(f"Processed {validator.datasets_processed} datasets")
    logger.info(f"Total forms: {validator.total_forms}")
    logger.info(f"Total languages: {validator.total_languages}")
    logger.info(f"Total parameters: {validator.total_parameters}")

    # Generate validation report
    logger.info("Generating validation report...")
    validation_report = validator.generate_report()

    # Write small tables (metadata, references) and other outputs
    if not args.dry_run:
        # Write metadata and references (small tables)
        logger.info("Writing metadata and references...")
        pd.DataFrame(validator.all_metadata).to_csv(
            output_dir / 'metadata.csv',
            index=False,
            encoding='utf-8'
        )
        pd.DataFrame(validator.all_references).to_csv(
            output_dir / 'references.csv',
            index=False,
            encoding='utf-8'
        )

        # Write BibTeX
        write_bibtex_file(validator.all_bibtex, output_dir)

        # Write validation report
        write_validation_report(validation_report, output_dir)

        logger.info(f"All outputs written to {output_dir}")
    else:
        logger.info("Dry run mode - no files written")
        logger.info(f"Validation report summary: {validation_report['summary']}")

    logger.info("Done!")


if __name__ == '__main__':
    main()
