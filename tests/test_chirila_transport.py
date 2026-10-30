"""Research staging must retain raw layers without bypassing public-source gates."""
import hashlib
import importlib.util
import json
import sqlite3
from pathlib import Path

import pytest

path = Path(__file__).resolve().parents[1] / 'scripts/audit_chirila_transport.py'
spec = importlib.util.spec_from_file_location('chirila_transport', path)
transport = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transport)


def test_private_transport_preserves_duplicate_layers_and_flags_short_record(tmp_path):
    source = tmp_path / 'native.csv'
    source.write_text('StdLangID,OriginalForm,PhonemicisedIPA,Reconstruction_Form\n'
                      '4,spelling,ipa,*hypothesis\n4,spelling,ipa,*hypothesis\n4,short\n')
    destination = tmp_path / 'research.sqlite'
    report = transport.stage(source, destination, hashlib.sha256(source.read_bytes()).hexdigest())
    assert report['rows'] == 3 and report['malformed_ordinals'] == [3]
    assert report['public_admission'] is False
    with sqlite3.connect(destination) as connection:
        rows = connection.execute('SELECT native_json,native_sha256 FROM native ORDER BY ordinal').fetchall()
    assert rows[0] == rows[1]
    assert json.loads(rows[0][0]) == dict(StdLangID='4', OriginalForm='spelling',
                                        PhonemicisedIPA='ipa', Reconstruction_Form='*hypothesis')
    assert json.loads(rows[2][0])['Reconstruction_Form'] is None
    with pytest.raises(ValueError, match='new private'):
        transport.stage(source, destination, report['source_sha256'])
    with pytest.raises(ValueError, match='payload changed'):
        transport.stage(source, tmp_path / 'other.sqlite', 'wrong')
