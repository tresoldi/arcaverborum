"""Stream complete non-English editions, retaining native entries without sense guessing."""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
from pathlib import Path

from arcaverborum.glottolog import load_glottolog, resolve_language
from arcaverborum.ingest import FORM_COLS, LANG_COLS, META_COLS, PARAM_COLS
from arcaverborum.sources.wiktionary.langmap import ISO639_1_TO_3

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = ROOT / 'src/arcaverborum/data/wiktionary_editions.json'


def stage(edition: str, archive: Path, output: Path):
    """One intake row per native entry/POS block; all senses and sounds stay native.

    Redirects and nonlexical objects remain in the pinned archive with measured
    counts. No translation-table targets, inferred IPA, cognates or concept IDs
    are manufactured. Generic source language codes do not certify a local lect.
    """
    spec = next(s for s in json.loads(MANIFEST.read_text()) if s['edition'] == edition)
    sha = hashlib.file_digest(archive.open('rb'), 'sha256').hexdigest()
    if sha != spec['sha256']:
        raise ValueError('Pinned Wiktionary edition changed')
    source = spec['dataset']
    output.mkdir(parents=True, exist_ok=True)
    glottolog = load_glottolog()
    languages, counts = {}, dict(native_objects=0, lexical_entries=0, nonlexical_objects=0, native_senses=0)
    form_fields = list(FORM_COLS)
    parameter_fields = list(PARAM_COLS)
    with ((output / 'forms.csv').open('w', newline='') as forms,
          (output / 'parameters_raw.csv').open('w', newline='') as parameters,
          gzip.open(archive, 'rt', encoding='utf-8') as entries):
        fw = csv.DictWriter(forms, fieldnames=form_fields, lineterminator='\n')
        pw = csv.DictWriter(parameters, fieldnames=parameter_fields, lineterminator='\n')
        fw.writeheader()
        pw.writeheader()
        for line_no, line in enumerate(entries, 1):
            entry = json.loads(line)
            counts['native_objects'] += 1
            if not entry.get('word') or not entry.get('lang_code'):
                counts['nonlexical_objects'] += 1
                continue
            code, name = entry['lang_code'], entry.get('lang', '')
            iso = ISO639_1_TO_3.get(code, code)
            if len(iso) != 3 or not iso.isalpha():
                iso = ''  # Bespoke/proto codes survive natively, never as invented ISO identifiers.
            gc = resolve_language('', iso, glottolog)
            lid = source + '_' + code + '_' + hashlib.sha256(name.encode()).hexdigest()[:12]
            if lid not in languages:
                languages[lid] = dict(ID=lid, Dataset=source, Name=name, ISO639P3code=iso,
                                     Glottocode=gc.glottocode if gc else '', Glottolog_Name=gc.name if gc else name,
                                     Family=gc.family if gc else '', Macroarea=gc.macroarea if gc else '',
                                     Latitude=gc.latitude if gc else '', Longitude=gc.longitude if gc else '',
                                     Remark='Source code/name; exact dialect/stage requires admission review')
            fid = source + '_line-' + str(line_no)
            senses = entry.get('senses', [])
            gloss = '; '.join(g for s in senses for g in s.get('glosses', []))
            evidence = dict(original=entry, archive_line=line_no,
                            native_line_sha256=hashlib.sha256(line.encode()).hexdigest(),
                            source_version=sha, edition=edition, gloss_language=edition, license=spec['license'],
                            source_citation='https://' + edition + '.wiktionary.org/wiki/' + entry['word'],
                            reading_basis='Native sounds preserved separately; no automatic interpretation',
                            source_genealogy='Edition overlap and shared dictionaries are not independent confirmation')
            form = dict(ID=fid, Dataset=source, Local_ID='line-' + str(line_no), Language_ID=lid,
                        Parameter_ID=fid, Value=entry['word'], Form=entry['word'],
                        Comment=json.dumps(evidence, ensure_ascii=False, separators=(',', ':')),
                        Source=source + '_snapshot', Glottocode=gc.glottocode if gc else '',
                        Glottolog_Name=gc.name if gc else name)
            fw.writerow({k: form.get(k, '') for k in form_fields})
            pw.writerow(dict(ID=fid, Dataset=source, Name=gloss, Concepticon_ID='', Concepticon_Gloss=''))
            counts['lexical_entries'] += 1
            counts['native_senses'] += len(senses)
    fields = list(LANG_COLS)
    with (output / 'languages.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows({k: r.get(k, '') for k in fields} for r in languages.values())
    fields = list(META_COLS)
    metadata = dict(Dataset=source, Title=edition + ' Wiktionary complete native entry archive',
                    Citation='Wiktionary contributors; Kaikki/Wiktextract pinned raw edition archive.',
                    URL=spec['url'], License=spec['license'], CLDF_Module='NativeJSONL', Repository_Version=sha,
                    Form_Count=counts['lexical_entries'], Language_Count=len(languages),
                    Parameter_Count=counts['lexical_entries'], Has_Cognates='False')
    with (output / 'metadata.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        writer.writerow({k: metadata.get(k, '') for k in fields})
    (output / 'sources.bib').write_text('@misc{' + source + '_snapshot,\n title = {' + metadata['Title']
                                        + '},\n url = {' + spec['url'] + '},\n note = {SHA256 ' + sha
                                        + '; ' + spec['license'] + '}\n}\n')
    counts['source_members'] = len(languages)
    counts['dataset'] = source
    (output / 'stage-proof.json').write_text(json.dumps(counts, indent=2) + '\n')
    return counts
