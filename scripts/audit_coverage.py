"""Rank existing intake alternatives to GLED without changing source choices.

Run after `build.py intake-db`. Metrics describe uncorrected intake, not a
reviewed construction; multiple source language IDs may share a Glottocode.
"""

from __future__ import annotations

import argparse
import csv
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

import yaml

from arcaverborum.concepts import load_concept_maps
from arcaverborum.forms_schema import load_parameter_index
from arcaverborum.phonology import normalize_segments

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path, default=ROOT / 'output/report/coverage.csv')
    args = parser.parse_args()
    configs = [yaml.safe_load(p.read_text()) for p in
               sorted((args.root / 'varieties').glob('*/config.yaml'))]
    registered = set()
    gled = defaultdict(list)
    for config in configs:
        registered.add(config.get('glottocode', '').strip().lower())
        gc = (config['sources'].get('source_glottocode') or config.get('glottocode', '')).strip().lower()
        registered.add(gc)
        if config['sources']['transcription'] == 'gled':
            gled[gc].append(config)
    parameters = {}
    for path in sorted((args.root / 'intake').glob('*/parameters_raw.csv')):
        parameters.update(load_parameter_index(path))
    concepts, _ = load_concept_maps(args.root / 'src/arcaverborum/data/concepts.csv')
    glottolog_levels = {}
    glottolog_path = args.root / 'raw/glottolog/languages.csv'
    if glottolog_path.exists():
        with glottolog_path.open() as f:
            glottolog_levels = {r['ID']: r.get('Level', '') for r in csv.DictReader(f)}
    with (args.root / 'src/arcaverborum/data/concept_core.csv').open() as f:
        core = {r['concept_id'] for r in csv.DictReader(f)}
    rows = []
    with sqlite3.connect((args.root / 'intake/intake.sqlite').resolve().as_uri() + '?mode=ro', uri=True) as db:
        db.row_factory = sqlite3.Row
        groups = db.execute('SELECT gc_lc, Dataset, COUNT(*) AS n FROM forms '
                            'GROUP BY gc_lc, Dataset').fetchall()
        for group in groups:
            gc, source = group['gc_lc'], group['Dataset']
            if not gc or source == 'gled':
                continue
            if gc not in gled and (gc in registered or source == 'wiktionary'):
                continue
            forms = db.execute('SELECT * FROM forms WHERE gc_lc=? AND Dataset=? ORDER BY seq',
                               (gc, source)).fetchall()
            mapped, clean = set(), set()
            statuses = Counter()
            language_ids = set()
            for form in forms:
                language_ids.add(form['Language_ID'])
                concepticon_id = (form['Concepticon_ID'] if 'Concepticon_ID' in form.keys() else '')
                concepticon_id = concepticon_id or parameters.get(form['Parameter_ID'], ('', ''))[0]
                concept = concepts.get(concepticon_id, ('', ''))[0]
                _, status = normalize_segments(form['Segments'], form['Form'] or form['Value'])
                statuses[status] += 1
                if concept:
                    mapped.add(concept)
                    if status == 'source':
                        clean.add(concept)
            targets = gled.get(gc) or [{}]
            baseline = set()
            if gc in gled:
                for form in db.execute('SELECT Parameter_ID FROM forms WHERE gc_lc=? AND Dataset=?',
                                       (gc, 'gled')):
                    cid = parameters.get(form['Parameter_ID'], ('', ''))[0]
                    concept = concepts.get(cid, ('', ''))[0]
                    if concept:
                        baseline.add(concept)
            for config in targets:
                rows.append(dict(
                    opportunity='replace_gled' if config else 'unregistered_glottocode',
                    av_id=config.get('av_id', ''), glottocode=gc, source=source,
                    glottolog_level=glottolog_levels.get(gc, 'unknown'),
                    pinned=config.get('pinned', False), source_language_ids=';'.join(sorted(language_ids)),
                    forms=len(forms), mapped_concepts=len(mapped), core_concepts=len(mapped & core),
                    gled_core_concepts=len(baseline & core),
                    gained_core_concepts=len((mapped - baseline) & core),
                    lost_core_concepts=len((baseline - mapped) & core),
                    cognate_forms=sum(bool(f['Cognacy'].strip()) for f in forms),
                    source_clean_core_concepts=len(clean & core), source_clean=statuses['source'],
                    resegmented=statuses['resegmented'], unclean=statuses['unclean'],
                ))
    rows.sort(key=lambda r: (r['source_clean_core_concepts'], r['core_concepts'],
                             r['mapped_concepts']), reverse=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else ['opportunity', 'av_id', 'glottocode', 'source']
    with args.output.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    print(f'{len(rows)} candidates written to {args.output}')
    print('Metrics describe intake only; review identity, provenance, and losses before pinning.')


if __name__ == '__main__':
    main()
