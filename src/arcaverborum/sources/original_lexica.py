"""Pinned original lexica with native context; spelling never becomes IPA on import."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import unicodedata
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = ROOT / 'src/arcaverborum/data/original_lexical_sources.json'


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def read(path):
    with path.open() as handle:
        return list(csv.DictReader(handle))


def write(path, rows):
    with path.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def plain_tex(text):
    """Remove only named typographic wrappers; never interpret phonetic symbols."""
    pattern = r'\\(?:pb|textbf|textit|phono|phononb|mbox|spanish|textsc|lsc|textipa|nohyphens)\{([^{}]*)\}'
    while re.search(pattern, text):
        text = re.sub(pattern, lambda m: m[1], text)
    return text.replace(r'\_', '_').replace(r'\%', '%')


def native_records(spec, payloads):
    if spec['kind'] == 'lexirumah':
        return lexirumah_records(spec, payloads)
    if spec['kind'] == 'tuatschin':
        return tuatschin_records(payloads)
    if spec['kind'] == 'reflex_full':
        return reflex_records(spec, payloads)
    if spec['kind'] == 'tex_dictionary':
        return dictionary_records(spec, payloads)
    if spec['kind'] not in {'reviewed_citations', 'reviewed_pdf'}:
        raise ValueError('Unknown original lexical source kind')
    result = []
    for review in read(ROOT / spec['review']):
        if review['decision'] != 'admit':
            continue
        quote = review['raw_quote']
        # PDF page quotations are independently checked by the optional page audit.
        # Transport still pins the complete original PDF, never an OCR surrogate.
        text = (quote if spec['kind'] == 'reviewed_pdf'
                else payloads[review['resource_key']].decode('utf-8'))
        if (not quote or quote not in text or review['Form'] not in plain_tex(quote)
                or review['source_sense'] not in quote):
            raise ValueError('Original citation or literal word/sense changed')
        native = dict(resource_key=review['resource_key'], raw_quote=quote,
                      member=review['member'], Form=review['Form'], source_sense=review['source_sense'])
        if spec['kind'] == 'reviewed_pdf':
            native['pdf_page'] = int(review['pdf_page'])
            if native['pdf_page'] < 1 or not payloads[review['resource_key']].startswith(b'%PDF'):
                raise ValueError('Original PDF citation requires an actual PDF and a page')
        if digest(native) != review['native_sha256']:
            raise ValueError('Original reviewed citation hash mismatch')
        result.append(dict(ID=review['native_id'], member=review['member'], Form=review['Form'],
                           source_sense=review['source_sense'], original=native))
    return result


def tex_arguments(text):
    """Read consecutive balanced arguments; keep inflection and sense fields separate."""
    values, cursor = [], 0
    while cursor < len(text):
        while cursor < len(text) and text[cursor].isspace():
            cursor += 1
        if cursor == len(text) or text[cursor] != '{':
            break
        start, depth = cursor + 1, 1
        cursor += 1
        while cursor < len(text) and depth:
            if text[cursor] in '{}' and text[cursor - 1] != '\\':
                depth += 1 if text[cursor] == '{' else -1
            cursor += 1
        if depth:
            raise ValueError('Unbalanced original dictionary arguments')
        values.append(text[start:cursor - 1])
    return values


def tuatschin_records(payloads):
    text = payloads['dictionary'].decode('utf-8')
    kinds = dict(entry=(1, 2, 3), presententry=(2, 4, 5), plentry=(3, 5, 6),
                 prsptcpentry=(4, 6, 7), onetwoentry=(1, 3, 4), nosyntentry=(1, None, 2),
                 verweis=(None, None, 1))
    matches = list(re.finditer(r'\\(' + '|'.join(kinds) + r')\s*(?=\{)', text))
    result = []
    for ordinal, match in enumerate(matches, 1):
        block = text[match.start():matches[ordinal].start() if ordinal < len(matches) else len(text)]
        args = tex_arguments(block[match.end() - match.start():])
        phonetic, pos, sense = kinds[match[1]]
        incomplete = len(args) <= max(x for x in [phonetic, pos, sense] if x is not None)
        if not args:
            raise ValueError('Original Tuatschin lexical block has no head')
        if incomplete:
            # Preserve malformed native entries, but do not repair a lost brace or
            # move a symbol between pronunciation and gloss without a separate review.
            native = dict(resource_key='dictionary', raw_block=block, macro=match[1], arguments=args,
                          headwords=[args[0]], phonetic=[], POS=[], senses=[], form_kind='parse hold')
            result.append(dict(ID='entry-' + str(ordinal), member='Dictionary', Form=plain_tex(args[0]),
                               source_sense='', original=native))
            continue
        native = dict(resource_key='dictionary', raw_block=block, macro=match[1], arguments=args,
                      headwords=[args[0]], phonetic=[args[phonetic]] if phonetic is not None else [],
                      POS=[args[pos]] if pos is not None else [], senses=[args[sense]],
                      form_kind='crossreference' if match[1] == 'verweis' else 'lexical citation')
        result.append(dict(ID='entry-' + str(ordinal), member='Dictionary', Form=plain_tex(args[0]),
                           source_sense=args[sense], original=native))
    return result


def lexirumah_records(spec, payloads):
    """Preserve the upstream source/profile layers rather than calling them IPA."""
    def table(key):
        return list(csv.DictReader(io.StringIO(payloads[key].decode())))

    lects = {r['ID']: r for r in table('lects')}
    concepts = {r['ID']: r for r in table('concepts')}
    if set(lects) != {m['ID'] for m in spec['members']}:
        raise ValueError('LexiRumah member inventory changed')
    if any(lects[m['ID']]['Glottocode'] != m['Glottocode'] for m in spec['members']):
        raise ValueError('LexiRumah member identity changed')
    result = []
    for row in table('forms'):
        lect, concept = lects[row['Lect_ID']], concepts[row['Concept_ID']]
        native = dict(record=row, lect=lect, concept=concept,
                      reading_basis='upstream_profile_conversion',
                      cognacy='No automatic cognate assignments imported as expert judgments')
        result.append(dict(ID=row['ID'], member=row['Lect_ID'], Form=row['Form'],
                           Value=row['Form_according_to_Source'], Segments=row['Segments'],
                           Source=row['Source'] or 'original', source_sense=concept['English'], original=native))
    return result


def macro_values(text, name):
    """Read balanced TeX arguments without flattening nested lexical information."""
    result = []
    for match in re.finditer(r'\\' + re.escape(name) + r'\{', text):
        start, depth, end = match.end(), 1, match.end()
        while end < len(text) and depth:
            if text[end] in '{}' and (end == 0 or text[end - 1] != '\\'):
                depth += 1 if text[end] == '{' else -1
            end += 1
        if depth:
            raise ValueError('Unbalanced original lexical macro: ' + name)
        result.append(text[start:end - 1])
    return result


def dictionary_records(spec, payloads):
    """Extract head entries, retaining subentries, examples and variants in context."""
    marker, head, gloss, phonetic, pos = {
        'chakali': ('newentry', 'headword', 'definition', 'ipa', 'synpos'),
        'dagaare': ('tbLX', 'tbLX', 'tbGE', 'tbPH', 'tbPS'),
        'beja': ('Blx', 'Blx', 'Bde', None, 'Bps'),
        'cayuga_nouns': ('lexicalunitbracket', 'lexicalunitbracket', 'trs', None, 'synpos'),
    }[spec['format']]
    result = []
    for resource in spec['resources']:
        if not resource.get('lexical'):
            continue
        text = payloads[resource['key']].decode('utf-8')
        # Commented-out entries are not independent dictionary evidence.
        text = re.sub(r'(?m)(?<!\\)%[^\n]*', '', text)
        blocks = re.split(r'(?=\\' + marker + (r'\{' if marker != 'newentry' else r'\b') + ')', text)[1:]
        for ordinal, block in enumerate(blocks, 1):
            heads = macro_values(block, head)
            if not heads:
                raise ValueError('Original lexical block has no headword')
            meanings = macro_values(block, gloss)
            citations = macro_values(block, 'cayuga') if spec['format'] == 'cayuga_nouns' else []
            citations = [citation + re.match(r'[ˀ:]*', block.split('\\cayuga{' + citation + '}', 1)[1])[0]
                         for citation in citations]
            native = dict(resource_key=resource['key'], entry_ordinal=ordinal, raw_block=block,
                          headwords=heads, senses=meanings, POS=macro_values(block, pos),
                          phonetic=macro_values(block, phonetic) if phonetic else [],
                          source_format=spec['format'])
            if spec['format'] == 'cayuga_nouns':
                native['full_citations'] = citations
                native['form_kind'] = 'cited word' if citations else 'lexical stem only'
            result.append(dict(ID=resource['key'] + '-' + str(ordinal), member='Dictionary',
                               Form=plain_tex(citations[0] if citations else heads[0]),
                               source_sense='; '.join(meanings), original=native))
    return result


def reflex_records(spec, payloads):
    """Keep complete selected editions; classification and notation stay explicit."""
    def metadata(key, identity):
        return {r[identity]: r for r in csv.DictReader(io.StringIO(payloads[key].decode()), delimiter='\t')}

    sources = metadata('sources', 'ID')
    languages = metadata('languages', 'id')
    references = metadata('references', 'ID')
    selected = {m['ID']: m for m in spec['members']}
    attribution = {}
    for key, member in selected.items():
        source = sources[key]
        language = languages[source['LANGUE']]
        reference = references[source['BIB']]
        if language['glottocode'] != member['Glottocode']:
            raise ValueError('RefLex original member identity changed')
        attribution[key] = dict(source=source, language=language, reference=reference)
    result = []
    for row in csv.DictReader(io.StringIO(payloads['records'].decode()), delimiter='\t'):
        if row['SOU'] not in selected:
            continue
        native = dict(record=row, attribution=attribution[row['SOU']])
        result.append(dict(ID='reflex-' + row['id'], member=row['SOU'], Form=row['FRM'],
                           source_sense=row['TRA'], original=native))
    return result


def materialize(raw_root, *, dataset, download=False):
    spec = next(s for s in json.loads(MANIFEST.read_text()) if s['dataset'] == dataset)
    root = raw_root / 'lexibank' / dataset
    root.mkdir(parents=True, exist_ok=True)
    payloads = {}
    for resource in spec['resources']:
        name = resource['filename']
        if Path(name).name != name:
            raise ValueError('Original resource requires a local filename')
        path = root / name
        if download:
            response = requests.get(resource['url'], timeout=60)
            response.raise_for_status()
            data = response.content
        else:
            data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != resource['sha256']:
            raise ValueError('Pinned original resource changed: ' + name)
        if download:
            path.write_bytes(data)
        payloads[resource['key']] = data
    records = native_records(spec, payloads)
    members = {m['ID']: m for m in spec['members']}
    forms, parameters, used = [], [], set()
    for record in records:
        if record['ID'] in used or record['member'] not in members:
            raise ValueError('Duplicate identity or unreviewed original member')
        used.add(record['ID'])
        native = record['original']
        evidence = dict(original=native, native_sha256=digest(native), source_version=spec['version'],
                        source_citation=spec['citation'], source_genealogy=spec['genealogy'],
                        license=spec['license'], reading_basis=native.get('reading_basis',
                                                                       'orthographic_transcription_only'))
        forms.append(dict(ID=record['ID'], Language_ID=record['member'], Parameter_ID=record['ID'],
                          Value=record.get('Value', record['Form']), Form=unicodedata.normalize('NFC', record['Form']),
                          Segments=record.get('Segments', ''), Source=record.get('Source', 'original'),
                          Comment=json.dumps(evidence, ensure_ascii=False, sort_keys=True)))
        parameters.append(dict(ID=record['ID'], Name=record['source_sense'], Concepticon_ID='', Concepticon_Gloss=''))
    if not forms:
        raise ValueError('Empty original lexical source')
    languages = [m for m in spec['members'] if m['ID'] in {r['member'] for r in records}]
    cldf = root / 'cldf'
    cldf.mkdir(exist_ok=True)
    term = 'http://cldf.clld.org/v1.0/terms.rdf#'
    props = dict(ID='id', Name='name', Form='form', Value='value', Segments='segments',
                 Language_ID='languageReference', Parameter_ID='parameterReference', Source='source',
                 Comment='comment', Glottocode='glottocode', Concepticon_ID='concepticonReference')
    meta = {'@context': 'http://www.w3.org/ns/csvw', 'dc:conformsTo': term + 'Wordlist',
            'dc:title': spec['name'], 'dc:license': spec['license'], 'dc:bibliographicCitation': spec['citation'],
            'dcat:accessURL': spec['url'], 'dc:source': 'sources.bib',
            'prov:wasDerivedFrom': [{'dc:title': 'Repository', 'dc:created': spec['version']}], 'tables': []}
    for name, rows, kind in [('forms.csv', forms, 'FormTable'), ('parameters.csv', parameters, 'ParameterTable'),
                             ('languages.csv', languages, 'LanguageTable')]:
        write(cldf / name, rows)
        columns = []
        for key in rows[0]:
            col = dict(name=key, datatype='string')
            if key in props:
                col['propertyUrl'] = term + props[key]
            if key in {'Segments', 'Source'}:
                col['separator'] = ' ' if key == 'Segments' else ';'
            columns.append(col)
        meta['tables'].append(dict(url=name, **{'dc:conformsTo': term + kind, 'dc:extent': len(rows)},
                                   tableSchema=dict(columns=columns, primaryKey='ID')))
    (cldf / 'cldf-metadata.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2) + '\n')
    bibliography = payloads.get('bibliography', b'').decode('utf-8')
    (cldf / 'sources.bib').write_text(bibliography + '\n@misc{original,\n title = {' + spec['citation'] + '},\n url = {'
                                    + spec['url'] + '},\n note = {Data license ' + spec['license'] + '}\n}\n')
    return dict(dataset=dataset, forms=len(forms), members=len(languages))
