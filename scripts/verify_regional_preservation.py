"""Compare every pre-regional published lexical record with refreshed shards."""
import csv
import gzip
import io
import itertools
import json
import subprocess
from pathlib import Path

from arcaverborum.concept_rows import array_rows

ROOT = Path(__file__).resolve().parents[1]
BEFORE = '774717ac90b34496941b3fdb50bf593bade04c46'
PROMOTED = {'map-busoa', 'map-kaimbulawa', 'map-wotu'}


def historical(path):
    return subprocess.check_output(['git', 'show', f'{BEFORE}:{path}'], cwd=ROOT)


def verify():
    previous = json.loads(historical('web/data/manifest.json'))
    current = json.loads((ROOT / 'web/data/manifest.json').read_text())
    assert previous['fields'] == current['fields']
    fields = previous['fields']
    av_index, source_index = fields.index('av_id'), fields.index('source_form_id')
    id_index = fields.index('ID')
    added = set()
    for name in ['horn', 'additional']:
        with (ROOT / f'docs/regional_{name}_reviews_2026-11-01.csv').open() as handle:
            added.update((r['av_id'], r['source_form_id']) for r in csv.DictReader(handle)
                         if r['decision'] == 'admit')
    added.update(('mon-china-buriat', r['source_form_id']) for r in json.loads(
        (ROOT / 'docs/regional_mongolic_reviews_2026-11-01.json').read_text()))
    checked = 0
    promoted_before, promoted_after = {}, {}
    def filtered(stream, promoted, exclude_added=False):
        for row in array_rows(stream):
            key = row[av_index], row[source_index]
            if row[av_index] in PROMOTED:
                assert key not in promoted
                promoted[key] = row
            elif not exclude_added or key not in added:
                yield row
    for family, shard in previous['shards'].items():
        process = subprocess.Popen(['git', 'show', f"{BEFORE}:web/{shard['url']}"],
                                   cwd=ROOT, stdout=subprocess.PIPE)
        with io.TextIOWrapper(gzip.GzipFile(fileobj=process.stdout), encoding='utf-8') as old_stream, gzip.open(
                ROOT / 'web' / current['shards'][family]['url'], 'rt', encoding='utf-8') as new_stream:
            old_rows = filtered(old_stream, promoted_before)
            new_rows = filtered(new_stream, promoted_after, exclude_added=True)
            for old, new in itertools.zip_longest(old_rows, new_rows):
                assert old is not None and new is not None, family
                old[id_index] = new[id_index] = ''  # Aggregate offsets are not native lexical identities.
                assert old == new, (family, old[av_index], old[source_index])
                checked += 1
        assert process.wait() == 0
    assert promoted_before.keys() == promoted_after.keys()
    promoted_rows, labels = len(promoted_before), 0
    for key, row in promoted_before.items():
        updated = promoted_after[key]
        for name, old, new in zip(fields, row, updated, strict=True):
            if name in {'ID', 'evidence_role', 'preferred_source'}:
                continue  # Derived authority labels change when the configured primary changes.
            if old != new:
                assert name == 'Comment' and row[fields.index('transcription_source')] == 'lexirumahoriginal'
                assert old.replace('Reviewed supplement:', 'Reviewed primary form:') == new
                labels += 1
    assert checked + promoted_rows == previous['counts']['forms'] == 2119754
    assert current['counts']['forms'] - previous['counts']['forms'] == len(added) == 64
    return dict(before_commit=BEFORE, previous_records=checked + promoted_rows,
                all_earlier_readings_mappings_cognacy_scores_preserved=True,
                changed_review_role_labels=labels, added_native_records=len(added),
                source_file_hashes=current['source_files'])


if __name__ == '__main__':
    result = verify()
    (ROOT / 'docs/regional_preservation_2026-11-01.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
