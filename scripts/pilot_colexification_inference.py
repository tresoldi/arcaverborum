"""Run the frozen exploratory inference protocol, with bounded process memory."""

import argparse
import json
import os
import resource
import sqlite3
import sys
import time
from pathlib import Path

os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument("--build", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--memory-mb", type=int, default=256)
    a = p.parse_args()
    if a.memory_mb < 128:
        p.error("Memory budget must be at least 128MiB")
    resource.setrlimit(resource.RLIMIT_AS, (a.memory_mb * 1024**2, a.memory_mb * 1024**2))
    from arcaverborum.colexification_inference import run

    started = time.monotonic()
    r = run(a.root, a.build, a.output)
    meta = dict(
        seconds=round(time.monotonic() - started, 3),
        peak_rss_mb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
        memory_limit_mb=a.memory_mb,
        signature=r["signature"],
        python=sys.version,
        sqlite=sqlite3.sqlite_version,
    )
    (a.output / "runtime.json").write_text(json.dumps(meta, indent=2) + "\n")
    from arcaverborum.colexification import sha

    complete = json.loads((a.output / "complete.json").read_text())
    complete["files"]["runtime.json"] = sha(a.output / "runtime.json")
    (a.output / "complete.json").write_text(json.dumps(complete, indent=2) + "\n")
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
