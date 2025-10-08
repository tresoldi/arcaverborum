# Release Workflow for Arca Verborum

This document describes how to create and publish new releases of Arca Verborum to Zenodo.

## Overview

The release system consists of:
- `prepare_release.py` - Automates release preparation (creates three ZIP archives)
- `zenodo_publish.py` - Handles Zenodo uploads using `zenodo-client` library
- `templates/` - Jinja2 templates for documentation
- `zenodo.metadata.yml` - Zenodo metadata configuration

**Note:** Each release includes THREE archives:
- `arcaverborum.V.full.YYYYMMDD.zip` - Full collection (all 149 datasets)
- `arcaverborum.V.core.YYYYMMDD.zip` - Core collection (13 curated datasets for teaching)
- `arcaverborum.V.corecog.YYYYMMDD.zip` - CoreCog collection (58 datasets with expert cognate data)

## Prerequisites

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up Zenodo API tokens:
   - **Sandbox (for testing):** Get token from https://sandbox.zenodo.org/account/settings/applications/tokens/new/
   - **Production:** Get token from https://zenodo.org/account/settings/applications/tokens/new/

   ```bash
   export ZENODO_SANDBOX_API_TOKEN="your-sandbox-token"  # For testing
   export ZENODO_API_TOKEN="your-production-token"       # For real releases
   ```

   **Note:** The `zenodo-client` library also supports storing tokens in `~/.config/zenodo.ini` using PyStow. See the [zenodo-client documentation](https://github.com/cthoyt/zenodo-client) for details.

## Release Process

### Step 1: Clone Datasets

Clone the Lexibank datasets (use collection flags for faster setup if testing):

```bash
# Clone all datasets (required for full release)
python clone_lexibank.py

# Or clone only core datasets (for testing, 13 datasets)
python clone_lexibank.py --core-only

# Or clone only corecog datasets (for testing cognate features, 58 datasets)
python clone_lexibank.py --corecog-only
```

### Step 2: Run the Merger

Build all three collections:

```bash
python merge_cldf_datasets.py
```

This creates:
- `output/full/` - Full collection (all datasets)
- `output/core/` - Core collection (13 curated datasets)
- `output/corecog/` - CoreCog collection (58 datasets with cognate data)

All directories contain complete CSV files, validation reports, and bibliography.

### Step 3: Prepare the Release

Run the release preparation script:

```bash
# Use today's date as version (V.YYYYMMDD format)
python prepare_release.py

# Or specify a custom version
python prepare_release.py --version A.20251001

# Force overwrite if version already exists
python prepare_release.py --version A.20251001 --force

# Create git tag automatically
python prepare_release.py --version A.20251001 --git-tag
```

This script will:
1. Load statistics from all three validation reports (`output/full/`, `output/core/`, `output/corecog/`)
2. Generate collection-specific `DATASET_DESCRIPTION.md` and `RELEASE_NOTES.md` from templates
3. Create THREE archives:
   - `releases/arcaverborum.V.full.YYYYMMDD.zip` (full collection)
   - `releases/arcaverborum.V.core.YYYYMMDD.zip` (core collection)
   - `releases/arcaverborum.V.corecog.YYYYMMDD.zip` (corecog collection)
4. Each archive contains:
   - All CSV files from respective collection
   - `sources.bib`
   - `validation_report.json`
   - Collection-specific documentation files
5. Compute SHA256 checksums for all three archives
6. Update `zenodo.metadata.yml` with version and all three file paths
7. Save state to `.zenodo_state.json`

### Step 4: Review the Release

Inspect the generated archives:

```bash
# List archive contents
unzip -l releases/arcaverborum.A.full.20251001.zip          # Full collection
unzip -l releases/arcaverborum.A.core.20251001.zip          # Core collection
unzip -l releases/arcaverborum.A.corecog.20251001.zip       # CoreCog collection

# View generated documentation
unzip -p releases/arcaverborum.A.full.20251001.zip arcaverborum-A-full-20251001/DATASET_DESCRIPTION.md | less
unzip -p releases/arcaverborum.A.core.20251001.zip arcaverborum-A-core-20251001/DATASET_DESCRIPTION.md | less
unzip -p releases/arcaverborum.A.corecog.20251001.zip arcaverborum-A-corecog-20251001/DATASET_DESCRIPTION.md | less
```

Preview the Zenodo metadata:

```bash
python zenodo_publish.py --show
```

### Step 5: Test on Zenodo Sandbox

Always test on sandbox first:

```bash
python zenodo_publish.py --sandbox
```

This will:
1. Create a draft deposition (or new version if concept DOI exists)
2. Upload ALL THREE ZIP files (full, core, and corecog)
3. Set metadata
4. Publish to sandbox

Verify the sandbox deposit at: https://sandbox.zenodo.org/

**Note:** All three archives will be uploaded to the same Zenodo record. Users can choose which to download.

### Step 6: Publish to Production Zenodo

Once everything looks good:

```bash
python zenodo_publish.py
```

This will:
1. Check if this is a new release or update to existing concept
2. Create deposition and upload ALL THREE files
3. Publish and receive DOI
4. Update `.zenodo_state.json` with DOI information

### Step 7: Post-Release

After successful publication:

1. **Update documentation with DOI information**:

   The `update_docs_doi.py` script automatically updates README.md and docs/index.html with DOI links and file sizes from `.zenodo_state.json`:

   ```bash
   # Preview changes first
   python update_docs_doi.py --dry-run

   # Apply updates
   python update_docs_doi.py
   ```

   This will:
   - Update DOI badge in README.md with concept DOI
   - Update download links with concept DOI and actual file sizes
   - Update BibTeX citations with concept DOI
   - Update website download buttons with direct file URLs
   - Add DOI badge to website citation section

2. **Commit all changes**:
   ```bash
   git add .zenodo_state.json zenodo.metadata.yml README.md docs/index.html
   git commit -m "Release version A.20251001 with DOI updates"
   ```

3. **Create git tag** (if not done in Step 2):
   ```bash
   python prepare_release.py --version A.20251001 --git-tag
   ```

4. **Push to GitHub**:
   ```bash
   git push origin master
   git push origin vA.20251001
   ```

## Version Scheme

- **Format:** `S.YYYYMMDD` where S is a letter indicating the data series (e.g., `A.20251001` for October 1, 2025)
- **Series letter:** `A` for Lexibank-derived data (Series A), `B` for Wiktionary (Series B, planned), etc.
- **Same-day revisions:** Append `.N` (e.g., `A.20251001.1`, `A.20251001.2`)

## File Structure

```
arcaverborum/
├── .gitignore                    # Excludes output/, releases/, lexibank/
├── .zenodo_state.json           # Release tracking (committed to git)
├── zenodo.metadata.yml          # Zenodo configuration (committed to git)
├── datasets.csv                 # Dataset list with CORE and CoreCog columns
├── clone_lexibank.py            # Clone Lexibank repositories
├── merge_cldf_datasets.py       # Main data processing script (builds all three collections)
├── prepare_release.py           # Release preparation automation (creates all three archives)
├── zenodo_publish.py            # Zenodo upload script (using zenodo-client)
├── update_docs_doi.py           # Update documentation with DOI information
├── templates/                   # Documentation templates
│   ├── DATASET_DESCRIPTION.md.j2
│   └── RELEASE_NOTES.md.j2
├── output/                      # Generated data (ignored by git)
│   ├── full/                    # Full collection (all 149 datasets)
│   │   ├── forms.csv
│   │   ├── languages.csv
│   │   ├── parameters.csv
│   │   ├── metadata.csv
│   │   ├── sources.bib
│   │   └── validation_report.json
│   ├── core/                    # Core collection (13 curated datasets)
│   │   ├── forms.csv
│   │   ├── languages.csv
│   │   ├── parameters.csv
│   │   ├── metadata.csv
│   │   ├── sources.bib
│   │   └── validation_report.json
│   └── corecog/                 # CoreCog collection (58 datasets with cognate data)
│       ├── forms.csv
│       ├── languages.csv
│       ├── parameters.csv
│       ├── metadata.csv
│       ├── sources.bib
│       └── validation_report.json
└── releases/                    # Release archives (ignored by git)
    ├── arcaverborum.V.full.YYYYMMDD.zip        # Full collection archive
    ├── arcaverborum.V.core.YYYYMMDD.zip        # Core collection archive
    └── arcaverborum.V.corecog.YYYYMMDD.zip     # CoreCog collection archive
```

## Troubleshooting

### "Version already released" error

Use `--force` flag:
```bash
python prepare_release.py --version A.20251001 --force
```

### Missing files in output/

Clone datasets and run the merger:
```bash
python clone_lexibank.py
python merge_cldf_datasets.py
```

### Zenodo upload fails

- Check your API token is valid
- Verify network connectivity
- Try sandbox first to debug

### Need to update documentation

Edit the templates in `templates/`:
- `DATASET_DESCRIPTION.md.j2` - Main dataset description
- `RELEASE_NOTES.md.j2` - Version-specific notes

Available template variables:
- `{{ version }}` - Release version
- `{{ release_date }}` - Release date
- `{{ forms_count }}` - Total forms
- `{{ languages_count }}` - Total languages
- `{{ parameters_count }}` - Total parameters
- `{{ cognates_datasets }}` - Datasets with cognates
- `{{ glottolog_coverage }}` - % with Glottolog
- `{{ concepticon_coverage }}` - % with Concepticon
- `{{ cognate_coverage }}` - % with cognates
- Plus many more (see `prepare_release.py` for full list)

## Customization

### Adding release notes

Specify changes for non-initial releases:

```bash
python prepare_release.py --version A.20251002 \
  --changes "Updated to Lexibank 2024 release" \
  --known-issues "Minor formatting issues in dataset XYZ"
```

### Modifying Zenodo metadata

Edit `zenodo.metadata.yml` directly. The `prepare_release.py` script will update the version and files, but preserve other fields.

## Support

For questions or issues:
- GitHub: https://github.com/tresoldi/arcaverborum/issues
- Email: tiago.tresoldi@lingfil.uu.se
