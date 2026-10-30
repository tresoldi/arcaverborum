"""Edition transport keeps all native evidence and never interprets spellings as IPA."""
import csv
import gzip
import hashlib
import json

import pytest

from arcaverborum.sources import wiktionary_editions as source


def test_full_native_transport_keeps_senses_variants_and_sound_labels(tmp_path, monkeypatch):
    archive = tmp_path / 'fr.gz'
    entries = [dict(word='abc', lang_code='lep', lang='Lepcha', pos='noun',
                    sounds=[dict(ipa='SAMPA-like', raw_tags=['SAMPA'])],
                    senses=[dict(glosses=['literal sense']), dict(glosses=['second sense'], tags=['rare'])],
                    translations=[dict(lang_code='en', word='not another entry')]),
               dict(word='abd', lang_code='lep', lang='Lepcha', pos='noun',
                    senses=[dict(glosses=['inflected sense'], form_of=[dict(word='abc')])]),
               dict(word='unresolved', lang_code='tu', lang='Tupi', pos='noun',
                    senses=[dict(glosses=['literal unresolved sense'])]),
               dict(title='redirect', redirect='abc', pos='hard-redirect')]
    with gzip.open(archive, 'wt') as handle:
        for entry in entries:
            handle.write(json.dumps(entry) + '\n')
    manifest = tmp_path / 'pins.json'
    manifest.write_text(json.dumps([dict(edition='fr', dataset='testedition',
                                        sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
                                        url='https://example.org/pinned',
                                        license='https://creativecommons.org/licenses/by-sa/4.0/')]))
    monkeypatch.setattr(source, 'MANIFEST', manifest)
    monkeypatch.setattr(source, 'ROOT', tmp_path)  # No local/generated intake required.
    output = tmp_path / 'stage'
    counts = source.stage('fr', archive, output)
    assert counts['lexical_entries'] == 3 and counts['native_senses'] == 4
    assert counts['nonlexical_objects'] == 1
    with (output / 'forms.csv').open() as handle:
        forms = list(csv.DictReader(handle))
    assert len(forms) == 3
    with (output / 'languages.csv').open() as handle:
        languages = list(csv.DictReader(handle))
    assert next(r for r in languages if r['Name'] == 'Tupi')['ISO639P3code'] == ''
    assert all(not row['Segments'] and not row['Cognacy'] for row in forms)
    assert json.loads(forms[0]['Comment'])['original'] == entries[0]
    assert json.loads(forms[1]['Comment'])['original']['senses'][0]['form_of']
    with (output / 'parameters_raw.csv').open() as handle:
        parameters = list(csv.DictReader(handle))
    assert parameters[0]['Name'] == 'literal sense; second sense'
    assert all(not row['Concepticon_ID'] for row in parameters)
    archive.write_bytes(b'changed')
    with pytest.raises(ValueError, match='edition changed'):
        source.stage('fr', archive, output)
