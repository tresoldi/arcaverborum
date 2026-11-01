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


def test_reading_policy_does_not_infer_ipa_from_restored_spelling():
    row = dict(ID='hg_1', Dataset='huntergatherer', Language_ID='hg',
               Value="dũhũ'ã", Form='dũhũ', Segments='d u h u', Comment='')
    decision = dict(source_form_id='hg_1', expected_evidence_sha256=evidence_hash(row),
                    Form=row['Value'], transcription_policy='orthographic_only')
    untouched = dict(row, ID='hg_2')
    result = _apply_transcription_overrides(pd.DataFrame([row, untouched]), pd.DataFrame([decision]))
    assert result.iloc[0].Form == row['Value']
    assert result.iloc[0].Segments == '' and result.iloc[0]._orthographic_only
    assert not result.iloc[1]._orthographic_only
    assert result.iloc[1].Segments == untouched['Segments']
    with pytest.raises(ValueError, match='guarded source evidence'):
        _apply_transcription_overrides(pd.DataFrame([row]),
            pd.DataFrame([decision | dict(expected_evidence_sha256='')]))
    with pytest.raises(ValueError, match='cannot supply phonetic'):
        _apply_transcription_overrides(pd.DataFrame([row]),
            pd.DataFrame([decision | dict(Segments='d u')]))


def test_supplied_phonemic_override_preserves_raw_contrasts_and_checks_derivation():
    from arcaverborum.sources.wiktionary.pronunciations import ipa_segments

    row = dict(ID='hg_1', Dataset='huntergatherer', Language_ID='hg',
               Value="ko'ojélaji", Form='ko', Segments='k o', Comment='')
    raw = 'koʔohélahi'
    decision = dict(source_form_id='hg_1', expected_evidence_sha256=evidence_hash(row),
                    Form=row['Value'], transcription_policy='supplied_phonemic',
                    raw_ipa=raw, Segments=ipa_segments(raw))
    result = _apply_transcription_overrides(pd.DataFrame([row]), pd.DataFrame([decision])).iloc[0]
    assert result._raw_ipa == raw and result.Segments == ipa_segments(raw)
    assert result.Value == row['Value'] and not result._orthographic_only
    with pytest.raises(ValueError, match='does not reproduce'):
        _apply_transcription_overrides(pd.DataFrame([row]),
            pd.DataFrame([decision | dict(Segments='k o')]))
