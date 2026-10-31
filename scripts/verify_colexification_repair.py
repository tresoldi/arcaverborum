"""Reconcile repaired analytical evidence against the earlier frozen snapshot."""
import argparse
import json
import sqlite3
from pathlib import Path

from arcaverborum.colexification import sha, verify_database, verify_public


def verify(before, after):
    before, after = Path(before), Path(after)
    verify_database(after)
    old = verify_public(before / 'public')
    new = verify_public(after / 'public')
    for name, value in old['inputs'].items():
        if name.startswith('output/aggregate/'):
            assert new['inputs'][name] == value, name
    db = sqlite3.connect(f'file:{after / "index.sqlite"}?mode=ro', uri=True)
    db.execute('PRAGMA cache_size=-16384')
    db.execute('PRAGMA temp_store=FILE')
    db.execute('PRAGMA mmap_size=0')
    db.execute('ATTACH DATABASE ? AS previous', (f'file:{before / "index.sqlite"}?mode=ro',))
    gained = db.execute('''SELECT COUNT(*) FROM edges n LEFT JOIN previous.edges o
      ON n.layer=o.layer AND n.kind=o.kind AND n.a=o.a AND n.b=o.b WHERE o.a IS NULL''').fetchone()[0]
    increased = db.execute('''SELECT COUNT(*) FROM edges n JOIN previous.edges o
      ON n.layer=o.layer AND n.kind=o.kind AND n.a=o.a AND n.b=o.b
      WHERE n.families>o.families OR n.languages>o.languages OR n.varieties>o.varieties''').fetchone()[0]
    bad_denominators = db.execute('''SELECT COUNT(*) FROM edges n JOIN previous.edges o
      ON n.layer=o.layer AND n.kind=o.kind AND n.a=o.a AND n.b=o.b WHERE n.kind='observed' AND
      json_extract(n.opportunities,'$.comparable_varieties')>json_extract(o.opportunities,'$.comparable_varieties')
      ''').fetchone()[0]
    assert gained == increased == bad_denominators == 0
    reconstructed = db.execute("SELECT COUNT(*) FROM readings WHERE fid='idssegmented_elamite-13-50-1'").fetchone()[0]
    assert reconstructed == 0
    networks = []
    for layer, kind, count in db.execute('SELECT layer,kind,COUNT(*) FROM edges GROUP BY layer,kind'):
        previous = db.execute(
            'SELECT COUNT(*) FROM previous.edges WHERE layer=? AND kind=?', (layer, kind)).fetchone()[0]
        removed = db.execute('''SELECT COUNT(*) FROM previous.edges o LEFT JOIN edges n
          ON n.layer=o.layer AND n.kind=o.kind AND n.a=o.a AND n.b=o.b
          WHERE o.layer=? AND o.kind=? AND n.a IS NULL''', (layer, kind)).fetchone()[0]
        networks.append(dict(layer=layer, kind=kind, previous=previous, repaired=count, removed=removed))
    def witnesses(schema):
        return f'''SELECT s.av,s.source,s.member,s.tags,s.basis,w.layer,w.kind,w.a,w.b,w.key
          FROM {schema}.witnesses w JOIN {schema}.scopes s ON s.id=w.sid'''
    gained_witnesses = db.execute('SELECT COUNT(*) FROM (' + witnesses('main') + ' EXCEPT ' +
                                  witnesses('previous') + ')').fetchone()[0]
    assert gained_witnesses == 0
    report = dict(before=old['build_id'], after=new['build_id'], networks=networks,
                  new_edges=gained, support_increases=increased, comparable_variety_increases=bad_denominators,
                  new_stable_witnesses=gained_witnesses, excluded_elamite_readings_remaining=reconstructed,
                  previous_witnesses=old['stats']['witnesses'], repaired_witnesses=new['stats']['witnesses'],
                  lexical_source_hashes_unchanged=True, repaired_stats=new['stats'],
                  completion_sha256=sha(after / 'complete.json'))
    db.close()
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before', type=Path, required=True)
    parser.add_argument('--after', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = verify(args.before, args.after)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report['networks'], indent=2))
