"""Verify the NXT lexical additions and one explicit spelling-uncertainty note.

Stream per-construction hashes; no corpus-wide word matrix or row list is built.
The baseline is frozen privately before this batch and identified in the receipt.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from itertools import groupby
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
csv.field_size_limit(sys.maxsize)
NOTE = (' NXT-04 reinspection could not independently resolve the final accent in the printed image. '
        'Retain the earlier Buyê reading explicitly as uncertain pending specialist/source collation; '
        'no replacement or phonetic inference is authorized.')
NEW = {'pan-reyesano', 'spe-kallawaya', 'len-toba-enenlhet', 'map-habun', 'atl-anyin-morofo'}


def verify(root, baseline):
    before = json.loads(Path(baseline).read_text())
    hashes, counts, additions, states = defaultdict(hashlib.sha256), Counter(), Counter(), Counter()
    core = {r['concept_id'] for r in csv.DictReader((root / 'src/arcaverborum/data/concept_core.csv').open())}
    review = root / 'docs/research/nxt_kipea_review_2026-11-02.csv'
    with review.open(newline='') as handle:
        new_kipea = {'kipeaoriginal_' + r['native_id'] for r in csv.DictReader(handle)
                     if r.get('reviewer_type') == 'model_assisted_visual_review' and r['decision'] == 'admit'}
    slots = Counter()
    note_count = 0
    seen = set()
    with (root / 'output/aggregate/forms.csv').open(newline='') as handle:
        for av, group in groupby(csv.DictReader(handle), key=lambda r: r['av_id']):
            if av in seen:
                raise ValueError('Aggregate constructions are not contiguous')
            seen.add(av)
            mapped, supported = set(), set()
            for row in group:
                cid = row['concept_id']
                states[row['Segments_Source']] += 1
                if cid:
                    mapped.add(cid)
                    if row['Segments_Source'] in {'source', 'profile'}:
                        supported.add(cid)
                if av in NEW or (av == 'kri-kipea' and row['source_form_id'] in new_kipea):
                    additions[av] += 1
                    continue
                if (av, row['source_form_id']) == ('kri-kipea', 'kipeaoriginal_mamiani1699-p4-big'):
                    if row['Comment'].count(NOTE) != 1:
                        raise ValueError('The reviewed uncertainty annotation differs')
                    row = {**row, 'Comment': row['Comment'].replace(NOTE, '', 1)}
                    note_count += 1
                hashes[av].update(json.dumps(row, ensure_ascii=False, sort_keys=True).encode() + b'\n')
                counts[av] += 1
            slots.update(mapped_all=len(mapped), supported_all=len(supported),
                         mapped_core=len(mapped & core), supported_core=len(supported & core))
    if ({k: h.hexdigest() for k, h in hashes.items()} != before['hashes'] or dict(counts) != before['counts']):
        raise ValueError('Protected earlier lexical fields or membership changed')
    if note_count != 1 or additions != Counter({'pan-reyesano': 9, 'spe-kallawaya': 7,
                                               'len-toba-enenlhet': 5, 'map-habun': 213,
                                               'atl-anyin-morofo': 189, 'kri-kipea': 18}):
        raise ValueError('New admissions differ from the reviewed cohort')
    with (root / 'output/aggregate/forms.csv').open('rb') as handle:
        digest = hashlib.file_digest(handle, 'sha256').hexdigest()
    return dict(protected_earlier_records=sum(counts.values()), earlier_lexical_constructions=len(counts),
                additions=dict(additions), added_records=sum(additions.values()),
                accepted_records=sum(counts.values()) + sum(additions.values()),
                lexical_constructions=len(seen), segment_sources=dict(states), slots=dict(slots),
                all_earlier_values_forms_readings_mappings_cognacy_alignments_unchanged=True,
                explicitly_qualified_earlier_comments=note_count,
                aggregate_forms_sha256=digest,
                baseline_sha256=hashlib.sha256(Path(baseline).read_bytes()).hexdigest(),
                qualification='One explicitly scoped comment qualifies an earlier accent reading; '
                'all other earlier fields and every original lexical assignment remain byte-equivalent '
                'as parsed CSV values. New construction counts distinguish four languages and one register.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.root, args.baseline)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
