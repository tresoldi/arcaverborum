"""High-precision IPA matching cannot erase source pronunciation distinctions."""
from arcaverborum.sources.wiktionary import pronunciations as ipa


def entry(value, **qualifiers):
    return {'sounds': [{'ipa': value, **qualifiers}]}


def test_exact_unqualified_pronunciation_only():
    status, raw, segments = ipa.decide([entry('/tʃaː/')])
    assert status == 'accept' and raw == '/tʃaː/' and segments
    assert ipa.decide([entry('/a/'), entry('/i/')])[0] == 'ambiguous_pronunciation'
    assert ipa.decide([entry('/ˈama/'), entry('/aˈma/')])[0] == 'ambiguous_pronunciation'
    assert ipa.decide([entry('/a/', tags=['regional'])])[0] == 'qualified_pronunciation'
    assert ipa.decide([entry('/a/'), {'sounds': []}])[0] == 'incomplete_homograph'


def test_no_optional_alternatives_or_word_boundary_loss():
    for value in ['/a(b)/', '/a, i/', '/a i/', '/漢/']:
        assert ipa.ipa_segments(value) == ''
    assert ipa.key('xx', 'a\u0301', 'noun') == ipa.key('xx', 'á', 'noun')
    assert ipa.key('xx', 'á', 'noun') != ipa.key('xy', 'á', 'noun')
    assert ipa.key('xx', 'á', 'noun') != ipa.key('xx', 'á', 'verb')


def test_ingestion_preserves_spelling_and_attaches_pronunciation_provenance():
    from arcaverborum.sources.wiktionary.emit import build_forms_df
    from arcaverborum.sources.wiktionary.extract import WiktTranslation

    class NoCognates:
        def get_cognate_ids(self, *_):
            return ''

        def is_loan(self, *_):
            return False

    translation = WiktTranslation('water', 'noun', 'liquid', 'á', 'Example', 'xx', '', '', (), (), '')
    data = {('water', 'noun', 'liquid'): [translation]}
    matches = {ipa.key('xx', 'á', 'noun'): ('/aː/', 'aː', '123')}
    forms = build_forms_df(data, NoCognates(), matches, {'dump_sha256': 'a' * 64})
    assert forms.iloc[0]['Form'] == 'á'
    assert forms.iloc[0]['Value'] == 'á'
    assert forms.iloc[0]['Segments'] == 'aː'
    assert 'https://en.wiktionary.org/wiki/' in forms.iloc[0]['Comment']
    assert 'aaaaaaaaaaaaaaaa' in forms.iloc[0]['Comment']


def test_asturian_profile_keeps_native_subset_conservative():
    import importlib.util
    from pathlib import Path

    spec = importlib.util.spec_from_file_location('asturian_profile',
                                                 Path(__file__).resolve().parents[1] / 'scripts/asturian_profile.py')
    profile = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(profile)
    assert profile.reading('quesu') == 'k e s u'
    assert profile.reading('llobu') == 'ʎ o b u'
    assert profile.reading('caru') == 'k a ɾ u'
    for form in ['pexe', 'yo', 'agua', 'árbol', 'muyer', 'hello world']:
        assert profile.reading(form) == ''


def test_shared_sense_corrections_are_guarded_and_local_overrides_win(tmp_path):
    import csv

    import pandas as pd
    import pytest

    from arcaverborum.variety import _apply_concept_map
    from arcaverborum.wiktionary_senses import load_rules

    parameter = tmp_path / 'parameters.csv'
    parameter.write_text('ID,Name,Concepticon_ID\np,that conjunction,78\n')
    rules = tmp_path / 'rules.csv'
    row = dict(Parameter_ID='p', expected_source_name='that conjunction', expected_source_concepticon_id='78',
               concept_id='', Concepticon_ID='', action='unmap')
    with rules.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)
    assert load_rules(rules, parameter)[0]['action'] == 'unmap'
    load_rules.cache_clear()
    parameter.write_text('ID,Name,Concepticon_ID\np,changed sense,78\n')
    with pytest.raises(ValueError, match='source changed'):
        load_rules(rules, parameter)
    forms = pd.DataFrame([dict(ID='f', Parameter_ID='p', Form='x', _concept_mapping_blocked=True)])
    local = pd.DataFrame([dict(Parameter_ID='p', concept_id='fun-this', Concepticon_ID='1214', action='map')])
    result = _apply_concept_map(forms, local)
    assert not result.iloc[0]['_concept_mapping_blocked']
    assert result.iloc[0]['_concept_id_override'] == 'fun-this'


def test_regional_alternatives_preserve_readings_and_require_every_homograph():
    import importlib.util
    from pathlib import Path

    spec = importlib.util.spec_from_file_location('qualified_pronunciations',
        Path(__file__).resolve().parents[1] / 'scripts/qualified_pronunciations.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    native = {'sounds': [{'ipa': '/a/', 'tags': ['Brazil']}, {'ipa': '[ɐ]', 'tags': ['Brazil']},
                         {'ipa': '/i/', 'tags': ['Portugal']}]}
    status, variants = module.scoped_readings([(1, native)], ['Brazil'])
    assert status == 'accept_alternatives' and set(variants) == {'/a/', '[ɐ]'}
    assert module.scoped_readings([(1, native), (2, {'sounds': []})], ['Brazil'])[0] != 'accept_alternatives'
    assert module.scoped_readings([(1, {'sounds': [{'ipa': '/a/', 'tags': ['Brazil', 'Rio-de-Janeiro']}]})],
                                  ['Brazil'])[0] != 'accept_alternatives'


def test_asturian_documented_hiatus_and_rhotic_contexts():
    import importlib.util
    from pathlib import Path
    spec = importlib.util.spec_from_file_location('asturian_profile_v2',
        Path(__file__).resolve().parents[1] / 'scripts/asturian_profile.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.reading('poeta') == 'p o e t a'
    assert module.reading('rodía') == 'r o d i a'
    assert module.reading('branu') == 'b ɾ a n u'
    assert module.reading('alredores') == 'a l r e d o ɾ e s'
    assert module.reading('falar') == ''  # documented tap/trill variation
    assert module.reading('agua') == ''  # remaining glide/hiatus uncertainty
