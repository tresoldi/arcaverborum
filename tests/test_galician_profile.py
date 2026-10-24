"""Galician dictionary reconciliation must preserve ambiguous vowel quality."""

import csv
import importlib.util
import json
from pathlib import Path

import pandas as pd

from arcaverborum.phonology import apply_profile, load_profile, normalize_segments, segments_are_valid
from arcaverborum.variety import _apply_concept_map

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('galician_dictionary', ROOT / 'scripts/galician_dictionary.py')
dictionary = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dictionary)


def test_homographs_with_different_vowels_are_not_guessed():
    assert dictionary.resolve([
        {'entry_id': '1', 'ipa': 'ˈoso̝'},
        {'entry_id': '2', 'ipa': 'ˈɔso̝'},
    ]) == ('', 'ambiguous_or_invalid')


def test_preferred_reading_shared_by_every_homograph():
    segments, status = dictionary.resolve([
        {'entry_id': '1', 'ipa': 'ˈsol'},
        {'entry_id': '1', 'ipa': '(ˈsɔl)'},
        {'entry_id': '2', 'ipa': 'ˈsol'},
    ])
    assert (segments, status) == ('s o l', 'dictionary')


def test_invalid_homograph_is_not_silently_discarded():
    assert dictionary.resolve([
        {'entry_id': '1', 'ipa': 'ˈsol'},
        {'entry_id': '2', 'ipa': '<?>'},
    ]) == ('', 'ambiguous_or_invalid')


def test_result_parser_removes_homograph_number_and_requires_exact_word():
    document = '''<td class="palabra"><a href="?l=2&ficha=1">sol<sup>1</sup></a></td>
    <td class="info">substantivo</td><td class="transcricion"><div class="ipa">ˈsol</div></td>
    <td class="audio">audio</td>
    <td class="palabra"><a href="?l=2&amp;ficha=2">solar</a></td>
    <td class="transcricion"><div class="ipa">soˈlaɾ</div></td><td class="audio">'''
    assert dictionary.parse_results(document, 'sol') == [
        {'entry_id': '1', 'headword': 'sol', 'ipa': 'ˈsol'}]


def test_unknown_headword_has_no_generated_pronunciation():
    assert dictionary.resolve([]) == ('', 'not_found')


def test_internal_stress_is_removed_before_ipa_tokenization():
    assert dictionary.resolve([{'entry_id': '1', 'ipa': 'aˈβɾiɾ'}]) == (
        'a β ɾ i ɾ', 'dictionary')


def test_exact_dictionary_entries_do_not_transcribe_unknown_concatenations():
    profile = {'^a$': 'a', '^sol$': 's o l'}
    assert apply_profile('sol', profile) == ('s o l', True)
    assert normalize_segments('', 'asol', profile) == ('', 'unclean')
    assert normalize_segments('', 'sola', profile) == ('', 'unclean')
    assert normalize_segments('', 'a sol', profile) == ('', 'unclean')


def test_exact_word_rule_precedes_greedy_rules_and_keeps_other_rules():
    profile = {'^oso$': 'ɔ s o', 'o': 'o', 's': 's'}
    assert apply_profile('oso', profile) == ('ɔ s o', True)
    assert apply_profile('soso', profile) == ('s o s o', True)


def test_exact_mapping_normalizes_unicode_and_preserves_word_boundaries():
    assert apply_profile('o\u0301so', {'^óso$': 'ɔ s o'}) == ('ɔ s o', True)
    assert apply_profile('estar de pé', {'^estar de pé$': 'e s t a ɾ _ d e _ p ɛ'}) == (
        'e s t a ɾ _ d e _ p ɛ', True)


def test_lone_boundary_characters_remain_literal_graphemes():
    assert apply_profile('^a$', {'^': '', '$': '', 'a': 'a'}) == ('a', True)


