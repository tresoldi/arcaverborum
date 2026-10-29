from arcaverborum.research_evidence import annotate, evidence_state, phonological_marks, representation_basis


def form(source, status='source', segments='a', ipa='', cid='phy-water'):
    return dict(transcription_source=source, Segments_Source=status, Segments=segments,
                raw_ipa=ipa, concept_id=cid)


def test_residual_coverage_is_not_independent_confirmation():
    gled, wikt = form('gled'), form('wiktionary', segments='ãː', ipa='/ˈãː/')
    state = evidence_state([gled, wikt], 'wiktionary')
    assert annotate(gled, 'wiktionary', state)['evidence_role'] == 'legacy_gled_overlap'
    assert annotate(wikt, 'wiktionary', state)['preferred_source'] == 'wiktionary'
    assert annotate(gled, 'wiktionary', state)['gled_dependence'] == 'overlap'
    residual = annotate(gled, 'wiktionary', evidence_state([gled], 'wiktionary'))
    assert residual['preferred_source'] == ''
    assert residual['evidence_role'] == 'legacy_gled_residual'
    assert residual['gled_dependence'] == 'gled_only'


def test_no_automatic_source_ranking_or_written_pronunciation():
    written, supplied = form('wiktionary', 'unclean'), form('gled')
    state = evidence_state([written, supplied], 'wiktionary')
    assert annotate(written, 'wiktionary', state)['preferred_source'] == ''
    assert annotate(written, 'wiktionary', state)['evidence_role'] == 'written_or_unresolved'
    assert 'ASJP-derived' in representation_basis(supplied)
    assert 'ASJP-derived' in representation_basis(form('gled', 'unclean'))
    assert 'profile' in representation_basis(form('dictionary', 'profile'))
    assert 'supplied IPA' in representation_basis(form('wiktionary', ipa='/a/'))


def test_observed_marks_are_not_inferred_from_absence_or_spelling():
    assert phonological_marks(form('gled', segments='ŋ a')) == ''
    assert phonological_marks(form('conversion', segments='a²¹')) == 'pitch_or_accent'
    assert phonological_marks(form('wiktionary', 'unclean', segments='ãː')) == ''
    marked = phonological_marks(form('wiktionary', segments='ãː á bʱ', ipa='/ˈãː/')).split(';')
    assert set(marked) == {'quantity', 'nasalization', 'pitch_or_accent', 'stress', 'laryngeal_or_aspiration'}
