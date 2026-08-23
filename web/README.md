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
| `vendor/leaflet.{js,css}` + `vendor/images/` | Leaflet (MIT), vendored (incl. marker/layer icons) |
| `vendor/world.geo.json` | world countries GeoJSON for the flat basemap |
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

If a change doesn't appear, your browser cached the old assets: **hard-refresh**
(Ctrl/Cmd-Shift-R). To prevent stale caches across deploys, `app.js`/`style.css`
and the data fetches carry a `?v=` cache-buster: bump `AV_VER` in `app.js` **and**
the `?v=` in `index.html` (keep them in sync) whenever you change the app or
rebuild the dataset.

## Views

Varieties · Concepts · **Map** · Search forms · Statistics · SQL (read-only). A
"basic-vocabulary core only" toggle filters to the 161 frozen core concepts.

**Maps** (Leaflet, vendored; flat vector basemap from `vendor/world.geo.json`,
no external tiles): the **Map** tab plots all varieties, colour-coded by family,
macroarea, tier, or coverage; each **concept** view carries a per-family
**cognate map** (varieties coloured by cognate set — the CLLD signature). Needs
`Latitude`/`Longitude` in the release (joined from Glottolog by `build.py
release`).

Shareable URLs via hash: top-level views (`#map`, `#concepts`, …) plus
deep-links `#concept:<concept_id>` and `#variety:<av_id>`.
