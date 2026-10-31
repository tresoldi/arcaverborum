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
let conceptIndex, activeConcept='', conceptBase;
const languageFamilies=new Map();
async function boundedJSON(spec,base,maxBytes,maxRaw=maxBytes){
  if(!spec||!Number.isInteger(spec.bytes)||spec.bytes<0||spec.bytes>maxBytes)throw Error('Invalid concept data size.');
  const url=new URL(spec.url,base);if(url.origin!==self.location.origin)throw Error('Invalid concept data URL.');
  async function bytes(stream,limit){
    const reader=stream.getReader(),chunks=[];let size=0;
    for(;;){const {done,value}=await reader.read();if(done)break;size+=value.length;if(size>limit){await reader.cancel();throw Error('Concept data exceeded its size limit.');}chunks.push(value);}
    const result=new Uint8Array(size);let at=0;for(const chunk of chunks){result.set(chunk,at);at+=chunk.length;}return result;
  }
  const response=await fetch(url);if(!response.ok)throw Error('Concept data download failed ('+response.status+').');
  let data=await bytes(response.body,spec.bytes);
  const hash=[...new Uint8Array(await crypto.subtle.digest('SHA-256',data))].map(x=>x.toString(16).padStart(2,'0')).join('');
  if(data.length!==spec.bytes||hash!==spec.sha256)throw Error('Concept data checksum mismatch. Reload to use a consistent snapshot.');
  if(data[0]===31&&data[1]===139)data=await bytes(new Blob([data]).stream().pipeThrough(new DecompressionStream('gzip')),maxRaw);
  if(data.length>maxRaw||(spec.raw_bytes!==undefined&&data.length!==spec.raw_bytes))throw Error('Invalid expanded concept data size.');
  return JSON.parse(new TextDecoder().decode(data));
}
function storeLexicalRows(rows,owned=false){
  const statement=db.prepare(`INSERT OR IGNORE INTO forms VALUES(${manifest.fields.map(()=>'?').join(',')})`),
    member=db.prepare('INSERT INTO memberships VALUES(?,?,?,?)'), owner=db.prepare('INSERT INTO concept_rows VALUES(?,?)');
  const ix=Object.fromEntries(manifest.fields.map((f,i)=>[f,i]));
  try{for(const row of rows){
    statement.run(row);if(!db.getRowsModified())continue;
    for(const code of JSON.parse(row[ix.cognate_sets]||'[]'))member.run([row[ix.ID],code,row[ix.concept_id],row[ix.cognate_source]]);
    if(owned)owner.run([row[ix.ID],languageFamilies.get(row[ix.av_id])||'Unclassified']);
  }}finally{statement.free();member.free();owner.free();}
}
async function loadConcept(cid,id){
  if(!manifest.concept_rows)throw Error('Concept entries have not been exported for this snapshot.');
  if(!conceptIndex){
    const spec=manifest.concept_rows;conceptBase=new URL(spec.url,self.location.href);
    conceptIndex=await boundedJSON(spec,self.location.href,4*1024*1024);
    const input=conceptIndex.inputs;
    if(JSON.stringify(input.fields)!==JSON.stringify(manifest.fields)||
       Object.entries(manifest.source_files).some(([k,v])=>input.source_files[k]!==v)||
       Object.keys(input.shards).length!==Object.keys(manifest.shards).length||
       Object.entries(manifest.shards).some(([k,v])=>input.shards[k]?.sha256!==v.sha256)){
      conceptIndex=null;throw Error('Concept entries and lexical data belong to different snapshots.');
    }
  }
  const info=conceptIndex.concepts[cid]||{rows:0,pages:[]};
  if(activeConcept===cid)return {cid,rows:info.rows,build_id:conceptIndex.build_id};
  db.run('PRAGMA query_only=OFF');db.run('BEGIN');
  try{
    db.run('DELETE FROM memberships WHERE form_id IN (SELECT id FROM concept_rows)');
    db.run('DELETE FROM forms WHERE ID IN (SELECT id FROM concept_rows)');db.run('DELETE FROM concept_rows');
    let total=0;
    for(const page of info.pages){
      postMessage({id,progress:`Loading concept entries: ${total.toLocaleString()} of ${info.rows.toLocaleString()}…`});
      const rows=await boundedJSON(page,conceptBase,1024*1024,8*1024*1024),ci=manifest.fields.indexOf('concept_id');
      if(!Array.isArray(rows)||rows.length!==page.rows||rows.length>1000||rows.some(r=>r.length!==manifest.fields.length||r[ci]!==cid))throw Error('Invalid concept entry chunk.');
      storeLexicalRows(rows,true);total+=rows.length;
    }
    if(total!==info.rows)throw Error('Incomplete concept entries.');
    db.run('COMMIT');activeConcept=cid;
  }catch(error){db.run('ROLLBACK');throw error;}finally{db.run('PRAGMA query_only=ON');}
  return {cid,rows:info.rows,build_id:conceptIndex.build_id};
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
      db.run(`CREATE TABLE forms(${manifest.fields.map(f=>ident(f)+(f==='ID'?' PRIMARY KEY':'')).join(',')})`);
      db.run('CREATE TABLE concept_rows(id TEXT PRIMARY KEY,family TEXT)');
      for(const l of catalog.languages)languageFamilies.set(l.av_id,l.Family||'Unclassified');
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
        try {
          storeLexicalRows(rows);
          db.run('DELETE FROM concept_rows WHERE family=?',[family]);
          db.run('COMMIT');loaded.add(family);
        } catch(error){db.run('ROLLBACK');throw error;}
        finally{db.run('PRAGMA query_only=ON');}
      }
      result = [...loaded];
    } else if (kind === 'concept') {
      result=await loadConcept(payload.cid,id);
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
