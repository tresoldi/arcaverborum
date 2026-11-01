"""Verify full lexical preservation and the reported BAG–WITCH correction."""
import csv
import gzip
import io
import itertools
import json
import subprocess
from collections import Counter
from pathlib import Path

from arcaverborum.concept_rows import array_rows

ROOT=Path(__file__).resolve().parents[1]
BEFORE='c83eed9d3dc4260242598f68fa91083bf74c328e'


def old(path):
    return subprocess.check_output(['git','show',f'{BEFORE}:{path}'],cwd=ROOT)


def verify():
    previous=json.loads(old('web/data/manifest.json'))
    current=json.loads((ROOT/'web/data/manifest.json').read_text())
    assert previous['fields']==current['fields']
    fields=previous['fields']
    mutations=json.loads((ROOT/'docs/colexification_mapping_changes_2026-11-01.json').read_text())
    changed={(r['av_id'],r['source_form_id']):r for r in mutations}
    semantic_parameters={r['Parameter_ID'] for r in json.loads(
        (ROOT/'docs/colexification_sense_reviews_2026-11-01.json').read_text())}
    counts=Counter()
    for family,shard in previous['shards'].items():
        latest=current['shards'][family]
        assert shard['forms']==latest['forms']
        if shard['sha256']==latest['sha256']:
            counts['identical_family_records']+=shard['forms']
            continue
        process=subprocess.Popen(['git','show',f"{BEFORE}:web/{shard['url']}"],cwd=ROOT,stdout=subprocess.PIPE)
        with io.TextIOWrapper(gzip.GzipFile(fileobj=process.stdout),encoding='utf-8') as before, gzip.open(
                ROOT/'web'/latest['url'],'rt',encoding='utf-8') as after:
            for a,b in itertools.zip_longest(array_rows(before),array_rows(after)):
                assert a is not None and b is not None
                left,right=dict(zip(fields,a,strict=True)),dict(zip(fields,b,strict=True))
                key=left['av_id'],left['source_form_id']
                assert left['ID']==right['ID']
                for name in fields:
                    if left[name]==right[name]:
                        continue
                    if name in {'concept_id','concept_label','Concepticon_ID','quality_score'}:
                        assert key in changed and name in changed[key]['changed'],(key,name)
                        assert left['source_parameter_id'] in semantic_parameters
                        counts['changed_'+name]+=1
                    elif name in {'mapping_review','mapping_note'}:
                        assert left['source_parameter_id'] in semantic_parameters,(key,name)
                    elif name not in {'is_core_concept','preferred_source','evidence_role','gled_dependence'}:
                        raise AssertionError((key,name))
                counts['compared_changed_family_records']+=1
        assert process.wait()==0
    assert sum(counts[k] for k in ['identical_family_records','compared_changed_family_records'])==2119818
    assert counts['changed_concept_id']==95 and counts['changed_quality_score']==156
    with (ROOT/'varieties/ine-galician/generated/forms.csv').open() as handle:
        galician=list(csv.DictReader(handle))
    bag=next(r for r in galician if r['source_form_id']=='wikt_467684')
    witch=next(r for r in galician if r['source_form_id']=='wikt_875155')
    assert bag['Form']==witch['Form']=='antaruxa' and not bag['concept_id'] and witch['concept_id']=='rel-witch'
    assert bag['raw_ipa']==witch['raw_ipa']=='[antaˈɾuʃɐ]'
    return dict(before_commit=BEFORE,preserved_lexical_records=2119818,record_count_unchanged=True,
                readings_native_ids_cognacy_and_source_comments_preserved=True,changes=dict(counts),
                galician_antaruxa_reading_retained_and_container_mapping_removed=True)


if __name__=='__main__':
    result=verify()
    (ROOT/'docs/colexification_robustness_preservation_2026-11-01.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
