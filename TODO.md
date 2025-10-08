# TODO: Future Enhancements

This file tracks planned improvements and features for Arca Verborum.

## Testing Infrastructure

### Automated Tests
- [ ] Add pytest test suite for core functionality
  - [ ] Test ID prefixing correctness (forms, languages, parameters)
  - [ ] Test BibTeX key prefixing
  - [ ] Test cognacy merging logic (forms.csv + cognates.csv)
  - [ ] Test metadata extraction from CLDF JSON
  - [ ] Test validation report generation
  - [ ] Test CSV streaming append functionality
  - [ ] Test release archive creation

### Test Data
- [ ] Create minimal test dataset (fixture)
- [ ] Add edge case tests (empty datasets, missing columns, etc.)
- [ ] Test partial cognacy handling (Morpheme_Index, Segment_Slice)

## Code Quality

### Development Tools
- [ ] Add pre-commit hooks (optional, if desired)
  - [ ] ruff linting
  - [ ] mypy type checking
  - [ ] Automatic formatting
- [ ] Add GitHub Actions CI/CD workflow
  - [ ] Run tests on push
  - [ ] Run linters
  - [ ] Build validation

### Documentation
- [ ] Add CITATION.cff for standardized citation format
- [ ] Add API documentation (if creating Python package)
- [ ] Add examples directory with Jupyter notebooks

## Data Enhancements

### Additional Collections
- [ ] Series B: Wiktionary etymological data (planned)
- [ ] Consider domain-specific collections (e.g., Austronesian-only)

### Data Quality
- [ ] Implement data validation rules beyond current checks
- [ ] Add data quality scoring per dataset
- [ ] Generate dataset-specific quality reports

## Features

### Release Automation
- [ ] Automate DOI placeholder updates after Zenodo publish
- [ ] Generate changelog automatically from git history
- [ ] Add version comparison tool (diff between releases)

### User Tools
- [ ] Create Python package for easy data loading
- [ ] Add CLI tool for querying data
- [ ] Create data exploration dashboard (web-based)

### Performance
- [ ] Profile memory usage for large datasets
- [ ] Optimize CSV streaming for very large collections
- [ ] Consider Parquet output option for big data workflows

## Documentation Improvements

- [ ] Add troubleshooting guide
- [ ] Add FAQ section
- [ ] Create tutorial for common use cases
- [ ] Add contribution guidelines (CONTRIBUTING.md)

## Infrastructure

- [ ] Set up automated release builds
- [ ] Add dataset version tracking
- [ ] Create data update monitoring (check for new Lexibank datasets)
- [ ] Add notification system for dataset updates

## Research Support

- [ ] Add export formats for common tools (BEAST, MrBayes, etc.)
- [ ] Create alignment visualization tools
- [ ] Add cognate network analysis utilities
- [ ] Support for custom filtering and subsetting

---

## Priority Labels

- **High**: Essential for next release
- **Medium**: Important but not blocking
- **Low**: Nice to have, future consideration
- **Research**: Requires investigation/prototyping

## Notes

- Tests are currently marked as **Medium** priority (post-first-release)
- Series B development is on hold until Series A is stable
- Focus on stability and documentation for initial releases
