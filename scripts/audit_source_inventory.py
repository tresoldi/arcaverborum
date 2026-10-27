"""Report public Lexibank repository inventory and screened language coverage.

Use cached public snapshots by default; --fetch refreshes repository metadata
and eight screened language tables. This never edits datasets.csv, accepted
choices, or active intake. New Glottocodes are identity-review candidates,
not verified independent varieties; repository names also include software.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import date
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]
SCREENED = ('lindseypahotuririver', 'rutulbasiclexicon', 'amazonianvoices', 'berrywestpapuan',
            'barlowlote', 'barlowkilliantomoip', 'abvdoceanic', 'seabor')
QUERY = 'org:lexibank archived:false'


def fetch(cache: Path) -> dict:
    repositories = []
    page = 1
    while True:
        response = requests.get('https://api.github.com/search/repositories',
                                params=dict(q=QUERY, per_page=100, page=page), timeout=30)
        response.raise_for_status()
        data = response.json()
        if data.get('incomplete_results') or data['total_count'] > 1000:
            raise ValueError('Repository search is incomplete')
        repositories.extend(dict(name=r['name'], url=r['html_url'], branch=r['default_branch'],
                                 full_name=r['full_name']) for r in data['items'])
        if len(data['items']) < 100:
            break
        page += 1
    snapshot = dict(checked_at=date.today().isoformat(), query=QUERY, repositories=repositories)
    cache.mkdir(parents=True, exist_ok=True)
    for repo in repositories:
        if repo['name'] in SCREENED:
            url = f"https://raw.githubusercontent.com/{repo['full_name']}/{repo['branch']}/cldf/languages.csv"
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            (cache / (repo['name'] + '-languages.csv')).write_bytes(response.content)
    (cache / 'lexibank-repositories.json').write_text(json.dumps(snapshot, indent=2) + '\n')
    return snapshot


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--fetch', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    cache = root / 'raw/curation/source-inventory'
    snapshot = fetch(cache) if args.fetch else json.loads((cache / 'lexibank-repositories.json').read_text())
    with (root / 'datasets.csv').open() as f:
        registry = {r['NAME']: r for r in csv.DictReader(f)}
    accepted = {}
    for path in (root / 'varieties').glob('*/config.yaml'):
        config = yaml.safe_load(path.read_text())
        for gc in {config['glottocode'], config['sources'].get('source_glottocode', '')} - {''}:
            accepted.setdefault(gc, []).append(config)
    rows = []
    for repo in sorted(snapshot['repositories'], key=lambda r: r['name']):
        name = repo['name']
        registered = registry.get(name)
        languages = cache / (name + '-languages.csv')
        members = []
        if languages.exists():
            with languages.open() as f:
                members = list(csv.DictReader(f))
        gcs = {r.get('Glottocode', '') for r in members} - {''}
        novel = gcs - accepted.keys()
        gled = {gc for gc in gcs if any(c['sources']['transcription'] == 'gled' for c in accepted.get(gc, []))}
        status = 'not_registered'
        if registered:
            status = ('registered' if registered['URL'].removesuffix('.git').lower() == repo['url'].lower()
                      else 'name_registered_other_repository')
        blob = ''
        if languages.exists():
            content = languages.read_bytes()
            blob = hashlib.sha1(b'blob ' + str(len(content)).encode() + b'\0' + content).hexdigest()
        rows.append(dict(snapshot_date=snapshot['checked_at'], dataset=name, repository=repo['url'],
                         branch=repo['branch'], registration=status,
                         registered_url=registered['URL'] if registered else '',
                         metadata_screened=bool(members), members=len(members) if members else '',
                         distinct_source_glottocodes=len(gcs) if members else '',
                         novel_glottocodes=';'.join(sorted(novel)), gled_glottocodes=';'.join(sorted(gled)),
                         language_table_blob=blob,
                         note='Counts describe source identifiers, not reviewed dialect independence or IPA quality.'))
    output = args.output or root / 'output/report/source_inventory.csv'
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows)} repositories; {sum(r['metadata_screened'] for r in rows)} language tables screened; "
          f"{sum(r['registration'] == 'not_registered' for r in rows)} unregistered names (including non-datasets)")


if __name__ == '__main__':
    main()
