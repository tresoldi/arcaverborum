"""Rank individual source members against accepted GLED core coverage.

Intake candidates remain unreviewed. Gains count validated source segments,
not IPA guessed from spelling. Raw mapping potential is reported separately.
No source choice or active intake is changed.
"""

from __future__ import annotations

import argparse
import csv
import sqlite3
from collections import defaultdict
from pathlib import Path

import yaml

from arcaverborum.concepts import load_concept_maps
from arcaverborum.forms_schema import load_parameter_index
from arcaverborum.phonology import normalize_segments

ROOT = Path(__file__).resolve().parents[1]


def coverage(forms, parameters, concepts, core):
    mapped, clean = set(), set()
    clean_count = 0
    for form in forms:
        cid = parameters.get(form['Parameter_ID'], ('', ''))[0]
        concept = concepts.get(cid, ('', ''))[0]
        _, status = normalize_segments(form['Segments'], form['Form'] or form['Value'])
        clean_count += status == 'source'
        if concept in core:
            mapped.add(concept)
            if status == 'source':
                clean.add(concept)
    return mapped, clean, clean_count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    targets = defaultdict(list)
    for path in sorted((root / 'varieties').glob('*/config.yaml')):
        config = yaml.safe_load(path.read_text())
        if config['sources']['transcription'] == 'gled':
            gc = config['sources'].get('source_glottocode') or config['glottocode']
            targets[gc.lower()].append(config)
    parameters = {}
    metadata = {}
    for path in sorted((root / 'intake').glob('*/parameters_raw.csv')):
        parameters.update(load_parameter_index(path))
    for path in sorted((root / 'intake').glob('*/metadata.csv')):
        with path.open() as f:
            metadata.update({r['Dataset']: r for r in csv.DictReader(f)})
    concepts, _ = load_concept_maps(root / 'src/arcaverborum/data/concepts.csv')
    with (root / 'src/arcaverborum/data/concept_core.csv').open() as f:
        core = {r['concept_id'] for r in csv.DictReader(f)}
    rows = []
    with sqlite3.connect((root / 'intake/intake.sqlite').as_uri() + '?mode=ro', uri=True) as db:
        db.row_factory = sqlite3.Row
        for gc, configs in sorted(targets.items()):
            groups = defaultdict(list)
            for form in db.execute('SELECT * FROM forms WHERE gc_lc=? ORDER BY seq', (gc,)):
                if form['Dataset'] != 'gled':
                    groups[form['Dataset'], form['Language_ID']].append(form)
            for config in configs:
                built = root / 'varieties' / config['av_id'] / 'generated/forms.csv'
                if not built.exists():
                    raise ValueError('Build accepted baseline first: ' + config['av_id'])
                with built.open() as f:
                    baseline = list(csv.DictReader(f))
                baseline_core = {r['concept_id'] for r in baseline if r['concept_id'] in core}
                baseline_clean = {r['concept_id'] for r in baseline
                                  if r['concept_id'] in core and r['Segments_Source'] in {'source', 'profile'}}
                for (source, member), forms in groups.items():
                    mapped, clean, clean_count = coverage(forms, parameters, concepts, core)
                    meta = metadata.get(source, {})
                    tier = ('source_ipa_candidate' if clean else 'orthography_review_required')
                    rows.append(dict(
                        av_id=config['av_id'], name=config['name'], glottocode=gc,
                        source=source, source_language_id=member, forms=len(forms),
                        baseline_core=len(baseline_core), baseline_clean_core=len(baseline_clean),
                        candidate_raw_core=len(mapped), candidate_source_clean_core=len(clean),
                        clean_core_gained=len(clean - baseline_clean),
                        clean_core_lost=len(baseline_clean - clean),
                        net_clean_core=len(clean) - len(baseline_clean),
                        raw_core_gained=len(mapped - baseline_core),
                        raw_core_lost=len(baseline_core - mapped),
                        potential_net_core=len(mapped) - len(baseline_clean), source_clean_forms=clean_count,
                        cognate_forms=sum(bool(f['Cognacy'].strip()) for f in forms),
                        review_route=tier, identity_review='required; exact source member only',
                        source_citation=meta.get('Citation', ''), license=meta.get('License', ''),
                        source_url=meta.get('URL', ''), source_version=meta.get('Repository_Version', ''),
                    ))
    rows.sort(key=lambda r: (0 if r['net_clean_core'] > 0 else 1,
                             -r['net_clean_core'] if r['net_clean_core'] > 0 else -r['potential_net_core'],
                             r['raw_core_lost'], -r['candidate_raw_core'],
                             r['av_id'], r['source'], r['source_language_id']))
    output = args.output or root / 'output/report/gled_replacements.csv'
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else ['av_id', 'source', 'source_language_id']
    with output.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    print(f'{len(rows)} member-level alternatives for {len(targets)} GLED identities; no accepted sources changed')


if __name__ == '__main__':
    main()
