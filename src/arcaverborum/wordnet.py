"""Versioned concept links. Candidates and inherited associations are not equivalences.

The relation direction is from the Arca concept to the target: ``broader``
means that the WordNet target is broader than the Arca meaning slot.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
import re
import tarfile
import unicodedata
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

DATA = Path(__file__).parent / 'data'
RELATIONS = {'exact', 'broader', 'narrower', 'related', 'association'}
STATUSES = {'accepted', 'source_association', 'candidate'}


def normalized(value):
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFKC', value).casefold()).strip().rstrip('.')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def concept_hash(concept):
    return digest({key: concept[key] for key in (
        'concept_id', 'concepticon_id', 'label', 'pos', 'definition', 'status', 'replacement_id')})


def read_csv(path, delimiter=','):
    with Path(path).open(encoding='utf-8', newline='') as handle:
        return list(csv.DictReader(handle, delimiter=delimiter))


def parse_oewn(path):
    """Read the pinned standard LMF release, retaining senses and ILI identities."""
    synsets, lemmas = {}, defaultdict(set)
    with gzip.open(path) as handle:
        for _, element in ET.iterparse(handle, events=['end']):
            if element.tag == 'Lexicon' and element.get('version') != '2025':
                raise ValueError('Expected OEWN 2025')
            if element.tag == 'LexicalEntry':
                lemma = element.find('Lemma').get('writtenForm')
                for sense in element.findall('Sense'):
                    lemmas[sense.get('synset')].add(lemma)
                element.clear()
            elif element.tag == 'Synset':
                sid = element.get('id')
                if sid in synsets:
                    raise ValueError(f'Duplicate synset: {sid}')
                synsets[sid] = dict(id=sid, resource='oewn', version='2025',
                                   ili=element.get('ili', ''), pos=element.get('partOfSpeech'),
                                   definition=element.findtext('Definition') or '')
                element.clear()
    for sid, row in synsets.items():
        row['lemmas'] = sorted(lemmas[sid])
    return synsets


def parse_princeton(path):
    """Offsets are version-specific; adjective satellites keep their native POS."""
    result = {}
    with tarfile.open(path) as archive:
        for member in archive.getmembers():
            if Path(member.name).name not in {'data.noun', 'data.verb', 'data.adj', 'data.adv'}:
                continue
            for line in archive.extractfile(member).read().decode().splitlines():
                if not line or line[0].isspace():
                    continue
                header, gloss = line.split('|', 1)
                parts = header.split()
                sid = parts[0] + '-' + parts[2]
                result[sid] = dict(definition=gloss.strip(), pos=parts[2], lemmas=[
                    parts[4 + 2 * i].replace('_', ' ') for i in range(int(parts[3], 16))])
    return result


def resolve_bridge(row, pwn):
    """Resolve Concepticon's inconsistent version label against the actual gloss.

    A satellite alias is permitted only when the complete PWN 3.0 gloss agrees.
    No offset identity is asserted between different WordNet versions.
    """
    sid = row['OPEN_WORDNET_ID']
    options = [sid] + ([sid[:-1] + 's'] if sid.endswith('-a') else [])
    for key in options:
        if key in pwn and normalized(pwn[key]['definition']) == normalized(row['WORDNET_DEFINITION']):
            return key
    raise ValueError(f'Unverified Concepticon/PWN 3.0 bridge: {sid}')


def load_bundle(directory=DATA / 'wordnet', concepts_path=DATA / 'concepts.csv', *, input_directory=None):
    """Validate frozen semantic guards before a consumer can publish the sidecar."""
    directory = Path(directory)
    if not (directory / 'bundle.json').exists():
        return None
    bundle = json.loads((directory / 'bundle.json').read_text())
    input_directory = Path(input_directory or directory)
    for name, expected in bundle.get('inputs', {}).items():
        if hashlib.sha256((input_directory / name).read_bytes()).hexdigest() != expected:
            raise ValueError(f'WordNet input drift; rebuild the sidecars: {name}')
    concepts = {c['concept_id']: c for c in read_csv(concepts_path)}
    if set(bundle['concepts']) != set(concepts):
        raise ValueError('WordNet concept catalog drift')
    for cid, entry in bundle['concepts'].items():
        if entry['concept_sha256'] != concept_hash(concepts[cid]):
            raise ValueError(f'WordNet semantic drift: {cid}')
        seen = set()
        for link in entry['links'] + entry['candidates']:
            if link['status'] not in STATUSES or link['relation'] not in RELATIONS:
                raise ValueError(f'Unknown WordNet relation/status: {cid}')
            if link['status'] == 'accepted' and link['relation'] == 'association':
                raise ValueError('An association cannot be an accepted sense mapping')
            if link['status'] != 'accepted' and link['relation'] != 'association':
                raise ValueError('Unreviewed associations cannot assert a semantic relation')
            if link in entry['candidates'] and link['status'] != 'candidate':
                raise ValueError('Review candidates cannot be accepted')
            if link in entry['links'] and link['status'] == 'candidate':
                raise ValueError('Candidate in the accepted/association channel')
            target = bundle['synsets'][link['target_id']]
            if digest(target) != link['target_sha256']:
                raise ValueError(f'WordNet target drift: {cid}')
            key = (link['target_id'], link['status'])
            if key in seen:
                raise ValueError(f'Duplicate WordNet link: {cid}')
            seen.add(key)
        if concepts[cid]['status'] != 'active' and (entry['links'] or entry['candidates']):
            raise ValueError(f'Merged concept cannot gain automatic links: {cid}')
    return bundle
