"""Check corpus-wide projection bounds, source gates and graph reconciliation."""
import argparse
import json
import resource
from pathlib import Path

from arcaverborum.colexification import connect, verify_database


def verify(built,before):
    verify_database(built)
    verify_database(before)
    db=connect(built/'index.sqlite')
    db.execute('ATTACH DATABASE ? AS previous',(str(before/'index.sqlite'),))
    # Independent invariants of the chosen influence model, not a claim of semantic truth.
    failures=db.execute('''SELECT COUNT(*) FROM assessments WHERE
      json_extract(value,'$.resource_survival_support') > json_extract(value,'$.adjusted_support')+1e-9 OR
      json_extract(value,'$.adjusted_support') > json_extract(value,'$.eligible_families')+1e-9 OR
      json_extract(value,'$.clustering_weight') < 0 OR
      (json_extract(value,'$.clustering_weight')>0 AND
       (json_extract(value,'$.eligible_families')<2 OR json_extract(value,'$.resource_blocks')<2)) OR
      (json_extract(value,'$.backbone_eligible')=0 AND json_extract(value,'$.clustering_weight')<>0)''').fetchone()[0]
    assert failures==0
    assert db.execute('SELECT COUNT(*) FROM projection_blocks WHERE mass<=0 OR mass>1').fetchone()[0]==0
    assert db.execute('''SELECT COUNT(*) FROM (
      SELECT w.sid,w.layer,w.key,COUNT(*)*2.0/(g.concepts*(g.concepts-1)) AS mass
      FROM witnesses w JOIN groups g ON g.sid=w.sid AND g.layer=w.layer AND g.key=w.key
      WHERE w.kind='observed' GROUP BY w.sid,w.layer,w.key HAVING mass>1+1e-9)''').fetchone()[0]==0
    # Representative pairs entering the model must have actually eligible meaning assignments.
    assert db.execute('''SELECT COUNT(*) FROM projection_blocks p WHERE NOT EXISTS (
      SELECT 1 FROM witnesses w JOIN scopes s ON s.id=w.sid JOIN varieties v ON v.av=s.av
      JOIN resource_blocks b ON b.source=s.source JOIN readings ra ON ra.id=w.ra JOIN readings rb ON rb.id=w.rb
      WHERE w.kind='observed' AND w.layer=p.layer AND w.a=p.a AND w.b=p.b AND v.family=p.family AND b.block=p.block
        AND ra.semantic<>'unreviewed_dictionary_sense'
        AND rb.semantic<>'unreviewed_dictionary_sense')''').fetchone()[0]==0
    assert db.execute("SELECT COUNT(*) FROM edges WHERE a='act-bag' AND b='rel-witch'").fetchone()[0]==0
    increased=db.execute('''SELECT COUNT(*) FROM edges n JOIN previous.edges o USING(layer,kind,a,b)
      WHERE n.families>o.families OR n.languages>o.languages OR n.varieties>o.varieties''').fetchone()[0]
    assert increased==0
    new=db.execute('''SELECT COUNT(*) FROM edges n LEFT JOIN previous.edges o USING(layer,kind,a,b)
      WHERE o.a IS NULL''').fetchone()[0]
    assert new==0
    removed=[dict(layer=layer,kind=kind,pairs=n) for layer,kind,n in db.execute('''SELECT o.layer,o.kind,COUNT(*)
      FROM previous.edges o LEFT JOIN edges n USING(layer,kind,a,b) WHERE n.a IS NULL GROUP BY o.layer,o.kind''')]
    report=dict(build_id=built.name,before_build_id=before.name,bag_witch_absent=True,projection_bound_failures=failures,
                unreviewed_semantics_cannot_create_model_support=True,unit_identity_mass_bound_verified=True,
                new_reported_edges=new,support_increases=increased,removed_reported_edges=removed,
                assessed_pairs=db.execute('SELECT COUNT(*) FROM assessments').fetchone()[0],
                positive_segmented_backbone=db.execute("SELECT COUNT(*) FROM assessments WHERE layer='segmented' "
                    "AND json_extract(value,'$.clustering_weight')>0").fetchone()[0])
    db.close()
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build',type=Path,required=True)
    parser.add_argument('--before',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    resource.setrlimit(resource.RLIMIT_AS,(256*1024*1024,)*2)
    result=verify(args.build,args.before)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
