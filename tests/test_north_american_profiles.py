"""Reviewed orthographic contrasts survive; unresolved source conventions stay held."""
import importlib.util
from pathlib import Path

from arcaverborum.phonology import apply_profile, load_profile

ROOT = Path(__file__).resolve().parents[1]


def script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_tseltal_glottals_and_unresolved_compounds():
    m = script('tseltal_profile')
    assert m.reading("ha'") == 'h a ʔ'
    assert m.reading('bak') == 'b a k'
    for word in ['ixim', "ok'-on", 'lumil tokal', 'casa']:
        assert not m.reading(word)
    m.compile_profile(ROOT)


def test_zapotec_tone_and_checked_nucleus_are_not_vowel_length():
    m = script('zapotec_dictionary_profile')
    assert m.reading('gye7') == 'ɡ j è ʔ'
    assert m.reading('a*ju') == 'ǎ h ù'
    assert m.reading('nisa') == 'n ì s à'
    for word in ['zee', 'bi-zaa', 'gi7xi', 'benda']:
        assert not m.reading(word)
    m.compile_profile(ROOT)


def test_alutiiq_length_and_lateral_withheld_apostrophe_rules():
    m = script('alutiiq_profile')
    assert m.reading('staaman') == 's t aː m a n'
    assert m.reading('talliman') == 't a ɬ i m a n'
    for word in ["mal'uk", 'fanaRuq', 'arnaq', 'macaq']:
        assert not m.reading(word)
    m.compile_profile(ROOT)
    profile = load_profile(ROOT / 'varieties/esk-pacific-gulf-yupik/custom/profile.tsv')
    assert apply_profile('unreviewed', profile) == ('', False)
