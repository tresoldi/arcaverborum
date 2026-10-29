"""Report concept-level source dependence and notation differences from accepted web data.

Additional notation is an observation, never proof of a phonemic contrast or of
independent corroboration. Preferred source follows the configured construction.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def report(output):
    manifest = json.loads((ROOT / 'web/data/manifest.json').read_text())
    fields = manifest['fields']
    totals = Counter()
    languages = defaultdict(Counter)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('w') as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            'av_id', 'concept_id', 'preferred_source', 'supported_sources',
            'gled_dependence', 'preferred_marks_not_recorded_in_gled',
        ], lineterminator='\n')
        writer.writeheader()
        for shard in manifest['shards'].values():
            concepts = {}
            with gzip.open(ROOT / 'web' / shard['url']) as source:
                for values in json.load(source):
                    row = dict(zip(fields, values, strict=True))
                    if not row['concept_id'] or row['Segments_Source'] not in {'source', 'profile'}:
                        continue
                    key = row['av_id'], row['concept_id']
                    entry = concepts.setdefault(key, dict(preferred=row['preferred_source'], sources=set(),
                                                         dependence=row['gled_dependence'], preferred_marks=set(),
                                                         gled_marks=set()))
                    entry['sources'].add(row['transcription_source'])
                    marks = set(filter(None, row['phonological_marks'].split(';')))
                    if row['transcription_source'] == row['preferred_source']:
                        entry['preferred_marks'].update(marks)
                    if row['transcription_source'] == 'gled':
                        entry['gled_marks'].update(marks)
            for (aid, cid), entry in sorted(concepts.items()):
                extra = entry['preferred_marks'] - entry['gled_marks'] if 'gled' in entry['sources'] else set()
                writer.writerow(dict(av_id=aid, concept_id=cid, preferred_source=entry['preferred'],
                                     supported_sources=';'.join(sorted(entry['sources'])),
                                     gled_dependence=entry['dependence'],
                                     preferred_marks_not_recorded_in_gled=';'.join(sorted(extra))))
                totals['supported_concepts'] += 1
                totals[entry['dependence']] += 1
                languages[aid][entry['dependence']] += 1
                if entry['preferred']:
                    totals['configured_primary_supported'] += 1
                if extra:
                    totals['preferred_additional_notation'] += 1
    summary = dict(totals=totals, languages=languages,
                   interpretation='Construction-level supported coverage; source overlap is not independent evidence. '
                                  'Notation differences do not certify phonemic contrasts or complete tone.')
    output.with_suffix('.json').write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n')
    print(json.dumps(totals, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'output/report/source_fidelity.csv')
    report(parser.parse_args().output)
