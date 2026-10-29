# Arca Verborum research explorer

The default explorer covers all accepted varieties. The **Core source collection** is a collection preset; the **161 basic concepts** are a separate vocabulary filter. The preceding Core-only interface is preserved at `core.html` and still uses `arca-core.sqlite.gz`.

Mixed-source constructions preserve original source IDs and reviewed supplementary evidence. Core source collection filtering applies per lexical row and uses its own coverage metrics; it never admits non-Core supplements. Separate supplied pronunciation readings retain raw IPA, qualifier tags and stable pronunciation IDs.

The initial catalog contains variety metadata, aliases from selected source samples, parent relationships, concept definitions, supported-core coverage and source metadata. Lexical records load by family only when requested. The complete accepted aggregate is split into 399 family shards (about 111 MB compressed in this build); no visitor downloads all shards on startup. Downloads are cached by content hash. Older form links with shifted aggregate row numbers resolve by unchanged variety/source-form identity when the match is unique. SQLite, decompression, search and SQL run in `research-worker.js`, off the UI thread.

## Rebuild and deploy

After the accepted builds and aggregate are current:

```bash
python scripts/build_research_web.py
python -m http.server 8799 --directory web
```

Commit `web/data/` alongside interface changes, then push master. The Pages workflow copies committed artifacts; it does not fetch sources or rebuild the aggregate. The manifest is revalidated at startup; catalog and family caches use content hashes. Bump `VERSION` in `research.js` and matching asset versions in `index.html` when changing interface/worker behavior. Check the public manifest, counts and representative workflows after deployment.

The builder never changes source acceptance, licenses, concept mappings or cognate judgments. It preserves form provenance, source glosses, local and shared mapping-review notes, uncertainty and loan flags, supplied alignment/morpheme evidence, and separate individual cognate memberships. It renames the aggregate's `Cognate_Source` to `cognate_evidence_source` to distinguish it from `cognate_source` in SQLite's case-insensitive column namespace.

The `rvidinfinitives` data component retains GPLv3 terms: [notice](data/RVID_NOTICE.txt),
[licence](data/RVID_GPL-3.0.txt), and [source/reproduction](../docs/RVID_DATA_LICENSE.md).
Source licences are independent of the repository software licence.

## Variety pages and geographic display

Variety pages show a regional catalog-location map, ISO/catalog/parent identity, country codes, source aliases, documentation dates, structured source citations and licenses, cognate-method counts, semantic-field coverage, and observed segment-token counts. Segment tokens come only from source/profile-supported forms in the current view, with their origins separated; this is not a verified phoneme inventory. Missing coordinates or metadata stay explicit. All maps share opaque land, contrasting country borders, country-name hover labels, and light/dark palettes. Locations are approximate catalog points, not inferred recording sites or language boundaries.

## Research workflows and limitations

- Select varieties in the catalog, then choose concepts in Compare. Matrices support up to 16 varieties and 200 concepts at once; all 161 basic concepts fit. Synonyms remain grouped in cells. Comparisons use explicit variety selections across catalog family/name/area filters, while collection, vocabulary and transcription choices are respected.
- Catalog family/name/area/tier/coverage filters select catalog entries. A linked variety detail follows that named variety plus vocabulary/transcription filters; it states that scope explicitly. Form provenance follows the explicit record. Concept and cognate views use the chosen family and catalog scope. SQL is explicitly independent of UI filters.
- Core coverage counts distinct supported concepts, not synonyms. Source-supplied and profile-inferred segments count as supported, but neither mechanical validity nor a tier certifies pronunciation accuracy. Resegmented and unresolved records stay distinguishable.
- Cognate codes remain source-scoped; combined codes are individual memberships, not a composite set. Morpheme alignment is displayed only when supplied; no alignments are inferred. Source etymology annotations are not relabeled expert comparative evidence.
- Search offers literal, segment-token and advanced regex modes. Optional combining-diacritic/case folding is a discovery aid, not phonemic equivalence. The displayed search/export subset is capped at 500 matches with a full match count; refine the query for larger results.
- CSV/TSV exports preserve original evidence fields; selection manifests include build hashes, filters, source versions, licenses and scope. Copy citation includes the build URL and dataset citations; individual form keys remain in `bibtex_key`, with original references in `data/sources.bib`. Missing source/license metadata is disclosed rather than invented.
- Historical/reconstruction labels are explicitly identified as catalog-name labels, not independent historical classifications. Documentation dates and Glottolog levels are displayed when available. Coordinates are approximate catalog locations, not speaker distributions or boundaries. Colocated records are grouped in map popups.
- Missing support means not supplied, not mapped, or unresolved here; it does not establish lexical absence. English sense reviews do not independently certify target-language translations. Source glosses, concept definitions, review notes and packets support further checking.
- SQL tables: `languages`, `parameters`, `sources`, `forms`, `memberships`. Catalog tables cover all accepted entries; lexical tables contain loaded families only. SQLite query-only mode and a schema-PRAGMA allowlist prevent writes through the SQL interface. Long SQL/regex work is terminated after 15 seconds; reload resets the worker while preserving URL selections. Very large multi-family sessions remain constrained by device memory; loading fewer families or reloading reduces memory use.

