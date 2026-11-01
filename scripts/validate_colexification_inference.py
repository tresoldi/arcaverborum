"""Execute the frozen broader validation protocol under a hard worker memory cap."""

import argparse
import json
import resource
import time
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument("--build", type=Path, required=True)
    p.add_argument("--protocol", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    resource.setrlimit(resource.RLIMIT_AS, (256 * 1024**2, 256 * 1024**2))
    from arcaverborum.colexification import sha
    from arcaverborum.colexification_validation import run

    start = time.monotonic()
    result = run(a.root, a.build, a.protocol, a.output)
    # VmHWM avoids a launcher-inherited ru_maxrss high-water mark on Linux.
    status = dict(line.split(":", 1) for line in Path("/proc/self/status").read_text().splitlines() if ":" in line)
    runtime = dict(
        seconds=time.monotonic() - start,
        peak_rss_mb=int(status["VmHWM"].split()[0]) / 1024,
        memory_limit_mb=256,
        signature=result["signature"],
    )
    (a.output / "runtime.json").write_text(json.dumps(runtime, indent=2) + "\n")
    complete = json.loads((a.output / "complete.json").read_text())
    complete["files"]["runtime.json"] = sha(a.output / "runtime.json")
    (a.output / "complete.json").write_text(json.dumps(complete, indent=2) + "\n")
    print(json.dumps(runtime, indent=2))


if __name__ == "__main__":
    main()
