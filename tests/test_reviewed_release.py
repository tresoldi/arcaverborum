import csv
import importlib.util
import json
import tarfile
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    'reviewed_export', Path(__file__).parents[1] / 'scripts/build_reviewed_release.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def prepare(root):
    aggregate = root / 'output/aggregate'
    aggregate.mkdir(parents=True)
    first = dict(av_id='v', transcription_source='allowed', cognate_source='allowed',
                 source_form_id='a', Value='native', Form='reading', Cognacy='set1',
                 concept_id='c', Segments_Source='source', bibtex_key='ref')
    for name, rows in {
        'forms.csv': [first, {**first, 'transcription_source': 'excluded', 'Value': 'FORBIDDEN_WORD'},
                      {**first, 'cognate_source': 'excluded', 'Value': 'FORBIDDEN_COGNACY'}],
        'metadata.csv': [dict(Dataset='allowed', License='CC-BY-4.0', Repository_Version='v1', Citation='Author')],
        'varieties.csv': [dict(av_id='v')], 'parameters.csv': [dict(concept_id='c')],
    }.items():
        with (aggregate / name).open('w', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    (aggregate / 'sources.bib').write_text('@book{ref, title={Author work}}\n')
    data = root / 'src/arcaverborum/data'
    data.mkdir(parents=True)
    (data / 'concepts.csv').write_text('concept_id\nc\n')
    (root / 'LICENSE').write_text('MIT\n')
    (root / 'pyproject.toml').write_text('[project]\nname="test"\n')
    secret = root / 'varieties/v/custom'
    secret.mkdir(parents=True)
    (secret / 'preserved_forms.csv').write_text('FORBIDDEN_RECIPE_WORD\n')
    policy = root / 'policy.json'
    policy.write_text(json.dumps(dict(sources=[dict(source='allowed', license='CC-BY-4.0',
                                                  upstream_version='v1', authority_url='https://example.org/terms')],
                                      conceptual_terms={'concepts': 'CC-BY-4.0'})))
    return policy


def test_scoped_archive_excludes_unreviewed_rows_and_recipe_payloads(tmp_path):
    policy = prepare(tmp_path)
    a, b = tmp_path / 'a', tmp_path / 'b'
    first = module.build(tmp_path, a, 'test-date', policy, data_revision='fixture')
    second = module.build(tmp_path, b, 'test-date', policy, data_revision='fixture')
    assert first == second and first['lexical_records'] == 1 and not first['full_collection']
    assert first['excluded_records_by_source'] == {'allowed:unreviewed_cognacy_source': 1, 'excluded': 1}
    archive = a / 'arca-reviewed-sources-test-date.tar.gz'
    assert archive.read_bytes() == (b / archive.name).read_bytes()
    with tarfile.open(archive) as tar:
        for member in tar:
            assert member.mtime == 0
            assert b'FORBIDDEN_' not in tar.extractfile(member).read()
    rows = module.read(a / 'payload/data/forms.csv')
    assert rows[0]['Value'] == 'native' and rows[0]['Cognacy'] == 'set1'
    assert rows[0]['release_source_license'] == 'CC-BY-4.0'
    with pytest.raises(FileExistsError):
        module.build(tmp_path, a, 'test-date', policy, data_revision='fixture')


def test_source_name_or_declared_license_alone_cannot_bypass_review(tmp_path):
    policy = prepare(tmp_path)
    data = json.loads(policy.read_text())
    data['sources'][0]['license'] = 'different'
    policy.write_text(json.dumps(data))
    with pytest.raises(ValueError, match='metadata differs'):
        module.build(tmp_path, tmp_path / 'a', 'date', policy, data_revision='fixture')
