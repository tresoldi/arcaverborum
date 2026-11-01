"""Stage the complete pinned Mongolic vocabulary edition with original notation."""
import argparse
import csv
import hashlib
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def entries(payload, *, expected_entries=921):
    blocks = re.findall(r'<li>\s*<br>\s*<div id="mon">.*?</ul></li>', payload.decode('utf-8'), re.S)
    if len(blocks) != expected_entries:
        raise ValueError('Mongolic edition entry inventory changed')
    for ordinal, block in enumerate(blocks, 1):
        match = re.search(r'<em>\s*Eng\.\s*</em>(.*?)</div>', block, re.S)
        if not match:
            raise ValueError('Missing original English sense')
        sense = html.unescape(re.sub('<[^>]+>', '', match[1])).strip()
        forms = re.findall(r'<em>\s*([^<]+?)\s*</em>\s*<b>(.*?)</b>', block, re.S)
        cells = [(label.strip(), html.unescape(re.sub('<[^>]+>', '', value)).strip()) for label, value in forms]
        if len({label for label, _ in cells}) != len(cells) or len(cells) != 14:
            raise ValueError('Incomplete/duplicated native member inventory')
        number = re.search(r';\s*(\d+|xx|--)\s*</li></ul></li>$', block)
        if not number:
            raise ValueError('Missing native questionnaire reference')
        header = re.search(r'<b>(.*?)</b>\s*\[([^]]+)\]', block, re.S)
        if not header:
            raise ValueError('Missing original reference lemma/POS')
        yield dict(ordinal=ordinal, sense=sense, questionnaire=number[1], cells=cells,
                   reference_lemma=html.unescape(header[1]).strip(), pos=header[2].strip(),
                   native_html=block, native_sha256=hashlib.sha256(block.encode()).hexdigest())


def stage(root, output, *, fetch=False):
    if output == root / 'intake' or root / 'intake' in output.parents:
        raise ValueError('Stage outside active intake')
    spec = json.loads((root / 'src/arcaverborum/data/regional/mongolicbv2026.json').read_text())
    blobs = {}
    for name, resource in spec['resources'].items():
        path = root / 'raw/curation' / resource['path']
        if fetch and not path.exists():
            import requests
            response = requests.get(resource['url'], timeout=90)
            response.raise_for_status()
            if hashlib.sha256(response.content).hexdigest() != resource['sha256']:
                raise ValueError('Downloaded Mongolic edition differs from pinned bytes')
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(response.content)
        body = path.read_bytes()
        if hashlib.sha256(body).hexdigest() != resource['sha256']:
            raise ValueError('Pinned Mongolic source changed')
        blobs[name] = body
    output.mkdir(parents=True, exist_ok=True)
    source = spec['dataset']
    parsed = list(entries(blobs['mongolic-20260325.html']))
    labels = sorted({label for entry in parsed for label, _ in entry['cells']})
    codes = {label: re.sub(r'[^a-z0-9]+', '', label.lower()) for label in labels}
    if len(set(codes.values())) != len(labels):
        raise ValueError('Native member code collision')
    forms, missing, parameters = [], [], []
    for entry in parsed:
        pid = f'{source}_entry{entry["ordinal"]:04}'
        parameters.append(dict(ID=pid, Dataset=source, Name=entry['sense'], Concepticon_ID='', Concepticon_Gloss=''))
        for label, value in entry['cells']:
            if value in {'', '--', '—', '―'}:
                missing.append(dict(entry=entry['ordinal'], member=label, original=value))
                continue
            identity = spec['identity_review'].get(label, {})
            native = dict(original=entry, member=label, original_form=value,
                          reading_policy='Literal source notation; no IPA inferred',
                          identity_status='reviewed' if identity else 'unreviewed')
            forms.append(dict(ID=f'{source}_{codes[label]}-entry{entry["ordinal"]:04}', Dataset=source,
                              Local_ID=f'{label}:{entry["ordinal"]}', Language_ID=source+'_'+codes[label],
                              Parameter_ID=pid, Value=value, Form=value, Segments='',
                              Comment=json.dumps(native, ensure_ascii=False, sort_keys=True),
                              Source=source+'_Yamakoshi',
                              Glottocode=identity.get('glottocode',''), Glottolog_Name=identity.get('name','')))
    languages = [dict(ID=source+'_'+codes[label], Dataset=source,
                      Name=spec['identity_review'].get(label,{}).get('native_name',label),
                      Glottocode=spec['identity_review'].get(label,{}).get('glottocode',''),
                      ISO639P3code=spec['identity_review'].get(label,{}).get('iso639p3',''),
                      Macroarea='Eurasia', Family='Mongolic-Khitan',
                      Remark='Original member '+label+'; no automatic phonetic conversion') for label in labels]
    metadata = [dict(Dataset=source, Title='Comparative dictionary of Mongolic languages', Citation=spec['citation'],
                     URL=spec['url'], License=spec['license'], CLDF_Module='Wordlist',
                     Repository_Version=spec['version'], Form_Count=len(forms), Language_Count=len(labels),
                     Parameter_Count=len(parsed), Has_Cognates='False')]
    for name, rows in [('forms.csv',forms),('languages.csv',languages),('parameters_raw.csv',parameters),
                       ('metadata.csv',metadata)]:
        with (root / 'intake/lexibank' / name).open() as f:
            fields = next(csv.reader(f))
        with (output / name).open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=fields,lineterminator='\n')
            writer.writeheader()
            for row in rows:
                writer.writerow({key:row.get(key,'') for key in fields})
    (output / 'sources.bib').write_text('@misc{mongolicbv2026_Yamakoshi,\n author={Yamakoshi, Yasuhiro},\n '
        'title={Database of Basic Vocabulary in Mongolic Languages},\n year={2026},\n '
        'url={https://mongolicbv.aa-ken.jp/}\n}\n')
    summary=dict(entries=len(parsed),native_cells=len(parsed)*len(labels),members=len(labels),forms=len(forms),
                 missing_cells=len(missing),source=spec)
    (output / 'source-proof.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n')
    (output / 'missing-cells.json').write_text(json.dumps(missing,indent=2,ensure_ascii=False)+'\n')
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--fetch', action='store_true', help='Fetch missing pinned original resources')
    args=parser.parse_args()
    print(json.dumps(stage(ROOT,args.output.resolve(),fetch=args.fetch),indent=2,ensure_ascii=False))
