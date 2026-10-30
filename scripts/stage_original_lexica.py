"""Stage pinned original lexica outside active intake."""
import argparse
from pathlib import Path

from arcaverborum.ingest import ingest_lexibank
from arcaverborum.sources.original_lexica import ROOT, materialize

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', required=True)
    parser.add_argument('--fetch', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    stage = (args.output or ROOT / 'raw/curation' / ('stage-' + args.dataset)).resolve()
    if stage == ROOT / 'intake' or ROOT / 'intake' in stage.parents:
        raise ValueError('Stage outside active intake')
    result = materialize(ROOT / 'raw', dataset=args.dataset, download=args.fetch)
    stats = ingest_lexibank(ROOT / 'raw', stage, datasets=[args.dataset])
    if stats['datasets_ingested'] != 1 or stats['total_forms'] != result['forms']:
        raise ValueError('Original source stage incomplete')
    print(result)
