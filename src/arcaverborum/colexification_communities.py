"""Offline exploratory communities and source diagnostics from sealed sparse evidence.

All-support observed segmented identities are the evidence. Partitions and block
resamples are named models; neither creates an observed lexical connection.
"""
from __future__ import annotations

import csv
import gzip
import importlib.metadata
import itertools
import json
import os
import random
import shutil
import sqlite3
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

from arcaverborum.colexification import Limits, digest, runtime, sha, verify_database, verify_public, write_json
from arcaverborum.colexification_graphs import induced

VERSIONS = {'infomap': '2.16.0', 'igraph': '1.0.0'}
SEEDS = tuple(range(1, 11))
REPLICATES = 50


def validate_runtime():
    for package, version in VERSIONS.items():
        if importlib.metadata.version(package) != version:
            raise ValueError(f'Community runtime requires {package}=={version}')


def canonical(partition):
    """Cluster labels are the smallest stable integer node in each module."""
    minima = {}
    for node, module in sorted(partition.items()):
        minima[module] = min(node, minima.get(module, node))
    return {node: minima[module] for node, module in sorted(partition.items())}


def partition(edges, method='infomap', seed=1, resolution=1):
    """Only positive-weight incident nodes participate; missing is never a cluster."""
    eligible = sorted({n for a, b, w in edges if w > 0 for n in (a, b)})
    if not eligible:
        return {}, None
    if method == 'infomap':
        import infomap
        model = infomap.Infomap(f'--two-level --silent --num-threads 1 --seed {seed} --num-trials 5')
        for a, b, w in edges:
            if w > 0:
                model.add_link(a, b, float(w))
        result = model.run()
        return canonical(dict(result.modules())), float(result.codelength)
    import igraph
    igraph.set_random_number_generator(random.Random(seed))
    index = {n: i for i, n in enumerate(eligible)}
    usable = [(a, b, w) for a, b, w in edges if w > 0]
    graph = igraph.Graph(n=len(eligible), edges=[(index[a], index[b]) for a, b, _ in usable])
    clusters = graph.community_leiden(objective_function='modularity', weights=[w for _, _, w in usable],
                                      resolution=resolution, n_iterations=-1)
    return canonical(dict(zip(eligible, clusters.membership))), float(clusters.quality)


def partition_isolated(edges, stage, method='infomap', seed=1, resolution=1):
    """Release native engine allocations after every sequential partition."""
    path = Path(stage) / '.worker-input.json'
    with path.open('w') as handle:
        json.dump(dict(edges=edges, method=method, seed=seed, resolution=resolution), handle)
    if path.stat().st_size > 16 * 1024 * 1024:
        raise ValueError('Partition worker input exceeds its byte budget')
    try:
        result = subprocess.run([sys.executable, '-m', __name__, '--worker', str(path)],
                                check=True, capture_output=True, text=True,
                                env=os.environ | {'OMP_NUM_THREADS': '1', 'OPENBLAS_NUM_THREADS': '1'})
        output = json.loads(result.stdout)
        return {int(n): module for n, module in output['partition'].items()}, output['objective']
    finally:
        path.unlink(missing_ok=True)


def agreement(left, right):
    """Adjusted Rand on common eligible nodes; no absent-node padding."""
    nodes = sorted(left.keys() & right.keys())
    if len(nodes) < 2:
        return dict(common_nodes=len(nodes), adjusted_rand=None)
    cells, a, b = Counter(), Counter(), Counter()
    for n in nodes:
        cells[left[n], right[n]] += 1
        a[left[n]] += 1
        b[right[n]] += 1
    def choose(n):
        return n * (n - 1) / 2
    observed = sum(map(choose, cells.values()))
    sa, sb = sum(map(choose, a.values())), sum(map(choose, b.values()))
    expected = sa * sb / choose(len(nodes))
    maximum = (sa + sb) / 2
    return dict(common_nodes=len(nodes), adjusted_rand=(observed - expected) / (maximum - expected)
                if maximum != expected else 1.0)


