"""Guarded retention of previously emitted native evidence during source migration.

This is not a transcription-admission route. Both raw evidence and a frozen prior
output are pinned; normalization, identity, mappings and native cognacy must agree.
Qualified/profile/overridden readings retain their original admission mechanisms.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re

from arcaverborum.forms_schema import FORMS_OUT_FIELDS
from arcaverborum.intake_db import IntakeDB
from arcaverborum.phonology import normalize_segments
from arcaverborum.supplements import evidence_hash


def previous_output_hash(row):
    payload = {key: str(row.get(key, '') or '') for key in FORMS_OUT_FIELDS}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def preserved_rows(custom_dir, intake, av_id, glottocode, param_index, concepts):
    path = custom_dir / 'preserved_forms.csv'
    if not path.exists():
        return []
    with path.open() as handle:
        snapshots = list(csv.DictReader(handle))
    result, seen = [], set()
    for prior in snapshots:
        source = prior['transcription_source']
        gc = prior['Glottocode'].strip().lower()
        if prior['av_id'] != av_id or gc != glottocode.strip().lower() or not prior['preservation_rationale']:
            raise ValueError('Preserved output identity or rationale changed')
        if previous_output_hash(prior) != prior['previous_output_sha256']:
            raise ValueError('Preserved previous output changed')
        identity = source, prior['source_form_id'], prior['source_pronunciation_id']
        if identity in seen:
            raise ValueError('Duplicate preserved output')
        seen.add(identity)
        if isinstance(intake, IntakeDB):
            frame = intake.slice(gc, source)
        else:
            frame = intake[intake['Glottocode'].str.lower().eq(gc) & intake['Dataset'].eq(source)]
        matches = frame[frame['ID'].eq(prior['source_form_id'])]
        if len(matches) != 1:
            raise ValueError('Preserved native source missing or duplicated')
        raw = matches.iloc[0].to_dict()
        if evidence_hash(raw) != prior['evidence_sha256']:
            raise ValueError('Preserved native evidence changed')
        if (raw['Language_ID'], raw['Parameter_ID']) != (prior['source_language_id'], prior['source_parameter_id']):
            raise ValueError('Preserved source member/parameter changed')
        raw_cid = raw.get('Concepticon_ID') or param_index.get(raw['Parameter_ID'], ('', ''))[0]
        if raw_cid != prior['expected_source_concepticon_id']:
            raise ValueError('Preserved source concept changed')
        cid = prior['concept_id']
        if cid:
            if cid not in concepts or concepts[cid] != prior['Concepticon_ID']:
                raise ValueError('Preserved mapped concept changed')
        elif prior['Concepticon_ID'] or prior['concept_label']:
            raise ValueError('Unmapped preserved evidence must stay unmapped')
        for field in ['Form', 'Value', 'Cognacy', 'Alignment', 'Morpheme_Index', 'Segment_Slice',
                      'Doubt', 'Cognate_Detection_Method', 'Cognate_Source', 'Loan']:
            if str(raw.get(field, '') or '') != prior[field]:
                raise ValueError('Preserved native field changed: ' + field)
        if str(raw.get('Source', '') or '') != prior['bibtex_key'] or prior['cognate_source'] != source:
            raise ValueError('Preservation cannot transfer source cognacy or bibliography')
        if str(raw.get('Comment', '') or '') not in prior['Comment']:
            raise ValueError('Preserved original comment lost')
        segments, status = normalize_segments(raw.get('Segments', ''), raw.get('Form') or raw.get('Value', ''))
        if (segments, status) != (prior['Segments'], prior['Segments_Source']):
            raise ValueError('Preservation cannot reinterpret or upgrade an earlier reading')
        match = (re.search(r'Pronunciation IPA ([^;]+);', str(raw.get('Comment', '')))
                 if source == 'wiktionary' else None)
        ipa = match[1] if match else ''
        pid = ('ipa-' + hashlib.sha256('|'.join([raw['Language_ID'], raw['Form'], ipa]).encode()).hexdigest()[:16]
               if ipa else '')
        if (prior['raw_ipa'], prior['pronunciation_tags'], prior['source_pronunciation_id']) != (ipa, '', pid):
            raise ValueError('Qualified pronunciation retention needs its original guarded admission')
        result.append({field: prior[field] for field in FORMS_OUT_FIELDS})
    return result
