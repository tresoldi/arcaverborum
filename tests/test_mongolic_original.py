"""The original dictionary transport keeps native notation and rejects drift."""
import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "mongolic_original", Path(__file__).parents[1] / "scripts/stage_mongolic_original.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def entry(question="xx", labels=None):
    labels = labels or [f"member{i}" for i in range(14)]
    cells = "".join(f"<li><em>{label}</em><b>ŋaː? / x</b></li>" for label in labels)
    return (f'<li><br><div id="mon"><b>reference</b> [N]<em>Eng.</em>water &amp; ice</div>'
            f'<ul>{cells}<li>; {question}</li></ul></li>').encode()


def test_literal_notation_and_unknown_native_questionnaire_are_preserved():
    row, = module.entries(entry(), expected_entries=1)
    assert row['questionnaire'] == 'xx'
    assert row['sense'] == 'water & ice'
    assert row['pos'] == 'N'
    assert all(value == 'ŋaː? / x' for _, value in row['cells'])
    assert 'native_html' in row and len(row['native_sha256']) == 64
    assert 'Segments' not in row


def test_edition_size_members_and_native_references_fail_closed():
    with pytest.raises(ValueError, match='inventory changed'):
        list(module.entries(entry()))
    with pytest.raises(ValueError, match='member inventory'):
        list(module.entries(entry(labels=['duplicate'] * 14), expected_entries=1))
    with pytest.raises(ValueError, match='questionnaire reference'):
        list(module.entries(entry(question='invented'), expected_entries=1))


def test_staging_cannot_replace_active_intake(tmp_path):
    with pytest.raises(ValueError, match='outside active intake'):
        module.stage(tmp_path, tmp_path / 'intake/lexibank')


def test_existing_source_drift_is_not_overwritten_by_fetch(tmp_path):
    manifest = tmp_path / 'src/arcaverborum/data/regional/mongolicbv2026.json'
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps(dict(resources={'edition':dict(path='edition.html', sha256='0'*64)})))
    source = tmp_path / 'raw/curation/edition.html'
    source.parent.mkdir(parents=True)
    source.write_bytes(b'changed original')
    with pytest.raises(ValueError, match='Pinned Mongolic source changed'):
        module.stage(tmp_path, tmp_path / 'stage', fetch=True)
    assert source.read_bytes() == b'changed original'
    assert not (tmp_path / 'stage').exists()
