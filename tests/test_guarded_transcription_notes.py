"""Attaching historical source context cannot silently follow changed evidence."""

import pandas as pd
import pytest

from arcaverborum.supplements import evidence_hash
from arcaverborum.variety import _apply_transcription_overrides


def test_guarded_context_preserves_lexical_evidence_and_rejects_drift():
    row = dict(ID='ids_elamite_1', Dataset='idssegmented', Language_ID='elamite',
               Glottocode='elam1237', Parameter_ID='p1', Value='AchE ba-at (?)-ir',
               Form='ba-at_-ir', Segments='b a + a t + i r', Comment='', Source='EW')
    override = dict(source_form_id=row['ID'], expected_evidence_sha256=evidence_hash(row),
                    Comment='Original IDS: AchE; EW111 and499; uncertainty retained.')
    result = _apply_transcription_overrides(pd.DataFrame([row]), pd.DataFrame([override])).iloc[0]
    assert result.Form == row['Form'] and result.Value == row['Value']
    assert result.Segments == row['Segments']
    assert result.Comment == override['Comment']
    for key, value in [('Value', 'ME different word'), ('Form', 'different'), ('Comment', 'new source context')]:
        with pytest.raises(ValueError, match='evidence changed'):
            _apply_transcription_overrides(pd.DataFrame([{**row, key: value}]), pd.DataFrame([override]))
    with pytest.raises(ValueError, match='exact source form'):
        _apply_transcription_overrides(pd.DataFrame([row]), pd.DataFrame([{**override, 'source_form_id': ''}]))
