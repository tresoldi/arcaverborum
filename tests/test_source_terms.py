import csv
import hashlib
import json

import pytest

from arcaverborum.source_terms import apply_reviewed_terms, metadata_hash


def test_terms_bind_to_original_values_and_not_a_source_name(tmp_path):
    row = dict(Dataset='source', License='', Citation='Original')
    form = dict(av_id='variety', source_form_id='f1', Value='native', Form='reading',
                transcription_source='source')
    path = tmp_path / 'forms.csv'
    with path.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(form))
        writer.writeheader()
        writer.writerow(form)
    doc = tmp_path / 'review.json'
    doc.write_text('{"review": "exact native witness"}\n')
    payload = json.dumps(['variety', 'f1', 'native', 'reading'], ensure_ascii=False,
                         separators=(',', ':')).encode() + b'\n'
    review = dict(source='source', expected_metadata_sha256=metadata_hash(row),
                  expected_accepted_records=1, accepted_binding_sha256=hashlib.sha256(payload).hexdigest(),
                  evidence_document='review.json',
                  evidence_document_sha256=hashlib.sha256(doc.read_bytes()).hexdigest(),
                  updates={'License': 'CC-BY-4.0'})
    result = apply_reviewed_terms([row], path, [review], evidence_root=tmp_path)
    assert result[0]['License'] == 'CC-BY-4.0' and row['License'] == ''
    with pytest.raises(ValueError, match='binding changed'):
        apply_reviewed_terms([{**row, 'Citation': 'Another edition'}], path, [review], evidence_root=tmp_path)
    path.write_text(path.read_text().replace('native', 'different'))
    with pytest.raises(ValueError, match='binding changed'):
        apply_reviewed_terms([row], path, [review], evidence_root=tmp_path)
    doc.write_text('different review')
    with pytest.raises(ValueError, match='evidence document changed'):
        apply_reviewed_terms([row], path, [review], evidence_root=tmp_path)
    assert apply_reviewed_terms([{'Dataset': 'other'}], path, [review]) == [{'Dataset': 'other'}]
