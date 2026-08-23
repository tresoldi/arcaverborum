#!/usr/bin/env python3
"""Build the browser SQLite for the Arca Verborum Core web explorer.

Reads a built release directory and writes a trimmed, indexed SQLite (essential
columns only) gzipped to web/arca-core.sqlite.gz, plus web/BUILD_INFO. The web
page fetches the .gz, inflates it with the browser's native DecompressionStream,
and queries it client-side via sql.js. No server required.

Usage:
  python scripts/build_web_db.py [--release-dir DIR] [--out web/arca-core.sqlite.gz]
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import shutil
import sqlite3
import sys
import tempfile
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

_FORM_COLS = ["ID", "Language_ID", "Parameter_ID", "concept_label", "Form", "Segments",
              "Segments_Source", "Cognacy", "canonical_cognate_id", "is_core_concept",
              "transcription_source", "tier"]
_LANG_COLS = ["ID", "Name", "Glottocode", "Family", "Macroarea", "Latitude", "Longitude",
              "tier", "forms_score", "cognates_score"]
_PARAM_COLS = ["ID", "Name", "Concepticon_ID", "pos", "semantic_field", "is_core"]
_FORM_INDEXES = ["Language_ID", "Parameter_ID", "Cognacy", "canonical_cognate_id", "is_core_concept"]


def _rows(path: Path, cols: list[str]):
    with path.open(encoding="utf-8") as f:
        for x in csv.DictReader(f):
            yield tuple(x.get(c, "") for c in cols)


def build_db(release_dir: Path, sqlite_path: Path) -> dict:
    if sqlite_path.exists():
        sqlite_path.unlink()
    con = sqlite3.connect(sqlite_path)
    cur = con.cursor()
    cur.execute(f"CREATE TABLE forms({','.join(_FORM_COLS)})")
    cur.execute(f"CREATE TABLE languages({','.join(_LANG_COLS)})")
    cur.execute(f"CREATE TABLE parameters({','.join(_PARAM_COLS)})")
    counts = {}
    cur.executemany(f"INSERT INTO forms VALUES({','.join('?' * len(_FORM_COLS))})",
                    _rows(release_dir / "forms.csv", _FORM_COLS))
    counts["forms"] = cur.execute("SELECT COUNT(*) FROM forms").fetchone()[0]
    cur.executemany(f"INSERT INTO languages VALUES({','.join('?' * len(_LANG_COLS))})",
                    _rows(release_dir / "languages.csv", _LANG_COLS))
    counts["languages"] = cur.execute("SELECT COUNT(*) FROM languages").fetchone()[0]
    cur.executemany(f"INSERT INTO parameters VALUES({','.join('?' * len(_PARAM_COLS))})",
                    _rows(release_dir / "parameters.csv", _PARAM_COLS))
    counts["parameters"] = cur.execute("SELECT COUNT(*) FROM parameters").fetchone()[0]
    for c in _FORM_INDEXES:
        cur.execute(f'CREATE INDEX ix_forms_{c} ON forms("{c}")')
    con.commit()
    con.close()
    return counts


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--release-dir",
                    default=str(PROJECT_ROOT / "output" / "release" / "arca-verborum-core-0.1.0"))
    ap.add_argument("--out", default=str(PROJECT_ROOT / "web" / "arca-core.sqlite.gz"))
    args = ap.parse_args(argv)

    release_dir = Path(args.release_dir)
    if not (release_dir / "forms.csv").exists():
        raise SystemExit(f"No release at {release_dir}; run `build.py release` first.")

    manifest = {}
    mpath = release_dir / "MANIFEST.json"
    if mpath.exists():
        manifest = json.loads(mpath.read_text(encoding="utf-8"))

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "arca-core.sqlite"
        counts = build_db(release_dir, db)
        raw = db.stat().st_size
        with db.open("rb") as fi, gzip.open(out, "wb", compresslevel=9) as fo:
            shutil.copyfileobj(fi, fo)
    gz = out.stat().st_size

    (out.parent / "BUILD_INFO").write_text(
        json.dumps({
            "title": "Arca Verborum Core",
            "version": manifest.get("version", "?"),
            "build_date": date.today().isoformat(),
            "merkmal_version": manifest.get("merkmal_version", "?"),
            "counts": counts,
            "db_bytes_raw": raw, "db_bytes_gz": gz,
        }, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote {out} ({gz/1e6:.1f} MB gz, {raw/1e6:.1f} MB raw) — "
          f"{counts['forms']} forms, {counts['languages']} languages, {counts['parameters']} concepts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