def support_diagnostics(db, a, b, families):
    family_sources, source_families, bases = defaultdict(set), defaultdict(set), Counter()
    for source, family, basis, size in db.execute('''SELECT s.source,v.family,s.basis,MAX(g.concepts)
      FROM witnesses w JOIN scopes s ON s.id=w.sid JOIN varieties v ON v.av=s.av
      JOIN groups g ON g.sid=w.sid AND g.layer=w.layer AND g.key=w.key
      WHERE w.layer='segmented' AND w.kind='observed' AND w.a=? AND w.b=?
      GROUP BY s.source,v.family,s.basis''', (a, b)):
        bases[basis] += 1
        if family:
            family_sources[family].add(source)
            source_families[source].add(family)
    exclusive = Counter(next(iter(s)) for s in family_sources.values() if len(s) == 1)
    sources = [r[0] for r in db.execute('''SELECT DISTINCT s.source FROM witnesses w
      JOIN scopes s ON s.id=w.sid WHERE w.layer='segmented' AND w.kind='observed' AND w.a=? AND w.b=?
      ORDER BY s.source''', (a, b))]
    maximum = db.execute('''SELECT MAX(g.concepts) FROM witnesses w JOIN groups g
      ON g.sid=w.sid AND g.layer=w.layer AND g.key=w.key
      WHERE w.layer='segmented' AND w.kind='observed' AND w.a=? AND w.b=?''', (a, b)).fetchone()[0]
    return dict(namespaces=len(sources), source_namespaces=sources,
                max_namespace_family_share=max(map(len, source_families.values()), default=0) / families
                if families else None,
                families_without_one_namespace_min=families - max(exclusive.values(), default=0),
                namespace_exclusive_families=dict(sorted(exclusive.items())),
                maximum_identity_concepts=maximum, comparison_bases=sorted(bases))


def family_block_edges(db, index, multiplicity):
    """One original known-family block per pair, with sampled multiplicity."""
    weights = Counter()
    for a, b, family in db.execute('''SELECT DISTINCT w.a,w.b,v.family FROM witnesses w
      JOIN scopes s ON s.id=w.sid JOIN varieties v ON v.av=s.av
      WHERE w.layer='segmented' AND w.kind='observed' AND v.family<>'' ORDER BY w.a,w.b,v.family'''):
        if multiplicity.get(family, 0):
            weights[index[a], index[b]] += multiplicity[family]
    return [(a, b, w) for (a, b), w in sorted(weights.items())]


