"""Compare cached and staged CLDF source snapshots without changing intake.

Reports identity, concept, form and cognate changes plus accepted-variety
exposure. Source labels are evidence; canonical accepted identities are not
rewritten automatically. Paths and source heads are explicit in summary.json.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
IDENTITY = {'Glottocode', 'ISO639P3code'}
CONCEPT = {'Concepticon_ID', 'Concepticon_Gloss'}


def indexed(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open() as f:
        rows = list(csv.DictReader(f))
    result = {r['ID']: r for r in rows}
    if len(result) != len(rows):
        raise ValueError('Duplicate source IDs: ' + str(path))
    return result


def differences(old: dict, new: dict):
    for key in sorted(old.keys() | new.keys()):
        if key not in old:
            yield key, 'added', '', None, new[key]
        elif key not in new:
            yield key, 'removed', '', old[key], None
        else:
            for field in sorted(old[key].keys() | new[key].keys()):
                before, after = old[key].get(field, ''), new[key].get(field, '')
                if before != after:
                    yield key, 'changed', field, before, after


def write_csv(path: Path, rows: list, fields: list):
    with path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def snapshot(path: Path) -> dict:
    sha = subprocess.check_output(['git', '-C', str(path), 'rev-parse', 'HEAD'], text=True).strip()
    files = {}
    for name in ['languages.csv', 'parameters.csv', 'forms.csv', 'cognates.csv', 'sources.bib']:
        p = path / 'cldf' / name
        files[name] = hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
    return dict(commit=sha, files=files)


def audit(root: Path, dataset: str, staged: Path, output: Path) -> dict:
    cached = root / 'raw/lexibank' / dataset
    output.mkdir(parents=True, exist_ok=True)
    summary = dict(dataset=dataset, cached=snapshot(cached), staged=snapshot(staged), tables={})
    changes, languages = [], None
    forms_before, forms_after = {}, {}
    for table in ['languages', 'parameters', 'forms', 'cognates']:
        old = indexed(cached / 'cldf' / (table + '.csv'))
        new = indexed(staged / 'cldf' / (table + '.csv'))
        fields = Counter()
        changed_ids = set()
        for key, kind, field, before, after in differences(old, new):
            fields[field or kind] += 1
            changed_ids.add(key)
            # Store hashes rather than redistributing full source descriptions.
            def encode(value):
                if isinstance(value, dict):
                    return json.dumps(value, sort_keys=True, ensure_ascii=False)
                return str(value or '')

            if table in {'forms', 'cognates'} and sum(fields.values()) > 500:
                continue
            changes.append(dict(table=table, source_id=key, change=kind, field=field,
                                before_sha256=hashlib.sha256(encode(before).encode()).hexdigest(),
                                after_sha256=hashlib.sha256(encode(after).encode()).hexdigest()))
        summary['tables'][table] = dict(before=len(old), after=len(new), added=len(new.keys()-old.keys()),
                                        removed=len(old.keys()-new.keys()), changed_rows=len(
                                            changed_ids & old.keys() & new.keys()), changed_fields=dict(fields))
        if table == 'languages':
            languages = old, new
        if table == 'forms':
            forms_before, forms_after = old, new
    old_langs, new_langs = languages
    summary['language_identity_changes'] = sum(
        any(old_langs[k].get(f, '') != new_langs[k].get(f, '') for f in IDENTITY)
        for k in old_langs.keys() & new_langs.keys())
    old_params = indexed(cached / 'cldf/parameters.csv')
    new_params = indexed(staged / 'cldf/parameters.csv')
    summary['concept_mapping_changes'] = sum(
        any(old_params[k].get(f, '') != new_params[k].get(f, '') for f in CONCEPT)
        for k in old_params.keys() & new_params.keys())
    migration = []
    for key in sorted(old_langs.keys() | new_langs.keys()):
        before, after = old_langs.get(key, {}), new_langs.get(key, {})
        if before != after:
            migration.append(dict(member=key, old_name=before.get('Name', ''), new_name=after.get('Name', ''),
                                  old_glottocode=before.get('Glottocode', ''),
                                  new_glottocode=after.get('Glottocode', '')))
    write_csv(output / 'language_migration.csv', migration,
              ['member', 'old_name', 'new_name', 'old_glottocode', 'new_glottocode'])
    before_groups, after_groups = defaultdict(dict), defaultdict(dict)
    for key, row in forms_before.items():
        before_groups[row['Language_ID']][key] = row
    for key, row in forms_after.items():
        after_groups[row['Language_ID']][key] = row
    exposure = []
    for path in sorted((root / 'varieties').glob('*/config.yaml')):
        c = yaml.safe_load(path.read_text())
        if dataset not in {c['sources']['transcription'], c['sources']['cognates']}:
            continue
        sources = c['sources']
        gc = sources.get('source_glottocode') or c['glottocode']
        prefix = dataset + '_'
        selected = sources.get('source_language_id', '')
        member = selected.removeprefix(prefix) if selected else ''

        def selected_ids(langs):
            return {k for k, row in langs.items() if row.get('Glottocode', '').lower() == gc.lower()
                    and (not member or k == member)}

        old_ids, new_ids = selected_ids(old_langs), selected_ids(new_langs)
        before = {k: r for lid in old_ids for k, r in before_groups[lid].items()}
        after = {k: r for lid in new_ids for k, r in after_groups[lid].items()}
        exposure.append(dict(av_id=c['av_id'], glottocode=c['glottocode'], pinned=c.get('pinned', False),
                             selected_member=selected, old_members=';'.join(sorted(old_ids)),
                             new_members=';'.join(sorted(new_ids)), old_forms=len(before), new_forms=len(after),
                             form_ids_added=len(after.keys()-before.keys()),
                             form_ids_removed=len(before.keys()-after.keys()),
                             shared_forms_changed=sum(before[k] != after[k] for k in before.keys() & after.keys()),
                             member_selection_changed=old_ids != new_ids))
    summary['accepted_varieties_exposed'] = len(exposure)
    summary['accepted_member_selections_changed'] = sum(r['member_selection_changed'] for r in exposure)
    summary['active_intake_changed'] = False
    summary['detail_policy'] = 'All language/parameter changes; first 500 form/cognate field changes per table. '
    summary['detail_policy'] += 'Summary counts cover every row; staged snapshots retain full evidence.'
    summary['decision'] = ('stage_only_identity_or_mapping_migration_required' if
                           summary['language_identity_changes'] or summary['concept_mapping_changes'] or
                           summary['accepted_member_selections_changed'] else
                           'stage_review_complete_no_identity_or_mapping_changes')
    write_csv(output / 'changes.csv', changes,
              ['table', 'source_id', 'change', 'field', 'before_sha256', 'after_sha256'])
    write_csv(output / 'accepted_varieties.csv', exposure,
              ['av_id', 'glottocode', 'pinned', 'selected_member', 'old_members', 'new_members', 'old_forms',
               'new_forms', 'form_ids_added', 'form_ids_removed', 'shared_forms_changed', 'member_selection_changed'])
    (output / 'summary.json').write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n')
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dataset')
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--staged-repository', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    summary = audit(args.root.resolve(), args.dataset, args.staged_repository.resolve(), args.output.resolve())
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
