"""Build source-scoped colexification without loading the lexical corpus into RAM."""
from __future__ import annotations

import argparse
import csv
import json
import resource
import sys
from pathlib import Path

from arcaverborum.colexification import Limits, build, connect, pair_status, publish


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output', type=Path)
    parser.add_argument('--publish', action='store_true')
    parser.add_argument('--memory-mb', type=int, default=384)
    parser.add_argument('--max-identity-concepts', type=int, default=64)
    parser.add_argument('--max-witnesses', type=int, default=5_000_000)
    parser.add_argument('--database-mb', type=int, default=3072)
    parser.add_argument('--pair', nargs=2, metavar=('CONCEPT_A', 'CONCEPT_B'))
    parser.add_argument('--database', type=Path)
    parser.add_argument('--layer', choices=['segmented', 'written', 'reduced'], default='segmented')
    args = parser.parse_args()
    if args.memory_mb < 128:
        parser.error('--memory-mb must be at least 128')
    # A hard process limit makes an unexpectedly large allocation fail closed.
    resource.setrlimit(resource.RLIMIT_AS, (args.memory_mb * 1024 * 1024, args.memory_mb * 1024 * 1024))
    if args.pair:
        if not args.database or not args.database.is_file():
            parser.error('--pair requires --database')
        db = connect(args.database)
        metadata = json.loads(db.execute("SELECT value FROM meta WHERE key='manifest'").fetchone()[0])
        if args.pair[0] == args.pair[1] or any(cid not in metadata['nodes'] for cid in args.pair):
            parser.error('--pair requires two different frozen catalog concepts')
        writer = csv.writer(sys.stdout, lineterminator='\n')
        writer.writerow(['av_id', 'language', 'family', 'status', 'build_id'])
        observed = {}
        for row in pair_status(db, *args.pair, args.layer):
            observed[row[1]] = max(observed.get(row[1], 0), row[4])
        for av, language, family in db.execute('SELECT av,language,family FROM varieties ORDER BY av'):
            state = 'colexified' if observed.get(av) else 'no_shared_form_observed' if av in observed else 'unknown'
            writer.writerow([av, language, family, state, metadata['build_id']])
        db.close()
        return
    limits = Limits(identity_concepts=args.max_identity_concepts,
                    max_witnesses=args.max_witnesses, database_mb=args.database_mb)
    built = build(args.root, args.output, limits)
    if args.publish:
        publish(args.root, built)
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    print(json.dumps(dict(build=str(built), peak_rss_mb=round(peak, 2), memory_limit_mb=args.memory_mb,
                          published=args.publish), indent=2))


if __name__ == '__main__':
    main()
