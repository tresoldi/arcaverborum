"""Reference comparison guards concept identities, source expansions and missingness."""
import csv
import json
import sqlite3
import zipfile

import pytest

from arcaverborum.colexification import sha
from arcaverborum.colexification_comparison import (
    compare,
    discordance_statuses,
    form_pair,
    gml_records,
    overlap,
    rank_correlation,
    status_counts,
    unique_crosswalk,
)


def csv_file(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def zipped(path, name, text):
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr(name, text)


def test_crosswalk_never_joins_ambiguous_or_merged_concepts():
    rows = [dict(concept_id=cid, concepticon_id=icon, status=status)
            for cid, icon, status in [('a', '1', 'active'), ('b', '1', 'active'),
                                     ('c', '2', 'active'), ('d', '3', 'merged'), ('e', '', 'active')]]
    unique, ambiguous = unique_crosswalk(rows)
    assert set(unique) == {'2'}
    assert ambiguous == {'1': ['a', 'b']}


def test_streamed_gml_ignores_provenance_and_decodes_labels(tmp_path):
    path = tmp_path / 'graph.zip'
    zipped(path, 'dir/network.gml', 'graph [\nnode [\nid 0\nlabel "1"\nGloss "A &amp; B"\n'
           'Words "large unneeded provenance"\n]\nedge [\nsource 0\ntarget 1\nFamilyWeight 3\n]\n]\n')
    assert list(gml_records(path)) == [('node', dict(id='0', label='1', Gloss='A & B')),
                                     ('edge', dict(source='0', target='1', FamilyWeight='3'))]
    zipped(path, 'dir/network.gml', 'graph [\nnode [\nid 0\n')
    with pytest.raises(ValueError, match='Truncated'):
        list(gml_records(path))


def test_missingness_is_not_negative_evidence_and_support_is_not_double_counted():
    assert status_counts({'x', 'y', 'z'}, {'x'}, {'x', 'y'}) == dict(
        confirmed=1, other_sampled_no_shared_form=1, other_unknown=1)
    assert overlap({1, 2}, {2, 3})['shared'] == 1
    assert form_pair('clics4-10-a-1/clics4-10-b-1') == ('10-a-1', '10-b-1')


def test_reference_expansions_stay_separate_in_end_to_end_comparison(tmp_path):
    root = tmp_path
    concepts = root / 'src/arcaverborum/data/concepts.csv'
    csv_file(concepts, [dict(concept_id=cid, concepticon_id=str(i), label=cid, status='active')
                        for i, cid in enumerate(['a', 'b', 'c'], 1)])
    glottolog = root / 'raw/glottolog/languages.csv'
    csv_file(glottolog, [dict(ID='lang0001', Level='language', Language_ID='lang0001')])
    build = root / 'output/colexification/test'
    build.mkdir(parents=True)
    db = sqlite3.connect(build / 'index.sqlite')
    db.executescript('''
      CREATE TABLE varieties(av TEXT,language TEXT,family TEXT);
      INSERT INTO varieties VALUES('av','lang0001','family');
      CREATE TABLE scopes(id INT,av TEXT,source TEXT);
      INSERT INTO scopes VALUES(1,'av','source');
      CREATE TABLE witnesses(sid INT,layer TEXT,kind TEXT,a TEXT,b TEXT);
      INSERT INTO witnesses VALUES(1,'segmented','observed','a','b');
      CREATE TABLE edges(layer TEXT,kind TEXT,a TEXT,b TEXT,families INT,languages INT,varieties INT);
      INSERT INTO edges VALUES('segmented','observed','a','b',1,1,1);
      CREATE TABLE coverage(sid INT,layer TEXT,cid TEXT,pmin TEXT,pmax TEXT,fmin TEXT,fmax TEXT);
      INSERT INTO coverage VALUES(1,'segmented','a','a','a','a','a');
      INSERT INTO coverage VALUES(1,'segmented','b','b','b','b','b');
      INSERT INTO coverage VALUES(1,'segmented','c','c','c','c','c');
    ''')
    db.commit()
    db.close()
    public = root / 'web/data'
    public.mkdir(parents=True)
    manifest = public / 'network.json'
    manifest.write_text(json.dumps(dict(build_id='test', inputs={
        str(p.relative_to(root)): sha(p) for p in [concepts, glottolog]})))
    (public / 'manifest.json').write_text(json.dumps(dict(
        colexification=dict(url='data/network.json', sha256=sha(manifest)))))
    cache = root / 'cache'
    cache.mkdir()
    zipped(cache / 'clics3-clics3-network.gml.zip', 'graph.gml',
           'graph [\nnode [\nid 0\nlabel "1"\nGloss "A"\n]\n'
           'node [\nid 1\nlabel "2"\nGloss "B"\n]\n'
           'edge [\nsource 0\ntarget 1\nFamilyWeight 3\nLanguageWeight 3\n]\n]\n')
    zipped(cache / 'clics4-concepts.csv.zip', 'concepts.csv',
           'ID,Concepticon_ID,Concepticon_Gloss,Original_Concept\na,1,A,\nb,2,B,B OR C\nc,3,C,B OR C\n')
    csv_file(cache / 'clics4-languages.csv', [dict(ID='10', Glottocode='lang0001')])
    zipped(cache / 'clics4-forms.csv.zip', 'forms.csv',
           'ID,Language_ID,Parameter_ID,ConceptInSource,Local_ID,Source,Form,Segments\n'
           '10-a-1,10,a,,native-a,source,x,x\n10-b-1,10,b,,native-b,source,x,x\n'
           '10-b-2,10,b,B OR C,native-broad,source,y,y\n10-c-1,10,c,B OR C,native-broad,source,y,y\n')
    zipped(cache / 'clics4-colexifications.csv.zip', 'colexifications.csv',
           'Source_Concept,Target_Concept,Family_Count,Language_Count,Variety_Count,Family_Weight,Forms\n'
           'A,B,1,1,1,0,clics4-10-a-1/clics4-10-b-1\n'
           'B,C,1,1,1,0,clics4-10-b-2/clics4-10-c-1\n')
    sources = [dict(path=p.name, bytes=p.stat().st_size, sha256=sha(p)) for p in sorted(cache.iterdir())]
    pins = root / 'src/arcaverborum/data/colexification'
    pins.mkdir()
    (pins / 'clics_sources.json').write_text(json.dumps(dict(sources=sources)))
    report = compare(root, cache, root / 'scratch', root / 'report')
    assert report['comparisons']['clics4']['all_support_overlap']['reference_only'] == 1
    assert report['matched_clics4']['pair_language_direct_readings']['reference_only'] == 0
    assert report['clics4_witness_classification']['same_native_form_pairs'] == 1
    diagnostic = next(r for r in report['diagnostics'] if r['concepticon_ids'] == ['2', '3'])
    assert diagnostic['reference_current_language_units_direct'] == 0
    assert diagnostic['reference_examples'][0]['same_native_form'] is True
    # Integrity drift is rejected before replacing a previously generated report.
    previous = (root / 'report.json').read_bytes()
    (cache / 'clics4-languages.csv').write_text('changed')
    with pytest.raises(ValueError, match='changed CLICS reference'):
        compare(root, cache, root / 'scratch', root / 'report')
    assert (root / 'report.json').read_bytes() == previous


def test_strength_rank_correlation_handles_ties_and_constant_counts():
    assert rank_correlation([(1, 1), (2, 2), (2, 2), (3, 3)]) == 1
    assert rank_correlation([(1, 3), (2, 2), (3, 1)]) == -1
    assert rank_correlation([(1, 2), (1, 3)]) is None


def test_sparse_discordance_audit_keeps_unknown_separate():
    assert discordance_statuses({('1', '2', 'known'), ('1', '2', 'unknown')},
                               lambda a, b: {'known'}) == dict(
        other_sampled_no_shared_form=1, other_unknown=1)
