# Arca Verborum Core — web explorer

A static, browser-native explorer for the Arca Verborum Core dataset. It loads a
gzipped SQLite of the release, inflates it with the browser's native
`DecompressionStream`, and queries it client-side with
[sql.js](https://github.com/sql-js/sql.js). No server, no backend, nothing to
install — deployable as static files (GitHub Pages, via `CNAME`).

## Files

| File | |
|---|---|
| `index.html`, `app.js`, `style.css` | the app (vanilla JS, no framework) |
| `vendor/sql-wasm.{js,wasm}` | sql.js (MIT), vendored |
| `arca-core.sqlite.gz` | the dataset (build artifact; see below) |
| `BUILD_INFO` | version/counts, shown in the header (build artifact) |
| `CNAME` | custom domain for GitHub Pages |

## Rebuilding the data

`arca-core.sqlite.gz` + `BUILD_INFO` are generated from a built release:

```bash
python build.py update <core ids> && python build.py aggregate && python build.py release
python scripts/build_web_db.py          # -> web/arca-core.sqlite.gz + web/BUILD_INFO
```

They are committed so the site deploys by pushing `web/`, but they are
regeneratable and should be refreshed whenever the release changes.

## Local preview

Serve over HTTP (a `file://` open won't work — `fetch` + WASM need a server):

```bash
python -m http.server 8799 --directory web
# open http://localhost:8799/
```

## Views

Varieties · Concepts · Search forms · Statistics · SQL (read-only). A
"basic-vocabulary core only" toggle filters to the 161 frozen core concepts.
Top-level views are shareable via URL hash (e.g. `#concepts`, `#stats`).
