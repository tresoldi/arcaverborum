"""Export concept-specific lexical chunks without rebuilding accepted lexical data."""
import argparse
import json
import os
import resource
import sys
from pathlib import Path

from arcaverborum.concept_rows import build

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--with-colexification', action='store_true')
    parser.add_argument('--with-communities', action='store_true')
    args = parser.parse_args()
    if args.with_communities and not args.with_colexification:
        parser.error('--with-communities requires --with-colexification')
    # Bound this exporter while allowing the next exec'd stage to set its own budget.
    hard = resource.getrlimit(resource.RLIMIT_AS)[1]
    budget = 256 * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (budget if hard == resource.RLIM_INFINITY else min(budget, hard), hard))
    destination = build(args.root)
    print(json.dumps(dict(directory=str(destination),
                          peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)))
    if args.with_colexification:
        sys.stdout.flush()
        script = Path(__file__).resolve().parent / 'build_colexification.py'
        command = [sys.executable, str(script), '--root', str(args.root), '--publish']
        if args.with_communities:
            command.append('--with-communities')
        os.execv(sys.executable, command)
