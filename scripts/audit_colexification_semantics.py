"""Rank unreviewed English dictionary senses contributing reported associations.

This queue never modifies words or mappings. Breadth is triage, not error proof.
"""
import argparse
import csv
import json
import resource
from pathlib import Path

from arcaverborum.colexification import connect, verify_database


def audit(root, built, output):
    verify_database(built)
    db=connect(built/'index.sqlite')
    with (root/'src/arcaverborum/data/concepts.csv').open() as handle:
        concepts={r['concept_id']:r for r in csv.DictReader(handle)}
    query='''WITH implicated AS (
      SELECT DISTINCT r.param,r.cid,w.a,w.b,s.av,v.language,v.family
      FROM witnesses w JOIN scopes s ON s.id=w.sid JOIN varieties v ON v.av=s.av
      JOIN readings r ON r.id=w.ra OR r.id=w.rb
      WHERE w.layer='segmented' AND w.kind='observed' AND r.semantic='unreviewed_dictionary_sense')
      SELECT param,cid,COUNT(DISTINCT a||'/'||b),COUNT(DISTINCT av),
        COUNT(DISTINCT NULLIF(language,'')),COUNT(DISTINCT NULLIF(family,''))
      FROM implicated GROUP BY param,cid ORDER BY COUNT(DISTINCT a||'/'||b) DESC,
        COUNT(DISTINCT NULLIF(family,'')) DESC,param,cid'''
    count=0
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('w',newline='') as handle:
        fields=['source_parameter_id','concept_id','source_sense','frozen_definition','reported_pairs',
                'varieties','languages','families','status']
        writer=csv.DictWriter(handle,fieldnames=fields,lineterminator='\n')
        writer.writeheader()
        for pid,cid,pairs,avs,languages,families in db.execute(query):
            names=[r[0] for r in db.execute('SELECT name FROM source_senses WHERE param=? ORDER BY name',(pid,))]
            writer.writerow(dict(zip(fields,[pid,cid,' | '.join(names),concepts[cid]['definition'],pairs,avs,
                languages,families,'unreviewed semantic mapping; not a proven error'])))
            count+=1
    db.close()
    report=dict(build_id=built.name,unreviewed_parameter_concept_pairs=count,
                method='Unreviewed dictionary senses in representative reported segmented witnesses; '
                       'ranking breadth is not an admission or error decision. Other senses may require review too.')
    output.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--build',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    resource.setrlimit(resource.RLIMIT_AS,(256*1024*1024,)*2)
    print(json.dumps(audit(args.root,args.build,args.output),indent=2))