def build(built, output=None):
    built = Path(built)
    seal = verify_database(built)
    parent = verify_public(built / 'public')
    validate_runtime()
    signature = dict(parent=parent['build_id'], parent_sha256=sha(built / 'public/manifest.json'),
                     database_sha256=seal['database_sha256'], code=sha(Path(__file__)),
                     versions=VERSIONS, runtime=runtime(), seeds=SEEDS, trials=5, family_replicates=REPLICATES,
                     flow='undirected two-level', worker='sequential isolated processes',
                     weights='distinct known family lineages', threads=1)
    build_id = digest(signature)[:24]
    destination = Path(output or built / 'communities') / build_id
    if destination.exists():
        verify(destination)
        return destination
    stage = destination.with_name('.' + build_id + '.building')
    stage.mkdir(parents=True, exist_ok=True)
    os.environ['SQLITE_TMPDIR'] = str(stage.resolve())
    db = sqlite3.connect(f'file:{built / "index.sqlite"}?mode=ro', uri=True)
    db.execute('PRAGMA cache_size=-16384')
    db.execute('PRAGMA mmap_size=0')
    db.execute('PRAGMA temp_store=FILE')
    try:
        cids = sorted(parent['nodes'])
        index = {cid: i for i, cid in enumerate(cids)}
        rows = db.execute("SELECT a,b,families FROM edges WHERE layer='segmented' AND kind='observed' ORDER BY a,b")
        edges = [(index[a], index[b], f) for a, b, f in rows]
        if len(cids) > 10000 or len(edges) > 250000:
            raise ValueError('Community pilot exceeds declared sparse graph budget')
        baseline = [(a, b, f) for a, b, f in edges if f > 0]
        runs, seed_partitions = [], []
        with gzip.open(stage / 'partitions.csv.gz', 'wt', newline='') as handle:
            writer = csv.writer(handle)
            writer.writerow(['run', 'concept_id', 'community_anchor'])

            def run(name, selected, method='infomap', seed=1, resolution=1):
                p, objective = partition_isolated(selected, stage, method, seed, resolution)
                for n, community in sorted(p.items()):
                    writer.writerow([name, cids[n], cids[community]])
                runs.append(dict(name=name, method=method, seed=seed, resolution=resolution,
                                 nodes=len(p), edges=sum(w > 0 for _, _, w in selected),
                                 communities=len(set(p.values())), objective=objective))
                print(f'Community pilot: {name}, {len(p)} nodes', flush=True)
                return p

            for seed in SEEDS:
                seed_partitions.append(run(f'seed-{seed}', baseline, seed=seed))
            best = min(range(len(SEEDS)), key=lambda i: (runs[i]['objective'], SEEDS[i]))
            reference = seed_partitions[best]
            for i, p in enumerate(seed_partitions):
                runs[i]['agreement_with_selected'] = agreement(reference, p)
            for resolution in (.5, 1, 2):
                p = run(f'leiden-{resolution}', baseline, 'leiden', resolution=resolution)
                runs[-1]['agreement_with_selected'] = agreement(reference, p)
            p = run('three-families', [(a, b, f) for a, b, f in baseline if f >= 3])
            runs[-1]['agreement_with_selected'] = agreement(reference, p)

            # SQL distinct families recomputes support after removing entire source scopes.
            def masked(where, params=()):
                query = ('''SELECT w.a,w.b,COUNT(DISTINCT NULLIF(v.family,''))
                  FROM witnesses w JOIN scopes s ON s.id=w.sid JOIN varieties v ON v.av=s.av
                  WHERE w.layer='segmented' AND w.kind='observed' AND (''' + where + ') '
                         'GROUP BY w.a,w.b ORDER BY w.a,w.b')
                return [(index[a], index[b], f) for a, b, f in db.execute(query, params) if f > 0]

            top_sources = list(db.execute('''SELECT s.source,COUNT(*) FROM witnesses w JOIN scopes s ON s.id=w.sid
              WHERE w.layer='segmented' AND w.kind='observed' GROUP BY s.source
              ORDER BY COUNT(*) DESC,s.source LIMIT 3'''))
            sources_to_probe = sorted({s for s, _ in top_sources}
                                      | {'huntergatherer', 'johanssonsoundsymbolic'})
            for source in sources_to_probe:
                p = run('without-source-' + source, masked('s.source<>?', (source,)))
                runs[-1]['agreement_with_selected'] = agreement(reference, p)
            areas = sorted({area.strip() for row in db.execute("SELECT DISTINCT area FROM varieties")
                            for area in row[0].split(';') if area.strip()})
            for area in areas:
                p = run('without-area-' + area, masked("instr(';'||v.area||';',';'||?||';')=0", (area,)))
                runs[-1]['agreement_with_selected'] = agreement(reference, p)
            p = run('Americas', masked("instr(';'||v.area||';',';North America;')>0 OR "
                                        "instr(';'||v.area||';',';South America;')>0"))
            runs[-1]['agreement_with_selected'] = agreement(reference, p)

            families = [r[0] for r in db.execute(
                "SELECT DISTINCT family FROM varieties WHERE family<>'' ORDER BY family")]
            probes = [(a, b) for a, b, _ in baseline]
            included, together = Counter(), Counter()
            rng = random.Random(104729)
            for replicate in range(REPLICATES):
                multiplicity = Counter(rng.choices(families, k=len(families)))
                sampled = family_block_edges(db, index, multiplicity)
                p = run(f'family-block-{replicate + 1}', sampled, seed=1)
                runs[-1]['agreement_with_selected'] = agreement(reference, p)
                for a, b in probes:
                    if a in p and b in p:
                        included[a, b] += 1
                        together[a, b] += p[a] == p[b]
            seed_together = {pair: sum(p[pair[0]] == p[pair[1]] for p in seed_partitions) for pair in probes}

        # Deterministic gzip, including header timestamp and original filename.
        import gzip as gz
        partition_bytes = stage / 'partitions.csv.gz'
        temp = stage / 'partitions.deterministic.gz'
        with gz.open(partition_bytes, 'rb') as source, temp.open('wb') as target:
            with gz.GzipFile(filename='', mode='wb', fileobj=target, mtime=0) as zipped:
                shutil.copyfileobj(source, zipped, length=65536)
        temp.replace(partition_bytes)
        diagnostics = {}
        with (stage / 'edge-diagnostics.csv').open('w', newline='') as handle:
            fields = ['concept_a', 'concept_b', 'families', 'comparable_families', 'positive_family_fraction',
                      'namespaces', 'max_namespace_family_share', 'families_without_one_namespace_min',
                      'maximum_identity_concepts', 'seed_coassignment', 'block_coassigned', 'block_eligible',
                      'source_namespaces', 'namespace_exclusive_families', 'comparison_bases']
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            single_source, fragile = 0, 0
            for a, b, f in edges:
                ca, cb = cids[a], cids[b]
                diagnostic = support_diagnostics(db, ca, cb, f)
                opportunity = json.loads(db.execute(
                    "SELECT opportunities FROM edges WHERE layer='segmented' AND kind='observed' AND a=? AND b=?",
                    (ca, cb)).fetchone()[0])
                denominator = opportunity['comparable_families']
                diagnostic.update(families=f, comparable_families=denominator,
                                  positive_family_fraction=f / denominator if denominator else None,
                                  seed_coassignment=seed_together.get((a, b)),
                                  block_coassigned=together[a, b], block_eligible=included[a, b])
                writer.writerow(dict(concept_a=ca, concept_b=cb, **{k: json.dumps(v, ensure_ascii=False, sort_keys=True)
                    if isinstance(v, (dict, list)) else v for k, v in diagnostic.items()}))
                # Only bounded display probes are retained; all rows stream to CSV.
                diagnostics[a, b] = {k: diagnostic[k] for k in ['namespaces', 'families_without_one_namespace_min',
                    'maximum_identity_concepts', 'seed_coassignment', 'block_coassigned', 'block_eligible']}
                single_source += diagnostic['namespaces'] == 1
                fragile += f >= 3 and diagnostic['families_without_one_namespace_min'] < 3
        members = defaultdict(list)
        for n, module in sorted(reference.items()):
            members[module].append(n)
        node_files = {}
        for cid in cids:
            n = index[cid]
            local = induced(db, cid, 'segmented', 'observed')
            probes_for_node = {}
            for neighbor in local['nodes'][1:]:
                key = tuple(sorted((n, index[neighbor])))
                probes_for_node[neighbor] = diagnostics[key]
            module = reference.get(n)
            group = members.get(module, [])
            group_set = set(group)
            # A stable degree ranking bounds the preview; complete memberships are downloadable.
            degree = Counter()
            for a, b, w in baseline:
                if a in group_set and b in group_set:
                    degree[a] += w
                    degree[b] += w
            selected = [n] + [v for v in sorted(group, key=lambda x: (-degree[x], cids[x])) if v != n][:30]
            selected_set = set(selected)
            selected_edges = []
            for a, b, w in baseline:
                if a in selected_set and b in selected_set:
                    counts = db.execute(
                        "SELECT languages,varieties FROM edges WHERE layer='segmented' AND kind='observed' "
                        'AND a=? AND b=?', (cids[a], cids[b])).fetchone()
                    selected_edges.append([cids[a], cids[b], w, *counts])
            node_status = json.loads((built / 'public' / parent['nodes'][cid]['url']).read_text())['status']
            payload = dict(concept_id=cid, community=cids[module] if module is not None else None,
                           status='assigned' if module is not None else
                           node_status if not local['edges'] else 'zero_known_family_support',
                           community_size=len(group), preview=[cids[v] for v in selected] if group else [],
                           preview_edges=selected_edges, diagnostics=probes_for_node)
            node_files[cid] = write_json(stage / (cid + '.json'), payload, Limits())
        files = {}
        for name in ['partitions.csv.gz', 'edge-diagnostics.csv']:
            p = stage / name
            if p.stat().st_size > 90 * 1024 * 1024:
                raise ValueError('Community export exceeded public file budget')
            files[name] = dict(url=name, bytes=p.stat().st_size, sha256=sha(p))
        manifest = dict(schema=1, build_id=build_id, parent_build_id=parent['build_id'], inputs=signature,
                        selected_seed=SEEDS[best], nodes=node_files, files=files, runs=runs,
                        summary=dict(evidence_edges=len(edges), eligible_family_edges=len(baseline),
                                     assigned_nodes=len(reference), communities=len(members),
                                     single_namespace_edges=single_source, recurrent_fragile_to_namespace=fragile),
                        interpretation=('Exploratory partitions; coassignment describes algorithm and '
                          'block perturbations, '
                          'not probability of a semantic category. Namespace removal does not identify independent '
                          'original sources. Family blocks are sampled corpus lineages, '
                          'not independent population draws.'))
        if verify_database(built)['database_sha256'] != signature['database_sha256']:
            raise ValueError('Analytical database changed during community generation')
        if sha(Path(__file__)) != signature['code']:
            raise ValueError('Community code changed during generation')
        write_json(stage / 'manifest.json', manifest, Limits(payload_bytes=4 * 1024 * 1024))
        verify(stage)
        destination.parent.mkdir(parents=True, exist_ok=True)
        stage.rename(destination)
        return destination
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    finally:
        db.close()


