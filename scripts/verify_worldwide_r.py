"""Reproduce R's exact dictionary readings and check authored native evidence guards."""
import csv
import json
import sqlite3
from pathlib import Path

from iquito_profile import reading as iquito_reading
from zapotec_dictionary_profile import reading as zapotec_reading

from arcaverborum.supplements import evidence_hash

ROOT = Path(__file__).resolve().parents[1]


def rows(path):
    with path.open() as handle:
        return list(csv.DictReader(handle))


checks = 0
with sqlite3.connect((ROOT / 'intake/intake.sqlite').as_uri() + '?mode=ro', uri=True) as db:
    db.row_factory = sqlite3.Row
    for track in ['r01', 'r05']:
        for review in rows(ROOT / f'docs/worldwide_{track}_profiles_2026-10-30.csv'):
            raw = dict(db.execute('select * from forms where Dataset=? and ID=?',
                                  (review['source'], review['source_form_id'])).fetchone())
            assert evidence_hash(raw) == review['evidence_sha256']
            expected = iquito_reading(raw['Form']) if track == 'r01' else zapotec_reading(review['pdlma'])
            assert expected and expected == review['segments']
            if track == 'r05':
                native = json.loads(raw['Comment'].split(': ', 1)[1])
                assert native['entry']['HeadwordPDLMA'] == review['pdlma']
            checks += 1
print(json.dumps(dict(exact_dictionary_readings=checks, tone_length_and_scope_preserved=True)))
