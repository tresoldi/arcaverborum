"""Independently audit reviewed page quotations against pinned original PDFs.

Optional tool: uv run --no-project --with pymupdf python scripts/audit_original_pdf_citations.py
The normal source transport needs no PDF library; this verifies manual page review.
"""
import csv
import hashlib
import json
import re
import unicodedata
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
results = []
for spec in json.loads((ROOT / 'src/arcaverborum/data/original_lexical_sources.json').read_text()):
    if spec['kind'] != 'reviewed_pdf':
        continue
    resources = {r['key']: r for r in spec['resources']}
    with (ROOT / spec['review']).open() as handle:
        reviews = list(csv.DictReader(handle))
    for review in reviews:
        resource = resources[review['resource_key']]
        path = ROOT / 'raw/lexibank' / spec['dataset'] / resource['filename']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == resource['sha256']
        with pymupdf.open(path) as document:
            page = document[int(review['pdf_page']) - 1].get_text()
        assert review['raw_quote'] == page, review['native_id']
        assert review['Form'] in page and review['source_sense'] in page
        results.append(dict(dataset=spec['dataset'], native_id=review['native_id'],
                            pdf_page=int(review['pdf_page']), pdf_sha256=resource['sha256'],
                            quote_sha256=hashlib.sha256(page.encode()).hexdigest()))
beja = ROOT / 'raw/curation/after-r-planning/beja2026.pdf'
beja_sha = 'f173826ab756fa35ab2ed3a043c13b38df13da72828106bffc65520a23fed111'
assert hashlib.sha256(beja.read_bytes()).hexdigest() == beja_sha
with pymupdf.open(beja) as document:
    pages = [unicodedata.normalize('NFC', page.get_text()) for page in document]
with (ROOT / 'docs/worldwide_s04_review_2026-10-30.csv').open() as handle:
    reviews = list(csv.DictReader(handle))
beja_results = []
for row in reviews:
    if row['av_id'] != 'afa-beja':
        continue
    word = unicodedata.normalize('NFC', row['Form'])
    found = None
    for page_index, text in enumerate(pages):
        for match in re.finditer(r'(?m)^' + re.escape(word) + r'(?=\s)', text):
            context = text[match.start():match.end() + 200]
            if (re.search(r'\bn\.', context)
                    and re.search(r'\b' + re.escape(row['source_sense']) + r'\b', context)):
                found = dict(source_form_id=row['source_form_id'], Form=row['Form'],
                             source_sense=row['source_sense'], pdf_page=page_index + 1,
                             original_pdf_context=context)
                break
        if found:
            break
    assert found, row['Form']
    beja_results.append(found)
proof = dict(citations=results, independently_audited_pdf_citations=len(results),
             beja_readings=beja_results, independently_checked_beja_readings=len(beja_results),
             beja_pdf_sha256=hashlib.sha256(beja.read_bytes()).hexdigest())
(ROOT / 'docs/worldwide_s_pdf_verification_2026-10-30.json').write_text(json.dumps(proof, indent=2) + '\n')
print('Verified', len(results), 'original PDF page quotations')
