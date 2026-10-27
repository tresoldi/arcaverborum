"""Shared English-sense corrections, before variety-specific concept overlays.

Raw intake remains unchanged. Name/Concepticon guards detect upstream drift;
consensus evidence is recorded in the authored source-specific rule table.
"""
from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path

RULES = Path(__file__).parent / 'data/wiktionary_sense_overrides.csv'
PARAMETERS = Path(__file__).resolve().parents[2] / 'intake/wiktionary/parameters_raw.csv'


@lru_cache(maxsize=4)
def load_rules(rule_path=RULES, parameter_path=PARAMETERS):
    with parameter_path.open() as f:
        parameters = {r['ID']: r for r in csv.DictReader(f)}
    with rule_path.open() as f:
        rules = list(csv.DictReader(f))
    seen = set()
    for rule in rules:
        pid = rule['Parameter_ID']
        if pid in seen:
            raise ValueError('Duplicate shared sense correction: ' + pid)
        seen.add(pid)
        source = parameters.get(pid, {})
        if (source.get('Name'), source.get('Concepticon_ID')) != (
                rule['expected_source_name'], rule['expected_source_concepticon_id']):
            raise ValueError('Shared sense source changed: ' + pid)
        if rule['action'] not in {'map', 'unmap'} or (rule['action'] == 'map') != bool(rule['concept_id']):
            raise ValueError('Invalid shared sense action: ' + pid)
    return rules


def apply_shared(forms, source):
    if source != 'wiktionary' or forms.empty:
        return forms
    with RULES.open() as f:
        authored = list(csv.DictReader(f))
    present = set(forms['Parameter_ID'])
    if not any(r['Parameter_ID'] in present for r in authored):
        return forms
    rules = load_rules()
    matching = {r['Parameter_ID']: r for r in rules if r['Parameter_ID'] in present}
    if not matching:
        return forms
    result = forms.copy()
    for column, default in [('Concepticon_ID', ''), ('_concept_id_override', ''), ('_concept_mapping_blocked', False)]:
        if column not in result:
            result[column] = default
    for pid, rule in matching.items():
        mask = result['Parameter_ID'] == pid
        result.loc[mask, 'Concepticon_ID'] = rule['Concepticon_ID']
        result.loc[mask, '_concept_id_override'] = rule['concept_id']
        result.loc[mask, '_concept_mapping_blocked'] = rule['action'] == 'unmap'
    return result
