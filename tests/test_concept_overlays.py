"""Concept corrections must also work when intake resolves IDs at emit time."""

import csv

import pandas as pd

from arcaverborum.catalog import Variety
from arcaverborum.variety import build_one, register


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
