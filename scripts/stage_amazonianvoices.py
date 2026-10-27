"""Stage Amazonian Voices with an explicit dataset-level citation.

The upstream forms have no individual Source references. This adds a citation
from upstream metadata, not a claim about individual recording authorship.
Raw source files and active intake are never changed. Append the staged source
with append_source_intake.py only after reviewing the source snapshot.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from arcaverborum.ingest import ingest_lexibank

ROOT = Path(__file__).resolve().parents[1]


def stage(root: Path, output: Path) -> dict:
    active = (root / 'intake').resolve()
    if output.resolve() == active or active in output.resolve().parents:
        raise ValueError('Staging must be outside active intake')
    result = ingest_lexibank(root / 'raw', output, datasets=['amazonianvoices'])
    if result['datasets_ingested'] != 1:
        raise ValueError('Amazonian Voices did not stage successfully')
    source = root / 'raw/lexibank/amazonianvoices/cldf/cldf-metadata.json'
    metadata = json.loads(source.read_text())
    citation = metadata.get('dc:bibliographicCitation', '')
    title = metadata.get('dc:title', '')
    url = metadata.get('dcat:accessURL', '')
    license_url = metadata.get('dc:license', '')
    license_label = ('CC-BY-NC-4.0' if license_url == 'https://creativecommons.org/licenses/by-nc/4.0/'
                     else license_url)
    if not all([citation, title, url, license_url]):
        raise ValueError('Dataset citation, title, URL and license are required')
    directory = output / 'lexibank'
    forms = pd.read_csv(directory / 'forms.csv', dtype=str, keep_default_na=False)
    if forms['Source'].str.strip().any() or (directory / 'sources.bib').read_text().strip():
        raise ValueError('Upstream now supplies sources; review before replacing citation policy')
    # Metadata is plain text, not BibTeX markup. Prevent unbalanced fields.
    def field(value: str) -> str:
        return value.replace('\\', '').replace('{', '').replace('}', '').replace('\n', ' ')
    key = 'amazonianvoices_dataset'
    (directory / 'sources.bib').write_text(
        '@misc{' + key + ',\n  title = {' + field(title) + '},\n'
        '  howpublished = {' + field(citation) + '},\n  url = {' + field(url) + '},\n'
        '  note = {Dataset-level citation from upstream metadata; individual form sources absent. '
        + field(license_label) + '},\n}\n')
    forms['Source'] = key
    forms.to_csv(directory / 'forms.csv', index=False)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path, default=ROOT / 'raw/curation/amazonian-stage')
    args = parser.parse_args()
    print(stage(args.root.resolve(), args.output.resolve()))


if __name__ == '__main__':
    main()
