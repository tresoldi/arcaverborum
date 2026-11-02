"""Apply reviewed attribution repairs only to the exact accepted lexical witness."""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

DATA = Path(__file__).parent / 'data'


def metadata_hash(row):
    return hashlib.sha256(json.dumps(row, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def apply_reviewed_terms(rows, forms_path, reviews=None, *, evidence_root=None):
    """Retain intake declarations; overlay only explicitly guarded source repairs.

    No inference from the project license or from a similarly named source is
    allowed. A change in the accepted original values/forms requires re-review.
    """
    if reviews is None:
        path = DATA / 'source_term_overrides.json'
        reviews = json.loads(path.read_text()) if path.exists() else []
    present = {row['Dataset'] for row in rows}
    selected = {r['source']: r for r in reviews if r['source'] in present}
    if len(selected) != sum(r['source'] in present for r in reviews):
        raise ValueError('Duplicate reviewed source terms')
    if not selected:
        return rows
    root = Path(evidence_root or DATA.parents[2]).resolve()
    for review in selected.values():
        document = (root / review['evidence_document']).resolve()
        if (not document.is_relative_to(root) or not document.is_file()
                or hashlib.sha256(document.read_bytes()).hexdigest() != review['evidence_document_sha256']):
            raise ValueError('Source terms evidence document changed')
    hashes = {source: hashlib.sha256() for source in selected}
    counts = Counter()
    with Path(forms_path).open(newline='') as handle:
        for row in csv.DictReader(handle):
            source = row['transcription_source']
            if source in selected:
                value = [row['av_id'], row['source_form_id'], row['Value'], row['Form']]
                hashes[source].update(json.dumps(value, ensure_ascii=False,
                                                separators=(',', ':')).encode() + b'\n')
                counts[source] += 1
    result = []
    for row in rows:
        review = selected.get(row['Dataset'])
        if review:
            if (metadata_hash(row) != review['expected_metadata_sha256']
                    or hashes[row['Dataset']].hexdigest() != review['accepted_binding_sha256']
                    or counts[row['Dataset']] != review['expected_accepted_records']):
                raise ValueError('Reviewed source terms binding changed: ' + row['Dataset'])
            if (not review.get('evidence_document_sha256')
                    or not set(review['updates']) <= {'License', 'URL', 'Repository_Version', 'Citation'}
                    or not review['updates'].get('License')):
                raise ValueError('Source terms require explicit reviewed attribution')
            row = {**row, **review['updates']}
        result.append(row)
    return result