def test_dictionary_profile_is_used_after_explicit_source_ipa():
    profile = {'^sol$': 's o l'}
    assert normalize_segments('s ɔ l', 'sol', profile) == ('s ɔ l', 'source')


def test_checked_profile_reproduces_from_tracked_dictionary_evidence():
    custom = ROOT / 'varieties/ine-galician/custom'
    profile = load_profile(custom / 'profile.tsv')
    with (custom / 'pronunciation_evidence.csv').open() as f:
        evidence = list(csv.DictReader(f))
    expected = {}
    for row in evidence:
        segments, status = dictionary.resolve(json.loads(row['dictionary_entries']))
        assert (segments, status) == (row['Segments'], row['status'])
        if status == 'dictionary':
            expected[f"^{row['Form']}$"] = segments
            assert segments_are_valid(segments)
    assert profile == expected


def test_attested_open_vowel_and_unknown_spelling():
    profile = load_profile(ROOT / 'varieties/ine-galician/custom/profile.tsv')
    assert normalize_segments('', 'óso', profile) == ('ɔ s o̝', 'profile')
    assert normalize_segments('', 'nome', profile) == ('n o m e̝', 'profile')
    assert normalize_segments('', 'corda', profile) == ('', 'unclean')
    assert normalize_segments('', 'asol', profile) == ('', 'unclean')


def test_letter_name_correction_preserves_pronoun_and_other_senses():
    mapping = pd.read_csv(ROOT / 'varieties/ine-galician/custom/concept_map.csv',
                          dtype=str, keep_default_na=False)
    forms = pd.DataFrame([
        {'Parameter_ID': 'wikt_i_noun_a07bf211', 'Concepticon_ID': '1209', 'Form': 'i'},
        {'Parameter_ID': 'wikt_i_pron_08eca2d6', 'Concepticon_ID': '1209', 'Form': 'eu'},
        {'Parameter_ID': 'wikt_black_adj_735f6ab3', 'Concepticon_ID': '163', 'Form': 'só'},
    ])
    corrected = _apply_concept_map(forms, mapping)
    assert list(corrected['Concepticon_ID']) == ['1024', '1209', '']
    assert list(corrected['_concept_id_override']) == ['lng-character', '', '']
    assert list(corrected['_concept_mapping_blocked']) == [False, False, True]


def test_dictionary_lookup_uses_accepted_concept_corrections(tmp_path):
    import sqlite3

    data = tmp_path / 'src/arcaverborum/data'
    data.mkdir(parents=True)
    (data / 'concepts.csv').write_text(
        'concept_id,concepticon_id,label,pos,semantic_field,definition,status,replacement_id,notes\n'
        'bod-horn,1393,horn,n,Body,horn,active,,\n'
        'kin-i,1209,I,pron,Kinship,I,active,,\n'
    )
    (data / 'concept_core.csv').write_text('concept_id\nbod-horn\nkin-i\n')
    intake = tmp_path / 'intake/wiktionary'
    intake.mkdir(parents=True)
    (intake / 'parameters_raw.csv').write_text('ID,Concepticon_ID\nhorn,\nletter,1209\n')
    with sqlite3.connect(tmp_path / 'intake/intake.sqlite') as db:
        db.execute('CREATE TABLE forms (gc_lc TEXT, Dataset TEXT, seq INTEGER, '
                   'Parameter_ID TEXT, Form TEXT)')
        db.executemany('INSERT INTO forms VALUES (?,?,?,?,?)', [
            ('gali1258', 'wiktionary', 1, 'horn', 'corno'),
            ('gali1258', 'wiktionary', 2, 'letter', 'i'),
        ])
    custom = tmp_path / 'varieties/ine-galician/custom'
    custom.mkdir(parents=True)
    (custom / 'concept_map.csv').write_text(
        'Parameter_ID,concept_id,action\nhorn,bod-horn,map\nletter,,unmap\n'
    )
    assert [row['Form'] for row in dictionary.core_forms(tmp_path)] == ['corno']
