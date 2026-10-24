"""Aragonese profile checks for spelling contrasts and conservative gaps."""

from pathlib import Path

import pytest

from arcaverborum.phonology import load_profile, normalize_segments, segments_are_valid

PROFILE = load_profile(Path(__file__).resolve().parents[1]
                       / 'varieties/ine-aragonese/custom/profile.tsv')


@pytest.mark.parametrize(('form', 'segments'), [
    ('capeza', 'k a p e θ a'),
    ('cinco', 'θ i n k o'),
    ('queso', 'k e s o'),
    ('quatro', 'k u a t ɾ o'),
    ('agüerro', 'a ɡ u e r o'),
    ('reloch', 'r e l o tʃ'),
    ('orella', 'o ɾ e ʎ a'),
    ('Espanya', 'e s p a ɲ a'),
    ('año', 'a ɲ o'),
    ('chunio', 'tʃ u n i o'),
    ('caixa', 'k a ʃ a'),
    ('paxaro', 'p a ʃ a ɾ o'),
    ('ro', 'ɾ o'),
    ('tres', 't ɾ e s'),
    ('Europa', 'e u ɾ o p a'),
    ('almirete', 'a l m i ɾ e t e'),
    ('nana roya', 'n a n a _ r o ʝ a'),
    ('areloch', 'a ɾ e l o tʃ'),
])
def test_aragonese_contrasts(form, segments):
    assert normalize_segments('', form, PROFILE) == (segments, 'profile')
    assert segments_are_valid(segments)


@pytest.mark.parametrize('form', ['taxi', 'caxot', 'geniva', "Territorio d'o Norte", 'Viṣṇu',
                                  'reloches', 'relochorella', 'paxaros'])
def test_uncertain_spellings_remain_unclean(form):
    assert normalize_segments('', form, PROFILE) == ('', 'unclean')


def test_profile_outputs_are_valid_ipa():
    assert all(segments_are_valid(value) for value in PROFILE.values() if value)


def test_source_ipa_overrides_broad_profile():
    assert normalize_segments('k w a t ɾ o', 'quatro', PROFILE) == ('k w a t ɾ o', 'source')
