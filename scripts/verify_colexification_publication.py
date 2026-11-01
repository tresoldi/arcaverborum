"""Stream-check every active derived asset on the canonical static site."""
import argparse
import hashlib
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urljoin

import requests

from arcaverborum.colexification import sha


def assets(root):
    web = root / 'web'
    manifest = json.loads((web / 'data/manifest.json').read_text())
    paths = {'data/manifest.json', 'index.html', 'colexification.js', 'research.js', 'research-worker.js'}
    paths.update(spec['url'] for spec in manifest['shards'].values())
    paths.update(spec['url'] for spec in manifest.get('wordnet', {}).get('files', []))
    paths.add(manifest['catalog']['url'])
    paths.add('data/sources.bib')
    if manifest.get('recordings'):
        paths.add(manifest['recordings']['url'])
    concept_spec = manifest.get('concept_rows')
    if concept_spec:
        paths.add(concept_spec['url'])
        concept_path = web / concept_spec['url']
        concept_manifest = json.loads(concept_path.read_text())
        for concept in concept_manifest['concepts'].values():
            for page in concept['pages']:
                paths.add(str(concept_path.parent.joinpath(page['url']).relative_to(web)))
    main = manifest['colexification']
    primary = web / main['url']
    network = json.loads(primary.read_text())
    paths.add(main['url'])
    for spec in network['files'].values():
        paths.add(str(primary.parent.joinpath(spec['url']).relative_to(web)))
    for spec in network['nodes'].values():
        node_path = primary.parent / spec['url']
        paths.add(str(node_path.relative_to(web)))
        node = json.loads(node_path.read_text())
        for layer in node['layers'].values():
            for kind in ['observed', 'inferred']:
                for page in layer[kind]['pages']:
                    paths.add(str(primary.parent.joinpath(page['url']).relative_to(web)))
    for name in ['subgraphs', 'communities']:
        spec = main[name]
        path = web / spec['url']
        paths.add(spec['url'])
        layer = json.loads(path.read_text())
        for file in list(layer['nodes'].values()) + list(layer.get('files', {}).values()):
            paths.add(str(path.parent.joinpath(file['url']).relative_to(web)))
    selected = [(path, web / path) for path in sorted(paths)]
    for path in ['COLEXIFICATION.md', 'COLEXIFICATION_COMMUNITIES.md', 'CLICS_COMPARISON.md',
                 'colexification_repair_verification_2026-10-31.json',
                 'colexification_communities_verification_2026-10-31.json']:
        selected.append(('docs/' + path, root / 'docs' / path))
    for path in ['REGIONAL_EXECUTION_2026-11-01.md', 'regional_summary_2026-11-01.json',
                 'regional_preservation_2026-11-01.json', 'regional_source_verification_2026-11-01.json',
                 'regional_holds_2026-11-01.csv']:
        if (root / 'docs' / path).exists():
            selected.append(('docs/' + path, root / 'docs' / path))
    comparison = root / 'docs/colexification_clics_regional_2026-11-01.bundle.json'
    if comparison.exists():
        bundle = json.loads(comparison.read_text())
        selected.append(('docs/' + comparison.name, comparison))
        for spec in bundle['files'].values():
            selected.append(('docs/' + spec['url'], root / 'docs' / spec['url']))
    for name in ['COLEXIFICATION_ROBUSTNESS_2026-11-01.md',
                 'colexification_robustness_metrics_2026-11-01.json',
                 'colexification_robustness_preservation_2026-11-01.json',
                 'colexification_robustness_network_verification_2026-11-01.json',
                 'colexification_robustness_communities_2026-11-01.json',
                 'colexification_sense_reviews_2026-11-01.json',
                 'colexification_semantic_queue_2026-11-01.csv']:
        if (root / 'docs' / name).exists():
            selected.append(('docs/' + name, root / 'docs' / name))
    return selected, manifest


def verify(root, base):
    selected, manifest = assets(root)
    state = threading.local()

    def check(item):
        relative, local = item
        expected, length = sha(local), local.stat().st_size
        if not hasattr(state, 'session'):
            state.session = requests.Session()
        failure = None
        for attempt in range(3):
            try:
                with state.session.get(urljoin(base, relative), stream=True, timeout=45,
                                       headers={'Cache-Control': 'no-cache'}) as response:
                    response.raise_for_status()
                    digest, size = hashlib.sha256(), 0
                    for chunk in response.iter_content(65536):
                        size += len(chunk)
                        if size > length:
                            raise ValueError('Remote asset exceeds expected size')
                        digest.update(chunk)
                    if size != length or digest.hexdigest() != expected:
                        raise ValueError('Remote asset differs from committed artifact')
                return None
            except (requests.RequestException, ValueError) as error:
                failure = dict(path=relative, error=str(error))
                time.sleep(attempt + 1)
        return failure

    # Avoid thousands of requests against an earlier deployment.
    root_item = next(item for item in selected if item[0] == 'data/manifest.json')
    error = check(root_item)
    if error:
        raise ValueError(error)
    errors = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        for index, result in enumerate(pool.map(check, selected), 1):
            if result:
                errors.append(result)
            if index % 1000 == 0:
                print(f'Canonical assets checked: {index}/{len(selected)}', flush=True)
    return dict(base_url=base, analytical_build_id=manifest['colexification']['build_id'],
                community_spec=manifest['colexification']['communities'], checked_assets=len(selected),
                failures=errors, all_match=not errors)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--url', default='https://arcaverborum.org/')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.root, args.url)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    if result['failures']:
        raise SystemExit(1)
