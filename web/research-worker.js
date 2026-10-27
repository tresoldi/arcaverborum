/* SQLite and large downloads live off the UI thread. */
importScripts('vendor/sql-wasm.js');
let db, manifest, catalog;
const loaded = new Set();
const ident = value => '"' + value.replaceAll('"', '""') + '"';
const scalar = value => value == null ? '' : typeof value === 'boolean' ? +value :
  typeof value === 'object' ? JSON.stringify(value) : value;
async function download(spec) {
  let cache;
  try { cache = await caches.open('arca-research-v1'); } catch (_) { /* private/offline cache unavailable */ }
  const key = new URL(spec.url + '?sha=' + spec.sha256, self.location.href).href;
  let response = cache && await cache.match(key);
  if (!response) {
    response = await fetch(key);
    if (!response.ok) throw Error('Download failed: ' + response.status);
    if (cache) { try { await cache.put(key, response.clone()); } catch (_) { /* storage quota */ } }
  }
  let bytes = new Uint8Array(await response.arrayBuffer());
  if (bytes[0] === 31 && bytes[1] === 139) {
    const hash = [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))]
      .map(x => x.toString(16).padStart(2, '0')).join('');
    if (hash !== spec.sha256) { if (cache) await cache.delete(key); throw Error('Data checksum mismatch; retry download.'); }
    bytes = new Uint8Array(await new Response(new Blob([bytes]).stream()
      .pipeThrough(new DecompressionStream('gzip'))).arrayBuffer());
  }
  return JSON.parse(new TextDecoder().decode(bytes));
}
function insertObjects(name, rows) {
  const fields = rows.length ? [...new Set(rows.flatMap(row => Object.keys(row)))] : ['ID'];
  db.run(`CREATE TABLE ${name}(${fields.map(ident).join(',')})`);
  const statement = db.prepare(`INSERT INTO ${name} VALUES(${fields.map(() => '?').join(',')})`);
  for (const row of rows) statement.run(fields.map(key => scalar(row[key])));
  statement.free();
}
function query(sql, params = [], limit = 1001) {
  const statement = db.prepare(sql);
  statement.bind(params);
  const rows = [];
  try { while (rows.length < limit && statement.step()) rows.push(statement.getAsObject()); }
  finally { statement.free(); }
  return rows;
}
let chain = Promise.resolve();
self.onmessage = ({data}) => { chain = chain.then(async () => {
  const {id, kind, payload = {}} = data;
  try {
    let result;
    if (kind === 'init') {
      manifest = await fetch('data/manifest.json?v=' + payload.version, {cache:'no-cache'}).then(r => {
        if (!r.ok) throw Error('Cannot load data manifest'); return r.json();
      });
      catalog = await download(manifest.catalog);
      const SQL = await initSqlJs({locateFile: name => 'vendor/' + name});
      db = new SQL.Database();
      db.run('BEGIN');
      insertObjects('languages', catalog.languages);
      insertObjects('parameters', catalog.concepts);
      insertObjects('sources', catalog.sources);
      db.run(`CREATE TABLE forms(${manifest.fields.map(ident).join(',')})`);
      db.run('CREATE TABLE memberships(form_id,set_id,concept_id,source)');
      db.run('CREATE INDEX forms_variety ON forms(av_id)');
      db.run('CREATE INDEX forms_concept ON forms(concept_id)');
      db.run('CREATE INDEX cognate_lookup ON memberships(set_id,concept_id)');
      db.run('COMMIT');
      db.run('PRAGMA query_only=ON');
      result = {manifest, catalog};
    } else if (kind === 'load') {
      for (const family of payload.families) {
        if (loaded.has(family)) continue;
        const spec = manifest.shards[family];
        if (!spec) throw Error('Unknown family: ' + family);
        postMessage({id, progress: `Loading ${family}: ${(spec.bytes / 1e6).toFixed(1)} MB…`});
        const rows = await download(spec);
        db.run('PRAGMA query_only=OFF');
        db.run('BEGIN');
        const st = db.prepare(`INSERT INTO forms VALUES(${manifest.fields.map(() => '?').join(',')})`);
        const member = db.prepare('INSERT INTO memberships VALUES(?,?,?,?)');
        const ix = Object.fromEntries(manifest.fields.map((f, i) => [f, i]));
        try {
          for (const row of rows) {
            st.run(row);
            for (const code of JSON.parse(row[ix.cognate_sets] || '[]'))
              member.run([row[ix.ID], code, row[ix.concept_id], row[ix.cognate_source]]);
          }
          db.run('COMMIT'); loaded.add(family);
        } catch (error) { db.run('ROLLBACK'); throw error; }
        finally { st.free(); member.free(); db.run('PRAGMA query_only=ON'); }
      }
      result = [...loaded];
    } else if (kind === 'query') {
      result = query(payload.sql, payload.params, payload.limit || 1001);
    } else if (kind === 'sql') {
      // SQLite enforces read-only even for CTEs, PRAGMAs and nested statements.
      if (!/^\s*(SELECT|WITH|EXPLAIN|PRAGMA)\b/i.test(payload.sql)) throw Error('Use a read-only query.');
      if (/^\s*PRAGMA\b/i.test(payload.sql) && !/^\s*PRAGMA\s+(?:(?:table_info|table_xinfo|index_list|index_info|foreign_key_list)\s*\(\s*[A-Za-z_][A-Za-z_0-9]*\s*\)|compile_options|database_list)\s*;?\s*$/i.test(payload.sql))
        throw Error('Only schema-inspection PRAGMAs are allowed.');
      result = query(payload.sql, [], 1001);
    } else if (kind === 'search') {
      const terms = payload.term;
      let regex;
      if (payload.mode === 'regex') { regex = new RegExp(terms, 'u'); }
      const fold = s => payload.fold ? s.normalize('NFD').replace(/\p{M}/gu, '').toLowerCase() : s;
      const statement = db.prepare(payload.sql);
      statement.bind(payload.params);
      let count = 0;
      const rows = [];
      try {
        while (statement.step()) {
          const row = statement.getAsObject();
          const text = row.Form + '\n' + row.Segments;
          const matches = payload.mode === 'tokens'
            ? (' ' + fold(row.Segments) + ' ').includes(' ' + fold(terms.trim().replace(/\s+/g, ' ')) + ' ')
            : regex ? regex.test(text) : fold(text).includes(fold(terms));
          if (matches) { count++; if (rows.length < 500) rows.push(row); }
        }
      } finally { statement.free(); }
      result = {rows, count};
    } else throw Error('Unknown operation');
    postMessage({id, result});
  } catch (error) { postMessage({id, error: error.message}); }
}); };
