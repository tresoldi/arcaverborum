"""Check reviewed Wiktionary core senses and compile explicit concept corrections.

The authored evidence is each pilot's custom/core_review.csv. --write-maps
compiles those decisions; the default checks source drift and built output.
This checks sense-to-concept compatibility, not native lexical accuracy.
"""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

import yaml

from arcaverborum.concepts import load_concept_maps, load_concepts
from arcaverborum.forms_schema import load_parameter_index

ROOT = Path(__file__).resolve().parents[1]
PILOTS = ('afa-somali', 'afa-afar', 'afa-saho', 'ine-aragonese', 'ine-galician',
          'ine-pannonian-ruthenian')


def compile_mapping(review: dict, concepts: dict) -> dict | None:
    decision = review['decision']
    target = review['target_concept_id']
    if decision not in ('retain', 'needs_review', 'map', 'unmap'):
        raise ValueError(f'Unknown review decision: {decision}')
    if decision == 'unmap':
        if target:
            raise ValueError('Unmapped sense must not have a target concept')
        return dict(Parameter_ID=review['Parameter_ID'], Concepticon_ID='',
                    Concepticon_Gloss='', concept_id='', action='unmap', notes=review['rationale'])
    if target not in concepts:
        raise ValueError(f'Unknown frozen concept: {target}')
    if decision in ('retain', 'needs_review'):
        if target != review['source_concept_id']:
            raise ValueError('A changed concept requires an explicit map decision')
        return None
    concept = concepts[target]
    return dict(Parameter_ID=review['Parameter_ID'], Concepticon_ID=concept.concepticon_id,
                Concepticon_Gloss='', concept_id=target, action='map', notes=review['rationale'])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--write-maps', action='store_true')
    args = parser.parse_args()
    root = args.root.resolve()
    parameters = {}
    for path in sorted((root / 'intake').glob('*/parameters_raw.csv')):
        with path.open() as f:
            parameters.update({r['ID']: r for r in csv.DictReader(f)})
    concepts = {c.concept_id: c for c in load_concepts(root / 'src/arcaverborum/data/concepts.csv')}
    index, _ = load_concept_maps(root / 'src/arcaverborum/data/concepts.csv')
    with (root / 'src/arcaverborum/data/concept_core.csv').open() as f:
        core = {r['concept_id'] for r in csv.DictReader(f)}
    lex_parameters = load_parameter_index(root / 'intake/lexibank/parameters_raw.csv')
    summaries = {}
    db = sqlite3.connect((root / 'intake/intake.sqlite').as_uri() + '?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    try:
        for aid in PILOTS:
            variety = root / 'varieties' / aid
            config = yaml.safe_load((variety / 'config.yaml').read_text())
            gc = config['sources'].get('source_glottocode') or config['glottocode']
            intake = db.execute('SELECT * FROM forms WHERE gc_lc=? AND Dataset=?',
                                (gc, config['sources']['transcription'])).fetchall()
            source_ids = {r['Parameter_ID'] for r in intake}
            source_forms = {r['ID']: r for r in intake}
            source_core = {pid for pid in source_ids
                           if index.get(parameters[pid]['Concepticon_ID'], ('', ''))[0] in core}
            with (variety / 'custom/core_review.csv').open() as f:
                reviews = list(csv.DictReader(f))
            reviewed = {r['Parameter_ID']: r for r in reviews}
            if len(reviewed) != len(reviews) or not source_core <= reviewed.keys():
                raise ValueError(f'{aid}: duplicated reviews or unreviewed current core senses')
            mappings = []
            for pid, review in reviewed.items():
                if pid not in source_ids:
                    raise ValueError(f'{aid}: reviewed parameter disappeared: {pid}')
                parameter = parameters[pid]
                source_concept = index.get(parameter['Concepticon_ID'], ('', ''))[0]
                if (review['source_name'], review['source_concept_id']) != (parameter['Name'], source_concept):
                    raise ValueError(f'{aid}: source sense or mapping changed: {pid}')
                mapping = compile_mapping(review, concepts)
                if mapping:
                    mappings.append(mapping)
            form_reviews = {}
            form_path = variety / 'custom/form_review.csv'
            if form_path.exists():
                with form_path.open() as f:
                    for review in csv.DictReader(f):
                        fid = review['source_form_id']
                        if fid in form_reviews or fid not in source_forms:
                            raise ValueError(f'{aid}: duplicate or missing reviewed form {fid}')
                        form = source_forms[fid]
                        if (form['Parameter_ID'], form['Form']) != (review['Parameter_ID'], review['source_form']):
                            raise ValueError(f'{aid}: source identity changed for reviewed form {fid}')
                        mapping = compile_mapping(review, concepts)
                        if mapping is None:
                            raise ValueError('Per-form review must explicitly map or unmap')
                        mapping.update(source_form_id=fid, expected_form=review['source_form'])
                        mappings.append(mapping)
                        form_reviews[fid] = review
            if args.write_maps:
                path = variety / 'custom/concept_map.csv'
                if path.exists():
                    with path.open() as f:
                        old = {r['Parameter_ID'] for r in csv.DictReader(f)}
                    if not old <= reviewed.keys():
                        raise ValueError(f'{aid}: refusing to discard unreviewed existing corrections')
                with path.open('w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=['Parameter_ID', 'Concepticon_ID',
                                            'Concepticon_Gloss', 'concept_id', 'action', 'notes',
                                            'source_form_id', 'expected_form'], lineterminator='\n')
                    writer.writeheader()
                    writer.writerows(mappings)
                print(f'{aid}: wrote {len(mappings)} reviewed corrections')
                continue
            with (variety / 'generated/forms.csv').open() as f:
                output = list(csv.DictReader(f))
            grouped = defaultdict(list)
            for row in output:
                if row['concept_id'] in core and row['source_parameter_id'] not in reviewed:
                    raise ValueError(f"{aid}: built core sense has no review: {row['source_parameter_id']}")
                grouped[row['source_parameter_id']].append(row)
            for pid, review in reviewed.items():
                if not grouped[pid]:
                    raise ValueError(f'{aid}: reviewed forms missing from build: {pid}')
                for row in grouped[pid]:
                    effective = form_reviews.get(row['source_form_id'], review)
                    target = effective['target_concept_id']
                    if row['concept_id'] != target:
                        raise ValueError(f'{aid}: rebuild needed or incorrect concept for {pid}')
                    expected_external = concepts[target].concepticon_id if target else ''
                    if effective['decision'] in ('map', 'unmap') and row['Concepticon_ID'] != expected_external:
                        raise ValueError(f'{aid}: inconsistent external concept for {pid}')
            current = {r['concept_id'] for r in output} & core
            clean = {r['concept_id'] for r in output if r['Segments_Source'] in ('source', 'profile')} & core
            gled = db.execute('SELECT Parameter_ID FROM forms WHERE gc_lc=? AND Dataset=?', (gc, 'gled'))
            prior = {index.get(lex_parameters.get(r[0], ('', ''))[0], ('', ''))[0] for r in gled} & core
            summaries[aid] = dict(reviewed_parameters=len(reviews), decisions=dict(Counter(
                r['decision'] for r in reviews)), forms=len(output), core_concepts=len(current),
                reviewed_forms=len(form_reviews),
                clean_core_concepts=len(clean), missing_gled_core=sorted(prior-current),
                clean_missing_gled_core=sorted(prior-clean))
            print(f'{aid}: {len(reviews)} senses checked; core {len(current)}, supported {len(clean)}')
    finally:
        db.close()
    if summaries:
        path = root / 'output/report/core_audit.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(summaries, indent=2) + '\n')


if __name__ == '__main__':
    main()
