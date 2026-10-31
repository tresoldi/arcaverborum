"""Compare accepted observed colexifications to pinned CLICS3/4 releases."""
import argparse
import json
import resource
from pathlib import Path

from arcaverborum.colexification_comparison import compare

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--fetch', action='store_true')
    parser.add_argument('--output', type=Path, default=Path('docs/colexification_clics_comparison_2026-10-31'))
    parser.add_argument('--memory-mb', type=int, default=256)
    args = parser.parse_args()
    if args.memory_mb < 128:
        parser.error('Memory budget must be at least 128 MiB')
    resource.setrlimit(resource.RLIMIT_AS, (args.memory_mb * 1024 * 1024,) * 2)
    report = compare(args.root, args.root / 'raw/curation/colexification/clics-comparison',
                     args.root / 'output/colexification-comparison', args.root / args.output, args.fetch)
    report['peak_rss_mib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    report['address_space_limit_mib'] = args.memory_mb
    (args.root / args.output).with_suffix('.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: report[key] for key in ['comparisons', 'matched_clics4', 'peak_rss_mib']}, indent=2))
