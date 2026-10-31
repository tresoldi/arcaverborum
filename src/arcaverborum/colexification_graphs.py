"""Bounded induced neighborhoods from the existing sparse colexification database."""
from __future__ import annotations

import json
import os
import shutil
import sqlite3
from pathlib import Path

from arcaverborum.colexification import KINDS, LAYERS, Limits, digest, sha, write_json

MAX_NEIGHBORS = 30


def induced(db, cid, layer, kind, minimum=0, neighbors=MAX_NEIGHBORS):
    if not 1 <= neighbors <= MAX_NEIGHBORS:
        raise ValueError('Induced graphs support 1–30 neighbors')
    rows = db.execute('''SELECT b AS cid,families,languages,varieties FROM edges
      WHERE layer=? AND kind=? AND a=? AND families>=? UNION ALL
      SELECT a AS cid,families,languages,varieties FROM edges
      WHERE layer=? AND kind=? AND b=? AND families>=?
      ORDER BY families DESC,languages DESC,varieties DESC,cid LIMIT ?''',
                      (layer, kind, cid, minimum, layer, kind, cid, minimum, neighbors)).fetchall()
    nodes = [cid] + [r[0] for r in rows]
    index = {value: i for i, value in enumerate(nodes)}
    marks = ','.join('?' for _ in nodes)
    edges = []
    # The selected set has at most 31 concepts and 465 actual undirected edges.
    query = f'''SELECT a,b,families,languages,varieties FROM edges
      WHERE layer=? AND kind=? AND families>=? AND a IN ({marks}) AND b IN ({marks}) ORDER BY a,b'''
    for a, b, families, languages, varieties in db.execute(query, (layer, kind, minimum, *nodes, *nodes)):
        edges.append([index[a], index[b], families, languages, varieties])
    return dict(nodes=nodes, edges=edges, max_neighbors=neighbors, minimum_families=minimum,
                neighbor_links=sum(a != 0 and b != 0 for a, b, *_ in edges))


def build_graphs(built):
    built = Path(built)
    parent = json.loads((built / 'public/manifest.json').read_text())
    signature = dict(parent=parent['build_id'], parent_sha256=sha(built / 'public/manifest.json'),
                     code=sha(Path(__file__)), max_neighbors=MAX_NEIGHBORS)
    build_id = digest(signature)[:24]
    destination = built / 'subgraphs' / build_id
    if (destination / 'manifest.json').exists():
        verify(destination)
        return destination
    stage = destination.with_name('.' + build_id + '.building')
    stage.parent.mkdir(exist_ok=True)
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir()
    db = sqlite3.connect(f'file:{built / "index.sqlite"}?mode=ro', uri=True)
    db.execute('PRAGMA cache_size=-16384')
    db.execute('PRAGMA temp_store=FILE')
    db.execute('PRAGMA mmap_size=0')
    nodes, stats = {}, dict(graphs=0, nonstar_graphs=0, max_nodes=0, max_edges=0)
    try:
        for cid in sorted(parent['nodes']):
            views = {}
            for layer in LAYERS:
                for kind in KINDS:
                    for strong, minimum in [('all', 0), ('recurrent', parent['policy']['recurrence_families'])]:
                        graph = induced(db, cid, layer, kind, minimum)
                        views[f'{layer}:{kind}:{strong}'] = graph
                        stats['graphs'] += 1
                        stats['nonstar_graphs'] += graph['neighbor_links'] > 0
                        stats['max_nodes'] = max(stats['max_nodes'], len(graph['nodes']))
                        stats['max_edges'] = max(stats['max_edges'], len(graph['edges']))
            nodes[cid] = write_json(stage / (cid + '.json'), dict(concept_id=cid, views=views), Limits())
        manifest = dict(schema=1, build_id=build_id, parent_build_id=parent['build_id'],
                        inputs=signature, max_neighbors=MAX_NEIGHBORS, nodes=nodes, stats=stats)
        write_json(stage / 'manifest.json', manifest, Limits(payload_bytes=4 * 1024 * 1024))
        stage.rename(destination)
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    finally:
        db.close()
    return destination


def verify(directory):
    directory = Path(directory)
    manifest = json.loads((directory / 'manifest.json').read_text())
    for cid, spec in manifest['nodes'].items():
        if spec['url'] != cid + '.json' or spec['bytes'] > 1024 * 1024:
            raise ValueError('Invalid induced graph asset')
        path = directory / spec['url']
        if path.stat().st_size != spec['bytes'] or sha(path) != spec['sha256']:
            raise ValueError('Corrupt induced graph asset')
    return manifest


def publish_graphs(root, directory):
    root, directory = Path(root), Path(directory)
    graph = verify(directory)
    path = root / 'web/data/manifest.json'
    web = json.loads(path.read_text())
    if web['colexification']['build_id'] != graph['parent_build_id']:
        raise ValueError('Induced graph and colexification snapshots differ')
    parent = root / 'web' / web['colexification']['url']
    if sha(parent) != graph['inputs']['parent_sha256'] or sha(Path(__file__)) != graph['inputs']['code']:
        raise ValueError('Stale induced graph inputs')
    destination = root / 'web/data/colexification-graphs' / graph['build_id']
    destination.parent.mkdir(exist_ok=True)
    if not destination.exists():
        stage = destination.with_name('.' + destination.name + '.publishing')
        if stage.exists():
            shutil.rmtree(stage)
        shutil.copytree(directory, stage)
        stage.rename(destination)
    else:
        verify(destination)
    target = directory / 'manifest.json'
    web['colexification']['subgraphs'] = dict(url=f'data/colexification-graphs/{graph["build_id"]}/manifest.json',
                                            sha256=sha(target), bytes=target.stat().st_size)
    temporary = path.with_suffix('.pending')
    temporary.write_text(json.dumps(web, ensure_ascii=False, indent=2) + '\n')
    os.replace(temporary, path)
