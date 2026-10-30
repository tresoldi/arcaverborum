"""Original spelling and quotation evidence must not turn into inferred pronunciation."""
import csv

import pytest

from arcaverborum.sources import original_lexica as source


def review(tmp_path, monkeypatch, **changes):
    quote = r'Original <q\textbf{i}ri> ‘tree’; other witness <qere>.'
    row = dict(native_id='M1', resource_key='chapter', member='M', Form='qiri', source_sense='tree',
               raw_quote=quote, decision='admit')
    native = {k: row[k] for k in ['resource_key', 'raw_quote', 'member', 'Form', 'source_sense']}
    row['native_sha256'] = source.digest(native)
    row.update(changes)
    path = tmp_path / 'review.csv'
    with path.open('w') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)
    monkeypatch.setattr(source, 'ROOT', tmp_path)
    return dict(kind='reviewed_citations', review='review.csv'), {'chapter': quote.encode()}


def test_exact_quotation_keeps_alternative_and_spelling(tmp_path, monkeypatch):
    spec, payloads = review(tmp_path, monkeypatch)
    rows = source.native_records(spec, payloads)
    assert rows[0]['Form'] == 'qiri'
    assert '<qere>' in rows[0]['original']['raw_quote']
    assert 'Segments' not in rows[0]


@pytest.mark.parametrize('changes', [dict(Form='quri'), dict(source_sense='root'),
                                     dict(native_sha256='changed'), dict(raw_quote='Invented qiri tree')])
def test_unreviewed_citation_changes_fail(tmp_path, monkeypatch, changes):
    spec, payloads = review(tmp_path, monkeypatch, **changes)
    with pytest.raises(ValueError):
        source.native_records(spec, payloads)


def test_typography_is_removed_without_phonetic_conversion():
    assert source.plain_tex(r'\phono{\pb{sh}imi}') == 'shimi'
    assert source.plain_tex(r'\unknown{sh}') == r'\unknown{sh}'


def test_balanced_arguments_keep_nested_translation_and_variants():
    assert source.tex_arguments(r'{word}{\textit{meaning {nested}}}{a / b}') == [
        'word', r'\textit{meaning {nested}}', 'a / b']
    with pytest.raises(ValueError, match='Unbalanced'):
        source.tex_arguments('{missing')


def test_dictionary_citations_keep_stem_and_word_separate():
    spec = dict(format='cayuga_nouns', resources=[dict(key='noun', lexical=True)])
    text = r'\lexicalunitbracket{stem}\cayuga{prefixed}ˀ \trs{your doctor}'
    row = source.dictionary_records(spec, {'noun': text.encode()})[0]
    assert row['Form'] == 'prefixedˀ'
    assert row['original']['headwords'] == ['stem']
    assert row['source_sense'] == 'your doctor'
    assert row['original']['full_citations'] == ['prefixedˀ']
    assert 'Segments' not in row


def test_dictionary_phonetic_and_inflection_fields_survive():
    spec = dict(format='dagaare', resources=[dict(key='a', lexical=True)])
    text = r'\tbLX{head}\tbPH{hɛ́d}\tbPS{n.}\tbGE{word}\tbOP{plural}\tbGE{second sense}'
    row = source.dictionary_records(spec, {'a': text.encode()})[0]
    assert row['Form'] == 'head'
    assert row['original']['phonetic'] == ['hɛ́d']
    assert row['original']['senses'] == ['word', 'second sense']
    assert r'\tbOP{plural}' in row['original']['raw_block']
    assert 'Segments' not in row


def test_tuatschin_malformed_original_is_preserved_without_repair():
    text = (r'\entry{word}{ˈwɔrd}{m.n}{word}' '\n'
            r'\presententry{mulá}{mòla}{muˈlaː}{ˈmɔːlɐ}{tr.v }g{rind}')
    rows = source.tuatschin_records({'dictionary': text.encode()})
    assert rows[0]['original']['phonetic'] == ['ˈwɔrd']
    assert rows[1]['original']['form_kind'] == 'parse hold'
    assert rows[1]['source_sense'] == ''
    assert rows[1]['original']['phonetic'] == []
    assert 'g{rind}' in rows[1]['original']['raw_block']


def test_tuatschin_inflection_remains_separate_from_lemma_reading():
    text = r'\plentry{head}{pl}{heads}{hɛd}{hɛdz}{m.n}{head}'
    row = source.tuatschin_records({'dictionary': text.encode()})[0]
    assert row['Form'] == 'head'
    assert row['original']['phonetic'] == ['hɛd']
    assert row['original']['arguments'][2] == 'heads'
    assert row['original']['arguments'][4] == 'hɛdz'


def test_reflex_source_identity_and_native_notes_are_guarded():
    spec = dict(members=[dict(ID='1', Glottocode='test1234')])
    payloads = dict(sources=b'ID\tLANGUE\tBIB\tCSO\n1\tL\tR\tCorrections after publication\n',
                    languages=b'id\tglottocode\nL\ttest1234\n',
                    references=b'ID\tTITRE\nR\tOriginal dictionary\n',
                    records=b'id\tSOU\tFRM\tTRA\tCOA\n9\t1\ta / b\ttree\tvariant\n'
                    b'10\t2\tignored\tleaf\t\n')
    rows = source.reflex_records(spec, payloads)
    assert len(rows) == 1
    assert rows[0]['Form'] == 'a / b'
    assert rows[0]['original']['record']['COA'] == 'variant'
    assert rows[0]['original']['attribution']['source']['CSO'] == 'Corrections after publication'
    assert 'Segments' not in rows[0]
    payloads['languages'] = b'id\tglottocode\nL\tother123\n'
    with pytest.raises(ValueError, match='identity'):
        source.reflex_records(spec, payloads)


def test_lexirumah_conversion_is_distinct_from_source_spelling():
    spec = dict(members=[dict(ID='L', Glottocode='test1234')])
    payloads = dict(lects=b'ID,Orthography,Glottocode\nL,p/general:p/L,test1234\n',
                    concepts=b'ID,English,Elicitation_Notes\nC,tree,not shrub\n',
                    forms=b'ID,Lect_ID,Concept_ID,Form_according_to_Source,Form,Local_Orthography,'
                    b'Segments,Source\nF,L,C,shaa,saa,sha,s a a,witness\n')
    row = source.lexirumah_records(spec, payloads)[0]
    assert (row['Value'], row['Form'], row['Segments']) == ('shaa', 'saa', 's a a')
    assert row['original']['record']['Local_Orthography'] == 'sha'
    assert row['original']['lect']['Orthography'] == 'p/general:p/L'
    assert row['original']['concept']['Elicitation_Notes'] == 'not shrub'
    assert row['original']['reading_basis'] == 'upstream_profile_conversion'
    assert 'cognacy' in row['original']
    with pytest.raises(ValueError, match='inventory'):
        source.lexirumah_records(dict(members=[]), payloads)


def test_original_manifest_identity_and_resources_are_unique():
    import json

    specs = json.loads(source.MANIFEST.read_text())
    assert len({r['dataset'] for r in specs}) == len(specs)
    for spec in specs:
        assert len({m['ID'] for m in spec['members']}) == len(spec['members'])
        assert len({r['key'] for r in spec['resources']}) == len(spec['resources'])
        assert len({r['filename'] for r in spec['resources']}) == len(spec['resources'])
        assert spec['license'].startswith('https://creativecommons.org/licenses/')
        assert all(len(r['sha256']) == 64 for r in spec['resources'])
