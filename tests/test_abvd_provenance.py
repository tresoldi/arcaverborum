"""Contribution evidence survives the compact source intake."""
import pandas as pd

from arcaverborum.sources.abvd_provenance import preserve


def test_preserves_qualifiers_without_inventing_individual_citation():
    raw = pd.DataFrame([
        dict(Contribution_ID='255', Cognacy_Comment='uncertain', Loan_Raw='possibly',
             Source='', Comment='original'),
        dict(Contribution_ID='819', Cognacy_Comment='', Loan_Raw='', Source='Author2020', Comment=''),
    ])
    result = preserve(raw)
    assert raw.iloc[0].Source == ''
    assert result.iloc[0].Source == 'Greenhilletal2008'
    assert 'Dataset-level citation only' in result.iloc[0].Comment
    assert 'language.php?id=255' in result.iloc[0].Comment
    assert 'uncertain' in result.iloc[0].Comment and 'possibly' in result.iloc[0].Comment
    assert result.iloc[0].Comment.startswith('original; ')
    assert result.iloc[1].Source == 'Author2020'
    assert 'citation_scope' not in result.iloc[1].Comment


def test_raw_numeric_labels_do_not_create_cross_meaning_cognate_sets():
    from arcaverborum.ingest import _merge_cognates

    raw = pd.DataFrame([
        dict(ID='hand', Contribution_ID='1', Cognacy='1,64', Source='Book', Comment=''),
        dict(ID='eye', Contribution_ID='1', Cognacy='1', Source='Book', Comment=''),
    ])
    forms = preserve(raw, use_cognate_table=True)
    cognates = pd.DataFrame([
        dict(Form_ID='hand', Cognateset_ID='abvd2026_hand-1'),
        dict(Form_ID='hand', Cognateset_ID='abvd2026_hand-64'),
        dict(Form_ID='eye', Cognateset_ID='abvd2026_eye-1'),
    ])
    merged = _merge_cognates(forms, cognates, 'abvd2026')
    assert merged.iloc[0].Cognacy == 'abvd2026_hand-1;abvd2026_hand-64'
    assert merged.iloc[1].Cognacy == 'abvd2026_eye-1'
    assert set(merged.iloc[0].Cognacy.split(';')).isdisjoint(merged.iloc[1].Cognacy.split(';'))
    assert '"Cognacy_Raw": "1,64"' in merged.iloc[0].Comment
    assert raw.iloc[0].Cognacy == '1,64'


def test_unmatched_structured_rows_do_not_erase_existing_uncertainty():
    from arcaverborum.ingest import _merge_cognates
    raw = pd.DataFrame([dict(ID='one', Cognacy='', Doubt='true', Alignment='original'),
                        dict(ID='two', Cognacy='', Doubt='', Alignment='')])
    judgments = pd.DataFrame([dict(Form_ID='two', Cognateset_ID='source_hand-1', Doubt='false', Alignment='a')])
    result = _merge_cognates(raw, judgments, 'source')
    assert result.iloc[0].Doubt == 'true' and result.iloc[0].Alignment == 'original'
    assert result.iloc[1].Doubt == 'false'
