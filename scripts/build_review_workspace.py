"""Build a sealed offline source-visible worksheet, or validate exported decisions."""

import argparse
import json
from pathlib import Path

from arcaverborum.review_workspace import packet_from_csv, render_workspace, validate_decisions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worksheet", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--decisions", type=Path)
    parser.add_argument("--review", action="append", type=Path, default=[])
    parser.add_argument("--native-labels", type=Path)
    args = parser.parse_args()
    packet = packet_from_csv(args.worksheet, reviews=args.review, native_labels=args.native_labels)
    if args.decisions:
        if args.decisions.stat().st_size > 8 * 1024**2:
            parser.error("Decision export exceeds 8 MiB budget")
        print(json.dumps(validate_decisions(packet, json.loads(args.decisions.read_text())), indent=2))
        return
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "packet.json").write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n")
    (args.output / "index.html").write_text(render_workspace(packet))
    print(json.dumps({"cases": len(packet["cases"]), "packet_sha256": packet["packet_sha256"]}))


if __name__ == "__main__":
    main()
