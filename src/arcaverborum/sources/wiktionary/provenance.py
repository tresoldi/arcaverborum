"""Dataset-level citation for the actual local Wiktextract snapshot."""
from __future__ import annotations

import csv
import hashlib

SOURCE_KEY = 'wiktionary_kaikki2026'
URL = 'https://kaikki.org/dictionary/raw-wiktextract-data.jsonl.gz'


def write_provenance(output_dir, dump, counts, metadata=None):
    digest = (metadata or {}).get('dump_sha256')
    if not digest:
        with dump.open('rb') as handle:
            digest = hashlib.file_digest(handle, 'sha256').hexdigest()
    citation = 'English Wiktionary contributors. English Wiktionary via Kaikki/Wiktextract; local frozen snapshot.'
    note = ('Original dump date and snapshot-specific license metadata were not recorded. '
            'Snapshot SHA256 ' + digest + '. The year in the legacy citation key is not a verified dump date.')
    row = dict(Dataset='wiktionary', Title='English Wiktionary via Kaikki/Wiktextract', Citation=citation,
               URL=URL, License='', CLDF_Module='', Repository_Version='sha256:' + digest, Python_Version='',
               Form_Count=counts['forms'], Language_Count=counts['languages'],
               Parameter_Count=counts['parameters'], Has_Cognates='True')
    with (output_dir / 'metadata.csv').open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row), lineterminator='\n')
        writer.writeheader()
        writer.writerow(row)
    (output_dir / 'sources.bib').write_text(
        '@misc{' + SOURCE_KEY + ',\n'
        '  author = {English Wiktionary contributors},\n'
        '  title = {English Wiktionary via Kaikki/Wiktextract, local frozen snapshot},\n'
        '  url = {' + URL + '},\n'
        '  note = {' + note + '}\n}\n', encoding='utf-8')
