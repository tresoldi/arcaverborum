"""Protect existing intake and source phonemes during coverage expansion."""

import csv
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


append = load_script('append_source_intake')
repair = load_script('repair_vakh_segments')


def intake_pair(tmp_path):
    target, staged = tmp_path / 'active', tmp_path / 'staged'
    for path, dataset in [(target, 'old'), (staged, 'new')]:
        path.mkdir()
        for name in append.TABLES:
            with (path / name).open('w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Dataset', 'Value'])
                writer.writerow([dataset, 'quoted, value\nsecond line'])
        (path / 'sources.bib').write_text('@misc{' + dataset + ', title={Reference}}\n')
    return staged, target


def snapshot(path):
    return {p.name: p.read_bytes() for p in path.iterdir()}


def test_append_preserves_existing_bytes_and_quoted_rows(tmp_path):
    staged, target = intake_pair(tmp_path)
    before = snapshot(target)
    assert append.append_intake(staged, target) == {'new'}
    assert snapshot(target) == before
    append.append_intake(staged, target, write=True)
    for name in append.TABLES:
        assert (target / name).read_bytes().startswith(before[name])
        with (target / name).open() as f:
            rows = list(csv.DictReader(f))
        assert [r['Dataset'] for r in rows] == ['old', 'new']
        assert all(r['Value'] == 'quoted, value\nsecond line' for r in rows)
    after = snapshot(target)
    with pytest.raises(ValueError, match='only new'):
        append.append_intake(staged, target, write=True)
    assert snapshot(target) == after


def test_schema_error_cannot_truncate_active_intake(tmp_path):
    staged, target = intake_pair(tmp_path)
    before = snapshot(target)
    (staged / 'parameters_raw.csv').write_text('Dataset,Wrong\nnew,value\n')
    with pytest.raises(ValueError, match='schema mismatch'):
        append.append_intake(staged, target, write=True)
    assert snapshot(target) == before


def test_failed_replacement_restores_previously_replaced_tables(tmp_path, monkeypatch):
    staged, target = intake_pair(tmp_path)
    before = snapshot(target)
    original = append.os.replace

    def fail_languages(source, destination):
        if Path(source).name == 'languages.csv':
            raise OSError('simulated replacement failure')
        return original(source, destination)

    monkeypatch.setattr(append.os, 'replace', fail_languages)
    with pytest.raises(OSError, match='simulated'):
        append.append_intake(staged, target, write=True)
    assert snapshot(target) == before


@pytest.mark.parametrize('vowel', ['ɑ', 'o', 'ø'])
def test_breve_repairs_keep_every_source_character(vowel):
    assert repair.attach_breves(f'p {vowel} ̆ l') == f'p {vowel}̆ l'


@pytest.mark.parametrize('segments', ['̆ a', 'p ̆ a', 'a ̆', 'p a , p i'])
def test_unreviewed_breve_bases_and_alternatives_are_not_guessed(segments):
    with pytest.raises(ValueError):
        repair.attach_breves(segments)


@pytest.mark.parametrize(('form', 'expected'), [
    ('chokma', 'tʃ o k m a'),
    ('lhá', 'ɬ a ⁵'),
    ('aali', 'aː l i'),
    ("a'ni", 'a ʔ n i'),
    ('a\u0331', 'ã'),
    ('shsh', 'ʃː'),
])
def test_chickasaw_explicit_modern_reading(form, expected):
    pilot = load_script('chickasaw_pilot')
    assert pilot.modern_reading(form) == expected


@pytest.mark.parametrize('form', ['tulhapi', 'e', 'č', 'a-b', 'á\u0300'])
def test_chickasaw_does_not_guess_legacy_or_unsupported_spelling(form):
    assert load_script('chickasaw_pilot').modern_reading(form) == ''


def test_chickasaw_plain_spelling_does_not_identify_orthography():
    pilot = load_script('chickasaw_pilot')
    assert not pilot.diagnostic('chokma')
    assert pilot.diagnostic("talhlhá'pi")


def test_replacement_rank_counts_only_validated_source_core():
    rank = load_script('rank_gled_replacements')
    forms = [
        {'Parameter_ID': 'p', 'Form': 'word', 'Value': '', 'Segments': ''},
        {'Parameter_ID': 'q', 'Form': 'a', 'Value': '', 'Segments': 'a'},
        {'Parameter_ID': 'r', 'Form': 'i', 'Value': '', 'Segments': 'i'},
    ]
    parameters = {'p': ('1', ''), 'q': ('2', ''), 'r': ('3', '')}
    concepts = {'1': ('core-one', ''), '2': ('core-two', ''), '3': ('other', '')}
    mapped, clean, count = rank.coverage(forms, parameters, concepts, {'core-one', 'core-two'})
    assert mapped == {'core-one', 'core-two'}
    assert clean == {'core-two'}
    assert count == 2


