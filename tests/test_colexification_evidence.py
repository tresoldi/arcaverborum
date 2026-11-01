"""Adversarial semantic and projection examples have explicit bounded influence."""
import itertools
import json
import math

import pytest

from arcaverborum.colexification_communities import medoid
from arcaverborum.colexification_evidence import SemanticEligibility, summarize


def test_single_resource_or_family_cannot_create_backbone_replication():
    assert summarize({'f1':{'dictionary':1},'f2':{'dictionary':1}})['clustering_weight']==0
    assert summarize({'f1':{'dictionary':1,'second':1}})['clustering_weight']==0
    value=summarize({'f1':{'dictionary':1},'f2':{'second':1}})
    assert value['clustering_weight']==1 and value['adjusted_support']==2
    assert value['families_without_one_block_min']==1


def test_duplicate_lects_sources_and_large_cliques_cannot_multiply_mass():
    value=summarize({'f1':{'a':1,'b':1,'c':1},'f2':{'d':1}})
    assert value['adjusted_support']==2
    for k in range(2,65):
        mass=2/(k*(k-1))
        assert sum(mass for _ in itertools.combinations(range(k),2))==pytest.approx(1)
        assert summarize({'f1':{'a':mass},'f2':{'b':mass}})['clustering_weight']==pytest.approx(mass)


def test_resampling_does_not_turn_duplicate_draws_into_independent_families():
    blocks={'f1':{'a':1},'f2':{'b':1}}
    assert summarize(blocks,{'f1':100})['clustering_weight']==0
    assert summarize(blocks,{'f1':3,'f2':2})['clustering_weight']==2
    for bad in [-1,math.inf,math.nan,1.1]:
        with pytest.raises(ValueError):
            summarize({'f':{'s':bad}})
    with pytest.raises(ValueError):
        summarize(blocks,{'f1':-1})


def test_dictionary_semantics_require_actual_review_not_correct_ipa(tmp_path):
    gate=SemanticEligibility(tmp_path)
    row=dict(av_id='galician',transcription_source='wiktionary',source_parameter_id='bag-ugly-woman',
             source_form_id='antaruxa',concept_id='bag-container',Segments='a n t a r u x a')
    assert gate.status(row)=='unreviewed_dictionary_sense'
    gate.local['galician','bag-ugly-woman']='bag-container'
    gate.shared['bag-ugly-woman']=''
    assert gate.status(row)=='unreviewed_dictionary_sense'  # contradictory older parameter override
    gate.local['galician','antaruxa']='witch'
    assert gate.status(row|dict(concept_id='witch'))=='reviewed_dictionary_sense'


def test_reported_dictionary_identities_survive_without_backbone_weight(tmp_path):
    from test_colexification import form, run
    built,db=run(tmp_path,[form(0,source='wiktionary'),form(1,source='wiktionary')])
    value=json.loads(db.execute("SELECT value FROM assessments WHERE layer='segmented'").fetchone()[0])
    assert value['status']=='semantic_review_required' and value['clustering_weight']==0
    assert db.execute("SELECT COUNT(*) FROM witnesses WHERE layer='segmented'").fetchone()[0]==1
    assert json.loads((built/'public/manifest.json').read_text())['stats']['semantic_readings'][
        'unreviewed_dictionary_sense']==4  # separate segmented and citation records
    db.close()


def test_medoid_avoids_a_lone_extreme_partition_with_better_compression():
    common={0:0,1:0,2:2,3:2}
    extreme={0:0,1:0,2:0,3:0}
    assert medoid([extreme,common,common],[0,2,3])==1


def test_reviewed_native_pair_is_not_hidden_by_earlier_unreviewed_alternatives(tmp_path):
    from test_colexification import csv_file, form, run
    csv_file(tmp_path/'varieties/a/custom/concept_map.csv',[
        dict(Parameter_ID='wikt_review0',action='map',concept_id='x-0'),
        dict(Parameter_ID='wikt_review1',action='map',concept_id='x-1')])
    rows=[form(i,source='wiktionary',fid=f'{prefix}-{i}',param=f'wikt_{parameter}{i}')
          for prefix,parameter in [('a','auto'),('z','review')] for i in [0,1]]
    _,db=run(tmp_path,rows)
    pair=db.execute("SELECT ra.fid,rb.fid FROM witnesses w JOIN readings ra ON ra.id=w.ra "
                    "JOIN readings rb ON rb.id=w.rb WHERE w.layer='segmented'").fetchone()
    assert pair==('z-0','z-1')
    value=json.loads(db.execute("SELECT value FROM assessments WHERE layer='segmented'").fetchone()[0])
    assert value['unreviewed_semantic_witnesses']==0
    db.close()


def test_colliding_legacy_parameter_ids_preserve_both_names_but_cannot_validate_senses(tmp_path):
    from test_colexification import csv_file, form, run
    source=tmp_path/'intake/wiktionary/parameters_raw.csv'
    csv_file(source,[dict(ID='wikt_collision',Name=name,Concepticon_ID='1')
                     for name in ['Reykjavik (name): capital','Reykjavík (name): capital']])
    _,db=run(tmp_path,[form(0,source='wiktionary',param='wikt_collision'),
                       form(1,source='wiktionary',param='wikt_other')])
    assert db.execute('SELECT COUNT(*) FROM source_senses').fetchone()[0]==2
    db.close()
    csv_file(tmp_path/'src/arcaverborum/data/wiktionary_sense_overrides.csv',[
        dict(Parameter_ID='wikt_collision',expected_source_name='Reykjavik (name): capital',
             expected_source_concepticon_id='1',action='map',concept_id='x-0')])
    with pytest.raises(ValueError,match='Ambiguous source parameter ID'):
        SemanticEligibility(tmp_path)


def test_different_namespaces_in_one_known_resource_block_are_not_replication(tmp_path):
    import csv

    from test_colexification import csv_file, fixture, form

    from arcaverborum.colexification import build, connect
    fixture(tmp_path,[form(i,av=av,source=source)
                      for av,source in [('a','source'),('b','second')] for i in [0,1]])
    path=tmp_path/'raw/glottolog/languages.csv'
    languages=list(csv.DictReader(path.open()))
    next(row for row in languages if row['ID']=='b')['Family_ID']='second-family'
    csv_file(path,languages)
    (tmp_path/'src/arcaverborum/data/colexification/resource_blocks.json').write_text(
        json.dumps(dict(blocks={'shared-compilation':['source','second']})))
    built=build(tmp_path)
    db=connect(built/'index.sqlite')
    assert db.execute("SELECT families FROM edges WHERE layer='segmented'").fetchone()[0]==2
    value=json.loads(db.execute("SELECT value FROM assessments WHERE layer='segmented'").fetchone()[0])
    assert value['resource_blocks']==1 and value['clustering_weight']==0
    db.close()
