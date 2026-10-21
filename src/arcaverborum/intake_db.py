"""SQLite store for the intake forms tables (one file, indexed per slice).

`update` used to stream the intake CSVs and hold every matching row in one
pandas DataFrame, then boolean-filter that frame once per variety. This
module replaces the data access with a single SQLite database, built once
from the intake ``forms.csv`` files, from which each variety reads its own
(glottocode, dataset) slice with one indexed query. Memory is bounded by
the largest slice plus SQLite's page cache, not by the intake size.

Design rules (they are what keeps the build output byte-identical):

* Values are parsed by the same reader the CSV path uses (``pd.read_csv``
  with ``dtype=str, keep_default_na=False``), stored as TEXT, never NULL.
* ``seq`` is the global intake row order (files in the order given, rows in
  file order) and is the table's rowid. Every read is ``ORDER BY seq`` so a
  slice comes back in exactly the order the DataFrame path saw it.
* ``gc_lc`` is computed with the original expression
  (``str.strip().str.lower()`` on ``Glottocode``).
* Only the columns ``build_one``/slice hashing read are stored
  (``variety._INTAKE_USECOLS`` that the files actually carry).

The file is a plain, documented schema so a later Go/C build step can read
it directly; see ``SCHEMA_SQL``.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import logging
import os
import sqlite3
import tempfile
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

SCHEMA_VERSION = "1"
# Bump when the ingest semantics change (parsing options, normalisation),
# so existing databases are rebuilt. The pandas version is recorded too,
# since pandas does the CSV parsing.
INGEST_VERSION = "1"
_CHUNKSIZE = 200_000


def _quote(col: str) -> str:
    return '"' + col.replace('"', '""') + '"'


def _schema_sql(columns: list[str]) -> str:
    cols = ",\n  ".join(f"{_quote(c)} TEXT NOT NULL" for c in columns)
    return (
        "CREATE TABLE forms (\n"
        "  seq INTEGER PRIMARY KEY,   -- global intake order; rowid\n"
        "  src INTEGER NOT NULL,      -- index into meta.sources\n"
        "  src_row INTEGER NOT NULL,  -- 0-based data row within that file\n"
        "  gc_lc TEXT NOT NULL,       -- lower(strip(Glottocode))\n"
        f"  {cols}\n"
        ");\n"
    )


INDEX_SQL = 'CREATE INDEX forms_slice ON forms(gc_lc, "Dataset");'


def _file_stamp(path: Path) -> dict:
    st = path.stat()
    return {"path": str(path.resolve()), "size": st.st_size, "mtime_ns": st.st_mtime_ns}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _loader_id() -> str:
    return f"{INGEST_VERSION}/pandas-{pd.__version__}"


def _fsync_path(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def build_intake_db(
    forms_paths: list[Path],
    db_path: Path,
    usecols: frozenset[str],
    chunksize: int = _CHUNKSIZE,
    cache_mib: int = 64,
) -> dict:
    """Load the intake forms CSVs into a fresh SQLite file at *db_path*.

    Written to a unique temporary file in the same directory, fsynced and
    atomically renamed, under an exclusive lock on ``<db_path>.lock`` so
    two concurrent builders cannot publish each other's partial file.
    Returns summary stats.
    """
    paths = [p for p in forms_paths if p.exists()]
    if not paths:
        raise FileNotFoundError("no intake forms.csv found")

    # Column set: the usecols each file carries. All files must agree —
    # the DataFrame path would otherwise produce NaN for a column missing
    # from one file, which a TEXT NOT NULL store cannot reproduce.
    columns: list[str] | None = None
    for p in paths:
        header = list(pd.read_csv(p, nrows=0, dtype=str).columns)
        present = [c for c in header if c in usecols]
        if columns is None:
            columns = present
        elif set(present) != set(columns):
            raise ValueError(
                f"{p}: intake column set {sorted(present)} differs from {sorted(columns)}"
            )
    assert columns is not None
    for required in ("Glottocode", "Dataset"):
        if required not in columns:
            raise ValueError(f"intake forms lack required column {required!r}")

    db_path.parent.mkdir(parents=True, exist_ok=True)
    lock_fd = os.open(db_path.with_name(db_path.name + ".lock"), os.O_CREAT | os.O_RDWR, 0o644)
    tmp: Path | None = None
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        fd, tmp_name = tempfile.mkstemp(prefix=db_path.name + ".", suffix=".tmp", dir=db_path.parent)
        os.close(fd)
        tmp = Path(tmp_name)
        umask = os.umask(0)
        os.umask(umask)
        os.chmod(tmp, 0o666 & ~umask)  # mkstemp creates 0600
        stats = _populate(tmp, paths, columns, usecols, chunksize, cache_mib)
        _fsync_path(tmp)
        os.replace(tmp, db_path)
        _fsync_path(db_path.parent)
    except BaseException:
        if tmp is not None:
            tmp.unlink(missing_ok=True)
        raise
    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        os.close(lock_fd)
    return stats


def _populate(
    tmp: Path,
    paths: list[Path],
    columns: list[str],
    usecols: frozenset[str],
    chunksize: int,
    cache_mib: int,
) -> dict:
    conn = sqlite3.connect(tmp)
    try:
        conn.execute("PRAGMA journal_mode=OFF")      # tmp file; atomic rename is the commit
        conn.execute("PRAGMA synchronous=OFF")
        conn.execute(f"PRAGMA cache_size=-{cache_mib * 1024}")
        conn.executescript(_schema_sql(columns))
        conn.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")

        insert_cols = ["seq", "src", "src_row", "gc_lc", *columns]
        sql = (f"INSERT INTO forms ({', '.join(_quote(c) for c in insert_cols)}) "
               f"VALUES ({', '.join('?' * len(insert_cols))})")
        seq = 0
        sources = []
        for src_idx, p in enumerate(paths):
            stamp = _file_stamp(p)
            stamp["sha256"] = _sha256(p)
            n_rows = 0
            for chunk in pd.read_csv(
                p, dtype=str, keep_default_na=False,
                chunksize=chunksize, usecols=lambda c: c in usecols,
            ):
                chunk = chunk.fillna("")
                gc = chunk["Glottocode"].astype(str).str.strip().str.lower()
                n = len(chunk)
                frame = pd.DataFrame({
                    "seq": range(seq, seq + n),
                    "src": src_idx,
                    "src_row": range(n_rows, n_rows + n),
                    "gc_lc": gc.to_numpy(),
                })
                for c in columns:
                    frame[c] = chunk[c].to_numpy()
                conn.executemany(sql, frame.itertuples(index=False, name=None))
                seq += n
                n_rows += n
            if _file_stamp(p) != {k: stamp[k] for k in ("path", "size", "mtime_ns")}:
                raise RuntimeError(f"{p} changed while it was being loaded")
            stamp["rows"] = n_rows
            sources.append(stamp)
            logger.info("intake-db: %s → %d rows", p, n_rows)

        logger.info("intake-db: creating index")
        conn.execute(INDEX_SQL)
        meta = {
            "schema_version": SCHEMA_VERSION,
            "loader": _loader_id(),
            "columns": json.dumps(columns),
            "sources": json.dumps(sources),
            "rows": str(seq),
        }
        conn.executemany("INSERT INTO meta VALUES (?, ?)", meta.items())
        conn.commit()
        conn.execute("ANALYZE")
        conn.commit()
    finally:
        conn.close()
    return {"rows": seq, "sources": sources, "columns": columns}


class IntakeDB:
    """Read-only handle on an intake database built by `build_intake_db`."""

    def __init__(self, db_path: Path, cache_kib: int | None = None) -> None:
        if cache_kib is None:
            cache_kib = int(os.environ.get("ARCA_INTAKE_DB_CACHE_KIB", "8192"))
        self.path = Path(db_path)
        if not self.path.exists():
            raise FileNotFoundError(self.path)
        self.conn = sqlite3.connect(f"file:{self.path}?mode=ro", uri=True)
        try:
            self.conn.execute(f"PRAGMA cache_size=-{int(cache_kib)}")
            self.conn.execute("PRAGMA mmap_size=0")
            meta = dict(self.conn.execute("SELECT key, value FROM meta"))
            if meta.get("schema_version") != SCHEMA_VERSION:
                raise ValueError(f"{self.path}: schema {meta.get('schema_version')!r}, want {SCHEMA_VERSION!r}")
            self.loader = meta.get("loader", "")
            self.columns: list[str] = json.loads(meta["columns"])
            self.sources: list[dict] = json.loads(meta["sources"])
            self.rows = int(meta["rows"])
        except BaseException:
            self.conn.close()
            raise
        self._select = ", ".join(_quote(c) for c in self.columns)

    def close(self) -> None:
        self.conn.close()

    def is_current(self, forms_paths: list[Path]) -> bool:
        """True when the DB was built, by this loader, from exactly these
        files with unchanged content (size, mtime and sha256)."""
        if self.loader != _loader_id():
            return False
        paths = [p for p in forms_paths if p.exists()]
        if len(paths) != len(self.sources):
            return False
        for p, rec in zip(paths, self.sources):
            stamp = _file_stamp(p)
            if any(stamp[k] != rec.get(k) for k in ("path", "size", "mtime_ns")):
                return False
            if _sha256(p) != rec.get("sha256"):
                return False
        return True

    def _frame(self, rows: list[tuple], with_gc: bool) -> pd.DataFrame:
        cols = [*self.columns, "_glottocode_lc"] if with_gc else list(self.columns)
        if not rows:
            return pd.DataFrame({c: pd.Series([], dtype=object) for c in cols})
        return pd.DataFrame.from_records(rows, columns=cols)

    def slice(self, gc_lc: str, dataset: str) -> pd.DataFrame:
        """Rows with this lower-cased glottocode and Dataset, in intake order.

        Same columns as the DataFrame path (`_load_intake_for_glottocodes`),
        including ``_glottocode_lc``. A non-string *dataset* (e.g. an int
        from YAML) matches nothing, as with pandas ``==`` on str values —
        SQLite's TEXT affinity would otherwise coerce it.
        """
        if not isinstance(gc_lc, str) or not isinstance(dataset, str):
            return self._frame([], with_gc=True)
        rows = self.conn.execute(
            f'SELECT {self._select}, gc_lc FROM forms '
            f'WHERE gc_lc = ? AND "Dataset" = ? ORDER BY seq',
            (gc_lc, dataset),
        ).fetchall()
        return self._frame(rows, with_gc=True)

    def iter_chunks(self, chunksize: int = _CHUNKSIZE):
        """Every row, in intake order, as DataFrames of *chunksize* rows."""
        cur = self.conn.execute(f"SELECT {self._select} FROM forms ORDER BY seq")
        while True:
            rows = cur.fetchmany(chunksize)
            if not rows:
                break
            yield self._frame(rows, with_gc=False)
