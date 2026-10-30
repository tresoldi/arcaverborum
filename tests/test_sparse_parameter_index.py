"""Large unmapped dictionaries preserve mapping lookup behavior without huge indexes."""
from arcaverborum.forms_schema import load_parameter_index


def test_unmapped_senses_do_not_change_mapping_or_duplicate_precedence(tmp_path):
    path = tmp_path / 'parameters.csv'
    path.write_text('ID,Name,Concepticon_ID,Concepticon_Gloss\n'
                    'water,water,948,WATER\n'
                    'basket,a specific basket,,\n'
                    'cleared,old water mapping,948,WATER\n'
                    'cleared,reviewed unrelated original sense,,\n'
                    'gloss,original gloss only,,GLOSS\n')
    result = load_parameter_index(path)
    assert result.get('water', ('', '')) == ('948', 'WATER')
    assert result.get('basket', ('', '')) == ('', '')
    assert result.get('cleared', ('', '')) == ('', '')
    assert result.get('gloss', ('', '')) == ('', 'GLOSS')
    assert len(result) == 2


def test_missing_mapping_columns_and_missing_file(tmp_path):
    path = tmp_path / 'parameters.csv'
    assert load_parameter_index(path) == {}
    path.write_text('ID,Name\nentry,literal dictionary sense\n')
    assert load_parameter_index(path) == {}