## Verification

```bash
pytest tests/test_research_web.py
node --check web/research.js
node --check web/research-worker.js
# Install Playwright and its browser dependencies in your test environment first.
uv run --no-project --with playwright python web/tests/research_browser.py http://127.0.0.1:8799/
```

The browser check covers collection scopes, persistent URLs, comparison, provenance, CSV/manifests, search, read-only SQL, maps, keyboard links, and mobile overflow. Run `web/tests/mixed_source_browser.py URL` as an additional check of pronunciation alternatives, source attribution and Core-source isolation. Source datasets and the full aggregate remain reproducible through the repository's normal build pipeline.

## Archived Core-only explorer



`arca-core.sqlite.gz` + `BUILD_INFO` are generated from a built release:

```bash
python build.py update <core ids> && python build.py aggregate && python build.py release
python scripts/build_web_db.py          # -> web/arca-core.sqlite.gz + web/BUILD_INFO
```

They are committed so the site deploys by pushing `web/`, but they are
regeneratable and should be refreshed whenever the release changes.

The Pages workflow copies these committed artifacts; it does **not** rebuild
the release or database. A successful deployment alone does not mean the data
is current. After a data refresh, bump the cache version described below, commit
the artifacts, and verify the live `/BUILD_INFO` date/counts against the local
file. The explorer shows the build date beside its counts.

Core includes only sources flagged `CORE=TRUE` in `datasets.csv`. Rebuilding
the full aggregate does not automatically admit other sources to this website.

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

Source-scoped orthographic supplements retain `Segments_Source=profile` in
research exports, with the profile name/hash and original dictionary evidence
in comments. They are distinct from supplied source IPA and do not apply to
primary-source forms. The Iquito pilot is covered by the mixed-source browser
check. Current coverage and held candidates are documented in
`docs/COVERAGE_BATCH_2026-10-27.md` and the ranked opportunity CSV.

Recording placeholders from Mixe-Zoquean Voices are excluded from lexical tables.
`data/recordings.csv` retains their source identities/citations; its manifest entry
hashes that separate metadata and affected variety pages link the download.

Historical-data checks: `web/tests/ancient_browser.py URL` verifies Etruscan and
Elamite written-only exports, automatic-conversion disclosure, exact Attic scope,
and the Classic Mayan scholarly transcription with its sign/attestation metadata.

African-data checks: `web/tests/african_browser.py URL` verifies written-only
Konyagi/Gimnime and NC-SA terms; Kam source-authorized readings with M-tone caveat;
Gyeli/Hdi/Fwe/Sidaama dictionary primaries retaining all earlier GLED rows; exact
Sidaama phonemic fields and semantic corrections; stable Momi/Vere identity;
Shashi optional-prefix evidence; original West African tone/nasality exports.
The AF01–AF09 and AX01–AX06 execution reports record source reviews and holds.
