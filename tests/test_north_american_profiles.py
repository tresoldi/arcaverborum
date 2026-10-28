"""Reviewed orthographic contrasts survive; unresolved source conventions stay held."""
import csv
import importlib.util
import unicodedata
from pathlib import Path

from arcaverborum.phonology import apply_profile, load_profile

ROOT = Path(__file__).resolve().parents[1]


def script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def authored_profiles(module, task, field, profiles):
    with (ROOT / 'docs' / f'north_america_na{task}_review_2026-10-28.csv').open() as f:
        rows = [r for r in csv.DictReader(f) if r['decision'] == 'admit']
    for source, path in profiles.items():
        chosen = [r for r in rows if not source or r.get('source') == source]
        expected = {unicodedata.normalize('NFC', '^' + r['Form'] + '$'): module.reading(r[field])
                    for r in chosen}
        assert expected and all(expected.values())
        assert load_profile(ROOT / path) == expected


def test_tseltal_glottals_and_unresolved_compounds():
    m = script('tseltal_profile')
    assert m.reading("ha'") == 'h a ʔ'
    assert m.reading('bak') == 'b a k'
    for word in ['ixim', "ok'-on", 'lumil tokal', 'casa']:
        assert not m.reading(word)
    authored_profiles(m, '04', 'Form', {
        'dicttseltal': 'varieties/may-tzeltal/custom/supplement_profiles/dicttseltal.tsv'})


def test_zapotec_tone_and_checked_nucleus_are_not_vowel_length():
    m = script('zapotec_dictionary_profile')
    assert m.reading('gye7') == 'ɡ j è ʔ'
    assert m.reading('a*ju') == 'ǎ h ù'
    assert m.reading('nisa') == 'n ì s à'
    for word in ['zee', 'bi-zaa', 'gi7xi', 'benda']:
        assert not m.reading(word)
    authored_profiles(m, '05', 'pdlma', {
        ds: 'varieties/oto-isthmus-zapotec/custom/supplement_profiles/' + ds + '.tsv'
        for ds in ['dictdiidxaza', 'dictdidxazageneral']})


def test_alutiiq_length_and_lateral_withheld_apostrophe_rules():
    m = script('alutiiq_profile')
    assert m.reading('staaman') == 's t aː m a n'
    assert m.reading('talliman') == 't a ɬ i m a n'
    for word in ["mal'uk", 'fanaRuq', 'arnaq', 'macaq']:
        assert not m.reading(word)
    authored_profiles(m, '06', 'Form', {'': 'varieties/esk-pacific-gulf-yupik/custom/profile.tsv'})
    profile = load_profile(ROOT / 'varieties/esk-pacific-gulf-yupik/custom/profile.tsv')
    assert apply_profile('unreviewed', profile) == ('', False)
