"""Pinned original American evidence; supplied citations and reconstructions stay distinct."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import unicodedata
from pathlib import Path

import requests

from arcaverborum.sources.ancient_lexica import write_csv
from arcaverborum.sources.wiktionary.pronunciations import ipa_segments

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / 'src/arcaverborum/data'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def extract(spec, payload, review):
    if spec['kind'] == 'hgn_phonemic':
        native = json.loads(payload)
        if native['id'] != review['member'] or native['name'] != review['member_name']:
            raise ValueError('HGN source-member drift')
        table = native['tables'][review['table']]
        cells = table['rows'][int(review['row_index'])]
        if len(cells) != len(table['header']) or len(set(table['header'])) != len(table['header']):
            raise ValueError('HGN table schema changed')
        row = dict(zip(table['header'], cells, strict=True))
        if row['Orthographic Form'].strip() or not row['Phonemicized Form'].strip():
            raise ValueError('HGN pilot requires omitted phonemic-only evidence')
        if row['English'][0] != review['feature']:
            raise ValueError('HGN source feature changed')
        original, sense = row['Phonemicized Form'], row['English'][1]
        # A finite reviewed whole citation; alternatives, bound forms and editorial text are held.
        citation = original.strip()
        if any(c in citation for c in ',;()[]/ -:') or not ipa_segments(citation):
            raise ValueError('HGN citation requires separate notation/alternative review')
        evidence = dict(native_row=row, member_metadata={k: v for k, v in native.items() if k != 'tables'})
        segments = ipa_segments(original)
        basis = 'source_reported_phonemic_citation'
    elif spec['kind'] == 'reconstruction_csv':
        rows = list(csv.DictReader(io.StringIO(payload.decode('utf-8-sig'))))
        row = rows[int(review['row_index'])]
        original, sense = row['FORM'], row['Gloss']
        if not original.strip().startswith('*'):
            raise ValueError('Reconstruction lacks original reconstruction marker')
        evidence = dict(native_row=row, reconstruction=True,
                        authority=review['authority'], scope=review['member_name'])
        segments, basis = '', 'source_reported_reconstruction'
    else:
        raise ValueError('Unknown reviewed American source kind')
    if digest(evidence) != review['native_sha256']:
        raise ValueError('Original American evidence changed')
    if original != review['Form'] or sense != review['source_sense']:
        raise ValueError('Original American form or sense changed')
    evidence.update(source_gloss=sense, reading_basis=basis, mapping_review=review['rationale'],
                    source_version=spec['version'], source_member=review['member'],
                    source_citation=spec['citation'], source_genealogy=spec['genealogy'])
    return unicodedata.normalize('NFC', original).strip(), segments, evidence


def materialize(raw_root, *, dataset, download=False):
    specs = json.loads((DATA / 'american_evidence_sources.json').read_text())
    spec = next(s for s in specs if s['dataset'] == dataset)
    root = raw_root / 'lexibank' / dataset
    root.mkdir(parents=True, exist_ok=True)
    payloads = {}
    for resource in spec['resources']:
        path = root / resource['filename']
        if Path(resource['filename']).name != resource['filename']:
            raise ValueError('American resource must use a local filename')
        if download:
            response = requests.get(resource['url'], timeout=40)
            response.raise_for_status()
            if hashlib.sha256(response.content).hexdigest() != resource['sha256']:
                raise ValueError('Pinned American resource changed')
            path.write_bytes(response.content)
        payloads[resource['filename']] = path.read_bytes()
        if hashlib.sha256(payloads[resource['filename']]).hexdigest() != resource['sha256']:
            raise ValueError('Pinned American resource hash mismatch')
    concepts = {r['concept_id']: r for r in csv.DictReader((DATA / 'concepts.csv').open())}
    reviews = list(csv.DictReader((ROOT / spec['review']).open()))
    forms, parameters, members, seen = [], [], {}, set()
    for review in reviews:
        if review['decision'] != 'admit':
            continue
        if review['dataset'] != dataset or not review['rationale'] or review['source_form_id'] in seen:
            raise ValueError('Invalid reviewed American admission')
        seen.add(review['source_form_id'])
        form, segments, evidence = extract(spec, payloads[review['filename']], review)
        c = concepts[review['concept_id']]
        fid = review['source_form_id']
        parameters.append(dict(ID=fid, Name=review['source_sense'],
                               Concepticon_ID=c['concepticon_id'], Concepticon_Gloss=c['label']))
        forms.append(dict(ID=fid, Language_ID=review['member'], Parameter_ID=fid, Form=form,
                          Value=review['Form'], Segments=segments, Source='source',
                          Comment=json.dumps(evidence, ensure_ascii=False, sort_keys=True)))
        members[review['member']] = dict(ID=review['member'], Name=review['member_name'],
                                         Glottocode=review['glottocode'], Glottolog_Name=review['member_name'],
                                         Family=review['family'],
                                         Macroarea='South America')
    if not forms:
        raise ValueError('Empty reviewed American stage')
    cldf = root / 'cldf'
    cldf.mkdir(exist_ok=True)
    term = 'http://cldf.clld.org/v1.0/terms.rdf#'
    props = dict(ID='id', Name='name', Form='form', Value='value', Segments='segments',
                 Language_ID='languageReference', Parameter_ID='parameterReference', Source='source',
                 Comment='comment', Glottocode='glottocode', Concepticon_ID='concepticonReference')
    metadata = {'@context': 'http://www.w3.org/ns/csvw', 'dc:conformsTo': term + 'Wordlist',
                'dc:title': spec['name'], 'dc:license': spec['license'],
                'dc:bibliographicCitation': spec['citation'], 'dcat:accessURL': spec['url'],
                'prov:wasDerivedFrom': [{'dc:title': 'Repository', 'dc:created': spec['version']}],
                'dc:source': 'sources.bib', 'tables': []}
    for name, rows, kind in [('forms.csv', forms, 'FormTable'), ('parameters.csv', parameters, 'ParameterTable'),
                             ('languages.csv', list(members.values()), 'LanguageTable')]:
        write_csv(cldf / name, rows)
        cols = []
        for key in rows[0]:
            col = dict(name=key, datatype='string')
            if key in props:
                col['propertyUrl'] = term + props[key]
            if key in {'Segments', 'Source'}:
                col['separator'] = ' ' if key == 'Segments' else ';'
            cols.append(col)
        metadata['tables'].append(dict(url=name, **{'dc:conformsTo': term + kind},
                                        tableSchema=dict(columns=cols, primaryKey='ID')))
    (cldf / 'cldf-metadata.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n')
    (cldf / 'sources.bib').write_text('@misc{source,\n title = {' + spec['citation'] + '},\n url = {'
                                    + spec['url'] + '},\n note = {Data license ' + spec['license'] + '}\n}\n')
    return dict(dataset=dataset, forms=len(forms), members=len(members))
