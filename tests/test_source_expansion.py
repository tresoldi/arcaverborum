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
