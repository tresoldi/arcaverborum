"""Language-specific checks for the Somali orthographic construction."""

from pathlib import Path

import pytest

from arcaverborum.phonology import load_profile, normalize_segments, segments_are_valid

PROFILE = load_profile(Path(__file__).resolve().parents[1]
                       / 'varieties/afa-somali/custom/profile.tsv')


@pytest.mark.parametrize(('form', 'expected'), [
    ('caano', 'ʕ aː n o'),
    ('dhagax', 'ɖ a ɡ a ħ'),
    ('khamiis', 'χ a m iː s'),
    ('shan', 'ʃ a n'),
    ('saddex', 's a dː e ħ'),
    ('gu’', 'ɡ u ʔ'),
    ('Shan', 'ʃ a n'),
    ('SHAN', 'ʃ a n'),
    ('afarta xilli', 'a f a r t a _ ħ i lː i'),
])
def test_somali_spelling_contrasts(form, expected):
    assert normalize_segments('', form, PROFILE) == (expected, 'profile')
    assert segments_are_valid(expected)


@pytest.mark.parametrize('form', ['𐒖𐒍', 'مُشَبَك', 'Tegucigalpa', 'cimri dheer!'])
def test_unsupported_spellings_remain_unclean(form):
    assert normalize_segments('', form, PROFILE) == ('', 'unclean')


def test_profile_emits_valid_ipa():
    assert all(segments_are_valid(value) for value in PROFILE.values())


def test_explicit_ipa_takes_precedence():
    assert normalize_segments('ʕ ɑː n ɔ', 'caano', PROFILE) == ('ʕ ɑː n ɔ', 'source')
