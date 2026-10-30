"""Pinned CLDF acquisition retaining complete native rows and upstream conversions."""
import csv
import hashlib
import io
import json
import tarfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = ROOT / 'src/arcaverborum/data/reviewed_cldf_sources.json'


def materialize(raw_root, *, dataset, download=False):
    spec = next(s for s in json.loads(MANIFEST.read_text()) if s['dataset'] == dataset)
    dest = raw_root / 'lexibank' / dataset
    dest.mkdir(parents=True, exist_ok=True)
    archive = dest / 'source.tar.gz'
    if download or not archive.exists():
        data = urllib.request.urlopen(spec['url'], timeout=90).read()
    else:
        data = archive.read_bytes()
    if hashlib.sha256(data).hexdigest() != spec['sha256']:
        raise ValueError('Pinned CLDF archive changed: ' + dataset)
    archive.write_bytes(data)
    native = {}
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as handle:
        for member in handle.getmembers():
            parts = Path(member.name).parts[1:]
            if member.isfile() and parts and '..' not in parts:
                native['/'.join(parts)] = handle.extractfile(member).read()
    metadata = json.loads(native['cldf/cldf-metadata.json'])
    declared = metadata.get('dc:license', '')
    if declared and declared != spec['license']:
        raise ValueError('Unexpected source license')
    # Heath declares the terms in the repository LICENSE rather than CLDF metadata.
    if not declared and hashlib.sha256(native['LICENSE']).hexdigest() != spec['license_file_sha256']:
        raise ValueError('Repository license changed')
    metadata['dc:license'] = spec['license']
    metadata['prov:wasDerivedFrom'] = [{'dc:title': 'Repository', 'dc:created': spec['sha256']}]
    cldf = dest / 'cldf'
    cldf.mkdir(exist_ok=True)
    for path, content in native.items():
        if path.startswith('cldf/') and len(Path(path).parts) == 2:
            (cldf / Path(path).name).write_bytes(content)
    def rows(name):
        return list(csv.DictReader(io.StringIO(native['cldf/' + name].decode('utf-8'))))
    forms = rows('forms.csv')
    languages = {r['ID']: r for r in rows('languages.csv')}
    parameters = {r['ID']: r for r in rows('parameters.csv')}
    for row in forms:
        evidence = dict(native_form=dict(row), native_language=languages[row['Language_ID']],
                        native_parameter=parameters[row['Parameter_ID']], archive_url=spec['url'],
                        archive_sha256=spec['sha256'], reading_basis='upstream_profile_conversion',
                        genealogy=spec['genealogy'], license=spec['license'])
        row['Comment'] = json.dumps(evidence, ensure_ascii=False, sort_keys=True)
    with (cldf / 'forms.csv').open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(forms[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(forms)
    (cldf / 'cldf-metadata.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n')
    return dict(dataset=dataset, forms=len(forms))
