"""Original phonemic cells and reconstructed notation must survive scoped extraction."""
import json

import pytest

from arcaverborum.sources import american_evidence as american


def hgn():
    native = dict(id='122', name='Roçado', tables={'basic': dict(
        header=['English', 'Orthographic Form', 'Phonemicized Form', 'General Notes'],
        rows=[[['/lexical/feature/1', 'bone'], '', 'kɨ̰ːʔ', 'Source context']])},
        **{'Data Sources': 'Original author'})
    row = dict(zip(native['tables']['basic']['header'], native['tables']['basic']['rows'][0]))
    evidence = dict(native_row=row, member_metadata={k: v for k, v in native.items() if k != 'tables'})
    review = dict(member='122', member_name='Roçado', table='basic', row_index='0', feature='/lexical/feature/1',
                  Form='kɨ̰ːʔ', source_sense='bone', native_sha256=american.digest(evidence), rationale='Reviewed')
    return native, review


def spec(kind):
    return dict(kind=kind, version='frozen', citation='Original', genealogy='Same original tradition')


def test_phonemic_only_reading_keeps_length_phonation_and_context():
    native, review = hgn()
    form, segments, evidence = american.extract(spec('hgn_phonemic'), json.dumps(native).encode(), review)
    assert form == 'kɨ̰ːʔ' and 'ɨ̰ː' in segments
    assert evidence['native_row']['General Notes'] == 'Source context'
    assert evidence['reading_basis'] == 'source_reported_phonemic_citation'
    assert evidence['member_metadata']['Data Sources'] == 'Original author'


@pytest.mark.parametrize('change', ['member', 'header', 'note', 'feature', 'spelling', 'alternatives'])
def test_hgn_drift_and_unreviewed_alternatives_fail_closed(change):
    native, review = hgn()
    if change == 'member':
        native['id'] = '121'
    elif change == 'header':
        native['tables']['basic']['header'].append('shifted')
    elif change == 'note':
        native['tables']['basic']['rows'][0][-1] = 'Different context'
    elif change == 'feature':
        review['feature'] = '/lexical/feature/2'
    elif change == 'spelling':
        native['tables']['basic']['rows'][0][1] = 'written'
    else:
        native['tables']['basic']['rows'][0][2] = 'kɨ̰ːʔ, other'
    with pytest.raises(ValueError):
        american.extract(spec('hgn_phonemic'), json.dumps(native).encode(), review)


def test_reconstruction_keeps_star_boundary_and_uncertainty_without_ipa():
    row = dict(FORM='*-aV ~ *-b', Gloss='water')
    review = dict(row_index='0', Form=row['FORM'], source_sense='water', authority='Compiler, edition uncertain',
                  member='ProtoX', member_name='Proto-X', rationale='Written hypothesis only')
    review['native_sha256'] = american.digest(dict(native_row=row, reconstruction=True,
                                                  authority=review['authority'], scope='Proto-X'))
    payload = b'FORM,Gloss\n*-aV ~ *-b,water\n'
    form, segments, evidence = american.extract(spec('reconstruction_csv'), payload, review)
    assert form == row['FORM'] and not segments
    assert evidence['reconstruction'] is True
    assert evidence['reading_basis'] == 'source_reported_reconstruction'
    with pytest.raises(ValueError):
        american.extract(spec('reconstruction_csv'), b'FORM,Gloss\naV,water\n', review)
