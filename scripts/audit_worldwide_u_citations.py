"""Recheck U historical source/page/image anchors; visual transcription remains authored evidence."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[1]


def main():
    specs = json.loads((ROOT / 'src/arcaverborum/data/original_lexical_sources.json').read_text())
    reports = []
    for spec in specs:
        review = spec.get('review') or spec.get('extraction', '')
        if not review.startswith('docs/worldwide_u'):
            continue
        resource = spec['resources'][0]
        path = ROOT / 'raw/lexibank' / spec['dataset'] / resource['filename']
        assert hashlib.file_digest(path.open('rb'), 'sha256').hexdigest() == resource['sha256']
        document = pymupdf.open(path)
        contexts = (json.loads((ROOT / spec['page_contexts']).read_text())
                    if spec.get('page_contexts') else {})
        anchors, count = set(), 0
        with (ROOT / review).open() as handle:
            for row in csv.DictReader(handle):
                page = document[int(row['pdf_page']) - 1]
                if spec['kind'] == 'documentary_ocr':
                    quote = contexts[row['pdf_page']] if contexts else row['raw_quote']
                    assert row['decision'] == 'stage_ocr' and page.get_text() == quote
                    if contexts:
                        assert hashlib.sha256(quote.encode()).hexdigest() == row['raw_quote_sha256']
                    anchors.add('pdf-page-' + row['pdf_page'])
                elif spec['kind'] == 'reviewed_facsimile':
                    xref = int(row['source_image_xref'])
                    assert xref in {image[0] for image in page.get_images(full=True)}
                    image_hash = hashlib.sha256(document.extract_image(xref)['image']).hexdigest()
                    assert image_hash == row['source_image_sha256']
                    anchors.add('image-' + str(xref))
                else:
                    raise ValueError('Unknown U historical audit kind')
                count += 1
        reports.append(dict(dataset=spec['dataset'], records=count, anchors=sorted(anchors),
                            classification='Unreviewed OCR intake' if spec['kind'] == 'documentary_ocr'
                            else 'Independently authored facsimile transcription',
                            limit='Hashes verify source/page/image identity, not automatic paleographic correctness. '
                                  'Source orthography is not IPA; unresolved items remain outside admission.'))
    output = ROOT / 'docs/worldwide_u_citation_proof_2026-10-30.json'
    output.write_text(json.dumps(reports, indent=2) + '\n')
    print([(r['dataset'], r['records']) for r in reports])


if __name__ == '__main__':
    main()
