"""Arca Verborum data explorer — a small console "database interface".

The aggregate output (``output/aggregate/``) is a 500 MB / ~2 M-row CSV
plus a few small companion tables. This module loads them once into a
local SQLite database (``output/explore.sqlite``) with the obvious
indexes, then answers exploratory questions instantly:

  index         (Re)build the SQLite index from output/aggregate/.
  langs         List varieties (filter by family/macroarea/tier/source/name).
  lang          All forms of one variety (av_id, Glottocode, or name).
  concept       All forms of a concept across varieties.
  cognate       All forms in a cognate set; or the sets for a concept.
  form          Search surface forms (Form/Value) with LIKE.
  concepts      List concepts with form/variety coverage.
  descendants   Etymological descent (Wiktionary) — not yet in the data.
  stats         Summary statistics, optionally scoped to one family.
  sql           Run a read-only SQL query against the index.
  info          Show the index's tables, columns, and build provenance.

Everything below the CLI is plain functions over a ``sqlite3.Connection``
returning ``(columns, rows)`` so it is easy to test and reuse. The DB is
all-TEXT (faithful to the CSVs); numeric work happens via ``CAST`` in SQL.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("explore")

# repo root = .../src/arcaverborum/explore.py -> parents[2]
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_AGG_DIR = PROJECT_ROOT / "output" / "aggregate"
DEFAULT_DB_PATH = PROJECT_ROOT / "output" / "explore.sqlite"

# CSV file -> SQLite table. forms is the big one (loaded in chunks).
_TABLES = {
    "forms": "forms.csv",
    "varieties": "varieties.csv",
    "parameters": "parameters.csv",
    "metadata": "metadata.csv",
}

# SQLite identifiers are case-insensitive, but the forms schema ships two
# columns that differ only in case: `Cognate_Source` (the CLDF source key)
# and `cognate_source` (the av-level cognate dataset pick). Give the CLDF one
# a distinct, descriptive name so both survive in the index.
_KNOWN_RENAMES = {"Cognate_Source": "Cognate_Source_cldf"}

# Indexes to create on the forms table after bulk load.
_FORM_INDEXES = (
    "av_id",
    "Glottocode",
    "concept_id",
    "concept_label",
    "Concepticon_ID",
    "canonical_cognate_id",
    "Cognacy",
    "Form",
)

# Cognate-set identity. ``canonical_cognate_id`` is the intended cross-variety
# id but is not populated yet; ``Cognacy`` holds the per-source cognate code.
# Prefer the canonical id when present, else fall back to Cognacy, so cognate
# queries work today and sharpen automatically once canonical ids are filled.
_COG_KEY = "COALESCE(NULLIF(canonical_cognate_id, ''), Cognacy)"

# Curated console column sets (CSV/`sql` output is never trimmed).
_LANG_COLS = ("concept_id", "concept_label", "Value", "Form",
              "Segments", "Cognacy", "canonical_cognate_id", "Loan", "quality_score")
_CONCEPT_COLS = ("av_id", "Variety_Name", "Family", "Form", "Segments",
                 "canonical_cognate_id", "Loan", "transcription_source")
_COGNATE_COLS = ("av_id", "Variety_Name", "concept_id", "concept_label", "Form",
                 "Segments", "Cognacy", "Loan")
_FORM_SEARCH_COLS = ("av_id", "Variety_Name", "concept_id", "concept_label", "Form",
                     "Segments", "canonical_cognate_id")


# --------------------------------------------------------------------------
# Index building
# --------------------------------------------------------------------------

def _file_sig(path: Path) -> str:
    if not path.exists():
        return ""
    st = path.stat()
    return f"{st.st_size}:{int(st.st_mtime)}"


def sources_signature(agg_dir: Path) -> str:
    """A signature over the source CSVs, used to detect a stale index."""
    return json.dumps({name: _file_sig(agg_dir / fn) for name, fn in _TABLES.items()},
                      sort_keys=True)


def dedupe_columns(columns: list[str]) -> dict[str, str]:
    """Map original→renamed column names so none collide case-insensitively.

    SQLite treats identifiers case-insensitively, so two CSV columns that
    differ only in case cannot coexist in one table. Apply the known,
    descriptive rename first; fall back to numeric suffixes otherwise.
    """
    rename: dict[str, str] = {}
    seen: set[str] = set()
    for col in columns:
        target = _KNOWN_RENAMES.get(col, col)
        if target.lower() in seen:
            i = 2
            while f"{target}_{i}".lower() in seen:
                i += 1
            target = f"{target}_{i}"
        seen.add(target.lower())
        if target != col:
            rename[col] = target
    return rename


def build_index(
    agg_dir: Path = DEFAULT_AGG_DIR,
    db_path: Path = DEFAULT_DB_PATH,
    *,
    force: bool = False,
    chunksize: int = 100_000,
) -> dict:
    """Load output/aggregate/*.csv into a fresh SQLite index.

    Skips the rebuild when the DB already reflects the current source
    files (unless ``force``). Returns a small stats dict.
    """
    import pandas as pd

    forms_csv = agg_dir / _TABLES["forms"]
    if not forms_csv.exists():
        raise FileNotFoundError(
            f"No aggregate forms.csv at {forms_csv}. Run `python build.py aggregate` first."
        )

    sig = sources_signature(agg_dir)
    if db_path.exists() and not force:
        try:
            con = sqlite3.connect(db_path)
            stored = con.execute(
                "SELECT value FROM _meta WHERE key='sources_signature'"
            ).fetchone()
            con.close()
            if stored and stored[0] == sig:
                logger.info("Index already up to date (%s). Use --force to rebuild.", db_path)
                return {"status": "up-to-date", "db": str(db_path)}
        except sqlite3.Error:
            pass  # malformed/old DB — fall through and rebuild

    db_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = db_path.with_suffix(".sqlite.tmp")
    if tmp_path.exists():
        tmp_path.unlink()

    con = sqlite3.connect(tmp_path)
    con.execute("PRAGMA journal_mode = OFF")
    con.execute("PRAGMA synchronous = OFF")

    counts: dict[str, int] = {}
    try:
        # Small companion tables: single read each.
        for table in ("varieties", "parameters", "metadata"):
            path = agg_dir / _TABLES[table]
            if not path.exists():
                logger.warning("Missing %s — skipping table %r", path, table)
                continue
            df = pd.read_csv(path, dtype=str, keep_default_na=False)
            df.rename(columns=dedupe_columns(list(df.columns)), inplace=True)
            df.to_sql(table, con, if_exists="replace", index=False)
            counts[table] = len(df)
            logger.info("Loaded %s: %d rows", table, len(df))

        # forms: chunked load so memory stays bounded.
        logger.info("Loading forms from %s (chunked) …", forms_csv)
        n = 0
        for i, chunk in enumerate(
            pd.read_csv(forms_csv, dtype=str, keep_default_na=False, chunksize=chunksize)
        ):
            chunk.rename(columns=dedupe_columns(list(chunk.columns)), inplace=True)
            chunk.to_sql("forms", con, if_exists="replace" if i == 0 else "append", index=False)
            n += len(chunk)
            if (i + 1) % 5 == 0:
                logger.info("  … %d rows", n)
        counts["forms"] = n
        logger.info("Loaded forms: %d rows", n)

        logger.info("Creating indexes …")
        for col in _FORM_INDEXES:
            con.execute(f'CREATE INDEX IF NOT EXISTS idx_forms_{col} ON forms("{col}")')

        con.execute("CREATE TABLE _meta (key TEXT PRIMARY KEY, value TEXT)")
        meta = {
            "sources_signature": sig,
            "built_on": datetime.now().isoformat(timespec="seconds"),
            "row_counts": json.dumps(counts),
            "aggregate_dir": str(agg_dir),
        }
        con.executemany("INSERT INTO _meta VALUES (?, ?)", list(meta.items()))
        con.commit()
    finally:
        con.close()

    tmp_path.replace(db_path)  # atomic swap: never leave a half-built DB in place
    logger.info("Wrote index → %s", db_path)
    return {"status": "built", "db": str(db_path), "counts": counts}


# --------------------------------------------------------------------------
# Connection helpers
# --------------------------------------------------------------------------

def connect(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Open the index read-only-ish; error clearly if it does not exist."""
    if not db_path.exists():
        raise FileNotFoundError(
            f"No index at {db_path}. Build it with `python explore.py index`."
        )
    con = sqlite3.connect(db_path)
    con.execute("PRAGMA query_only = ON")
    return con


def index_is_stale(con: sqlite3.Connection, agg_dir: Path = DEFAULT_AGG_DIR) -> bool:
    """True when the source CSVs have changed since the index was built."""
    row = con.execute("SELECT value FROM _meta WHERE key='sources_signature'").fetchone()
    return bool(row) and row[0] != sources_signature(agg_dir)


def _table_columns(con: sqlite3.Connection, table: str) -> list[str]:
    return [r[1] for r in con.execute(f"PRAGMA table_info({table})").fetchall()]


# --------------------------------------------------------------------------
# Query helpers — each returns (columns, rows)
# --------------------------------------------------------------------------

def _fetch(con: sqlite3.Connection, sql: str, params: tuple = ()) -> tuple[list[str], list[tuple]]:
    cur = con.execute(sql, params)
    cols = [d[0] for d in cur.description]
    return cols, cur.fetchall()


def _limit_clause(limit: int) -> str:
    # limit <= 0 means "no limit"; otherwise fetch one extra to flag truncation.
    return "" if limit <= 0 else f" LIMIT {limit + 1}"


def _concept_cond(value: str, col_prefix: str = "") -> tuple[str, list[str]]:
    """SQL condition + params matching a concept by our concept_id (exact),
    its label (substring), or — for an all-digits value — the legacy
    numeric Concepticon id.

        bod-hair  -> concept_id = 'bod-hair'
        water     -> concept_id = 'water' OR concept_label LIKE '%water%'
        948       -> Concepticon_ID = '948'
    """
    v = value.strip()
    if v.isdigit():
        return f"{col_prefix}Concepticon_ID = ?", [v]
    return (f"({col_prefix}concept_id = ? OR {col_prefix}concept_label LIKE ?)",
            [v, f"%{v}%"])


def resolve_variety(con: sqlite3.Connection, ident: str) -> str:
    """Resolve an av_id / Glottocode / name to a single av_id.

    Raises LookupError with candidate suggestions on miss or ambiguity.
    """
    ident = ident.strip()
    # 1) exact av_id
    if con.execute("SELECT 1 FROM varieties WHERE av_id = ?", (ident,)).fetchone():
        return ident
    # 2) exact Glottocode
    rows = con.execute(
        "SELECT av_id, Name FROM varieties WHERE lower(Glottocode) = lower(?)", (ident,)
    ).fetchall()
    # 3) exact name (case-insensitive)
    if not rows:
        rows = con.execute(
            "SELECT av_id, Name FROM varieties WHERE lower(Name) = lower(?)", (ident,)
        ).fetchall()
    # 4) name substring
    if not rows:
        rows = con.execute(
            "SELECT av_id, Name FROM varieties WHERE Name LIKE ? ORDER BY Name LIMIT 25",
            (f"%{ident}%",),
        ).fetchall()
    if len(rows) == 1:
        return rows[0][0]
    if not rows:
        raise LookupError(f"No variety matches {ident!r} (tried av_id, Glottocode, name).")
    hint = ", ".join(f"{a} ({n})" for a, n in rows[:25])
    raise LookupError(f"{ident!r} is ambiguous — candidates: {hint}")


def q_langs(
    con: sqlite3.Connection,
    *,
    family: str | None = None,
    macroarea: str | None = None,
    tier: str | None = None,
    source: str | None = None,
    search: str | None = None,
    limit: int = 50,
) -> tuple[list[str], list[tuple]]:
    """List varieties with their form counts, newest filters applied."""
    where, params = [], []
    if family:
        where.append("v.Family LIKE ?")
        params.append(f"%{family}%")
    if macroarea:
        where.append("v.Macroarea = ?")
        params.append(macroarea)
    if tier:
        where.append("v.tier = ?")
        params.append(tier)
    if source:
        where.append("(v.transcription_source = ? OR v.cognate_source = ?)")
        params += [source, source]
    if search:
        where.append("v.Name LIKE ?")
        params.append(f"%{search}%")
    wsql = (" WHERE " + " AND ".join(where)) if where else ""
    sql = (
        "SELECT v.av_id, v.Name, v.Glottocode, v.Family, v.Macroarea, v.tier, "
        "v.transcription_source, COUNT(f.av_id) AS n_forms "
        "FROM varieties v LEFT JOIN forms f ON f.av_id = v.av_id"
        f"{wsql} GROUP BY v.av_id ORDER BY n_forms DESC, v.Name"
        f"{_limit_clause(limit)}"
    )
    return _fetch(con, sql, tuple(params))


def q_lang(
    con: sqlite3.Connection,
    av_id: str,
    *,
    concept: str | None = None,
    limit: int = 0,
) -> tuple[list[str], list[tuple]]:
    """All forms of one variety (optionally filtered to a concept)."""
    where, params = ["av_id = ?"], [av_id]
    if concept:
        cond, cps = _concept_cond(concept)
        where.append(cond)
        params += cps
    sql = (f"SELECT * FROM forms WHERE {' AND '.join(where)} "
           f"ORDER BY concept_id{_limit_clause(limit)}")
    return _fetch(con, sql, tuple(params))


def q_concept(
    con: sqlite3.Connection,
    concept: str,
    *,
    family: str | None = None,
    limit: int = 50,
) -> tuple[list[str], list[tuple]]:
    """All forms of a concept across varieties (concept_id, label, or numeric ID)."""
    cond, cparams = _concept_cond(concept, "f.")
    where, params = [cond], list(cparams)
    if family:
        where.append("v.Family LIKE ?")
        params.append(f"%{family}%")
    sql = (
        "SELECT f.*, v.Family FROM forms f JOIN varieties v ON f.av_id = v.av_id "
        f"WHERE {' AND '.join(where)} ORDER BY v.Family, f.av_id"
        f"{_limit_clause(limit)}"
    )
    return _fetch(con, sql, tuple(params))


def q_cognate(
    con: sqlite3.Connection,
    cognate_id: str,
    *,
    limit: int = 0,
) -> tuple[list[str], list[tuple]]:
    """All forms in a cognate set (matched on canonical_cognate_id or Cognacy)."""
    sql = (f"SELECT * FROM forms WHERE canonical_cognate_id = ? OR Cognacy = ? "
           f"ORDER BY av_id{_limit_clause(limit)}")
    return _fetch(con, sql, (cognate_id, cognate_id))


def q_cognate_sets(
    con: sqlite3.Connection,
    concept: str,
    *,
    family: str | None = None,
    limit: int = 50,
) -> tuple[list[str], list[tuple]]:
    """Cognate sets attested for a concept, with member/variety counts."""
    cond, cparams = _concept_cond(concept, "f.")
    where = [cond, f"{_COG_KEY} <> ''"]
    params = list(cparams)
    join = ""
    if family:
        join = "JOIN varieties v ON f.av_id = v.av_id"
        where.append("v.Family LIKE ?")
        params.append(f"%{family}%")
    sql = (
        f"SELECT {_COG_KEY} AS cognate_key, f.concept_id, f.concept_label, "
        "COUNT(*) AS n_forms, COUNT(DISTINCT f.av_id) AS n_varieties "
        f"FROM forms f {join} WHERE {' AND '.join(where)} "
        f"GROUP BY {_COG_KEY}, f.concept_id, f.concept_label "
        f"ORDER BY n_varieties DESC, n_forms DESC{_limit_clause(limit)}"
    )
    return _fetch(con, sql, tuple(params))


def q_form_search(
    con: sqlite3.Connection,
    pattern: str,
    *,
    av_id: str | None = None,
    concept: str | None = None,
    exact: bool = False,
    limit: int = 50,
) -> tuple[list[str], list[tuple]]:
    """Search surface forms by Form/Value (substring by default)."""
    needle = pattern if exact else f"%{pattern}%"
    where = ["(Form LIKE ? OR Value LIKE ?)"]
    params: list[str] = [needle, needle]
    if av_id:
        where.append("av_id = ?")
        params.append(av_id)
    if concept:
        cond, cps = _concept_cond(concept)
        where.append(cond)
        params += cps
    sql = (f"SELECT * FROM forms WHERE {' AND '.join(where)} "
           f"ORDER BY av_id, concept_id{_limit_clause(limit)}")
    return _fetch(con, sql, tuple(params))


def q_concepts(
    con: sqlite3.Connection,
    *,
    search: str | None = None,
    limit: int = 50,
) -> tuple[list[str], list[tuple]]:
    """Concepts with form and variety coverage, most-covered first."""
    where, params = [], []
    if search:
        cond, cps = _concept_cond(search)
        where.append(cond)
        params += cps
    wsql = (" WHERE " + " AND ".join(where)) if where else ""
    sql = (
        "SELECT concept_id, concept_label, Concepticon_ID, COUNT(*) AS n_forms, "
        "COUNT(DISTINCT av_id) AS n_varieties "
        f"FROM forms{wsql} GROUP BY concept_id, concept_label, Concepticon_ID "
        f"ORDER BY n_varieties DESC, n_forms DESC{_limit_clause(limit)}"
    )
    return _fetch(con, sql, tuple(params))


def q_stats(con: sqlite3.Connection, family: str | None = None) -> dict:
    """Summary statistics over all forms, or one family's subset."""
    if family:
        scope = "WHERE av_id IN (SELECT av_id FROM varieties WHERE Family LIKE ?)"
        fp: tuple = (f"%{family}%",)
    else:
        scope, fp = "", ()

    totals = con.execute(
        f"SELECT COUNT(*), COUNT(DISTINCT av_id), COUNT(DISTINCT concept_id), "
        f"SUM(CASE WHEN Segments <> '' THEN 1 ELSE 0 END), "
        f"SUM(CASE WHEN {_COG_KEY} <> '' THEN 1 ELSE 0 END), "
        f"COUNT(DISTINCT CASE WHEN {_COG_KEY} <> '' THEN {_COG_KEY} END), "
        f"SUM(CASE WHEN Loan = 'true' THEN 1 ELSE 0 END), "
        f"AVG(CASE WHEN quality_score <> '' THEN CAST(quality_score AS REAL) END) "
        f"FROM forms {scope}", fp,
    ).fetchone()

    out: dict = {
        "scope": family or "ALL",
        "forms": totals[0] or 0,
        "varieties": totals[1] or 0,
        "concepts": totals[2] or 0,
        "with_segments": totals[3] or 0,
        "with_cognate": totals[4] or 0,
        "cognate_sets": totals[5] or 0,
        "loans": totals[6] or 0,
        "avg_quality": totals[7],
    }

    def grouped(col: str, table_alias_join: str = "") -> list[tuple]:
        return con.execute(
            f"SELECT {col}, COUNT(*) AS n FROM forms {table_alias_join} {scope} "
            f"GROUP BY {col} ORDER BY n DESC", fp,
        ).fetchall()

    out["by_tier"] = grouped("tier")
    out["by_segments_source"] = grouped("Segments_Source")
    out["by_transcription_source"] = con.execute(
        f"SELECT transcription_source, COUNT(*) AS n FROM forms {scope} "
        f"GROUP BY transcription_source ORDER BY n DESC LIMIT 15", fp,
    ).fetchall()

    if not family:
        out["by_family"] = con.execute(
            "SELECT v.Family, COUNT(*) AS n FROM forms f "
            "JOIN varieties v ON f.av_id = v.av_id "
            "GROUP BY v.Family ORDER BY n DESC LIMIT 15"
        ).fetchall()
    return out


def run_sql(con: sqlite3.Connection, query: str, limit: int = 200) -> tuple[list[str], list[tuple]]:
    """Run a single read-only statement. Rejects anything that could write."""
    stripped = query.strip().rstrip(";").strip()
    if ";" in stripped:
        raise ValueError("Only a single statement is allowed (no ';').")
    head = stripped.split(None, 1)[0].lower() if stripped else ""
    if head not in {"select", "with", "pragma", "explain"}:
        raise ValueError("Only read-only queries are allowed (SELECT / WITH / PRAGMA / EXPLAIN).")
    if limit > 0 and head in {"select", "with"} and " limit " not in f" {stripped.lower()} ":
        stripped += f" LIMIT {limit}"
    return _fetch(con, stripped)


def index_info(con: sqlite3.Connection, agg_dir: Path = DEFAULT_AGG_DIR) -> dict:
    """Provenance + schema of the index, for `info`."""
    meta = dict(con.execute("SELECT key, value FROM _meta").fetchall())
    tables = [r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' "
        "AND name <> '_meta' ORDER BY name"
    ).fetchall()]
    schema = {}
    for t in tables:
        n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        schema[t] = {"rows": n, "columns": _table_columns(con, t)}
    return {"meta": meta, "schema": schema, "stale": index_is_stale(con, agg_dir)}


# --------------------------------------------------------------------------
# Output formatting
# --------------------------------------------------------------------------

def _truncate(text: str, width: int) -> str:
    return text if len(text) <= width else text[: width - 1] + "…"


def print_table(
    cols: list[str],
    rows: list[tuple],
    *,
    show_cols: tuple[str, ...] | None = None,
    max_col_width: int = 36,
    limit: int = 0,
    file=None,
) -> None:
    """Pretty-print rows as an aligned table, projecting to ``show_cols``.

    If ``limit`` > 0 and exactly ``limit + 1`` rows were fetched, the last
    is dropped and a "more rows exist" note is shown (the +1 sentinel).
    """
    file = file or sys.stdout
    truncated = limit > 0 and len(rows) > limit
    if truncated:
        rows = rows[:limit]

    if show_cols:
        keep = [(i, c) for i, c in enumerate(cols) if c in show_cols]
        # preserve the requested order
        order = {c: k for k, c in enumerate(show_cols)}
        keep.sort(key=lambda ic: order.get(ic[1], 1_000))
        idx = [i for i, _ in keep]
        headers = [c for _, c in keep]
    else:
        idx = list(range(len(cols)))
        headers = list(cols)

    if not rows:
        print("(no rows)", file=file)
        return

    cells = [[_truncate(str(r[i]), max_col_width) for i in idx] for r in rows]
    widths = [len(h) for h in headers]
    for row in cells:
        for c, val in enumerate(row):
            widths[c] = max(widths[c], len(val))

    term_w = shutil.get_terminal_size((120, 24)).columns
    sep = "  "
    # Trim trailing columns that overflow the terminal, noting the elision.
    keep_n = len(headers)
    while keep_n > 1 and sum(widths[:keep_n]) + len(sep) * (keep_n - 1) > term_w:
        keep_n -= 1
    dropped = len(headers) - keep_n

    def fmt(values: list[str]) -> str:
        return sep.join(v.ljust(widths[c]) for c, v in enumerate(values[:keep_n]))

    print(fmt(headers), file=file)
    print(sep.join("-" * widths[c] for c in range(keep_n)), file=file)
    for row in cells:
        print(fmt(row), file=file)

    notes = [f"{len(rows)} row(s)"]
    if truncated:
        notes.append("more exist — raise --limit (0 = all)")
    if dropped:
        notes.append(f"{dropped} column(s) hidden — use --csv for all")
    print("(" + "; ".join(notes) + ")", file=file)


def write_csv(cols: list[str], rows: list[tuple], *, limit: int = 0, file=None) -> None:
    file = file or sys.stdout
    if limit > 0 and len(rows) > limit:
        rows = rows[:limit]
    w = csv.writer(file, lineterminator="\n")  # unix-friendly for pipelines
    w.writerow(cols)
    w.writerows(rows)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def _emit(args, cols, rows, default_cols):
    if getattr(args, "csv", False):
        write_csv(cols, rows, limit=args.limit)
    else:
        print_table(cols, rows, show_cols=default_cols, limit=args.limit)


def _warn_if_stale(con, args):
    try:
        if index_is_stale(con, Path(args.aggregate)):
            logger.warning("Index is older than output/aggregate/ — "
                           "run `python explore.py index` to refresh.")
    except sqlite3.Error:
        pass


def cmd_index(args) -> int:
    build_index(Path(args.aggregate), Path(args.db), force=args.force)
    return 0


def cmd_langs(args) -> int:
    con = connect(Path(args.db))
    _warn_if_stale(con, args)
    cols, rows = q_langs(con, family=args.family, macroarea=args.macroarea,
                         tier=args.tier, source=args.source, search=args.search,
                         limit=args.limit)
    _emit(args, cols, rows, None)
    return 0


def cmd_lang(args) -> int:
    con = connect(Path(args.db))
    _warn_if_stale(con, args)
    try:
        av_id = resolve_variety(con, args.variety)
    except LookupError as exc:
        logger.error("%s", exc)
        return 1
    if av_id != args.variety:
        logger.info("Resolved %r → %s", args.variety, av_id)
    cols, rows = q_lang(con, av_id, concept=args.concept, limit=args.limit)
    _emit(args, cols, rows, _LANG_COLS)
    return 0


def cmd_concept(args) -> int:
    con = connect(Path(args.db))
    _warn_if_stale(con, args)
    cols, rows = q_concept(con, args.concept, family=args.family, limit=args.limit)
    _emit(args, cols, rows, _CONCEPT_COLS)
    return 0


def cmd_cognate(args) -> int:
    con = connect(Path(args.db))
    _warn_if_stale(con, args)
    if args.concept:
        cols, rows = q_cognate_sets(con, args.concept, family=args.family, limit=args.limit)
        _emit(args, cols, rows, None)
    elif args.cognate_id:
        cols, rows = q_cognate(con, args.cognate_id, limit=args.limit)
        _emit(args, cols, rows, _COGNATE_COLS)
    else:
        logger.error("Give a cognate id (a Cognacy/canonical_cognate_id value, e.g. "
                     "`cognate kesslersignificance_6`) or `--concept phy-water` to list "
                     "a concept's cognate sets.")
        return 1
    return 0


def cmd_form(args) -> int:
    con = connect(Path(args.db))
    _warn_if_stale(con, args)
    av_id = None
    if args.lang:
        try:
            av_id = resolve_variety(con, args.lang)
        except LookupError as exc:
            logger.error("%s", exc)
            return 1
    cols, rows = q_form_search(con, args.pattern, av_id=av_id, concept=args.concept,
                               exact=args.exact, limit=args.limit)
    _emit(args, cols, rows, _FORM_SEARCH_COLS)
    return 0


def cmd_concepts(args) -> int:
    con = connect(Path(args.db))
    _warn_if_stale(con, args)
    cols, rows = q_concepts(con, search=args.search, limit=args.limit)
    _emit(args, cols, rows, None)
    return 0


def cmd_descendants(args) -> int:
    print(
        "Etymological descent links are not in the dataset yet.\n"
        "\n"
        "The aggregate forms table carries cognate-set membership "
        "(`Cognacy` / `canonical_cognate_id`), not parent→child descent. Wiktionary "
        "descendant chains are not ingested into the per-variety schema, so a\n"
        "true descendant tree cannot be built from the current data.\n"
        "\n"
        "Closest available relations:\n"
        f"  • forms judged cognate to one form:   "
        f"python explore.py cognate <canonical_cognate_id>\n"
        f"  • cognate sets attested for a concept: "
        f"python explore.py cognate --concept {args.form or '<concept_id>'}\n"
        f"  • find a form first:                   "
        f"python explore.py form {args.form or '<text>'}\n"
        "\n"
        "When descent data is ingested, this command will walk it; the stub "
        "keeps the interface stable."
    )
    return 0


def cmd_stats(args) -> int:
    con = connect(Path(args.db))
    _warn_if_stale(con, args)
    s = q_stats(con, family=args.family)
    if args.csv:
        json.dump(s, sys.stdout, default=str, indent=2)
        print()
        return 0

    def pct(n):
        return f"{n / s['forms']:.1%}" if s["forms"] else "—"

    print(f"Arca Verborum — scope: {s['scope']}")
    print(f"  forms:        {s['forms']:>12,}")
    print(f"  varieties:    {s['varieties']:>12,}")
    print(f"  concepts:     {s['concepts']:>12,}")
    print(f"  with segments:{s['with_segments']:>12,}  ({pct(s['with_segments'])})")
    print(f"  with cognate: {s['with_cognate']:>12,}  ({pct(s['with_cognate'])})  "
          f"in {s['cognate_sets']:,} sets")
    print(f"  loans:        {s['loans']:>12,}  ({pct(s['loans'])})")
    if s["avg_quality"] is not None:
        print(f"  avg quality:  {s['avg_quality']:>12.3f}")

    def block(title, pairs, n=10):
        if not pairs:
            return
        print(f"\n{title}:")
        for label, count in pairs[:n]:
            print(f"  {str(label or '(none)'):28s} {count:>10,}  ({pct(count)})")

    block("By tier", s["by_tier"])
    block("By segments source", s["by_segments_source"])
    block("Top transcription sources", s["by_transcription_source"], n=15)
    if "by_family" in s:
        block("Top families (by forms)", s["by_family"], n=15)
    return 0


def cmd_sql(args) -> int:
    con = connect(Path(args.db))
    _warn_if_stale(con, args)
    try:
        cols, rows = run_sql(con, args.query, limit=args.limit)
    except (ValueError, sqlite3.Error) as exc:
        logger.error("%s", exc)
        return 1
    if args.csv:
        write_csv(cols, rows)
    else:
        print_table(cols, rows, limit=0)
    return 0


def cmd_info(args) -> int:
    con = connect(Path(args.db))
    info = index_info(con, Path(args.aggregate))
    m = info["meta"]
    print(f"Index: {args.db}")
    print(f"  built on:   {m.get('built_on', '?')}")
    print(f"  aggregate:  {m.get('aggregate_dir', '?')}")
    print(f"  stale:      {'YES — rerun `explore.py index`' if info['stale'] else 'no'}")
    print("\nTables:")
    for t, meta in info["schema"].items():
        print(f"  {t:12s} {meta['rows']:>10,} rows")
        print(f"      {', '.join(meta['columns'])}")
    return 0


def _add_common(parser, *, default_limit: int) -> None:
    parser.add_argument("--limit", type=int, default=default_limit,
                        help="Max rows (0 = no limit)")
    parser.add_argument("--csv", action="store_true", help="Emit CSV (all columns) to stdout")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help=argparse.SUPPRESS)
    parser.add_argument("--aggregate", default=str(DEFAULT_AGG_DIR), help=argparse.SUPPRESS)


EXAMPLES = """\
Examples
========

First build the index once (it reads output/aggregate/, produced by
`python build.py aggregate`); rebuild only when the aggregate changes:

  python explore.py index                       # ~25s; --force to rebuild anyway
  python explore.py info                         # tables, columns, is the index stale?

Browse varieties (filters combine):

  python explore.py langs                                  # all, most forms first
  python explore.py langs --family Indo-European
  python explore.py langs --macroarea Eurasia --tier bronze
  python explore.py langs --source wiktionary --search greek
  python explore.py langs --limit 0 --csv > varieties.csv  # full list as CSV

Look at one variety — by av_id, Glottocode, or name (exact then substring):

  python explore.py lang Latin
  python explore.py lang lati1261 --concept phy-water
  python explore.py lang ine-latin --csv > latin.csv       # all 28 columns

Concepts (address by our concept_id, a label substring, or a numeric
Concepticon id):

  python explore.py concepts                               # ranked by coverage
  python explore.py concepts --search hand
  python explore.py concept phy-water                      # our concept_id
  python explore.py concept water                          # label substring
  python explore.py concept phy-water --family Indo-European
  python explore.py concept 948                            # legacy Concepticon ID

Cognates (keyed on canonical_cognate_id, else the per-source Cognacy code):

  python explore.py cognate --concept phy-water            # the sets for a concept
  python explore.py cognate --concept water --family Indo-European
  python explore.py cognate iecor_335                      # members of one set

Search surface forms (Form/Value):

  python explore.py form aqua                              # substring
  python explore.py form water --concept phy-water
  python explore.py form shui --lang mandarin --exact

Statistics:

  python explore.py stats                                  # global
  python explore.py stats --family Sino-Tibetan
  python explore.py stats --csv                            # emit JSON

Raw read-only SQL (tables: forms, varieties, parameters, metadata):

  python explore.py sql "SELECT tier, COUNT(*) FROM forms GROUP BY tier"
  python explore.py sql "SELECT concept_id, COUNT(DISTINCT av_id) n \\
                         FROM forms GROUP BY 1 ORDER BY n DESC LIMIT 10"
  python explore.py sql "SELECT * FROM varieties WHERE Family='Uralic'" --csv

Common flags: --limit N (0 = all rows), --csv (full-fidelity output;
JSON for `stats`). The console view shows a curated subset of columns;
--csv and `sql` emit everything. Run `python explore.py <command> -h`
for a command's own options.
"""


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    argv = sys.argv[1:] if argv is None else list(argv)
    p = argparse.ArgumentParser(
        prog="explore.py", description=__doc__, epilog=EXAMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = p.add_subparsers(dest="cmd", metavar="<command>")

    p_idx = sub.add_parser("index", help="(Re)build the SQLite index from output/aggregate/")
    p_idx.add_argument("--force", action="store_true", help="Rebuild even if up to date")
    p_idx.add_argument("--db", default=str(DEFAULT_DB_PATH))
    p_idx.add_argument("--aggregate", default=str(DEFAULT_AGG_DIR))
    p_idx.set_defaults(fn=cmd_index)

    p_langs = sub.add_parser("langs", aliases=["varieties"], help="List varieties")
    p_langs.add_argument("--family")
    p_langs.add_argument("--macroarea")
    p_langs.add_argument("--tier")
    p_langs.add_argument("--source")
    p_langs.add_argument("--search", help="Name substring")
    _add_common(p_langs, default_limit=50)
    p_langs.set_defaults(fn=cmd_langs)

    p_lang = sub.add_parser("lang", help="All forms of one variety (av_id / Glottocode / name)")
    p_lang.add_argument("variety")
    p_lang.add_argument("--concept",
                        help="Filter to a concept (concept_id, label substring, or Concepticon ID)")
    _add_common(p_lang, default_limit=0)
    p_lang.set_defaults(fn=cmd_lang)

    p_con = sub.add_parser("concept", help="All forms of a concept across varieties")
    p_con.add_argument("concept",
                       help="concept_id (e.g. phy-water), label substring, or Concepticon ID")
    p_con.add_argument("--family")
    _add_common(p_con, default_limit=50)
    p_con.set_defaults(fn=cmd_concept)

    p_cog = sub.add_parser("cognate", help="Forms in a cognate set, or sets for a concept")
    p_cog.add_argument("cognate_id", nargs="?", help="canonical_cognate_id")
    p_cog.add_argument("--concept", help="Instead list the cognate sets for this concept")
    p_cog.add_argument("--family")
    _add_common(p_cog, default_limit=0)
    p_cog.set_defaults(fn=cmd_cognate)

    p_frm = sub.add_parser("form", help="Search surface forms (Form/Value)")
    p_frm.add_argument("pattern")
    p_frm.add_argument("--lang", help="Restrict to one variety")
    p_frm.add_argument("--concept", help="Restrict to a concept")
    p_frm.add_argument("--exact", action="store_true", help="Exact match (no substring)")
    _add_common(p_frm, default_limit=50)
    p_frm.set_defaults(fn=cmd_form)

    p_cs = sub.add_parser("concepts", help="List concepts with coverage")
    p_cs.add_argument("--search", help="concept_id, label substring, or Concepticon ID")
    _add_common(p_cs, default_limit=50)
    p_cs.set_defaults(fn=cmd_concepts)

    p_desc = sub.add_parser("descendants", help="Etymological descent (not yet in data)")
    p_desc.add_argument("form", nargs="?")
    p_desc.set_defaults(fn=cmd_descendants)

    p_stats = sub.add_parser("stats", help="Summary statistics")
    p_stats.add_argument("--family", help="Scope to one family")
    p_stats.add_argument("--csv", action="store_true", help="Emit JSON")
    p_stats.add_argument("--db", default=str(DEFAULT_DB_PATH))
    p_stats.add_argument("--aggregate", default=str(DEFAULT_AGG_DIR))
    p_stats.set_defaults(fn=cmd_stats)

    p_sql = sub.add_parser("sql", help="Run a read-only SQL query")
    p_sql.add_argument("query")
    p_sql.add_argument("--limit", type=int, default=200,
                       help="Auto-append LIMIT if absent (0 = none)")
    p_sql.add_argument("--csv", action="store_true")
    p_sql.add_argument("--db", default=str(DEFAULT_DB_PATH))
    p_sql.add_argument("--aggregate", default=str(DEFAULT_AGG_DIR))
    p_sql.set_defaults(fn=cmd_sql)

    p_info = sub.add_parser("info", aliases=["schema"], help="Show index tables and provenance")
    p_info.add_argument("--db", default=str(DEFAULT_DB_PATH))
    p_info.add_argument("--aggregate", default=str(DEFAULT_AGG_DIR))
    p_info.set_defaults(fn=cmd_info)

    # No command → show the detailed help with examples (not an error).
    if not argv:
        p.print_help()
        return 0

    args = p.parse_args(argv)
    try:
        return args.fn(args)
    except FileNotFoundError as exc:
        logger.error("%s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
