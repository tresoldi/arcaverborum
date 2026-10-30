'use strict';
const VERSION = 'research-20261030-t';
const $ = selector => document.querySelector(selector);
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt = value => Number(value || 0).toLocaleString();
const defaults = {view:'varieties',collection:'all',vocab:'all',family:'',area:'',tier:'',status:'',minCore:0,
  search:'',sort:'supported_core',dir:-1,page:0,columns:[],selected:[],concepts:[],id:'',cid:'',cog:'',term:'',mode:'literal',fold:false};
let state = {...defaults}, catalog, manifest, worker, serial=0, pending=new Map(), loaded=[], epoch=0, map;
const languages = new Map(), concepts = new Map(), sources = new Map();
const statusNames = {source:'Source-supplied',profile:'Profile-inferred',resegmented:'Resegmented',unclean:'Unresolved'};
function href(patch) {
  const next={...state,...patch};
  const compact=Object.fromEntries(Object.entries(next).filter(([key,value])=>JSON.stringify(value)!==JSON.stringify(defaults[key])));
  return '#s=' + encodeURIComponent(JSON.stringify(compact));
}
function navigate(patch, replace=false) {
  const url=href(patch);
  if(replace) { history.replaceState(null,'',url); readRoute(); }
  else if(location.hash!==url) location.hash=url;
  else readRoute();
}
function readRoute() {
  try {
    if(location.hash.startsWith('#s=')) state={...defaults,...JSON.parse(decodeURIComponent(location.hash.slice(3)))};
    else if(location.hash.startsWith('#variety:')) state={...defaults,view:'variety',id:decodeURIComponent(location.hash.slice(9))};
    else if(location.hash.startsWith('#concept:')) state={...defaults,view:'concept',cid:decodeURIComponent(location.hash.slice(9))};
    else state={...defaults,view:location.hash.slice(1)||'varieties'};
    if(!Array.isArray(state.selected)||!Array.isArray(state.concepts)) throw Error('Invalid selection');
    render();
  } catch(error) { $('#app').innerHTML=`<p role="alert">Invalid saved view. <a href="#varieties">Open catalog</a></p>`; }
}
function notice(text, error=false) { $('#activity').textContent=text; $('#activity').classList.toggle('err',error); }
function request(kind,payload={}) {
  const id=++serial;
  return new Promise((resolve,reject)=>{
    const timer=setTimeout(()=>{
      worker.terminate();
      for(const item of pending.values()) { clearTimeout(item.timer); item.reject(Error('Operation timed out. Reload the explorer to reset its data worker; the URL preserves your selection.')); }
      pending.clear(); notice('Query stopped. Reload to reset the data worker.',true);
    },kind==='sql'||kind==='search'?15000:180000);
    pending.set(id,{resolve,reject,timer}); worker.postMessage({id,kind,payload});
  });
}
async function query(sql,params=[],limit=1001) { return request('query',{sql,params,limit}); }
async function ensure(families) {
  const wanted=[...new Set(families)].filter(f=>manifest.shards[f]&&!loaded.includes(f));
  if(wanted.length) { loaded=await request('load',{families:wanted}); notice(`${loaded.length} families loaded. Downloads are cached on this device.`); }
  $('#loaded').textContent=`${loaded.length} families loaded`;
}
function link(text,patch,cls='') { return `<a class="${cls}" href="${esc(href(patch))}">${esc(text)}</a>`; }
function safeURL(url) { return /^https?:\/\//i.test(url||'') ? url : ''; }
function external(text,url) { const valid=safeURL(url); return valid?`<a href="${esc(valid)}" target="_blank" rel="noopener">${esc(text)} ↗</a>`:esc(text); }
function options(items,current,empty='All') { return `<option value="">${esc(empty)}</option>`+items.map(item=>`<option value="${esc(item)}" ${item===current?'selected':''}>${esc(item)}</option>`).join(''); }
function collectionLanguage(l) { return state.collection==='core'&&l?.core_metrics?{...l,...l.core_metrics}:l; }
function coreSourceCondition(alias='f') {
  if(state.collection!=='core')return '1';
  const names=(catalog.core_sources||[]).map(s=>"'"+s.replaceAll("'","''")+"'");
  return names.length?`${alias?alias+'.':''}transcription_source IN (${names.join(',')})`:'0';
}
function scopedLanguages() {
  const term=state.search.toLocaleLowerCase();
  return catalog.languages.map(collectionLanguage).filter(l=>(state.collection!=='core'||l.core_collection)&&(!state.family||(l.Family||'Unclassified')===state.family)&&
    (!state.area||l.Macroarea===state.area)&&(!state.tier||l.tier===state.tier)&&Number(l.supported_core)>=Number(state.minCore||0)&&
    (!state.status||(state.status==='usable'?(l.statuses.source||l.statuses.profile):(l.statuses[state.status]||0)))&&
    (!term||[l.Name,l.av_id,l.Glottocode,l.iso639p3,l.notes,...(l.aliases||[])].some(v=>String(v||'').toLocaleLowerCase().includes(term))));
}
function languageCondition(alias='f') {
  const ids=scopedLanguages().map(l=>l.av_id);
  if(!ids.length) return {sql:'0',params:[]};
  let sql=`${alias}.av_id IN (${ids.map(()=>'?').join(',')})`,params=[...ids];
  sql+=` AND ${coreSourceCondition(alias)}`;
  if(state.vocab==='core') sql+=` AND ${alias}.is_core_concept='true'`;
  if(state.status==='usable') sql+=` AND ${alias}.Segments_Source IN ('source','profile')`;
  else if(state.status) { sql+=` AND ${alias}.Segments_Source=?`; params.push(state.status); }
  return {sql,params};
}
function toolbar() {
  $('#scope').innerHTML=`<label>Collection<select id="collection"><option value="all">All accepted</option><option value="core" ${state.collection==='core'?'selected':''}>Core sources</option></select></label>
    <label>Vocabulary<select id="vocab"><option value="all">All concepts</option><option value="core" ${state.vocab==='core'?'selected':''}>161 basic concepts</option></select></label>
    <label>Family<select id="family">${options([...new Set(catalog.languages.map(l=>l.Family||'Unclassified'))].sort(),state.family,'All families')}</select></label>
    <details class="filter-panel"><summary>More filters</summary><div class="controls">
      <label>Macroarea<select id="area">${options([...new Set(catalog.languages.map(l=>l.Macroarea))].filter(Boolean).sort(),state.area,'All macroareas')}</select></label>
      <label>Construction tier<select id="tier">${options(['gold','silver','bronze','copper'],state.tier,'All tiers')}</select></label>
      <label>Transcription<select id="statusfilter">${options(['usable',...Object.keys(statusNames)],state.status,'Any status').replace('>usable<','>Source or profile<').replace(/>(source|profile|resegmented|unclean)</g,(_,s)=>'>'+statusNames[s]+'<')}</select></label>
      <label>Minimum supported core<input id="minCore" type="number" min="0" max="161" value="${+state.minCore||0}"></label>
      <button id="resetfilters">Reset filters</button></div></details>`;
  for(const key of ['collection','vocab','family','area','tier','minCore']) $('#'+key).onchange=e=>navigate({[key]:e.target.value,page:0});
  $('#statusfilter').onchange=e=>navigate({status:e.target.value,page:0});
  $('#resetfilters').onclick=()=>navigate({family:'',area:'',tier:'',status:'',minCore:0,search:'',page:0});
}
function pager(count,size=50) {
  const pages=Math.max(1,Math.ceil(count/size)),current=Math.min(+state.page||0,pages-1);
  return `<div class="pagination"><button data-page="${current-1}" ${current<=0?'disabled':''}>Previous</button>
    <span>Page ${current+1} of ${pages} · ${fmt(count)} results</span><button data-page="${current+1}" ${current>=pages-1?'disabled':''}>Next</button></div>`;
}
function table(columns,rows,{paginate=true,select=false}={}) {
  if(!rows.length) return '<p class="empty">No matching records. Try removing a filter.</p>';
  const chosen=state.columns.length?columns.filter(c=>state.columns.includes(c.key)||c.key===columns[0].key):columns.filter(c=>!c.optional&&(!select||!matchMedia('(max-width:700px)').matches||['Name','supported_core'].includes(c.key)));
  const sorted=[...rows].sort((a,b)=>{
    const x=a[state.sort],y=b[state.sort];
    return (typeof x==='number'&&typeof y==='number'?x-y:String(x??'').localeCompare(String(y??'')))*(state.dir||1);
  });
  const page=Math.min(+state.page||0,Math.max(0,Math.ceil(sorted.length/50)-1));
  const shown=paginate?sorted.slice(page*50,page*50+50):sorted;
  return `<details class="columns"><summary>Columns</summary>${columns.map(c=>`<label><input type="checkbox" data-column="${esc(c.key)}" ${chosen.includes(c)?'checked':''}>${esc(c.label)}</label>`).join('')}</details>
    ${paginate?pager(rows.length):''}<div class="scroll" role="region" aria-label="Results table" tabindex="0"><table class="${select?'selectable':''}"><thead><tr>${select?'<th scope="col">Compare</th>':''}${chosen.map(c=>`<th scope="col" aria-sort="${state.sort===c.key?(state.dir===1?'ascending':'descending'):'none'}"><button class="sort" data-sort="${esc(c.key)}">${esc(c.label)}${state.sort===c.key?(state.dir===1?' ↑':' ↓'):''}</button></th>`).join('')}</tr></thead><tbody>${shown.map(row=>`<tr>${select?`<td><input type="checkbox" data-select="${esc(row.av_id)}" aria-label="Compare ${esc(row.Name)}" ${state.selected.includes(row.av_id)?'checked':''}></td>`:''}${chosen.map(c=>`<td class="${c.key==='Segments'?'ipa':''}">${c.render?c.render(row):esc(row[c.key])}</td>`).join('')}</tr>`).join('')}</tbody></table></div>${paginate?pager(rows.length):''}`;
}
function wireTable() {
  document.querySelectorAll('[data-page]').forEach(b=>b.onclick=()=>navigate({page:+b.dataset.page}));
  document.querySelectorAll('[data-sort]').forEach(b=>b.onclick=()=>navigate({sort:b.dataset.sort,dir:state.sort===b.dataset.sort?-state.dir:1,page:0}));
  document.querySelectorAll('[data-column]').forEach(input=>input.onchange=()=>navigate({columns:[...document.querySelectorAll('[data-column]:checked')].map(i=>i.dataset.column),page:0}));
  document.querySelectorAll('[data-select]').forEach(input=>input.onchange=()=>{
    const selected=new Set(state.selected); input.checked?selected.add(input.dataset.select):selected.delete(input.dataset.select);
    navigate({selected:[...selected]});
  });
}
function statusBadge(row) { return `<span class="chip status-${esc(row.Segments_Source)}" title="Transcription status is not a certification of pronunciation accuracy">${esc(statusNames[row.Segments_Source]||row.Segments_Source)}</span>`; }
function cognatesCell(row) {
  let codes=[];try{codes=JSON.parse(row.cognate_sets||'[]');}catch(_){/* unavailable */}
  return codes.map(code=>link(code,{view:'cognate',cog:code,cid:row.concept_id,family:languages.get(row.av_id)?.Family||state.family,page:0,columns:[],sort:'Form',dir:1})).join('<br>')||'Not assigned';
}
function formColumns() { return [
  {key:'concept_label',label:'Concept',render:r=>r.concept_id?link(r.concept_label,{view:'concept',cid:r.concept_id,page:0,columns:[]}):'<span class="muted">Unmapped</span>'},
  {key:'Form',label:'Form',render:r=>link(r.Form||r.Value,{view:'form',id:r.ID,columns:[]})},
  {key:'Segments',label:'Segments'},
  {key:'Segments_Source',label:'Transcription',render:statusBadge},
  {key:'av_id',label:'Variety',render:r=>link(languages.get(r.av_id)?.Name||r.av_id,{view:'variety',id:r.av_id,page:0,columns:[]})},
  {key:'cognate_sets',label:'Cognate sets',render:cognatesCell},
  {key:'Cognate_Detection_Method',label:'Cognate evidence',optional:true},
  {key:'transcription_source',label:'Sources',optional:true,render:l=>Object.keys(l.source_counts||{[l.transcription_source]:0}).filter(s=>state.collection!=='core'||catalog.core_sources.includes(s)).map(sourceLink).join(' · ')},
  {key:'Doubt',label:'Source doubt flag',optional:true},
  {key:'Loan',label:'Source loan flag',optional:true},
  {key:'source_gloss',label:'Original source gloss',optional:true},
  {key:'License',label:'License',optional:true}]; }
function downloadFile(name,text,type='text/plain') {
  const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([text],{type}));a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),2000);
}
function delimited(rows,delimiter) {
  const fields=manifest.fields;
  const cell=x=>'"'+String(x??'').replaceAll('"','""')+'"';
  return [fields.map(cell).join(delimiter),...rows.map(r=>fields.map(k=>cell(r[k])).join(delimiter))].join('\r\n');
}
function citation(rows=[]) {
  const used=[...new Set(rows.map(r=>r.transcription_source))];
  return `Arca Verborum research explorer. Build ${manifest.build_date}. ${location.href}\n`+
    used.map(key=>{const s=sources.get(key);return s?`${s.Citation||s.Title||key}\n${s.URL||''}\nLicense: ${s.License||'Not recorded; consult upstream terms'}`:`${key}: consult original source terms.`;}).join('\n\n')+
    '\nForm-level source keys are retained in bibtex_key; consult the bibliography for original references.';
}
function exportControls(rows,description='current selection') {
  const id='exports';
  setTimeout(()=>{
    if(!$('#'+id))return;
    $('#exportcsv').onclick=()=>downloadFile('arca-selection.csv',delimited(rows,','),'text/csv');
    $('#exporttsv').onclick=()=>downloadFile('arca-selection.tsv',delimited(rows,'\t'),'text/tab-separated-values');
    $('#exportmanifest').onclick=()=>downloadFile('arca-selection-manifest.json',JSON.stringify({build:manifest.build_date,
      source_files:manifest.source_files,catalog_sha256:manifest.catalog.sha256,
      family_shards:Object.fromEntries(loaded.map(f=>[f,manifest.shards[f].sha256])),filters:state,url:location.href,loaded_families:loaded,records:rows.length,
      sources:[...new Set(rows.map(r=>r.transcription_source))].map(s=>sources.get(s)||{Dataset:s,License:'Not recorded'}),
      scope:description,transcription_notice:'Profile readings and resegmentation are inferred; valid tokens do not certify pronunciation.'},null,2),'application/json');
    $('#copycitation').onclick=async()=>{try{await navigator.clipboard.writeText(citation(rows));notice('Citation copied.');}catch(_){downloadFile('citation.txt',citation(rows));}};
  },0);
  return `<div id="${id}" class="controls exports"><span>${fmt(rows.length)} records · ${esc(description)}</span><button id="exportcsv">CSV</button><button id="exporttsv">TSV</button><button id="exportmanifest">Selection manifest</button><button id="copycitation">Copy citation</button><a href="data/sources.bib" download>Bibliography</a></div>`;
}
function debouncedInput(selector,key) {
  let timer;const input=$(selector);
  input.oninput=()=>{clearTimeout(timer);timer=setTimeout(()=>navigate({[key]:input.value,page:0},true),300);};
}
async function render() {
  if(!catalog)return;
  const token=++epoch;
  const focused=document.activeElement?.id,position=document.activeElement?.selectionStart;
  if(map){map.remove();map=null;}
  toolbar();
  $('#nav').innerHTML=[['varieties','Varieties'],['concepts','Concepts'],['compare',`Compare (${state.selected.length})`],['map','Map'],['search','Search'],['stats','Coverage'],['sources','Sources'],['sql','SQL'],['about','Guide']]
    .map(([v,label])=>`<a href="${esc(href({view:v,page:0,columns:[],sort:v==='varieties'?'supported_core':'Name',dir:v==='varieties'?-1:1}))}" ${state.view===v?'aria-current="page"':''}>${esc(label)}</a>`).join('');
  $('#app').innerHTML='<p class="empty" role="status">Preparing view…</p>';
  try {
    const views={varieties:showVarieties,variety:showVariety,concepts:showConcepts,concept:showConcept,form:showForm,
      cognate:showCognate,compare:showCompare,map:showMap,search:showSearch,stats:showStats,sources:showSources,sql:showSQL,about:showAbout};
    await (views[state.view]||showVarieties)(token);
    if(token!==epoch)return;
    wireTable();
    if(focused&&$('#'+focused)){const e=$('#'+focused);e.focus();if(position!=null&&e.setSelectionRange)e.setSelectionRange(position,position);}
  } catch(error) { if(token===epoch)$('#app').innerHTML=`<p role="alert" class="err">${esc(error.message)}</p><button onclick="location.reload()">Reload explorer</button>`; }
}
function showVarieties() {
  const rows=scopedLanguages();
  $('#app').innerHTML=`<h2>Varieties</h2><p class="sub">${fmt(rows.length)} matches. Supported core: distinct concepts with source or profile segments. Token validity is not pronunciation verification.</p>
    <label class="search-label">Name, alias, Glottocode or ISO code<input id="varietysearch" type="search" value="${esc(state.search)}" placeholder="e.g. Somali, pann1240, Sinchi Roca"></label>
    <p>${link(`Open comparison workspace (${state.selected.length} selected)`,{view:'compare',page:0,columns:[]},'button')}</p>
    ${table([
      {key:'Name',label:'Variety',render:l=>link(l.Name,{view:'variety',id:l.av_id,page:0,columns:[]})},
      {key:'supported_core',label:'Supported core / 161',render:l=>`<strong>${l.supported_core}/161</strong><span class="coveragebar" style="--coverage:${l.supported_core/161*100}%"></span>`},
      {key:state.vocab==='core'?'core_concepts':'mapped_concepts',label:state.vocab==='core'?'Mapped core concepts':'Mapped concepts'}, {key:'Family',label:'Family'},
      {key:'forms',label:'Forms',optional:true}, {key:'core_concepts',label:'Mapped core',optional:true},
      {key:'Macroarea',label:'Macroarea',optional:true}, {key:'tier',label:'Tier',optional:true},
      {key:'transcription_source',label:'Sources',optional:true,render:l=>Object.keys(l.source_counts||{[l.transcription_source]:0}).filter(s=>state.collection!=='core'||catalog.core_sources.includes(s)).map(sourceLink).join(' · ')}, {key:'Glottocode',label:'Glottocode',optional:true},
    ],rows,{select:true})}`;
  debouncedInput('#varietysearch','search');
}
function present(value) { return value === '' || value == null ? 'Not recorded' : esc(value); }
function metadataList(entries) { return '<dl class="metadata-list">'+entries.map(([label,value])=>`<dt>${esc(label)}</dt><dd>${value}</dd>`).join('')+'</dl>'; }
function validCoordinates(l) {
  return l.latitude!==''&&l.longitude!==''&&l.latitude!=null&&l.longitude!=null&&
    Number.isFinite(+l.latitude)&&Number.isFinite(+l.longitude)&&Math.abs(+l.latitude)<=90&&Math.abs(+l.longitude)<=180;
}
function varietyEvidence(rows) {
  const inventory=new Map(),methods=new Map(),fields=new Map(),sets=new Set();
  let segmented=0,assigned=0,multiple=0,loans=0,doubts=0,reviewed=0;
  const mapped=new Set();
  for(const r of rows){
    if(['source','profile'].includes(r.Segments_Source)&&r.Segments){
      segmented++;
      for(const segment of r.Segments.trim().split(/\s+/).filter(t=>!['+','_','#'].includes(t))){
        const count=inventory.get(segment)||{source:0,profile:0};count[r.Segments_Source]++;inventory.set(segment,count);
      }
    }
    const codes=JSON.parse(r.cognate_sets||'[]');if(codes.length)assigned++;if(codes.length>1)multiple++;
    for(const code of codes)sets.add((r.cognate_source||'not recorded')+':'+code);
    const method=r.Cognate_Detection_Method||'Not recorded';methods.set(method,(methods.get(method)||0)+1);
    if(/^(true|yes|1)$/i.test(r.Loan))loans++;
    if(/^(true|yes|1)$/i.test(r.Doubt))doubts++;
    if(['map','retain','unmap'].includes((r.mapping_review||'').replace(/^shared /,'')))reviewed++;
    if(r.concept_id&&!mapped.has(r.concept_id)){
      mapped.add(r.concept_id);const field=concepts.get(r.concept_id)?.semantic_field||'Not classified';fields.set(field,(fields.get(field)||0)+1);
    }
  }
  return {inventory,methods,fields,sets,segmented,assigned,multiple,loans,doubts,reviewed};
}
function sourceMetadata(key,roles) {
  const source=sources.get(key)||{};
  return `<section class="metadata-card"><h3>${esc(roles)}</h3><p>${sourceLink(key)}</p>${metadataList([
    ['Dataset ID',esc(key)],['Citation',present(source.Citation)],['Source version',present(source.Repository_Version)],
    ['License',present(source.License)],['Upstream source',external(source.URL||'Not recorded',source.URL)]])}</section>`;
}
async function showVariety(token) {
  const l=collectionLanguage(languages.get(state.id));if(!l)throw Error('Variety not found in this build.');
  await ensure([l.Family||'Unclassified']);if(token!==epoch)return;
  let sql='SELECT * FROM forms f WHERE av_id=? AND '+coreSourceCondition('f'),params=[l.av_id];
  if(state.vocab==='core')sql+=" AND is_core_concept='true'";
  if(state.status==='usable')sql+=" AND Segments_Source IN ('source','profile')";
  else if(state.status){sql+=' AND Segments_Source=?';params.push(state.status);}
  const rows=await query(sql,params,100000);if(token!==epoch)return;
  const missing=catalog.core.filter(c=>!l.supported_ids.includes(c)),e=varietyEvidence(rows);
  const label=/^Proto[- ]/i.test(l.Name)?'Reconstruction (catalog name label)':/^(Old|Middle|Classical|Ancient|Late|Early Modern|Ottoman) /i.test(l.Name)?'Historical stage (catalog name label)':'Not independently classified';
  $('#app').innerHTML=`<p>${link('← Varieties',{view:'varieties',page:0,columns:[]})}</p><h2>${esc(l.Name)}</h2>
    <div class="controls page-jumps"><button id="jumprecords">Lexical records ↓</button><button id="jumpinventory">Segment evidence ↓</button></div>
    <p class="sub">${esc(l.Family)} · ${esc(l.Macroarea)} · ${external(l.Glottocode,'https://glottolog.org/resource/languoid/id/'+l.Glottocode)}</p>
    <div class="metrics"><div><strong>${l.supported_core}/161</strong> supported core</div><div><strong>${l.mapped_concepts}</strong> mapped concepts</div><div><strong>${fmt(l.forms)}</strong> total forms</div><div><strong>${fmt(rows.length)}</strong> forms in this view</div></div>
    ${l.recordings?`<p class="sub">${fmt(l.recordings)} untranscribed recordings are kept separately from lexical forms. <a href="data/recordings.csv" download>Download recording metadata</a> (all varieties; filter by variety ID).</p>`:''}
    <div class="variety-overview"><section class="metadata-card"><h3>Location</h3>
    ${validCoordinates(l)?'<div id="varietymap" class="map variety-map" role="region" aria-label="Approximate catalog location"></div><p class="sub">Approximate catalog point, not a speaker distribution, language boundary, or necessarily a recording site.</p>':'<p class="empty">No valid catalog coordinates recorded. No location is inferred.</p>'}
    <p>${validCoordinates(l)?`Latitude ${(+l.latitude).toFixed(4)} · Longitude ${(+l.longitude).toFixed(4)}`:''}</p>
    ${link('Explore this family on the full map',{view:'map',family:l.Family||'Unclassified',search:'',page:0,columns:[]})}</section>
    <section class="metadata-card"><h3>Linguistic identity</h3>${metadataList([
      ['Accepted variety ID',esc(l.av_id)],['Language family',present(l.Family)],['Macroarea',present(l.Macroarea)],
      ['Catalog level',present(l.identity_level)],['ISO 639-3',present(l.iso639p3)],
      ['Parent variety',l.parent_av_id?link(languages.get(l.parent_av_id)?.Name||l.parent_av_id,{view:'variety',id:l.parent_av_id}):'Not recorded'],
      ['Source names / aliases',esc((l.aliases||[]).join('; ')||'Not recorded')],['Historical status',label],
      ['First documentation',present(l.first_documented)],['Last documentation',present(l.last_documented)],
      ['Catalog country codes',present(l.countries)],
      ['Catalog classification',l.glottolog_family_id?external(l.glottolog_family_id,'https://glottolog.org/resource/languoid/id/'+l.glottolog_family_id):'Not recorded']])}
      <p class="sub">Documentation dates are catalog annotations, not necessarily dates of the lexical sample. Historical labels above describe the catalog name.</p></section></div>
    <section class="metadata-card"><h3>Lexical and transcription evidence</h3>
      <p>${Object.entries(l.statuses).map(([status,n])=>`${esc(statusNames[status]||status)}: <strong>${fmt(n)}</strong>`).join(' · ')} (whole variety in the current collection)</p>
      ${metadataList([['Forms with cognate assignments',`${fmt(e.assigned)} / ${fmt(rows.length)} in this view`],
        ['Source-scoped cognate sets',fmt(e.sets.size)],['Forms with multiple assignments',fmt(e.multiple)],
        ['Source-flagged loans',fmt(e.loans)],['Source-flagged doubt',fmt(e.doubts)],
        ['Forms with recorded sense-review decisions',fmt(e.reviewed)],
        ['Concepts with preferred supported readings in this view',fmt(new Set(rows.filter(r=>r.preferred_source===r.transcription_source&&['source','profile'].includes(r.Segments_Source)).map(r=>r.concept_id).filter(Boolean)).size)],
        ['Concepts in this view with only GLED support in the whole construction',fmt(new Set(rows.filter(r=>r.gled_dependence==='gled_only').map(r=>r.concept_id).filter(Boolean)).size)],
        ['Construction tier',esc(l.tier)],['Transcription score',present(l.forms_score)],['Cognate score',present(l.cognates_score)]])}
      <p class="sub">Counts here use the current vocabulary/transcription filters unless marked otherwise. Source flags and sense reviews are not independent native-speaker verification; empty flags do not establish absence. ${link('Interpret evidence and tiers',{view:'about'})}</p>
      <p class="sub">Source preference follows the configured construction for each concept where it supplies a supported reading. Alternatives remain visible. GLED dependence compares the whole construction, including sources outside the current collection. Scores summarize feature presence; they do not measure phonetic fidelity or completeness of tone.</p>
      <details><summary>Cognate evidence methods</summary>${metadataList([...e.methods].sort((a,b)=>b[1]-a[1]).map(([method,n])=>[method,fmt(n)+' forms']))}</details>
      <details><summary>Semantic-field coverage</summary><p>Distinct mapped concepts in this view; synonyms count once.</p>${metadataList([...e.fields].sort((a,b)=>b[1]-a[1]).map(([field,n])=>[field,fmt(n)]))}</details>
    </section>
    <details class="metadata-card" id="segmentinventory"><summary>Observed segment tokens (${e.inventory.size})</summary>
      <p>Attested tokens from ${fmt(e.segmented)} source-supplied/profile-inferred forms in this view, including any prosodic marks. Boundary markers are excluded. This is a lexical-sample inventory, not a verified phoneme inventory. Counts include repeated occurrences.</p>
      <div class="segment-inventory">${[...e.inventory].sort((a,b)=>a[0].localeCompare(b[0])).map(([segment,n])=>`<span class="segment-token"><b class="ipa">${esc(segment)}</b><span>${fmt(n.source+n.profile)} occurrences</span><small>source ${fmt(n.source)} · profile ${fmt(n.profile)}</small></span>`).join('')||'<p>No source/profile-supported segment tokens in the current view.</p>'}</div></details>
    <div class="source-cards">${[...new Set(rows.map(r=>r.transcription_source))].filter(s=>s!==l.transcription_source&&s!==l.cognate_source).map(s=>sourceMetadata(s,'Supplemental lexical source')).join('')}${sourceMetadata(l.transcription_source,l.transcription_source===l.cognate_source?'Lexical and cognate source':'Lexical source')}${l.transcription_source!==l.cognate_source?sourceMetadata(l.cognate_source,'Cognate source'):''}</div>
    <details class="metadata-card"><summary>Identity notes, curation and missing core concepts</summary><p>${esc(l.notes||'No additional identity notes recorded.')}</p>
      <p>${l.packet_url?external('Read the curation packet',l.packet_url):'No published curation packet for this variety.'}</p>
      <p>${missing.map(c=>link(concepts.get(c)?.label||c,{view:'concept',cid:c})).join(', ')||'All core concepts have supported entries.'}</p><p>Missing support means not supplied, not mapped, or unresolved here. It does not establish lexical absence.</p></details>
    <p class="sub">This detail page follows the named variety and vocabulary/transcription filters. Family, name, area, tier and minimum-coverage controls select catalog entries; they do not hide this linked record. Data build: ${esc(manifest.build_date)}.</p>
    <h3 id="lexicalrecords" tabindex="-1">Lexical records</h3>${exportControls(rows,'this named variety; vocabulary/transcription filters applied')}${table(formColumns(),rows)}`;
  $('#jumprecords').onclick=()=>{$('#lexicalrecords').scrollIntoView();$('#lexicalrecords').focus({preventScroll:true});};
  $('#jumpinventory').onclick=()=>{const panel=$('#segmentinventory');panel.open=true;panel.scrollIntoView();panel.querySelector('summary').focus({preventScroll:true});};
  if(validCoordinates(l))await drawVarietyMap(l,token);
}
function sourceLink(key) {const s=sources.get(key);return external(s?.Title||key,s?.URL||'');}
function showConcepts() {
  const ls=scopedLanguages(),terms=state.term.toLowerCase(),count=new Map();
  for(const l of ls)for(const c of l.concept_ids||l.core_ids) count.set(c,(count.get(c)||0)+1);
  const rows=catalog.concepts.filter(c=>(state.vocab!=='core'||c.is_core)&&(!terms||[c.label,c.concept_id,c.concepticon_id,c.definition].some(v=>(v||'').toLowerCase().includes(terms))))
    .map(c=>({...c,nvarieties:count.get(c.concept_id)||0}));
  $('#app').innerHTML=`<h2>Concepts</h2><label class="search-label">Concept, definition or Concepticon ID<input id="conceptsearch" type="search" value="${esc(state.term)}"></label>
    ${table([{key:'label',label:'Concept',render:c=>link(c.label,{view:'concept',cid:c.concept_id,columns:[],page:0})+(c.is_core?' <span class="chip">161 core</span>':'')},
      {key:'nvarieties',label:'Varieties in scope'}, {key:'semantic_field',label:'Semantic field'}, {key:'pos',label:'Part of speech'},
      {key:'definition',label:'Definition',optional:true}],rows)}`;
  debouncedInput('#conceptsearch','term');
}
function familyPrompt() {
  return `<p class="empty">Choose a family above to load lexical records. The catalog already covers every accepted variety. Family downloads keep the explorer responsive.</p>
    <div class="family-grid">${[...new Set(scopedLanguages().map(l=>l.Family||'Unclassified'))].sort().map(f=>link(`${f} · ${(manifest.shards[f]?.bytes/1e6||0).toFixed(1)} MB`,{family:f,page:0})).join('')}</div>`;
}
async function scopedRows(extra='',params=[],limit=100000) {
  const condition=languageCondition();
  return query(`SELECT f.* FROM forms f WHERE ${condition.sql}${extra}`,condition.params.concat(params),limit);
}
async function showConcept(token) {
  const c=concepts.get(state.cid);if(!c)throw Error('Concept not found.');
  const title=`<p>${link('← Concepts',{view:'concepts',columns:[],page:0})}</p><h2>${esc(c.label)} ${c.is_core?'<span class="chip">161 basic concepts</span>':''}</h2>
    <p class="definition">${esc(c.definition||'No definition recorded.')}</p><p>${esc(c.semantic_field)} · ${esc(c.pos)} · ${external('Concepticon '+c.concepticon_id,'https://concepticon.clld.org/parameters/'+c.concepticon_id)}</p>`;
  if(!state.family){$('#app').innerHTML=title+familyPrompt();return;}
  await ensure([state.family]);if(token!==epoch)return;
  const rows=await scopedRows(' AND concept_id=?',[state.cid]);if(token!==epoch)return;
  $('#app').innerHTML=title+`<p>${rows.length} forms in this scope. Source glosses and mapping decisions are available from each form.</p>
    <div id="conceptmap" class="map small"></div><div id="maplegend" class="maplegend"></div>`+exportControls(rows)+table(formColumns(),rows);
  await drawMap(rows.map(r=>({...languages.get(r.av_id),...r})),true,token);
}
async function showForm(token) {
  const av=state.id.split(':')[0],l=languages.get(av);if(!l)throw Error('Unknown form variety.');
  await ensure([l.Family||'Unclassified']);if(token!==epoch)return;
  let [r]=await query('SELECT * FROM forms WHERE ID=?',[state.id]);
  if(!r){
    // Older links contain an aggregate row number, which shifts as coverage grows.
    const first=state.id.indexOf(':'),last=state.id.lastIndexOf(':');
    if(last>first&&/^\d+$/.test(state.id.slice(last+1))){
      const matches=await query('SELECT * FROM forms WHERE av_id=? AND source_form_id=? LIMIT 2',
        [av,state.id.slice(first+1,last)]);
      if(matches.length===1)r=matches[0];
    }
  }
  if(token!==epoch)return;if(!r)throw Error('Form not found uniquely in this build.');
  const s=sources.get(r.transcription_source);
  $('#app').innerHTML=`<p>${link('← '+l.Name,{view:'variety',id:av})}</p><h2 class="ipa">${esc(r.Form)}</h2>
    <p class="ipa large">${esc(r.Segments)}</p><p>${statusBadge(r)} · ${link('Interpret transcription and uncertainty',{view:'about'})}</p>
    <p>Concept: ${r.concept_id?link(r.concept_label,{view:'concept',cid:r.concept_id}):'Unmapped'} · Original source gloss: ${esc(r.source_gloss||'Not recorded')}</p>
    <p>Mapping review: <strong>${esc(r.mapping_review||'Not recorded')}</strong>. ${esc(r.mapping_note||'No sense-review note recorded; consult source definitions.')}</p>
    <p>Reading evidence: ${esc(r.representation_basis||'Not recorded')}. Source role: ${esc((r.evidence_role||'not recorded').replaceAll('_',' '))}.</p>
    <p>Preferred supported source for this concept: ${esc(r.preferred_source||'No supported reading from the configured primary')}. GLED dependence: ${esc(r.gled_dependence||'Not recorded')}.</p>
    <p>Observed notation marks: ${esc((r.phonological_marks||'none recorded').replaceAll('_',' '))}. These are marks in the retained reading, not a complete phoneme inventory; absence does not establish absence of a contrast.</p>
    <p>Cognate membership: ${cognatesCell(r)}. Method: ${esc(r.Cognate_Detection_Method||'Not recorded')}; source: ${esc(r.cognate_evidence_source||r.cognate_source)}.</p>
    <p>Doubt flag: ${esc(r.Doubt||'Not recorded')} · Loan flag: ${esc(r.Loan||'Not recorded')}. Empty flags do not mean verified absence.</p>
    <details open><summary>Alignment and morpheme evidence</summary><dl>${['Alignment','Morpheme_Index','Segment_Slice','canonical_cognate_id'].map(k=>`<dt>${esc(k)}</dt><dd class="ipa">${esc(r[k]||'Not supplied')}</dd>`).join('')}</dl></details>
    <h3>Provenance</h3><dl>${['Value','raw_ipa','pronunciation_tags','source_pronunciation_id','source_form_id','source_language_id','source_parameter_id','bibtex_key','Comment'].map(k=>`<dt>${esc(k.replaceAll('_',' '))}</dt><dd>${esc(r[k]||'Not supplied')}</dd>`).join('')}</dl>
    <p>${esc(s?.Citation||r.transcription_source)} ${sourceLink(r.transcription_source)}</p>
    <p>Source version: ${esc(s?.Repository_Version||'Not recorded')} · License: ${esc(r.License)}</p>
    ${l.packet_url?external('Review construction and mapping decisions',l.packet_url):'<p>No published mapping review packet. Consult the original source before assuming the English sense mapping is independently reviewed.</p>'}
    ${exportControls([r],'one form with full provenance')}`;
}
async function showCognate(token) {
  if(!state.family){$('#app').innerHTML='<h2>Cognate membership</h2>'+familyPrompt();return;}
  await ensure([state.family]);if(token!==epoch)return;
  const condition=languageCondition();
  const rows=await query(`SELECT f.* FROM forms f JOIN memberships m ON m.form_id=f.ID WHERE ${condition.sql} AND m.set_id=? AND m.concept_id=?`,condition.params.concat([state.cog,state.cid]),100000);
  if(token!==epoch)return;
  $('#app').innerHTML=`<h2>Cognate set ${esc(state.cog)}</h2><p>Individual set membership for ${link(concepts.get(state.cid)?.label||state.cid,{view:'concept',cid:state.cid})}. Identifiers are source-scoped; identical colors or labels across sources do not establish cognacy.</p>${exportControls(rows)}${table(formColumns(),rows)}`;
}
async function showCompare(token) {
  const selected=state.selected.map(id=>languages.get(id)).filter(l=>l&&(state.collection!=='core'||l.core_collection));
  const available=catalog.concepts.filter(c=>state.vocab!=='core'||c.is_core);
  const chosen=state.concepts.filter(cid=>concepts.has(cid)&&(state.vocab!=='core'||concepts.get(cid).is_core));
  $('#app').innerHTML=`<h2>Compare varieties</h2><p>Select varieties in the catalog, then choose concepts here. Comparison uses your explicit variety selection across catalog family/area/name filters; transcription filters apply to its records. The vocabulary control limits the concept chooser. Synonyms stay together; missing entries are not inferred lexical absences.</p>
    <p>${state.selected.length-selected.length?esc(state.selected.length-selected.length)+' selected varieties are outside the current collection. ':''}${selected.map(l=>link(l.Name,{view:'variety',id:l.av_id})).join(' · ')||'No varieties selected. '+link('Choose varieties',{view:'varieties'})}</p>
    <button id="clearselection">Clear variety selection</button>
    <label>Concepts (select multiple)<select id="comparisonconcepts" multiple size="8">${available.map(c=>`<option value="${esc(c.concept_id)}" ${state.concepts.includes(c.concept_id)?'selected':''}>${esc(c.label)} (${esc(c.concept_id)})</option>`).join('')}</select></label>
    <div class="controls"><button id="coreconcepts">Choose all 161 core concepts</button><button id="buildmatrix" class="primary">Build comparison</button></div><div id="matrix"></div>`;
  $('#clearselection').onclick=()=>navigate({selected:[]});
  $('#coreconcepts').onclick=()=>navigate({concepts:catalog.core});
  $('#comparisonconcepts').onchange=e=>navigate({concepts:[...e.target.selectedOptions].map(o=>o.value)});
  $('#buildmatrix').onclick=async()=>{
    try {
      if(!selected.length||!chosen.length)throw Error('Select at least one variety and one concept.');
      if(selected.length>16)throw Error('Compare up to 16 varieties at once for a readable matrix.');
      if(chosen.length>200)throw Error('Select up to 200 concepts at once; all 161 core concepts fit in one matrix.');
      await ensure(selected.map(l=>l.Family||'Unclassified'));if(token!==epoch)return;
      let sql=`SELECT * FROM forms WHERE av_id IN (${selected.map(()=>'?').join(',')}) AND concept_id IN (${chosen.map(()=>'?').join(',')}) AND ${coreSourceCondition('')}`;
      const params=selected.map(l=>l.av_id).concat(chosen);
      if(state.status==='usable')sql+=" AND Segments_Source IN ('source','profile')";
      else if(state.status){sql+=' AND Segments_Source=?';params.push(state.status);}
      const rows=await query(sql,params,100000);if(token!==epoch)return;
      $('#matrix').innerHTML=exportControls(rows,'comparison selection')+`<div class="scroll" role="region" aria-label="Comparative wordlist" tabindex="0"><table><thead><tr><th scope="col">Concept</th>${selected.map(l=>`<th scope="col">${esc(l.Name)}</th>`).join('')}</tr></thead><tbody>${chosen.map(cid=>`<tr><th scope="row">${link(concepts.get(cid)?.label||cid,{view:'concept',cid})}</th>${selected.map(l=>{const cell=rows.filter(r=>r.av_id===l.av_id&&r.concept_id===cid);return `<td>${cell.map(r=>`<div class="matrixform">${link(r.Form,{view:'form',id:r.ID})}<div class="ipa">${esc(r.Segments)}</div>${statusBadge(r)}<div>${cognatesCell(r)}</div></div>`).join('')||'<span class="muted">Not supplied in this selection</span>'}</td>`;}).join('')}</tr>`).join('')}</tbody></table></div>`;
    }catch(error){notice(error.message,true);}
  };
}
async function showSearch(token) {
  $('#app').innerHTML=`<h2>Search lexical records</h2><label class="search-label">Spelling or segment sequence<input id="formsearch" value="${esc(state.term)}" placeholder="e.g. aqua or t ʃ"></label>
    <div class="controls"><label>Match mode<select id="searchmode"><option value="literal">Literal substring</option><option value="tokens" ${state.mode==='tokens'?'selected':''}>Whole segment tokens</option><option value="regex" ${state.mode==='regex'?'selected':''}>Regular expression (advanced)</option></select></label>
    <label><input id="foldsearch" type="checkbox" ${state.fold?'checked':''}> Ignore case and combining diacritics (literal/token mode)</label><button id="runsearch" class="primary">Search selected family</button></div>
    <p class="sub">Search runs inside the current family and scope. Token mode respects spaces between supplied segments; combining marks are not standalone segments. Diacritic-insensitive search is a discovery aid, not phonemic equivalence.</p><div id="searchresults">${state.family?'Choose a query and run search.':familyPrompt()}</div>`;
  $('#searchmode').onchange=e=>navigate({mode:e.target.value});
  $('#foldsearch').onchange=e=>navigate({fold:e.target.checked});
  $('#formsearch').onchange=e=>navigate({term:e.target.value});
  $('#runsearch').onclick=async()=>{
    try{
      if(!state.family||!state.term)throw Error('Choose a family and enter a query.');
      await ensure([state.family]);if(token!==epoch)return;
      const c=languageCondition();
      const result=await request('search',{sql:`SELECT * FROM forms f WHERE ${c.sql}`,params:c.params,term:state.term,mode:state.mode,fold:state.fold});
      if(token!==epoch)return;
      $('#searchresults').innerHTML=`<p role="status">${fmt(result.count)} matches. Showing ${result.rows.length}; refine your search above 500 results. Exports contain the displayed records.</p>`+exportControls(result.rows,'displayed search results')+table(formColumns(),result.rows);wireTable();
    }catch(error){notice(error.message,true);}
  };
}
function showStats() {
  const rows=scopedLanguages(),byFamily=new Map();
  for(const l of rows){let f=byFamily.get(l.Family);if(!f){f={Family:l.Family,n:0,forms:0,support:0,unclean:0};byFamily.set(l.Family,f);}f.n++;f.forms+=l.forms;f.support+=l.supported_core;f.unclean+=l.statuses.unclean||0;}
  const sourceCounts=new Map();
  for(const l of rows){const key=l.transcription_source;const entry=sourceCounts.get(key)||{source:key,varieties:0,forms:0};entry.varieties++;entry.forms+=l.forms;sourceCounts.set(key,entry);}
  const bins=Array.from({length:9},(_,i)=>({label:`${i*20}–${Math.min(161,i*20+19)}`,n:rows.filter(l=>l.supported_core>=i*20&&l.supported_core<Math.min(162,i*20+20)).length}));
  $('#app').innerHTML=`<h2>Coverage and sampling</h2><p>${fmt(rows.length)} varieties in scope. Counts are not a balanced sample of world languages; related dialects, source choices, synonyms, and historical varieties affect them.</p>
    <h3>Supported concepts out of the fixed 161</h3><div class="histogram">${bins.map(b=>`<div><span>${b.label}</span><meter min="0" max="${Math.max(1,...bins.map(x=>x.n))}" value="${b.n}">${b.n}</meter><strong>${b.n}</strong></div>`).join('')}</div>
    ${table([{key:'Family',label:'Family'}, {key:'n',label:'Varieties'}, {key:'forms',label:'Forms'},
      {key:'mean',label:'Mean supported core',render:f=>(f.support/f.n).toFixed(1)+'/161'}, {key:'unclean',label:'Unresolved forms'}],[...byFamily.values()])}
    <h3>Source composition</h3><div class="source-composition">${[...sourceCounts.values()].sort((a,b)=>b.varieties-a.varieties).map(s=>`<p><strong>${esc(s.source)}</strong>: ${s.varieties} varieties · ${fmt(s.forms)} forms (all concepts)</p>`).join('')}</div>
    <p>Support counts source-supplied and profile-inferred segments. Mechanical segment validity is not a judgment of phonetic or lexical accuracy. Synonyms count once for concept coverage. Missing records cannot establish that a language lacks a word.</p>`;
}
async function showMap(token) {
  const rows=scopedLanguages();
  $('#app').innerHTML=`<h2>Variety map</h2><p>${rows.filter(l=>!validCoordinates(l)).length} varieties in scope have no coordinates. Points are approximate catalog locations, not language boundaries, historical ranges, or speaker distributions.</p>
    <label>Color by<select id="mapmode"><option value="Family">Family</option><option value="Macroarea">Macroarea</option><option value="tier">Construction tier</option><option value="coverage">Supported core coverage</option></select></label>
    <div class="map-layout"><div id="mapcanvas" class="map"></div><div id="maplegend" class="maplegend"></div></div>`;
  $('#mapmode').onchange=()=>drawMap(rows,false,token);
  await drawMap(rows,false,token);
}
let worldPromise;
async function baseMap(container,center,zoom,token) {
  worldPromise ||= fetch('vendor/world.geo.json').then(r=>{if(!r.ok)throw Error('Cannot load map geography');return r.json();});
  const world=await worldPromise;if(token!==epoch)return null;
  if(map)map.remove();
  map=L.map(container,{attributionControl:true,scrollWheelZoom:false}).setView(center,zoom);
  const css=getComputedStyle(document.documentElement);
  const colors={land:css.getPropertyValue('--map-land').trim(),border:css.getPropertyValue('--map-border').trim()};
  L.geoJSON(world,{style:{fillColor:colors.land,fillOpacity:1,color:colors.border,opacity:1,weight:1.15},
    onEachFeature:(feature,layer)=>layer.bindTooltip(esc(feature.properties?.name||'Country'),{sticky:true})}).addTo(map);
  map.attributionControl.addAttribution('Locations: Arca catalog / Glottolog; approximate');
  L.control.scale({imperial:false}).addTo(map);
  return map;
}
async function drawVarietyMap(l,token) {
  const m=await baseMap('varietymap',[+l.latitude,+l.longitude],3,token);if(!m)return;
  L.circleMarker([+l.latitude,+l.longitude],{radius:8,color:'#fff',weight:2,fillColor:'#a63828',fillOpacity:1}).addTo(m)
    .bindTooltip(esc(l.Name),{permanent:true,direction:'top',className:'location-label'})
    .bindPopup(`<strong>${esc(l.Name)}</strong><br>${esc(l.Family)}<br>Approximate catalog location`);
}
async function drawMap(rows,cognate,token) {
  if(!await baseMap(cognate?'conceptmap':'mapcanvas',[15,10],2,token))return;
  const field=cognate?'cognate_sets':$('#mapmode').value, keys=[];
  const values=r=>cognate?JSON.parse(r.cognate_sets||'[]'):field==='coverage'?[`${Math.floor(r.supported_core/40)*40}–${Math.min(161,Math.floor(r.supported_core/40)*40+39)}`]:[r[field]||'Unspecified'];
  for(const row of rows)for(const key of values(row))if(!keys.includes(key))keys.push(key);
  keys.sort();const colors=Object.fromEntries(keys.map((k,i)=>[k,`hsl(${(i*137.508)%360} 55% 44%)`]));
  const layer=L.layerGroup().addTo(map),coordinates=new Map();
  const draw=selected=>{
    layer.clearLayers();coordinates.clear();
    for(const row of rows){if(!validCoordinates(row))continue;const labels=values(row);if(selected&&!labels.includes(selected))continue;
      const key=row.latitude+','+row.longitude;let group=coordinates.get(key);if(!group){group=[];coordinates.set(key,group);}group.push(row);}
    for(const group of coordinates.values()){
      const row=group[0],labels=values(row),color=selected?colors[selected]:labels.length===1?colors[labels[0]]:'#777';
      const popup=group.map(r=>`${link(r.Name||languages.get(r.av_id)?.Name,{view:'variety',id:r.av_id})}${r.Form?' · '+esc(r.Form):''}`).join('<br>');
      L.circleMarker([+row.latitude,+row.longitude],{radius:Math.min(12,4+Math.log2(group.length+1)),color:'#fff',weight:1,fillColor:color||'#aaa',fillOpacity:.9}).addTo(layer)
        .bindTooltip(`${group.length>1?group.length+' colocated records: ':''}${esc(row.Name||languages.get(row.av_id)?.Name)}`).bindPopup(popup);
    }
  };
  $('#maplegend').innerHTML=`<p>${keys.length} ${cognate?'source-scoped cognate sets':'categories'}. ${cognate?'Gray points have multiple/no assignments. Select a set to see individual membership.':''}</p><button data-legend="">Show all</button>`+keys.map(key=>`<button data-legend="${esc(key)}"><span class="swatch" style="background:${colors[key]}"></span>${esc(key)}</button>`).join('');
  document.querySelectorAll('[data-legend]').forEach(b=>b.onclick=()=>draw(b.dataset.legend));draw('');
  const coords=[...coordinates.values()].map(g=>[+g[0].latitude,+g[0].longitude]);if(cognate&&coords.length)map.fitBounds(L.latLngBounds(coords).pad(.15));
}
function showSources() {
  const used=new Set(scopedLanguages().flatMap(l=>Object.keys(l.source_counts||{[l.transcription_source]:0})).filter(s=>state.collection!=='core'||catalog.core_sources.includes(s)));
  $('#app').innerHTML=`<h2>Sources and attribution</h2><p>Licenses remain per source; inclusion in Arca does not relicense the underlying data. Records missing license metadata explicitly require checking upstream terms.</p>
    ${table([{key:'Title',label:'Dataset',render:s=>external(s.Title||s.Dataset,s.URL)}, {key:'Citation',label:'Citation'}, {key:'License',label:'License'},
      {key:'Repository_Version',label:'Version'}],[...used].map(key=>sources.get(key)||{Dataset:key,Title:key,Citation:'Citation metadata not recorded; inspect the form source keys and upstream data.',License:'Not recorded'}))}
    <p><a href="data/sources.bib" download>Download original bibliography</a> · ${link('Collection and quality guide',{view:'about'})}</p>`;
}
function showSQL() {
  $('#app').innerHTML=`<h2>SQL workspace</h2><p>Queries run read-only in an isolated worker. Tables: <code>languages</code>, <code>parameters</code>, <code>sources</code>, <code>forms</code>, <code>memberships</code>. Lexical tables contain only the ${loaded.length} loaded families; catalog tables cover all varieties. Global filters are not automatically injected into SQL.</p>
    <details><summary>Schema and examples</summary><p>forms: ${manifest.fields.map(esc).join(', ')}</p><p>memberships: form_id, set_id, concept_id, source</p></details>
    <label>Read-only query<textarea id="sqlquery" rows="7">${esc(state.sql||'SELECT Name, Family, supported_core FROM languages ORDER BY supported_core DESC LIMIT 20')}</textarea></label>
    <button id="runsql">Run query</button><div id="sqlresults"></div><p>Results are limited to 1,000 displayed rows. Long-running queries are stopped after 15 seconds; reload resets the worker and retains URL selections.</p>`;
  $('#runsql').onclick=async()=>{try{
    const sql=$('#sqlquery').value;history.replaceState(null,'',href({sql}));state.sql=sql;
    const rows=await request('sql',{sql});
    $('#sqlresults').innerHTML=`<p>${rows.length>1000?'More than 1,000':rows.length} rows.</p>`+table(Object.keys(rows[0]||{}).map(key=>({key,label:key})),rows.slice(0,1000));wireTable();
  }catch(error){notice(error.message,true);}};
}
function showAbout() {
  $('#app').innerHTML=`<h2>Research guide</h2>
    <h3>Two independent scopes</h3><p><strong>Collection</strong> chooses all accepted varieties or the Core source collection (sources flagged CORE in the repository). <strong>Vocabulary</strong> chooses all mapped concepts or the fixed 161 basic concepts. Neither scope changes source acceptance. Family filters limit lexical downloads, comparison and map scope.</p>
    <h3>Reading transcription evidence</h3><dl><dt>Source-supplied</dt><dd>Supplied source segments pass the token validator; this is not independent phonetic verification.</dd><dt>Profile-inferred</dt><dd>Reading inferred from a reviewed orthographic profile, potentially broad phonemic rather than surface phonetic. Consult the curation packet for omitted distinctions.</dd><dt>Resegmented</dt><dd>Fallback segmentation from source text; review before phonological analysis.</dd><dt>Unresolved</dt><dd>Unsupported or invalid segmentation remains visible. It is not certified IPA.</dd></dl>
    <h3>Cognate evidence</h3><p>Expert source judgments, computed methods and Wiktionary etymology annotations are distinguished in each form's evidence. Multiple assignments are independent memberships, not a composite set. Alignment and morpheme fields are preserved where supplied. Codes are source-scoped and do not establish equivalence across datasets.</p>
    <h3>Coverage and tiers</h3><p>Supported core coverage is the count of distinct core concepts with source-supplied or profile-inferred segments. Synonyms do not increase it. The construction tier summarizes selection/scoring history; it is not a universal confidence rating. Forms scores combine segment availability/validity, mapping, coverage, loan annotation and density; cognate scores combine assignment availability, expert labeling, alignments and partial-cognacy evidence. Pins and curated decisions can affect tiers. Inspect separate measures and packets rather than treating a tier as accuracy.</p>
    <h3>Sampling, history and missingness</h3><p>Varieties can represent languages, dialects, historical stages or reconstructions. Parent relationships and original identity notes are retained when available; historical dates and reconstruction status are not consistently structured and must be checked in the source. Catalog coordinates are approximate. An absent record means no supported supplied/mapped entry here, not that the language has no word. Concept definitions and source glosses may differ; consult mapping notes and source-specific senses before comparison.</p>
    <h3>Reproducing a selection</h3><p>Share the URL to retain filters, selected varieties and concepts. Export CSV/TSV together with the selection manifest and original bibliography. The manifest records the build date, exact aggregate hashes, source versions, licenses and filters. Search exports explicitly cover displayed results. Data is cached by content hash on this device; changing builds downloads new shards. ${external('Source repository','https://github.com/tresoldi/arcaverborum')}</p>
    <button id="clearcache">Clear downloaded data cache</button>`;
  $('#clearcache').onclick=async()=>{await caches.delete('arca-research-v1');notice('Download cache cleared; in-memory data remains until reload.');};
}
async function boot() {
  worker=new Worker('research-worker.js?v='+VERSION);
  worker.onmessage=({data})=>{
    const item=pending.get(data.id);if(!item)return;
    if(data.progress){notice(data.progress);return;}
    clearTimeout(item.timer);pending.delete(data.id);data.error?item.reject(Error(data.error)):item.resolve(data.result);
  };
  worker.onerror=error=>notice('Data worker error: '+error.message,true);
  try{
    ({manifest,catalog}=await request('init',{version:VERSION}));
    for(const l of catalog.languages)languages.set(l.av_id,l);
    for(const c of catalog.concepts)concepts.set(c.concept_id,c);
    for(const s of catalog.sources)sources.set(s.Dataset,s);
    $('#counts').textContent=`${fmt(manifest.counts.forms)} forms · ${fmt(manifest.counts.varieties)} varieties · ${fmt(manifest.counts.concepts)} concepts · updated ${manifest.build_date}`;
    notice('Catalog loaded. Lexical data downloads by family when needed.');
    window.onhashchange=readRoute;readRoute();
  }catch(error){notice(error.message,true);$('#app').innerHTML='<p>Could not load the catalog. Check your connection and reload.</p>';}
}
$('.skip').addEventListener('click',event=>{event.preventDefault();$('#app').focus();});
boot();
