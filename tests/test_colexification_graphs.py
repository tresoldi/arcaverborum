"""Induced graphs include only real edges, including links among focal neighbors."""
import itertools
import sqlite3

import pytest

from arcaverborum.colexification_graphs import induced


def database(rows):
    db = sqlite3.connect(':memory:')
    db.execute('CREATE TABLE edges(layer TEXT,kind TEXT,a TEXT,b TEXT,families INT,languages INT,varieties INT)')
    db.executemany('INSERT INTO edges VALUES(?,?,?,?,?,?,?)', rows)
    return db


def test_triangle_is_not_rendered_as_a_star():
    db = database([('segmented', 'observed', a, b, 5, 6, 7)
                   for a, b in [('a', 'b'), ('a', 'c'), ('b', 'c')]])
    graph = induced(db, 'a', 'segmented', 'observed')
    assert graph['nodes'] == ['a', 'b', 'c']
    assert graph['edges'] == [[0, 1, 5, 6, 7], [0, 2, 5, 6, 7], [1, 2, 5, 6, 7]]
    assert graph['neighbor_links'] == 1
    db.close()


def test_missing_links_are_not_invented_and_modes_do_not_mix():
    db = database([('segmented', 'observed', 'a', 'b', 4, 5, 6),
                   ('segmented', 'observed', 'a', 'c', 4, 5, 6),
                   ('written', 'observed', 'b', 'c', 9, 9, 9),
                   ('segmented', 'inferred', 'b', 'c', 9, 9, 9)])
    graph = induced(db, 'a', 'segmented', 'observed')
    assert len(graph['edges']) == 2 and graph['neighbor_links'] == 0
    db.close()


def test_threshold_applies_to_neighbor_links_as_well_as_focal_edges():
    db = database([('segmented', 'observed', a, b, n, n, n)
                   for a, b, n in [('a', 'b', 5), ('a', 'c', 4), ('b', 'c', 2)]])
    assert induced(db, 'a', 'segmented', 'observed')['neighbor_links'] == 1
    assert induced(db, 'a', 'segmented', 'observed', minimum=3)['neighbor_links'] == 0
    db.close()


def test_dense_neighborhood_is_bounded_and_selection_is_deterministic():
    ids = [f'n{i:02}' for i in range(50)]
    db = database([('segmented', 'observed', a, b, 4, 4, 4) for a, b in itertools.combinations(ids, 2)])
    first = induced(db, 'n00', 'segmented', 'observed')
    assert first == induced(db, 'n00', 'segmented', 'observed')
    assert len(first['nodes']) == 31 and len(first['edges']) == 465
    with pytest.raises(ValueError, match='1–30'):
        induced(db, 'n00', 'segmented', 'observed', neighbors=31)
    db.close()
