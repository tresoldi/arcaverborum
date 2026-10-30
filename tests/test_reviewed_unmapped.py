"""Reviewed dictionary depth must not invent concept matches or pronunciation."""
import json

import pandas as pd
import pytest

from arcaverborum.catalog import Variety
from arcaverborum.supplements import evidence_hash, reviewed_frames
from arcaverborum.variety import emit_forms


def evidence():
    row = dict(ID='dictionary_1', Dataset='dictionary', Language_ID='dictionary_lect',
               Glottocode='xxxx1234', Parameter_ID='dictionary_sense1', Value='abc', Form='abc',
               Segments='', Comment=json.dumps({'original': {'sense': 'a very specific basket'}}))
    decision = dict(source='dictionary', source_form_id=row['ID'], source_language_id=row['Language_ID'],
                    source_glottocode=row['Glottocode'], evidence_sha256=evidence_hash(row),
                    expected_source_concepticon_id='948', concept_id='', decision='admit',
                    rationale='Reviewed literal native sense, lect and written citation; no exact catalog sense.',
                    mapping_decision='retain_source_sense_unmapped',
                    expected_source_sense='a very specific basket', source_sense_path='original.sense',
                    entry_kind='lemma', transcription_policy='orthographic_only')
    return row, decision


def frames(tmp_path, row, decision):
    return list(reviewed_frames(tmp_path, pd.DataFrame([row]), 'xxxx1234',
                                {row['Parameter_ID']: ('948', 'WATER')}, {'phy-water': '948'},
                                decisions=[decision]))


def test_retained_sense_blocks_even_an_existing_upstream_core_mapping(tmp_path):
    row, decision = evidence()
    source, frame, profile = frames(tmp_path, row, decision)[0]
    emitted = emit_forms(frame, av_id='und-test', variety=Variety(av_id='und-test'),
                         transcription_source=source, cognate_source=source,
                         forms_score=0.5, tier='copper', param_index={row['Parameter_ID']: ('948', 'WATER')},
                         concept_index={'948': 'phy-water'}, concept_labels={'phy-water': 'water'},
                         profile=profile)[0]
    assert emitted['concept_id'] == '' and emitted['Concepticon_ID'] == ''
    assert emitted['Segments'] == '' and emitted['Segments_Source'] == 'unclean'
    assert emitted['source_form_id'] == row['ID']
    assert 'a very specific basket' in emitted['Comment']


@pytest.mark.parametrize('change', [dict(concept_id='phy-water'), dict(expected_source_sense='basket'),
                                  dict(source_sense_path='missing.sense'), dict(entry_kind='crossreference'),
                                  dict(entry_kind='parse_hold'), dict(expected_source_sense='')])
def test_incomplete_or_false_unmapped_review_fails_closed(tmp_path, change):
    row, decision = evidence()
    with pytest.raises(ValueError, match='Unmapped admission'):
        frames(tmp_path, row, {**decision, **change})


def test_native_drift_and_source_mapping_drift_remain_guarded(tmp_path):
    row, decision = evidence()
    with pytest.raises(ValueError, match='evidence changed'):
        frames(tmp_path, {**row, 'Comment': '{}'}, decision)
    with pytest.raises(ValueError, match='concept changed'):
        frames(tmp_path, row, {**decision, 'expected_source_concepticon_id': ''})
