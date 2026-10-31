"""Build and optionally publish bounded exploratory global communities."""
import argparse
import fcntl
import json
import os
import resource
from pathlib import Path

os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
from arcaverborum.colexification_communities import build, publish  # noqa: E402

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--publish', action='store_true')
    parser.add_argument('--memory-mb', type=int, default=256)
    args = parser.parse_args()
    if args.memory_mb < 128:
        parser.error('Memory budget must be at least 128 MiB')
    resource.setrlimit(resource.RLIMIT_AS, (args.memory_mb * 1024 * 1024,) * 2)
    build_lock = (args.build / '.community-build.lock').open('a')
    try:
        fcntl.flock(build_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        parser.error('Another community build is running')
    result = build(args.build)
    if args.publish:
        publish(args.root, result)
    print(json.dumps(dict(directory=str(result), peak_rss_mb=max(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                                          resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss) / 1024,
                          parent_peak_rss_mb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
                          worker_peak_rss_mb=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1024,
                          memory_limit_mb=args.memory_mb, published=args.publish), indent=2))
