"""Independently check influence bounds, catalog gates and guarded source additions."""

import argparse
import csv
import json
import resource
import sqlite3
from collections import defaultdict
from pathlib import Path

from arcaverborum.colexification import verify_database


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument("--build", type=Path, required=True)
    p.add_argument("--before", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    resource.setrlimit(resource.RLIMIT_AS, (256 * 1024**2, 256 * 1024**2))
    current, previous = verify_database(a.build), verify_database(a.before)
    db = sqlite3.connect(f"file:{a.build / 'index.sqlite'}?mode=ro", uri=True)
    db.execute("PRAGMA cache_size=-8000")
    db.execute("PRAGMA temp_store=FILE")
    db.execute("PRAGMA mmap_size=0")
    db.execute("ATTACH DATABASE ? AS old", (str(a.before / "index.sqlite"),))
    assert db.execute("SELECT COUNT(*) FROM projection_blocks WHERE mass<=0 OR mass>1").fetchone()[0] == 0
    assert (
        db.execute("""SELECT COUNT(*) FROM (
        SELECT w.sid,w.layer,w.key,COUNT(*)*2.0/(g.concepts*(g.concepts-1)) AS mass
        FROM witnesses w JOIN groups g ON g.sid=w.sid AND g.layer=w.layer AND g.key=w.key
        WHERE w.kind='observed' GROUP BY w.sid,w.layer,w.key HAVING mass>1+1e-9)""").fetchone()[0]
        == 0
    )
    assert db.execute("SELECT COUNT(*) FROM edges WHERE a='act-bag' AND b='rel-witch'").fetchone()[0] == 0
    assert (
        db.execute("""SELECT COUNT(*) FROM projection_blocks p WHERE NOT EXISTS (
        SELECT 1 FROM witnesses w JOIN scopes s ON s.id=w.sid JOIN varieties v ON v.av=s.av
        JOIN resource_blocks b ON b.source=s.source JOIN readings ra ON ra.id=w.ra
        JOIN readings rb ON rb.id=w.rb WHERE w.kind='observed' AND w.layer=p.layer
        AND w.a=p.a AND w.b=p.b AND v.family=p.family AND b.block=p.block
        AND ra.semantic<>'unreviewed_dictionary_sense'
        AND rb.semantic<>'unreviewed_dictionary_sense')""").fetchone()[0]
        == 0
    )
    relations = {(x, y) for x, y in db.execute("SELECT a,b FROM concept_relations")}
    assessed = 0
    for layer, x, y, encoded in db.execute("SELECT layer,a,b,value FROM assessments ORDER BY layer,a,b"):
        value = json.loads(encoded)
        masses = defaultdict(dict)
        for family, block, mass in db.execute(
            "SELECT family,block,mass FROM projection_blocks WHERE layer=? AND a=? AND b=?", (layer, x, y)
        ):
            masses[family][block] = mass
        total = sum(max(v.values()) for v in masses.values())
        blocks = {b for v in masses.values() for b in v}
        survival = min(
            (
                sum(max((w for b, w in v.items() if b != excluded), default=0) for v in masses.values())
                for excluded in blocks
            ),
            default=0,
        )
        assert value["eligible_families"] == len(masses)
        assert abs(value["adjusted_support"] - total) < 1e-9
        assert abs(value["resource_survival_support"] - survival) < 1e-9
        eligible = len(masses) >= 2 and survival > 0 and (x, y) not in relations
        assert value["backbone_eligible"] == eligible
        assert abs(value["clustering_weight"] - (survival if eligible else 0)) < 1e-9
        assert 0 <= survival <= total + 1e-9 <= len(masses) + 1e-8
        assessed += 1
    ledgers = {}
    for av in ["sab-piaroa", "tuc-wa-ikhana", "ara-yucuna"]:
        ledgers[av] = {
            r["source_form_id"]
            for r in csv.DictReader((a.root / "varieties" / av / "custom/transcriptions.csv").open())
        }
    additions = defaultdict(int)
    for av, fid_a, fid_b in db.execute("""SELECT ns.av,ra.fid,rb.fid FROM witnesses n
        JOIN scopes ns ON ns.id=n.sid JOIN readings ra ON ra.id=n.ra JOIN readings rb ON rb.id=n.rb
        LEFT JOIN old.scopes os ON os.av=ns.av AND os.source=ns.source AND os.member=ns.member
          AND os.tags=ns.tags AND os.basis=ns.basis
        LEFT JOIN old.witnesses o ON o.sid=os.id AND o.layer=n.layer AND o.kind=n.kind
          AND o.a=n.a AND o.b=n.b AND o.key=n.key WHERE o.id IS NULL"""):
        assert av in ledgers and (fid_a in ledgers[av] or fid_b in ledgers[av])
        additions[av] += 1
    new_edges = [
        dict(layer=layer, kind=kind, a=x, b=y)
        for layer, kind, x, y in db.execute("""SELECT n.layer,n.kind,n.a,n.b
        FROM edges n LEFT JOIN old.edges o USING(layer,kind,a,b) WHERE o.a IS NULL""")
    ]
    assert new_edges == [dict(layer="written", kind="observed", a="bod-scratch", b="mot-turn")]
    report = dict(
        build=current["build_id"],
        before=previous["build_id"],
        assessed_pairs=assessed,
        influence_formula_recovered=True,
        unreviewed_semantics_cannot_create_support=True,
        unit_identity_mass_bound_verified=True,
        catalog_overlap_zero_weight=True,
        bag_witch_absent=True,
        added_witnesses_by_reviewed_variety=dict(additions),
        new_reported_edges=new_edges,
        interpretation="Representation evidence and conservative influence weights; not calibrated polysemy confidence",
        memory_limit_mb=256,
    )
    a.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
