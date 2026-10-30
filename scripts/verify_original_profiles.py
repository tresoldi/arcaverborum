"""Verify S finite reading profiles against guarded recipes and actual accepted output."""
import csv
import hashlib
import json
import unicodedata
from pathlib import Path

from arcaverborum.phonology import load_profile, normalize_segments

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    with path.open() as handle:
        return list(csv.DictReader(handle))


results = []
for path in sorted((ROOT / 'docs').glob('worldwide_s0*_profiles_2026-10-30.csv')):
    for row in read(path):
        aid = row.get('av_id', 'man-goo')
        directory = ROOT / 'varieties' / aid
        ledgers = [r for name in ['primary.csv', 'supplements.csv'] if (directory / 'custom' / name).exists()
                   for r in read(directory / 'custom' / name)]
        matches = [r for r in ledgers if r['source_form_id'] == row['source_form_id']]
        assert len(matches) == 1
        decision = matches[0]
        profile = directory / 'custom/supplement_profiles' / decision['profile_file']
        assert hashlib.sha256(profile.read_bytes()).hexdigest() == decision['profile_sha256']
        expected, status = normalize_segments('', row['Form'], load_profile(profile))
        assert status == 'profile'
        proposed, _ = normalize_segments(row['segments'], row['Form'])
        assert unicodedata.normalize('NFC', expected) == unicodedata.normalize('NFC', proposed)
        forms = [r for r in read(directory / 'generated/forms.csv')
                 if r['source_form_id'] == row['source_form_id']]
        assert len(forms) == 1 and forms[0]['Segments_Source'] == 'profile'
        assert forms[0]['Segments'] == expected
        results.append(dict(av_id=aid, source_form_id=row['source_form_id'], Form=row['Form'],
                            segments=expected, profile_sha256=decision['profile_sha256']))
upstream = json.loads((ROOT / 'docs/worldwide_s06_identity_profiles_2026-10-30.json').read_text())['profiles']
for resource in upstream:
    path = ROOT / 'raw/curation/s/lexirumah-profiles' / resource['path']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == resource['sha256']
proof = dict(exact_readings=len(results), readings=results, upstream_profile_hashes=len(upstream))
(ROOT / 'docs/worldwide_s_profile_verification_2026-10-30.json').write_text(json.dumps(proof, indent=2) + '\n')
print('Verified', len(results), 'finite profiles against guarded admissions and accepted output')