def verify(directory):
    directory = Path(directory)
    manifest = json.loads((directory / 'manifest.json').read_text())
    for spec in itertools.chain(manifest['nodes'].values(), manifest['files'].values()):
        if Path(spec['url']).name != spec['url']:
            raise ValueError('Unsafe community asset path')
        path = directory / spec['url']
        if path.stat().st_size != spec['bytes'] or sha(path) != spec['sha256']:
            raise ValueError('Corrupt community asset')
    return manifest


def publish(root, directory):
    root, directory = Path(root), Path(directory)
    manifest = verify(directory)
    path = root / 'web/data/manifest.json'
    web = json.loads(path.read_text())
    if web['colexification']['build_id'] != manifest['parent_build_id']:
        raise ValueError('Community and evidence snapshots differ')
    parent = root / 'web' / web['colexification']['url']
    if sha(parent) != manifest['inputs']['parent_sha256'] or sha(Path(__file__)) != manifest['inputs']['code']:
        raise ValueError('Stale community inputs')
    verify_database(root / 'output/colexification' / manifest['parent_build_id'])
    destination = root / 'web/data/colexification-communities' / manifest['build_id']
    if not destination.exists():
        stage = destination.with_name('.' + destination.name + '.publishing')
        shutil.copytree(directory, stage)
        stage.rename(destination)
    else:
        verify(destination)
    public_manifest = destination / 'manifest.json'
    web['colexification']['communities'] = dict(url=str(public_manifest.relative_to(root / 'web')),
        bytes=public_manifest.stat().st_size, sha256=sha(public_manifest))
    temporary = path.with_suffix('.community-publishing')
    temporary.write_text(json.dumps(web, ensure_ascii=False, indent=2) + '\n')
    os.replace(temporary, path)


if __name__ == '__main__':
    import argparse
    import resource

    parser = argparse.ArgumentParser(description='Isolated community partition worker')
    parser.add_argument('--worker', type=Path, required=True)
    args = parser.parse_args()
    inherited = resource.getrlimit(resource.RLIMIT_AS)[0]
    budget = 256 * 1024 * 1024
    if inherited != resource.RLIM_INFINITY:
        budget = min(budget, inherited)
    resource.setrlimit(resource.RLIMIT_AS, (budget, budget))
    if args.worker.stat().st_size > 16 * 1024 * 1024:
        parser.error('Worker input exceeds byte budget')
    payload = json.loads(args.worker.read_text())
    if len(payload['edges']) > 250000:
        parser.error('Worker edge budget exceeded')
    membership, objective = partition(**payload)
    json.dump(dict(partition=membership, objective=objective), sys.stdout, sort_keys=True)
