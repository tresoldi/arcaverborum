"""Stream accepted readings for source-specific prefix-loss review candidates."""
import argparse
import csv
import json
from collections import Counter
from pathlib import Path

from arcaverborum.colexification import analytical_exclusion, identity, sha


def audit(root):
    csv.field_size_limit(8 * 1024 * 1024)
    path = root / 'output/aggregate/forms.csv'
    counts, examples = Counter(), []
    reviewed_examples = {}
    with path.open(newline='', encoding='utf-8') as handle:
        for row in csv.DictReader(handle):
            reason = analytical_exclusion(row)
            value, word = identity(row.get('Value', '')), identity(row.get('Form', ''))
            if not reason and row['transcription_source'] == 'huntergatherer' and "'" in value:
                if word and word == value.split("'", 1)[0]:
                    reason = 'apostrophe_prefix_review_only'
            if not reason and row['transcription_source'] == 'huntergatherer' and '/' in value:
                if word and word == value.split('/', 1)[0]:
                    reason = 'slash_prefix_review_only'
            if reason:
                if reason in {'source_extraction_prefix', 'held_washo_prefix_reading', 'reviewed_reconstruction'}:
                    selected = reviewed_examples.setdefault(reason, [])
                    if len(selected) < 10:
                        selected.append({k: row.get(k, '') for k in
                                         ['av_id', 'source_form_id', 'Value', 'Form', 'Segments']})
                counts[(reason, row['av_id'])] += 1
                if len(examples) < 100:
                    examples.append({k: row.get(k, '') for k in
                                     ['av_id', 'source_form_id', 'Value', 'Form', 'Segments']} | {'reason': reason})
    extractor = root / 'raw/lexibank/huntergatherer/lexibank_huntergatherer.py'
    return {'forms_sha256': sha(path), 'audit_code_sha256': sha(Path(__file__)),
            'guard_code_sha256': sha(root / 'src/arcaverborum/colexification.py'),
            'upstream_parser_sha256': sha(extractor) if extractor.exists() else None,
            'reviewed_examples': reviewed_examples, 'counts': [dict(reason=k[0], av_id=k[1], rows=v)
             for k, v in sorted(counts.items())], 'examples': examples,
            'interpretation': ('Unheld prefix candidates require source review; '
                               'these counts are readings, not erroneous edges.')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.root)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
