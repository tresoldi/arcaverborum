"""Frozen native evidence survives a primary change without becoming new IPA."""
import csv
from pathlib import Path

import pandas as pd
import pytest

from arcaverborum import tracking
from arcaverborum.forms_schema import FORMS_OUT_FIELDS
from arcaverborum.phonology import normalize_segments
from arcaverborum.preservation import preserved_rows, previous_output_hash
from arcaverborum.supplements import evidence_hash, input_keys


def fixture(tmp_path):
    raw = dict(ID='old-1', Dataset='legacy', Glottocode='abcd1234', Language_ID='legacy-a',
               Parameter_ID='unmapped', Form='Yokaana', Value='Yokaana', Segments='', Comment='', Source='oldbib')
    row = dict.fromkeys(FORMS_OUT_FIELDS, '')
    segments, status = normalize_segments('', raw['Form'])
    row.update(av_id='fam-a', Glottocode='abcd1234', Form=raw['Form'], Value=raw['Value'],
               Segments=segments, Segments_Source=status, transcription_source='legacy', cognate_source='legacy',
               source_form_id=raw['ID'], source_language_id=raw['Language_ID'],
               source_parameter_id=raw['Parameter_ID'], bibtex_key='oldbib', quality_score='0.1', tier='copper')
    row.update(evidence_sha256=evidence_hash(raw), expected_source_concepticon_id='',
               previous_output_sha256=previous_output_hash(row),
               preservation_rationale='Retain unmapped native evidence')
    write(tmp_path, [row])
    return raw, row


def write(tmp_path, rows):
    with (tmp_path / 'preserved_forms.csv').open('w') as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)


def run(tmp_path, raw):
    return preserved_rows(tmp_path, pd.DataFrame([raw]), 'fam-a', 'abcd1234', {}, {})


def test_unmapped_native_record_and_score_survive_verbatim(tmp_path):
    raw, row = fixture(tmp_path)
    assert run(tmp_path, raw) == [{key: row[key] for key in FORMS_OUT_FIELDS}]
    assert ('abcd1234', 'legacy') in input_keys(tmp_path)
    assert 'preserved_forms.csv' in tracking._CUSTOM_FILES
    assert 'preservation.py' in tracking._RECIPE_FILES


@pytest.mark.parametrize('change', ['raw', 'snapshot', 'reading', 'mapping', 'duplicate', 'cognacy'])
def test_preservation_rejects_drift_or_reinterpretation(tmp_path, change):
    raw, row = fixture(tmp_path)
    if change == 'raw':
        raw['Form'] = 'different'
    elif change == 'snapshot':
        row['quality_score'] = '1.0'
    elif change == 'reading':
        row.update(Segments='j o k a n a', Segments_Source='source')
        row['previous_output_sha256'] = previous_output_hash(row)
    elif change == 'mapping':
        row.update(concept_id='cog-know', Concepticon_ID='1410')
        row['previous_output_sha256'] = previous_output_hash(row)
    elif change == 'cognacy':
        row['cognate_source'] = 'primary'
        row['previous_output_sha256'] = previous_output_hash(row)
    write(tmp_path, [row, row] if change == 'duplicate' else [row])
    with pytest.raises(ValueError):
        run(tmp_path, raw)


def test_accepted_snapshots_match_preceding_native_output():
    root = Path(__file__).parents[1]
    for av, count in [('atl-ruuli', 6), ('sit-chintang', 85)]:
        with (root / 'varieties' / av / 'custom/preserved_forms.csv').open() as handle:
            rows = list(csv.DictReader(handle))
        assert len(rows) == count
        assert all(previous_output_hash(row) == row['previous_output_sha256'] for row in rows)
        assert sum(not row['concept_id'] for row in rows) == (4 if count == 6 else 2)
