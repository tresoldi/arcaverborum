"""A frozen conversion must retain native context and refuse changed bytes/terms."""
import csv
import hashlib
import io
import json
import tarfile

import pytest

from arcaverborum.sources import reviewed_cldf


def archive(license='https://creativecommons.org/licenses/by/4.0/'):
    files = {
        'cldf/cldf-metadata.json': json.dumps({'dc:license': license}),
        'cldf/forms.csv': 'ID,Language_ID,Parameter_ID,Form,Value,Segments,Plural_Form,Digital_Source\nf,L,P,a,a,a,aa,https://example.org/f\n',
        'cldf/languages.csv': 'ID,Name\nL,Exact village\n',
        'cldf/parameters.csv': 'ID,Name\nP,leaf\n',
    }
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode='w:gz') as handle:
        for name, text in files.items():
            data = text.encode()
            member = tarfile.TarInfo('repo-tag/' + name)
            member.size = len(data)
            handle.addfile(member, io.BytesIO(data))
    return output.getvalue()


def setup(tmp_path, monkeypatch, data):
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps([dict(dataset='pilot', url='https://example.org/source',
                                        sha256=hashlib.sha256(data).hexdigest(),
                                        license='https://creativecommons.org/licenses/by/4.0/',
                                        genealogy='One underlying witness')]))
    monkeypatch.setattr(reviewed_cldf, 'MANIFEST', manifest)
    dest = tmp_path / 'lexibank/pilot'
    dest.mkdir(parents=True)
    (dest / 'source.tar.gz').write_bytes(data)
    return dest


def test_complete_native_evidence_survives(tmp_path, monkeypatch):
    dest = setup(tmp_path, monkeypatch, archive())
    assert reviewed_cldf.materialize(tmp_path, dataset='pilot')['forms'] == 1
    row = next(csv.DictReader((dest / 'cldf/forms.csv').open()))
    evidence = json.loads(row['Comment'])
    assert evidence['native_form']['Plural_Form'] == 'aa'
    assert evidence['native_form']['Digital_Source'] == 'https://example.org/f'
    assert evidence['native_language']['Name'] == 'Exact village'
    assert evidence['native_parameter']['Name'] == 'leaf'
    assert evidence['reading_basis'] == 'upstream_profile_conversion'


def test_changed_archive_fails_before_output(tmp_path, monkeypatch):
    dest = setup(tmp_path, monkeypatch, archive())
    (dest / 'source.tar.gz').write_bytes(b'changed')
    with pytest.raises(ValueError, match='archive changed'):
        reviewed_cldf.materialize(tmp_path, dataset='pilot')
    assert not (dest / 'cldf').exists()


def test_conflicting_terms_fail(tmp_path, monkeypatch):
    setup(tmp_path, monkeypatch, archive('https://example.org/restricted'))
    with pytest.raises(ValueError, match='license'):
        reviewed_cldf.materialize(tmp_path, dataset='pilot')
