"""Recheck T historical page/image anchors against privately cached original PDFs."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[1]


def main():
    sources = json.loads((ROOT / 'src/arcaverborum/data/original_lexical_sources.json').read_text())
    reports = []
    for spec in sources:
        if not spec.get('review', '').startswith('docs/southern_t'):
            continue
        resource = spec['resources'][0]
        path = ROOT / 'raw/lexibank' / spec['dataset'] / resource['filename']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == resource['sha256']
        document = pymupdf.open(path)
        count, anchors = 0, set()
        with (ROOT / spec['review']).open() as handle:
            for row in csv.DictReader(handle):
                if row['decision'] != 'admit':
                    continue
                page = document[int(row['pdf_page']) - 1]
                if spec['kind'] == 'reviewed_pdf':
                    assert page.get_text() == row['raw_quote']
                    anchors.add('pdf-page-' + row['pdf_page'])
                else:
                    xref = int(row['source_image_xref'])
                    assert xref in {image[0] for image in page.get_images(full=True)}
                    image = document.extract_image(xref)['image']
                    assert hashlib.sha256(image).hexdigest() == row['source_image_sha256']
                    anchors.add('image-' + str(xref))
                count += 1
        reports.append(dict(dataset=spec['dataset'], citations=count, anchors=sorted(anchors),
                            proof=('Pinned PDF and page OCR or embedded-image hash; '
                                   'handwritten/image readings require the authored visual review')))
    output = ROOT / 'docs/southern_t_citation_proof_2026-10-30.json'
    output.write_text(json.dumps(reports, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(reports))


if __name__ == '__main__':
    main()
