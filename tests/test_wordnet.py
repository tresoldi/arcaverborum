"""WordNet semantic guards and pinned-resource decoding use no local intake."""
import copy
import csv
import gzip
import io
import json
import tarfile
from pathlib import Path

import pytest

from arcaverborum.wordnet import (
    DATA,
    concept_hash,
    digest,
    load_bundle,
    parse_oewn,
    parse_princeton,
    read_csv,
    resolve_bridge,
)


def test_satellite_alias_requires_actual_gloss():
    pwn = {'00000001-s': dict(definition='a particular color; "example"')}
    row = dict(OPEN_WORDNET_ID='00000001-a', WORDNET_DEFINITION='a particular color; "example"')
    assert resolve_bridge(row, pwn) == '00000001-s'
    row['WORDNET_DEFINITION'] = 'a different sense'
    with pytest.raises(ValueError, match='Unverified'):
        resolve_bridge(row, pwn)


def test_oewn_parser_preserves_ili_pos_and_many_lemmas(tmp_path):
    path = tmp_path / 'oewn.gz'
    with gzip.open(path, 'wt') as handle:
        handle.write('''<LexicalResource><Lexicon version="2025">
          <LexicalEntry><Lemma writtenForm="red"/><Sense synset="oewn-1-s"/></LexicalEntry>
          <LexicalEntry><Lemma writtenForm="reddish"/><Sense synset="oewn-1-s"/></LexicalEntry>
          <Synset id="oewn-1-s" ili="i1" partOfSpeech="s"><Definition>red color</Definition></Synset>
        </Lexicon></LexicalResource>''')
    target = parse_oewn(path)['oewn-1-s']
    assert target['ili'] == 'i1' and target['pos'] == 's'
    assert target['lemmas'] == ['red', 'reddish']
    with gzip.open(path, 'wt') as handle:
        handle.write('<LexicalResource><Lexicon version="2026"/></LexicalResource>')
    with pytest.raises(ValueError, match='2025'):
        parse_oewn(path)


def test_princeton_keeps_native_satellite_and_full_gloss(tmp_path):
    path = tmp_path / 'pwn.tar.gz'
    text = b'  copyright\n00000001 00 s 01 deep_red 0 000 | a color; "an example"\n'
    with tarfile.open(path, 'w:gz') as archive:
        member = tarfile.TarInfo('dict/data.adj')
        member.size = len(text)
        archive.addfile(member, io.BytesIO(text))
    assert parse_princeton(path) == {'00000001-s': dict(
        definition='a color; "an example"', pos='s', lemmas=['deep red'])}


def fixture_bundle(tmp_path):
    concept = dict(concept_id='x-test', concepticon_id='1', label='test', pos='n', definition='A test.',
                   status='active', replacement_id='')
    concepts = tmp_path / 'concepts.csv'
    with concepts.open('w') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(concept))
        writer.writeheader()
        writer.writerow(concept)
    target = dict(id='oewn-1-n', definition='A test.', resource='oewn', version='2025')
    link = dict(target_id=target['id'], target_sha256=digest(target), status='candidate', relation='association')
    bundle = dict(concepts={'x-test': dict(concept_sha256=concept_hash(concept), links=[], candidates=[link])},
                  synsets={target['id']: target})
    return concepts, bundle


def test_bundle_rejects_concept_drift_and_target_drift(tmp_path):
    concepts, bundle = fixture_bundle(tmp_path)
    path = tmp_path / 'bundle.json'
    path.write_text(json.dumps(bundle))
    assert load_bundle(tmp_path, concepts)
    bundle['synsets']['oewn-1-n']['definition'] = 'A different sense'
    path.write_text(json.dumps(bundle))
    with pytest.raises(ValueError, match='target drift'):
        load_bundle(tmp_path, concepts)
    _, bundle = fixture_bundle(tmp_path)
    bundle['concepts']['x-test']['concept_sha256'] = 'stale'
    path.write_text(json.dumps(bundle))
    with pytest.raises(ValueError, match='semantic drift'):
        load_bundle(tmp_path, concepts)


