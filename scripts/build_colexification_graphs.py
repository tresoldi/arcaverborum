"""Export bounded interconnected subgraphs without rebuilding lexical colexifications."""
import argparse
import json
import resource
from pathlib import Path

from arcaverborum.colexification_graphs import build_graphs, publish_graphs

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--build', type=Path)
    parser.add_argument('--publish', action='store_true')
    parser.add_argument('--memory-mb', type=int, default=256)
    args = parser.parse_args()
    if args.memory_mb < 128:
        parser.error('Memory budget must be at least 128 MiB')
    resource.setrlimit(resource.RLIMIT_AS, (args.memory_mb * 1024 * 1024,) * 2)
    built = args.build
    if not built:
        web = json.loads((args.root / 'web/data/manifest.json').read_text())
        built = args.root / 'output/colexification' / web['colexification']['build_id']
    exported = build_graphs(built)
    if args.publish:
        publish_graphs(args.root, exported)
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    print(json.dumps(dict(directory=str(exported), peak_rss_mb=peak,
                          memory_limit_mb=args.memory_mb, published=args.publish), indent=2))
