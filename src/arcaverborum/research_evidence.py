"""Descriptive evidence annotations; never score or infer missing phonology."""
from __future__ import annotations

import unicodedata

SUPPORTED = {'source', 'profile'}


def representation_basis(row):
    if row['transcription_source'] == 'gled':
        return 'ASJP-derived; normalization cannot restore omitted contrasts'
    if row['Segments_Source'] not in SUPPORTED:
        return 'written_or_unresolved'
    if row['Segments_Source'] == 'profile':
        return 'source-scoped profile; consult original reading authority'
    if row.get('raw_ipa'):
        return 'supplied IPA; retained notation is not independent verification'
    return 'upstream segments/conversion; consult original notation'


def phonological_marks(row):
    """Observe notation, not a language's contrast inventory or completeness."""
    if row['Segments_Source'] not in SUPPORTED:
        return ''
    text = unicodedata.normalize('NFD', row.get('Segments', '') + row.get('raw_ipa', ''))
    marks = []
    for label, characters in [
        ('quantity', 'ːˑ'), ('nasalization', '\u0303'),
        ('pitch_or_accent', '˥˦˧˨˩¹²³⁴⁵\u0300\u0301\u0302\u030c'),
        ('stress', 'ˈˌ'), ('laryngeal_or_aspiration', 'ʰʱ\u0324\u0330ˀʼ'),
    ]:
        if any(c in text for c in characters):
            marks.append(label)
    return ';'.join(marks)


def update_state(state, row, primary):
    if row['concept_id'] and row['Segments_Source'] in SUPPORTED:
        state[0] |= row['transcription_source'] == primary
        state[1] |= row['transcription_source'] == 'gled'
        state[2] |= row['transcription_source'] != 'gled'
    return state


def evidence_state(rows, primary):
    state = [False, False, False]
    for row in rows:
        update_state(state, row, primary)
    return tuple(state)


def annotate(row, primary, state):
    preferred, gled, other = state
    source = row['transcription_source']
    if row['Segments_Source'] not in SUPPORTED:
        role = 'written_or_unresolved'
    elif not row['concept_id']:
        role = 'unmapped_supported'
    elif source == primary:
        role = 'configured_primary_supported'
    elif source == 'gled':
        role = 'legacy_gled_overlap' if preferred else 'legacy_gled_residual'
    else:
        role = 'supported_alternative'
    return dict(
        preferred_source=primary if preferred else '', evidence_role=role,
        gled_dependence='gled_only' if gled and not other else 'overlap' if gled else 'none',
        representation_basis=representation_basis(row), phonological_marks=phonological_marks(row),
    )