def test_candidates_cannot_become_accepted_or_duplicate(tmp_path):
    concepts, bundle = fixture_bundle(tmp_path)
    path = tmp_path / 'bundle.json'
    entry = bundle['concepts']['x-test']
    entry['candidates'][0].update(status='accepted', relation='exact')
    path.write_text(json.dumps(bundle))
    with pytest.raises(ValueError, match='cannot be accepted'):
        load_bundle(tmp_path, concepts)
    entry['candidates'][0].update(status='candidate', relation='association')
    entry['candidates'].append(copy.deepcopy(entry['candidates'][0]))
    path.write_text(json.dumps(bundle))
    with pytest.raises(ValueError, match='Duplicate'):
        load_bundle(tmp_path, concepts)


def test_decision_edits_require_rebuilding_sidecars(tmp_path):
    concepts, bundle = fixture_bundle(tmp_path)
    import hashlib

    review = tmp_path / 'review.csv'
    review.write_text('initial decision\n')
    bundle['inputs'] = {'review.csv': hashlib.sha256(review.read_bytes()).hexdigest()}
    (tmp_path / 'bundle.json').write_text(json.dumps(bundle))
    assert load_bundle(tmp_path, concepts)
    review.write_text('changed decision\n')
    with pytest.raises(ValueError, match='input drift'):
        load_bundle(tmp_path, concepts)


def test_published_catalog_sense_distinctions_and_full_accounting():
    bundle = load_bundle()
    assert set(bundle['inputs']) == {'sources.json', 'review.csv', 'holds.json'}
    concepts = read_csv(DATA / 'concepts.csv')
    assert len(bundle['concepts']) == len(concepts)
    for row in concepts:
        entry = bundle['concepts'][row['concept_id']]
        if row['status'] != 'active':
            assert not entry['links'] and not entry['candidates']
    water = bundle['concepts']['phy-water']['links']
    assert any(r['target_id'] == 'oewn-14869913-n' and r['relation'] == 'exact' for r in water)
    assert any(r['target_id'] == 'oewn-09381123-n' and r['relation'] == 'exact'
               for r in bundle['concepts']['phy-moon']['links'])
    child = [r for r in bundle['concepts']['kin-child']['links'] if r['status'] == 'accepted']
    assert len(child) == 2 and {r['relation'] for r in child} == {'narrower'}
    assert not bundle['concepts']['cog-who']['candidates']
    assert 'pronoun' in bundle['concepts']['cog-who']['hold_reason']
    for cid in ('act-bend', 'qua-alone'):
        assert not any(r['status'] == 'accepted' for r in bundle['concepts'][cid]['links'])
    for row in read_csv(DATA / 'wordnet/review.csv'):
        assert digest(bundle['synsets'][row['target_id']]) == row['target_sha256']
        links = bundle['concepts'][row['concept_id']]['links']
        assert any(link['target_id'] == row['target_id'] and link['status'] == 'accepted'
                   and link['relation'] == row['relation'] and link['evidence'] == row['rationale'] for link in links)
    core = {r['concept_id'] for r in read_csv(DATA / 'concept_core.csv')}
    reviewed = {r['concept_id'] for r in read_csv(DATA / 'wordnet/review.csv')}
    held = set(json.loads((DATA / 'wordnet/holds.json').read_text()))
    assert core <= reviewed | held


def test_export_totals_match_bundle():
    bundle = load_bundle()
    directory = Path(DATA) / 'wordnet'
    assert len(read_csv(directory / 'links.csv')) == sum(len(e['links']) for e in bundle['concepts'].values())
    assert len(read_csv(directory / 'candidates.csv')) == sum(len(e['candidates']) for e in bundle['concepts'].values())
    assert len(read_csv(directory / 'coverage.csv')) == len(bundle['concepts'])
    for filename, group in [('links.csv', 'links'), ('candidates.csv', 'candidates')]:
        for row in read_csv(directory / filename):
            entry = bundle['concepts'][row['concept_id']]
            target = bundle['synsets'][row['target_id']]
            assert row['concept_sha256'] == entry['concept_sha256']
            assert row['target_sha256'] == digest(target)
            assert row['definition'] == target['definition']
            assert row['version'] == target['version'] and row['resource'] == target['resource']
            assert any(link['target_id'] == row['target_id'] and link['status'] == row['status']
                       and link['relation'] == row['relation'] for link in entry[group])
