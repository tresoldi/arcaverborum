"""Build pinned, sense-guarded WordNet sidecars. No lexical records are changed.

Run with --fetch on a clean checkout; resources are verified before parsing.
Review decisions are explicit and never inferred from candidate rank.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

import requests

from arcaverborum.wordnet import (
    DATA,
    concept_hash,
    digest,
    load_bundle,
    normalized,
    parse_oewn,
    parse_princeton,
    read_csv,
    resolve_bridge,
)

STOP = set('a an the of in to or and with that is which for as by from on one someone something '
           'be being having used any into it its usually especially person act state make'.split())


def tokens(value):
    return set(re.findall(r'[a-z]+', normalized(value))) - STOP


def write_csv(path, rows, fields):
    with path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def build(raw, output, fetch=False):
    output.mkdir(parents=True, exist_ok=True)
    sources = json.loads((DATA / 'wordnet/sources.json').read_text())
    raw.mkdir(parents=True, exist_ok=True)
    for pin in sources['resources']:
        path = raw / pin['filename']
        if fetch and not path.exists():
            response = requests.get(pin['url'], timeout=120)
            response.raise_for_status()
            path.write_bytes(response.content)
        if hashlib.sha256(path.read_bytes()).hexdigest() != pin['sha256']:
            raise ValueError(f'Resource checksum failed: {path}')
    synsets = parse_oewn(raw / 'oewn2025.xml.gz')
    pwn = parse_princeton(raw / 'pwn30.tar.gz')
    pwn_ili = {}
    for line in (raw / 'ili-map-pwn30.tab').read_text().splitlines():
        ili, sid = line.split('\t')
        pwn_ili[sid] = ili
    ili_oewn = defaultdict(list)
    for sid, row in synsets.items():
        if row['ili'] and row['ili'] != 'in':
            ili_oewn[row['ili']].append(sid)
    ili_pwn = defaultdict(list)
    for sid, ili in pwn_ili.items():
        ili_pwn[ili].append(sid)
    for row in synsets.values():
        row['pwn30'] = sorted(ili_pwn.get(row['ili'], []))
    bridges = {}
    bridge_rows = read_csv(raw / 'concepticon-wordnet.tsv', '\t')
    for row in bridge_rows:
        key = resolve_bridge(row, pwn)
        ili = pwn_ili.get(key, '')
        targets = ili_oewn.get(ili, [])
        if not targets:
            sid = 'pwn30-' + key
            synsets[sid] = dict(id=sid, resource='pwn', version='3.0', ili=ili,
                                pwn30=[key], **pwn[key])
            targets = [sid]
        bridges[row['CONCEPTICON_ID']] = (targets, key)
    lemma_index, definition_index, inverted = defaultdict(set), defaultdict(set), defaultdict(set)
    termsets = {}
    for sid, row in synsets.items():
        definition_index[normalized(row['definition'])].add(sid)
        for lemma in row['lemmas']:
            lemma_index[normalized(lemma.replace('_', ' '))].add(sid)
        termsets[sid] = tokens(row['definition'] + ' ' + ' '.join(row['lemmas']))
        for term in termsets[sid]:
            inverted[term].add(sid)
    idf = {term: math.log(1 + len(synsets) / len(ids)) for term, ids in inverted.items()}
    reviews_path = DATA / 'wordnet/review.csv'
    reviews = defaultdict(list)
    for row in read_csv(reviews_path) if reviews_path.exists() else []:
        reviews[row['concept_id']].append(row)
    concepts = read_csv(DATA / 'concepts.csv')
    holds_path = DATA / 'wordnet/holds.json'
    holds = json.loads(holds_path.read_text()) if holds_path.exists() else {}
    entries, retained, flat, candidates, coverage = {}, {}, [], [], []
    for concept in concepts:
        cid = concept['concept_id']
        chash = concept_hash(concept)
        entry = dict(concept_sha256=chash, status=concept['status'], links=[], candidates=[])
        entries[cid] = entry
        proposals = {}
        if concept['status'] == 'active':
            labels = {normalized(concept['label'].replace('_', ' '))}
            labels |= {normalized(x.strip()) for x in re.split(r' / | or |\(|\)', concept['label']) if x.strip()}
            direct = set().union(*(lemma_index.get(label, set()) for label in labels))
            exact_defs = definition_index.get(normalized(concept['definition']), set())
            cterms = tokens(concept['label'] + ' ' + concept['definition'])
            denominator = max(1, sum(idf.get(t, 0) for t in sorted(cterms)))
            pool = direct | exact_defs
            for term in cterms:
                pool |= inverted.get(term, set())
            for sid in pool:
                row = synsets[sid]
                common = cterms & termsets[sid]
                score = sum(idf[t] for t in sorted(common)) / denominator
                if sid in direct:
                    score += 1
                if sid in exact_defs:
                    score += 3
                proposals[sid] = (score, 'definition_identity' if sid in exact_defs else
                                  'label_lemma' if sid in direct else 'definition_overlap')
            targets, bridge_id = bridges.get(concept['concepticon_id'], ([], ''))
            for sid in targets:
                proposals[sid] = (max(proposals.get(sid, (0, ''))[0], 2), 'concepticon_pwn30_verified')
                row = dict(target_id=sid, relation='association', status='source_association',
                           evidence='Concepticon v2.6.0 association; PWN 3.0 full gloss verified; '
                                    'OEWN correspondence via CILI where available',
                           source_reference=bridge_id)
                entry['links'].append(row)
            # A unique definition identity is an accepted equivalence only with a
            # matching lexical label. All other automated matches remain review candidates.
            compatible = {'n': {'n'}, 'v': {'v'}, 'adj': {'a', 's'},
                          'x': {'n', 'v', 'a', 's', 'r'}}.get(concept['pos'], set())
            matches = {sid for sid in exact_defs & direct if synsets[sid]['pos'] in compatible}
            if len(matches) == 1:
                sid = next(iter(matches))
                entry['links'] = [r for r in entry['links'] if r['target_id'] != sid]
                entry['links'].append(dict(target_id=sid, relation='exact', status='accepted',
                                           evidence='Unique normalized full definition and lexical label identity',
                                           source_reference='definition_identity'))
            for review in reviews.get(cid, []):
                if review['concept_sha256'] != chash or review['target_sha256'] != digest(synsets[review['target_id']]):
                    raise ValueError(f'Stale review: {cid}')
                if review['relation'] not in {'exact', 'broader', 'narrower', 'related'}:
                    raise ValueError(f'Invalid reviewed relation: {cid}')
                entry['links'] = [r for r in entry['links'] if r['target_id'] != review['target_id']]
                entry['links'].append(dict(target_id=review['target_id'], relation=review['relation'],
                                           status='accepted', evidence=review['rationale'],
                                           source_reference='review.csv'))
            linked = {r['target_id'] for r in entry['links']}
            for sid, (score, reason) in sorted(proposals.items(), key=lambda x: (-x[1][0], x[0])):
                if sid not in linked and score >= .25 and len(entry['candidates']) < 3:
                    entry['candidates'].append(dict(target_id=sid, relation='association', status='candidate',
                                                   evidence=reason, source_reference='', score=round(score, 5)))
        for group, rows in [('links', flat), ('candidates', candidates)]:
            if cid in holds:
                if holds[cid]['concept_sha256'] != chash:
                    raise ValueError(f'Stale hold: {cid}')
                entry['hold_reason'] = holds[cid]['reason']
                entry['candidates'] = []
            for link in entry[group]:
                target = synsets[link['target_id']]
                retained[target['id']] = target
                link['target_sha256'] = digest(target)
                rows.append(dict(concept_id=cid, concept_sha256=chash, **link,
                                 resource=target['resource'], version=target['version'], ili=target['ili'],
                                 pwn30=';'.join(target['pwn30']), lemmas='; '.join(target['lemmas']),
                                 definition=target['definition']))
        accepted = sum(r['status'] == 'accepted' for r in entry['links'])
        associations = len(entry['links']) - accepted
        state = ('merged' if concept['status'] != 'active' else 'accepted' if accepted else
                 'source_association' if associations else 'review' if entry['candidates'] else 'unlinked')
        entry['coverage'] = state
        coverage.append(dict(concept_id=cid, concept_sha256=chash, status=concept['status'],
                             coverage=state, accepted_links=accepted, source_associations=associations,
                             candidates=len(entry['candidates']), replacement_id=concept['replacement_id']))
    unknown = set(reviews) - set(entries)
    if unknown:
        raise ValueError(f'Unknown reviewed concepts: {unknown}')
    summary = dict(catalog_concepts=len(concepts), coverage=dict(Counter(r['coverage'] for r in coverage)),
                   links=dict(Counter(r['status'] + ':' + r['relation'] for r in flat)),
                   candidates=len(candidates), concepticon_bridge_rows_verified=len(bridge_rows),
                   oewn_version='2025', princeton_version='3.0',
                   relation_direction='Arca to target: broader means target broader; narrower means target narrower',
                   scope='Frozen concept catalog only; no lexical record or native unmapped sense is remapped')
    inputs = {name: hashlib.sha256((DATA / 'wordnet' / name).read_bytes()).hexdigest()
              for name in ('sources.json', 'review.csv', 'holds.json')}
    bundle = dict(schema=1, inputs=inputs, summary=summary, concepts=entries, synsets=retained)
    (output / 'bundle.json').write_text(
        json.dumps(bundle, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n')
    (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    fields = ['concept_id', 'concept_sha256', 'target_id', 'relation', 'status', 'evidence',
              'source_reference', 'target_sha256', 'resource', 'version', 'ili', 'pwn30', 'lemmas', 'definition']
    write_csv(output / 'links.csv', flat, fields)
    write_csv(output / 'candidates.csv', candidates, fields + ['score'])
    write_csv(output / 'coverage.csv', coverage, list(coverage[0]))
    load_bundle(output, input_directory=DATA / 'wordnet')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw', type=Path, default=Path('raw/wordnet'))
    parser.add_argument('--output', type=Path, default=DATA / 'wordnet')
    parser.add_argument('--fetch', action='store_true')
    args = parser.parse_args()
    build(args.raw, args.output, args.fetch)
