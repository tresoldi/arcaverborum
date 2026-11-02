"""Independently compare stable witness identities across this lexical/metadata migration."""

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path

from arcaverborum.colexification import verify_database


def witnesses(directory):
    db = sqlite3.connect(f"file:{directory / 'index.sqlite'}?mode=ro", uri=True)
    db.execute("PRAGMA cache_size=-16384")
    db.execute("PRAGMA temp_store=FILE")
    sql = """SELECT s.av,s.source,s.member,s.tags,s.basis,w.layer,w.kind,w.a,w.b,w.key,
             w.original_concept,ra.fid,ra.param,rb.fid,rb.param
             FROM witnesses w JOIN scopes s ON s.id=w.sid
             JOIN readings ra ON ra.id=w.ra JOIN readings rb ON rb.id=w.rb
             ORDER BY s.av,s.source,s.member,s.tags,s.basis,w.layer,w.kind,w.a,w.b,w.key,
                      w.original_concept,ra.fid,ra.param,rb.fid,rb.param"""
    digest, count = hashlib.sha256(), 0
    try:
        for row in db.execute(sql):
            digest.update(json.dumps(row, ensure_ascii=False).encode() + b"\n")
            count += 1
    finally:
        db.close()
    return dict(witnesses=count, stable_identity_sha256=digest.hexdigest())


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--before", type=Path, required=True)
    p.add_argument("--after", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    seals = {name: verify_database(path) for name, path in (("before", a.before), ("after", a.after))}
    old, new = witnesses(a.before), witnesses(a.after)
    if old != new:
        raise ValueError("Observed/inferred witness identities changed; inspect the new evidence before publication")
    result = dict(schema=1, before_build_id=seals["before"]["build_id"],
                  after_build_id=seals["after"]["build_id"], **new,
                  unchanged_positive_identities=True, lexical_readings_mapped_in_written_channel_only=True,
                  qualification="Unchanged positive witnesses do not imply unchanged comparison coverage. "
                  "No semantic confidence or lexical absence is inferred.")
    a.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
