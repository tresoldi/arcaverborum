"""Community models preserve missing eligibility and explicit evidence support."""
import json

import pytest

from arcaverborum.colexification_communities import agreement, canonical, partition


def test_partition_labels_and_common_eligibility():
    assert canonical({4: 9, 2: 9, 7: 1}) == {2: 2, 4: 2, 7: 7}
    assert agreement({1: 1, 2: 1}, {1: 5, 2: 5, 9: 9}) == dict(common_nodes=2, adjusted_rand=1)
    assert agreement({1: 1}, {2: 2})['adjusted_rand'] is None


def test_weighted_global_partition_is_seeded_and_does_not_assign_zero_support():
    pytest.importorskip('infomap')
    edges = [(0, 1, 10), (1, 2, 10), (0, 2, 10), (3, 4, 10), (4, 5, 10), (3, 5, 10), (6, 7, 0)]
    a, _ = partition(edges)
    assert a == partition(edges)[0]
    assert a[0] == a[1] == a[2]
    assert a[3] == a[4] == a[5] != a[0]
    assert 6 not in a and 7 not in a


def test_complete_pilot_and_source_diagnostics(tmp_path, monkeypatch):
    pytest.importorskip('infomap')
    pytest.importorskip('igraph')
    import csv

    from test_colexification import csv_file, fixture, form

    from arcaverborum import colexification_communities as communities
    from arcaverborum.colexification import build, connect
    rows = [form(0), form(1), form(0, av='b',source='second'), form(1, av='b',source='second')]
    fixture(tmp_path, rows)
    path = tmp_path / 'raw/glottolog/languages.csv'
    languages = list(csv.DictReader(path.open()))
    next(row for row in languages if row['ID']=='b')['Family_ID']='second-family'
    csv_file(path,languages)
    built = build(tmp_path)
    db = connect(built / 'index.sqlite')
    diagnostic = communities.support_diagnostics(db, 'x-0', 'x-1', 2)
    assert diagnostic['namespaces'] == 2
    family = db.execute("SELECT family FROM varieties WHERE av='a'").fetchone()[0]
    assert communities.family_block_edges(db, {'x-0': 0, 'x-1': 1}, {family: 7}) == [(0, 1, 7)]
    assert communities.family_block_edges(db, {'x-0': 0, 'x-1': 1}, {}) == []
    assert diagnostic['families_without_one_namespace_min'] == 1  # same family survives either source
    db.close()
    original_diagnostics = communities.support_diagnostics
    monkeypatch.setattr(communities, 'support_diagnostics',
                        lambda *a, **kw: original_diagnostics(*a, **kw) | {'catalog_relation': 'contains'})
    monkeypatch.setattr(communities, 'REPLICATES', 2)
    output = communities.build(built)
    manifest = communities.verify(output)
    with (output / 'edge-diagnostics.csv').open() as handle:
        assert next(csv.DictReader(handle))['catalog_relation'] == 'contains'
    assert manifest['summary']['assigned_nodes'] == 2
    node = json.loads((output / 'x-2.json').read_text())
    assert node['community'] is None
    assert len(node['preview']) == 0
    assert communities.build(built) == output
    second = communities.build(built, output=tmp_path / 'independent-output')
    assert (second / 'manifest.json').read_bytes() == (output / 'manifest.json').read_bytes()
    assert (second / 'partitions.csv.gz').read_bytes() == (output / 'partitions.csv.gz').read_bytes()


def test_family_blocks_count_repeated_draws_and_collapse_duplicate_sources():
    import sqlite3

    from arcaverborum.colexification_communities import family_block_edges
    db = sqlite3.connect(':memory:')
    db.executescript('''
      CREATE TABLE witnesses(a TEXT,b TEXT,sid INT,layer TEXT,kind TEXT);
      CREATE TABLE scopes(id INT,av TEXT);
      CREATE TABLE varieties(av TEXT,family TEXT);
      INSERT INTO varieties VALUES('v','family');
      INSERT INTO scopes VALUES(1,'v'),(2,'v');
      INSERT INTO witnesses VALUES('a','b',1,'segmented','observed'),('a','b',2,'segmented','observed');
    ''')
    assert family_block_edges(db, {'a': 0, 'b': 1}, {'family': 4}) == [(0, 1, 4)]
    assert family_block_edges(db, {'a': 0, 'b': 1}, {}) == []
    db.close()
