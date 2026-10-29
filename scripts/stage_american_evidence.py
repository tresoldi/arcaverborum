"""Stage individually reviewed original HGN and reconstructed American evidence."""
import argparse
from pathlib import Path

from arcaverborum.ingest import ingest_lexibank
from arcaverborum.sources.american_evidence import ROOT, materialize

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', required=True)
    parser.add_argument('--fetch', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    stage = (args.output or ROOT / 'raw/curation' / ('stage-' + args.dataset)).resolve()
    if stage == ROOT / 'intake' or ROOT / 'intake' in stage.parents:
        raise ValueError('Stage outside active intake')
    stats = materialize(ROOT / 'raw', dataset=args.dataset, download=args.fetch)
    result = ingest_lexibank(ROOT / 'raw', stage, datasets=[args.dataset])
    if result['datasets_ingested'] != 1 or result['total_forms'] != stats['forms']:
        raise ValueError('American source stage incomplete')
    print(stats)
