"""Stage a pinned complete Wiktionary edition outside active intake."""
import argparse
from pathlib import Path

from arcaverborum.sources.wiktionary_editions import ROOT, stage

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--edition', required=True)
    parser.add_argument('--archive', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    destination = args.output.resolve()
    if destination == ROOT / 'intake' or ROOT / 'intake' in destination.parents:
        raise ValueError('Stage outside active intake')
    print(stage(args.edition, args.archive, destination), flush=True)
