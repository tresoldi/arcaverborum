"""Export a deterministic, explicitly licensed subset of accepted lexical rows.

This is a source-scoped lexical export, not the All accepted archive, a full
intake dump or a substitute for complete source acquisition/build recipes.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import shutil
import sys
import tarfile
from collections import Counter
from pathlib import Path

from arcaverborum.aggregate import write_sources_bib

ROOT = Path(__file__).resolve().parents[1]
csv.field_size_limit(sys.maxsize)


def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def read(path):
    with Path(path).open(newline='') as handle:
        return list(csv.DictReader(handle))


def write(path, rows, fields):
    with Path(path).open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def build(root, output, date, policy_path, *, data_revision):
    root, output = Path(root), Path(output)
    if output.exists():
        raise FileExistsError(output)
    policy = json.loads(Path(policy_path).read_text())
    allowed = {r['source']: r for r in policy['sources']}
    if not allowed or len(allowed) != len(policy['sources']):
        raise ValueError('Release requires unique reviewed source terms')
    for review in allowed.values():
        if not review.get('license') or not review.get('authority_url') or not review.get('upstream_version'):
            raise ValueError('Release source terms incomplete')
        for pin in review.get('local_authorities', []):
            path = (root / pin['path']).resolve()
            if not path.is_relative_to(root.resolve()) or sha(path) != pin['sha256']:
                raise ValueError('Release authority changed')
    aggregate = root / 'output/aggregate'
    metadata = {r['Dataset']: r for r in read(aggregate / 'metadata.csv')}
    for source, review in allowed.items():
        if (source not in metadata or metadata[source].get('License') != review['license']
                or metadata[source].get('Repository_Version') != review['upstream_version']):
            raise ValueError('Release metadata differs from reviewed source terms: ' + source)
    output.mkdir(parents=True)
    payload = output / 'payload'
    data = payload / 'data'
    data.mkdir(parents=True)
    counts, sources, excluded, evidence = Counter(), Counter(), Counter(), Counter()
    concepts, bibliography = set(), set()
    with (aggregate / 'forms.csv').open(newline='') as handle, (data / 'forms.csv').open('w', newline='') as dest:
        reader = csv.DictReader(handle)
        writer = csv.DictWriter(dest, fieldnames=[*reader.fieldnames, 'release_source_license'], lineterminator='\n')
        writer.writeheader()
        for row in reader:
            source = row['transcription_source']
            if source not in allowed:
                excluded[source] += 1
                continue
            if row.get('Cognacy') and row.get('cognate_source', source) not in allowed:
                excluded[source + ':unreviewed_cognacy_source'] += 1
                continue
            writer.writerow({**row, 'release_source_license': allowed[source]['license']})
            counts[row['av_id']] += 1
            sources[source] += 1
            evidence[row.get('Segments_Source', '')] += 1
            if row.get('concept_id'):
                concepts.add(row['concept_id'])
            bibliography.update(k.strip() for k in row.get('bibtex_key', '').split(';') if k.strip())
    if not counts:
        raise ValueError('Refusing empty reviewed release')
    rows = [r for r in read(aggregate / 'varieties.csv') if r['av_id'] in counts]
    if {r['av_id'] for r in rows} != set(counts):
        raise ValueError('Subset variety attribution missing')
    # Primary source labels describe the explorer construction, not necessarily
    # the selected row source. Add actual subset counts instead of implying full coverage.
    for row in rows:
        row['release_lexical_rows'] = counts[row['av_id']]
    write(data / 'varieties.csv', rows, list(rows[0]))
    rows = [r for r in read(aggregate / 'parameters.csv') if r['concept_id'] in concepts]
    write(data / 'parameters.csv', rows, list(rows[0]) if rows else ['concept_id'])
    rows = [metadata[source] for source in sorted(sources)]
    rows = [{**row, 'release_lexical_rows': sources[row['Dataset']]} for row in rows]
    write(data / 'metadata.csv', rows, list(rows[0]))
    write_sources_bib(aggregate / 'sources.bib', bibliography, data)
    licenses = payload / 'licenses'
    licenses.mkdir()
    shutil.copyfile(policy_path, licenses / 'source-reviews.json')
    for path in policy.get('supporting_documents', []):
        source = root / path
        shutil.copyfile(source, licenses / source.name)
    # Only the explicitly licensed conceptual sidecar; no other lexical recipes,
    # preserved forms, raw archives, audio or arbitrary src/data dictionaries.
    conceptual = payload / 'concepts'
    conceptual.mkdir()
    shutil.copyfile(root / 'src/arcaverborum/data/concepts.csv', conceptual / 'concepts.csv')
    wordnet = root / 'src/arcaverborum/data/wordnet'
    if wordnet.exists():
        shutil.copytree(wordnet, conceptual / 'wordnet')
    reproduction = payload / 'reproduce'
    reproduction.mkdir()
    shutil.copyfile(Path(__file__), reproduction / Path(__file__).name)
    shutil.copyfile(root / 'pyproject.toml', reproduction / 'pyproject.toml')
    shutil.copyfile(root / 'LICENSE', reproduction / 'CODE_LICENSE.txt')
    readme = payload / 'README.txt'
    readme.write_text(
        f'Arca Verborum — Reviewed sources {date}\n\n'
        'A lexical subset of the accepted explorer, selected by reviewed source terms. '
        'It is not All accepted, the historical Core release, a new language census, '
        'or a complete original dictionary dump. Recording files and source scans are excluded.\n\n'
        'Each lexical row retains all accepted fields plus release_source_license. '
        'Source licenses, contributors, snapshots, attribution and modifications are in '
        'licenses/source-reviews.json, data/metadata.csv, data/sources.bib and original row provenance. '
        'Keep these notices and the original per-entry URLs when redistributing. '
        'Wiktionary-derived records and Arca adaptations to those records are CC BY-SA 4.0; '
        'other source terms remain as declared per row, not replaced by the code MIT license.\n\n'
        'Arca selects, normalizes and annotates source material and reviews semantic mappings. '
        'Source and profile flags include documented upstream conversions; they are not '
        'independent certification of IPA. Written-only and unresolved evidence remain explicit. '
        'Typed WordNet links, inherited associations and retrieval candidates are distinct. '
        'Source-specific cognacy does not imply independent fieldwork or colexification.\n\n'
        'Cite Arca Verborum, Reviewed sources '+date+', archive SHA256, together with the '
        'individual original sources used. No DOI or new version of the historical CITATION.cff is asserted.\n\n'
        'This export reproduces from the accepted aggregate and reviewed policy; source reacquisition '
        'uses the project repository at the recorded data revision. Included CSVs are self-contained '
        'lexical tables, not the full intake/build environment. Primary labels in varieties.csv '
        'describe the explorer; release_lexical_rows counts only included rows.\n')
    files = [{'path': str(p.relative_to(payload)), 'bytes': p.stat().st_size, 'sha256': sha(p)}
             for p in sorted(payload.rglob('*')) if p.is_file()]
    manifest = dict(schema=1, collection='Reviewed sources', version=date, data_revision=data_revision,
                    lexical_records=sum(sources.values()), constructions_with_included_rows=len(counts),
                    sources=dict(sources), evidence_counts=dict(evidence),
                    excluded_records_by_source=dict(sorted(excluded.items())), recording_files_included=0,
                    source_policy_sha256=sha(policy_path), aggregate_forms_sha256=sha(aggregate / 'forms.csv'),
                    full_collection=False, files=files,
                    conceptual_terms=policy['conceptual_terms'])
    (payload / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + '\n')
    archive = output / f'arca-reviewed-sources-{date}.tar.gz'
    paths = sorted(p for p in payload.rglob('*') if p.is_file())
    with archive.open('wb') as raw, gzip.GzipFile(fileobj=raw, filename='', mode='wb', mtime=0) as z:
        with tarfile.open(fileobj=z, mode='w|') as tar:
            for path in paths:
                info = tar.gettarinfo(str(path), arcname=str(path.relative_to(payload)))
                info.uid = info.gid = info.mtime = 0
                info.uname = info.gname = ''
                info.mode = 0o644
                with path.open('rb') as handle:
                    tar.addfile(info, handle)
    expected = {str(p.relative_to(payload)): sha(p) for p in paths}
    seen = set()
    with tarfile.open(archive, mode='r|gz') as tar:
        for member in tar:
            if not member.isfile() or member.name not in expected or member.name in seen:
                raise ValueError('Unexpected archive member')
            with tar.extractfile(member) as handle:
                if hashlib.file_digest(handle, 'sha256').hexdigest() != expected[member.name]:
                    raise ValueError('Archive member differs')
            seen.add(member.name)
    if seen != set(expected):
        raise ValueError('Archive member missing')
    shutil.copyfile(payload / 'manifest.json', output / 'manifest.json')
    shutil.copyfile(readme, output / 'README.txt')
    (output / 'archive-sha256.txt').write_text(sha(archive) + '  ' + archive.name + '\n')
    (output / 'complete.json').write_text(json.dumps(dict(
        archive_filename=archive.name, archive_sha256=sha(archive), archive_bytes=archive.stat().st_size,
        manifest_sha256=sha(output / 'manifest.json'), verified_members=len(seen)), indent=2) + '\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--date', required=True)
    parser.add_argument('--data-revision', required=True)
    parser.add_argument('--policy', type=Path, default=ROOT / 'src/arcaverborum/data/release_source_reviews.json')
    args = parser.parse_args()
    result = build(args.root, args.output, args.date, args.policy, data_revision=args.data_revision)
    keys = ['collection', 'lexical_records', 'constructions_with_included_rows', 'sources']
    print(json.dumps({k: result[k] for k in keys}, indent=2))
