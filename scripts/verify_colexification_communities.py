"""Check every community preview against sealed evidence and complete membership."""
import argparse
import csv
import gzip
import json
import resource
import sqlite3
import tempfile
from collections import Counter
from pathlib import Path

from arcaverborum.colexification import verify_database
from arcaverborum.colexification_communities import partition_isolated
from arcaverborum.colexification_communities import verify as verify_assets


def verify(built, directory, recompute=False):
    verify_database(built)
    manifest = verify_assets(directory)
    db = sqlite3.connect(f'file:{built / "index.sqlite"}?mode=ro', uri=True)
    db.execute('PRAGMA cache_size=-16384')
    db.execute('PRAGMA mmap_size=0')
    evidence = {(a, b): (f, languages, v) for a, b, f, languages, v in db.execute(
        "SELECT a,b,families,languages,varieties FROM edges WHERE layer='segmented' AND kind='observed'")}
    nodes = set(manifest['nodes'])
    selected, partition_rows = {}, 0
    per_run = Counter()
    with gzip.open(directory / 'partitions.csv.gz', 'rt', newline='') as handle:
        for row in csv.DictReader(handle):
            assert row['concept_id'] in nodes and row['community_anchor'] in nodes
            per_run[row['run']] += 1
            partition_rows += 1
            if row['run'] == 'seed-' + str(manifest['selected_seed']):
                selected[row['concept_id']] = row['community_anchor']
    assert per_run == Counter({r['name']: r['nodes'] for r in manifest['runs']})
    sizes = Counter(selected.values())
    examined, maximum_nodes, maximum_edges = 0, 0, 0
    for cid, spec in manifest['nodes'].items():
        node = json.loads((directory / spec['url']).read_text())
        assert node['concept_id'] == cid
        assert node['community'] == selected.get(cid)
        assert node['community_size'] == sizes.get(node['community'], 0)
        assert len(node['preview']) <= 31 and len(node['preview_edges']) <= 465
        assert len(set(node['preview'])) == len(node['preview'])
        for member in node['preview']:
            assert selected.get(member) == selected.get(cid)
        if node['preview']:
            assert node['preview'][0] == cid
        for a, b, *counts in node['preview_edges']:
            assert a in node['preview'] and b in node['preview']
            assert tuple(counts) == evidence[a, b]
            examined += 1
        maximum_nodes = max(maximum_nodes, len(node['preview']))
        maximum_edges = max(maximum_edges, len(node['preview_edges']))
    diagnostic_rows = 0
    with (directory / 'edge-diagnostics.csv').open(newline='') as handle:
        for row in csv.DictReader(handle):
            a, b = row['concept_a'], row['concept_b']
            assert int(row['families']) == evidence[a, b][0]
            assert 0 <= int(row['families_without_one_namespace_min']) <= int(row['families'])
            assert 0 <= int(row['block_coassigned']) <= int(row['block_eligible']) <= 50
            assert 2 <= int(row['maximum_identity_concepts']) <= 64
            diagnostic_rows += 1
    assert diagnostic_rows == len(evidence)
    if recompute:
        cids = sorted(nodes)
        index = {cid: n for n, cid in enumerate(cids)}
        edges = [(index[a], index[b], f) for (a, b), (f, _, _) in sorted(evidence.items()) if f > 0]
        with tempfile.TemporaryDirectory(dir=built) as scratch:
            partition, objective = partition_isolated(edges, scratch, seed=manifest['selected_seed'])
        assert {cids[n]: cids[module] for n, module in partition.items()} == selected
        reference = next(r for r in manifest['runs'] if r['name'] == 'seed-' + str(manifest['selected_seed']))
        assert objective == reference['objective']
    db.close()
    return dict(build_id=manifest['build_id'], parent_build_id=manifest['parent_build_id'],
                node_files=len(nodes), assigned=len(selected), communities=len(sizes), runs=len(per_run),
                membership_rows=partition_rows, verified_preview_edges=examined, diagnostic_rows=diagnostic_rows,
                maximum_preview_nodes=maximum_nodes, maximum_preview_edges=maximum_edges,
                selected_partition_reproduced=recompute, summary=manifest['summary'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--recompute-selected', action='store_true')
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024,) * 2)
    result = verify(args.build, args.directory, args.recompute_selected)
    result['parent_peak_rss_mib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    result['worker_peak_rss_mib'] = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1024
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