@pytest.mark.parametrize(('word', 'expected'), [
    ('вода', 'v o d a'), ('нєбо', 'nʲ e b o'), ('лїст', 'lʲ i s t'),
    ('корень', 'k o r e nʲ'), ('я', 'j a'), ('гуториц', 'ɦ u t o r i ts'),
    ('хижа', 'h i ʒ a'), ('щ', 'ʃ tʃ'), ('маю', 'm a j u'),
])
def test_pannonian_native_spelling_distinctions(word, expected):
    assert load_script('pannonian_profile').reading(word)[0] == expected


@pytest.mark.parametrize('word', ['умeрaц', 'слово слово', 'дзецко', 'дж', 'ь', 'рь', '-ти', 'во́да'])
def test_pannonian_rejects_unreviewed_contexts(word):
    assert load_script('pannonian_profile').reading(word)[0] == ''


def test_amazonian_staging_adds_only_explicit_dataset_citation(tmp_path, minimal_dataset_path):
    import shutil

    import pandas as pd

    script = load_script('stage_amazonianvoices')
    raw = tmp_path / 'raw/lexibank/amazonianvoices/cldf'
    shutil.copytree(minimal_dataset_path, raw)
    forms = pd.read_csv(raw / 'forms.csv', dtype=str, keep_default_na=False)
    forms['Source'] = ''
    forms.to_csv(raw / 'forms.csv', index=False)
    (raw / 'sources.bib').write_text('')
    (raw / 'cognates.csv').unlink()
    before = (raw / 'forms.csv').read_bytes()
    output = tmp_path / 'staged'
    script.stage(tmp_path, output)
    result = pd.read_csv(output / 'lexibank/forms.csv', dtype=str, keep_default_na=False)
    assert set(result['Source']) == {'amazonianvoices_dataset'}
    bibliography = (output / 'lexibank/sources.bib').read_text()
    assert 'Dataset-level citation' in bibliography
    assert 'CC-BY-4.0' in bibliography
    assert 'CC-BY-NC-4.0' not in bibliography
    assert (raw / 'forms.csv').read_bytes() == before
    (raw / 'sources.bib').write_text('@misc{individual, title={Individual source}}')
    with pytest.raises(ValueError, match='now supplies sources'):
        script.stage(tmp_path, output)


def test_refresh_audit_detects_mapping_and_member_drift(tmp_path):
    import json
    import subprocess

    import yaml

    script = load_script('audit_source_refresh')
    paths = [tmp_path / 'raw/lexibank/demo', tmp_path / 'staged']
    for i, path in enumerate(paths):
        cldf = path / 'cldf'
        cldf.mkdir(parents=True)
        gc = 'abcd1234' if i == 0 else 'efgh1234'
        (cldf / 'languages.csv').write_text('ID,Name,Glottocode\nL,Sample,' + gc + '\n')
        (cldf / 'parameters.csv').write_text('ID,Concepticon_ID\np,' + str(i+1) + '\n')
        (cldf / 'forms.csv').write_text('ID,Language_ID,Parameter_ID,Form\nf,L,p,a\n')
        subprocess.run(['git', 'init', '-q', str(path)], check=True)
        subprocess.run(['git', '-C', str(path), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(path), '-c', 'user.name=Test', '-c', 'user.email=test@example.org',
                        'commit', '-q', '-m', 'Fixture'], check=True)
    directory = tmp_path / 'varieties/demo'
    directory.mkdir(parents=True)
    (directory / 'config.yaml').write_text(yaml.safe_dump(dict(
        av_id='demo', glottocode='abcd1234', sources=dict(transcription='demo', cognates='demo'))))
    result = script.audit(tmp_path, 'demo', paths[1], tmp_path / 'report')
    assert result['language_identity_changes'] == 1
    assert result['concept_mapping_changes'] == 1
    assert result['accepted_member_selections_changed'] == 1
    assert not result['active_intake_changed']
    assert json.loads((tmp_path / 'report/summary.json').read_text())['tables']['forms']['changed_rows'] == 0
    with (tmp_path / 'report/accepted_varieties.csv').open() as f:
        row = next(csv.DictReader(f))
    assert row['old_forms'] == '1' and row['new_forms'] == '0'


def test_refresh_refuses_duplicate_ids(tmp_path):
    script = load_script('audit_source_refresh')
    path = tmp_path / 'forms.csv'
    path.write_text('ID,Form\nf,a\nf,i\n')
    with pytest.raises(ValueError, match='Duplicate source IDs'):
        script.indexed(path)


def test_amazonian_staging_refuses_active_intake(tmp_path):
    active = tmp_path / 'intake'
    active.mkdir()
    marker = active / 'forms.csv'
    marker.write_text('existing evidence\n')
    with pytest.raises(ValueError, match='outside active intake'):
        load_script('stage_amazonianvoices').stage(tmp_path, active)
    assert marker.read_text() == 'existing evidence\n'
