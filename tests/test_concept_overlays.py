"""Concept corrections must also work when intake resolves IDs at emit time."""

import csv

import pandas as pd
import pytest

from arcaverborum.catalog import Variety
from arcaverborum.variety import _apply_concept_map, build_one, register


def test_one_concept_correction_preserves_unmapped_intake_rows(tmp_path):
    root = tmp_path / 'varieties'
    vd = register('test-language', root, 'alpha', glottocode='abcd1234')
    vd.custom_dir.mkdir()
    (vd.custom_dir / 'concept_map.csv').write_text(
        'Parameter_ID,Concepticon_ID,Concepticon_Gloss,concept_id\n'
        'alpha_letter,2,CHARACTER,lng-character\n'
    )
    forms = pd.DataFrame([
        dict(ID='letter', Dataset='alpha', Language_ID='alpha_lang', Glottocode='abcd1234',
             Parameter_ID='alpha_letter', Value='i', Form='i', Segments='i'),
        dict(ID='water', Dataset='alpha', Language_ID='alpha_lang', Glottocode='abcd1234',
             Parameter_ID='alpha_water', Value='aka', Form='aka', Segments='a k a'),
    ])
    catalog = {'test-language': Variety('test-language', glottocode='abcd1234')}
    assert build_one(
        'test-language', root, forms, catalog,
        param_index={'alpha_letter': ('3', 'I'), 'alpha_water': ('1', 'WATER')},
        concept_index={'1': ('phy-water', 'water'), '2': ('lng-character', 'character')},
        concept_labels={'phy-water': 'water', 'lng-character': 'character'},
    ) == 2
    with vd.generated_forms.open() as f:
        emitted = {row['source_form_id']: row for row in csv.DictReader(f)}
    assert emitted['letter']['Concepticon_ID'] == '2'
    assert emitted['letter']['concept_id'] == 'lng-character'
    assert emitted['water']['Concepticon_ID'] == '1'
    assert emitted['water']['concept_id'] == 'phy-water'
    assert emitted['water']['concept_label'] == 'water'


def test_unmap_keeps_form_and_provenance_without_parameter_fallback(tmp_path):
    root = tmp_path / 'varieties'
    vd = register('test-language', root, 'alpha', glottocode='abcd1234')
    vd.custom_dir.mkdir()
    (vd.custom_dir / 'concept_map.csv').write_text(
        'Parameter_ID,action\nalpha_false,unmap\n'
    )
    forms = pd.DataFrame([
        dict(ID='false-sense', Dataset='alpha', Language_ID='alpha_lang', Glottocode='abcd1234',
             Parameter_ID='alpha_false', Value='WHO', Form='OMS', Segments='o m s', Source='alpha_ref'),
        dict(ID='true-sense', Dataset='alpha', Language_ID='alpha_lang', Glottocode='abcd1234',
             Parameter_ID='alpha_true', Value='who', Form='quen', Segments='k e n', Source='alpha_ref'),
    ])
    catalog = {'test-language': Variety('test-language', glottocode='abcd1234')}
    assert build_one(
        'test-language', root, forms, catalog,
        param_index={'alpha_false': ('1235', 'WHO'), 'alpha_true': ('1235', 'WHO')},
        concept_index={'1235': ('cog-who', 'who')}, concept_labels={'cog-who': 'who'},
    ) == 2
    with vd.generated_forms.open() as f:
        emitted = {row['source_form_id']: row for row in csv.DictReader(f)}
    row = emitted['false-sense']
    assert (row['concept_id'], row['concept_label'], row['Concepticon_ID']) == ('', '', '')
    assert (row['Form'], row['Segments'], row['source_parameter_id'], row['bibtex_key']) == (
        'OMS', 'o m s', 'alpha_false', 'alpha_ref')
    assert emitted['true-sense']['concept_id'] == 'cog-who'


@pytest.mark.parametrize('correction', [
    {'Parameter_ID': 'p', 'action': 'unmapp'},
    {'Parameter_ID': 'p', 'action': 'unmap', 'concept_id': 'cog-who'},
])
def test_invalid_or_conflicting_actions_are_rejected(correction):
    with pytest.raises(ValueError):
        _apply_concept_map(pd.DataFrame([{'Parameter_ID': 'p'}]), pd.DataFrame([correction]))


def test_per_form_unmap_does_not_clear_other_translations_of_same_sense():
    forms = pd.DataFrame([
        {'ID': 'water', 'Parameter_ID': 'p', 'Form': 'biyo', 'Concepticon_ID': '948'},
        {'ID': 'irrigation', 'Parameter_ID': 'p', 'Form': 'waraabin', 'Concepticon_ID': '948'},
    ])
    corrections = pd.DataFrame([
        {'Parameter_ID': 'p', 'concept_id': 'phy-water', 'action': 'map',
         'source_form_id': '', 'expected_form': ''},
        {'Parameter_ID': 'p', 'concept_id': '', 'action': 'unmap',
         'source_form_id': 'irrigation', 'expected_form': 'waraabin'},
    ]).fillna('')
    result = _apply_concept_map(forms, corrections)
    assert list(result['_concept_mapping_blocked']) == [False, True]
    assert list(result['Concepticon_ID']) == ['948', '']
    assert list(result['_concept_id_override']) == ['phy-water', '']


@pytest.mark.parametrize('changed', [{'Form': 'biyo'}, {'Parameter_ID': 'other'}])
def test_per_form_guard_rejects_reused_source_ids(changed):
    form = {'ID': 'irrigation', 'Parameter_ID': 'p', 'Form': 'waraabin'}
    form.update(changed)
    corrections = pd.DataFrame([{'Parameter_ID': 'p', 'source_form_id': 'irrigation',
                                 'expected_form': 'waraabin', 'action': 'unmap'}])
    with pytest.raises(ValueError, match='no longer matches'):
        _apply_concept_map(pd.DataFrame([form]), corrections)


def test_reviewed_source_form_disappearing_is_not_silently_ignored():
    forms = pd.DataFrame([{'ID': 'new-id', 'Parameter_ID': 'p', 'Form': 'waraabin'}])
    corrections = pd.DataFrame([{'source_form_id': 'old-id', 'action': 'unmap'}])
    with pytest.raises(ValueError, match='disappeared'):
        _apply_concept_map(forms, corrections)
