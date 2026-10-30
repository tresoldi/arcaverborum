'use strict';
// Fetch one concept neighborhood at a time; never load the complete edge/witness tables.
window.ArcaColexification=(()=>{
  let rootHash='', rootPromise;
  const basisNames={supplied_ipa:'Supplied IPA',explicit_stress_citation:'Source citation with explicit stress',normalized_segments:'Normalized supplied/profile segments',citation_form:'Citation form',reduced_asjp:'ASJP-derived representation'};
  const cache=new Map(), MAX_ROOT=4*1024*1024, MAX_PAGE=1024*1024;
  async function checkedJSON(spec,base,limit=MAX_PAGE) {
    const url=new URL(spec.url,base);
    if(url.origin!==location.origin||!Number.isInteger(spec.bytes)||spec.bytes<0||spec.bytes>limit)throw Error('Invalid or oversized colexification asset.');
    const key=spec.sha256;
    if(cache.has(key)){const value=cache.get(key);cache.delete(key);cache.set(key,value);return value;}
    const response=await fetch(url,{cache:'no-cache'});if(!response.ok)throw Error('Colexification download failed ('+response.status+').');
    const chunks=[],reader=response.body.getReader();let length=0;
    for(;;){const {done,value}=await reader.read();if(done)break;length+=value.length;if(length>limit||length>spec.bytes){await reader.cancel();throw Error('Colexification payload exceeded its declared limit.');}chunks.push(value);}
    if(length!==spec.bytes)throw Error('Incomplete colexification download.');
    const bytes=new Uint8Array(length);let position=0;for(const chunk of chunks){bytes.set(chunk,position);position+=chunk.length;}
    const hash=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(x=>x.toString(16).padStart(2,'0')).join('');
    if(hash!==key)throw Error('Colexification checksum mismatch. Reload to use a consistent data snapshot.');
    const parsed=JSON.parse(new TextDecoder().decode(bytes));cache.set(key,parsed);
    while(cache.size>8)cache.delete(cache.keys().next().value);
    return parsed;
  }
  function placeholder(){return '<section id="colexification" aria-label="Colexification"><h3>Colexification</h3><p>Loading the concept network…</p></section>';}
  async function render(concept,release,context) {
    const {esc,href,concepts,languages,isCurrent,onState,networkState={}}=context, host=document.querySelector('#colexification');
    if(!host)return;
    const active=()=>isCurrent()&&document.querySelector('#colexification')===host;
    if(!release.colexification){host.innerHTML='<h3>Colexification</h3><p>A network has not been built for this data snapshot.</p>';return;}
    try{
      const spec=release.colexification,base=new URL(spec.url,location.href);
      if(rootHash!==spec.sha256){rootHash=spec.sha256;rootPromise=checkedJSON(spec,location.href,MAX_ROOT);}
      const root=await rootPromise;if(!active())return;
      for(const file of ['forms.csv','varieties.csv','parameters.csv']){
        if(root.inputs['output/aggregate/'+file]!==release.source_files[file])throw Error('Colexification and lexical data belong to different snapshots.');
      }
      const nodeSpec=root.nodes[concept.concept_id];if(!nodeSpec)throw Error('Concept missing from the colexification registry.');
      const node=await checkedJSON(nodeSpec,base);if(!active())return;
      let layer=['segmented','written','reduced'].includes(networkState.colexLayer)?networkState.colexLayer:'segmented',
        kind=['observed','inferred'].includes(networkState.colexKind)?networkState.colexKind:'observed',
        page=Number.isInteger(networkState.colexPage)&&networkState.colexPage>=0?networkState.colexPage:0,
        strong=networkState.colexStrong===true,request=0;
      const recurrence=root.policy.recurrence_families;
      const label=cid=>concepts.get(cid)?.label||cid;
      const conceptLink=cid=>`<a href="${esc(href({view:'concept',cid,page:0,columns:[]}))}">${esc(label(cid))}</a>`;
      const recordLink=(id,text)=>`<a href="${esc(href({view:'form',id,page:0,columns:[]}))}">${esc(text)}</a>`;
      function drawGraph(edges){
        const selected=edges.slice(0,12),count=selected.length;
        if(!count)return '';
        const nodes=selected.map((edge,i)=>{const angle=2*Math.PI*i/count-Math.PI/2;return {edge,x:400+270*Math.cos(angle),y:220+165*Math.sin(angle)};});
        const lines=nodes.map(n=>`<line x1="400" y1="220" x2="${n.x}" y2="${n.y}" stroke-width="${Math.min(6,1+Math.sqrt(n.edge.families))}"/>`).join('');
        const points=nodes.map(n=>`<a href="${esc(href({view:'concept',cid:n.edge.concept_id,page:0,columns:[]}))}"><title>${esc(label(n.edge.concept_id))}: ${n.edge.families} known family lineages, ${n.edge.varieties} varieties</title><circle cx="${n.x}" cy="${n.y}" r="9"/><text x="${n.x}" y="${n.y+23}" text-anchor="middle">${esc([...label(n.edge.concept_id)].slice(0,25).join(''))}</text></a>`).join('');
        return `<figure class="colex-graph"><svg viewBox="0 0 800 440" role="img" aria-label="Colexification network for ${esc(concept.label)}"><g class="colex-edges">${lines}</g><g class="colex-nodes">${points}<circle class="colex-center" cx="400" cy="220" r="13"/><text x="400" y="250" text-anchor="middle">${esc(concept.label)}</text></g></svg><figcaption>${count} connections from this page. Line width reflects known family support. The table provides complete labels and evidence.</figcaption></figure>`;
      }
      function example(edge){
        const e=edge.example;
        return `<details><summary>Source example</summary><p>${recordLink(e.record_a,e.form_a||e.identity_display||e.identity)} / ${recordLink(e.record_b,e.form_b||e.identity_display||e.identity)} · <a href="${esc(href({view:'variety',id:e.av_id,page:0,columns:[]}))}">${esc(languages.get(e.av_id)?.Name||e.av_id)}</a></p>
          <p>Identity: <span class="ipa">${esc(e.identity_display||e.identity)}</span>${e.accepted_segments?' (accepted segments: <span class="ipa">'+esc(e.accepted_segments)+'</span>)':''}. Comparison basis: ${esc(basisNames[e.comparison_basis]||e.comparison_basis)}. Source: ${esc(e.source)}; member: ${esc(e.source_language_id)}${e.pronunciation_tags?'; pronunciation scope: '+esc(e.pronunciation_tags):''}.</p>
          <p>Source forms: ${esc(e.source_form_a)} / ${esc(e.source_form_b)}. Source meanings: ${esc(e.parameter_a)} / ${esc(e.parameter_b)}. Reading basis: ${esc(e.segments_source_a)} / ${esc(e.segments_source_b)}.</p>
          ${e.original_concept?'<p>Inferred from one broad catalog slot: '+conceptLink(e.original_concept)+'. This is not two independently recorded target meanings.</p>':''}
          ${e.loan_a||e.loan_b?'<p>Original loan flags: '+esc(e.loan_a||'not recorded')+' / '+esc(e.loan_b||'not recorded')+'.</p>':''}
          <p>Bibliography keys: ${esc(e.bibtex_a||'not recorded')} / ${esc(e.bibtex_b||'not recorded')}.</p></details>`;
      }
      async function update(){
        if(!active())return;
        const turn=++request,info=node.layers[layer],network=info[kind];
        const available=strong?Math.ceil(network.recurrent_neighbors/root.limits.page_edges):network.pages.length;
        page=Math.min(page,Math.max(0,available-1));
        if(onState)onState({colexLayer:layer,colexKind:kind,colexStrong:strong,colexPage:page});
        host.innerHTML=`<h3>Colexification</h3><p class="colex-status">Segmented-data status: ${esc(({observed:'Recorded whole-form connections',no_shared_form_observed:'Usable records present; no recorded segmented connections',no_comparable_segmented_data:'No usable segmented records',merged:'Merged concept; excluded from inference'})[node.status]||node.status)}.</p>
          <p class="sub">Whole-form identity is neutral between polysemy and homophony. These precomputed networks cover all accepted varieties; the lexical filters do not change their counts. WordNet associations do not create network edges.</p>
          <div class="controls"><label>Representation <select id="colex-layer"><option value="segmented">Supplied / profile segments</option><option value="written">Citation forms (not phonetic evidence)</option><option value="reduced">ASJP / GLED reduced representations</option></select></label>
          <label>Evidence <select id="colex-kind"><option value="observed">Recorded meaning pairs</option><option value="inferred">Broad-concept inferences</option></select></label>
          <label><input type="checkbox" id="colex-strong"> At least ${recurrence} known family lineages</label></div>
          ${root.concept_expansions[concept.concept_id]?'<p>This catalog slot is underspecified. Separately labelled inferences link '+root.concept_expansions[concept.concept_id].map(pair=>conceptLink(pair.a)+' and '+conceptLink(pair.b)).join('; ')+'. Open either target and choose “Broad-concept inferences” to inspect the evidence. The original meaning is unchanged.</p>':''}
          <p id="colex-counts">${info.usable_varieties} varieties with usable records for this concept; ${network.neighbors} connections, ${network.recurrent_neighbors} supported by at least ${recurrence} known family lineages.</p>
          <p class="sub">${esc(root.policy.layers[layer])}. ${kind==='inferred'?'Broad-concept inferences are hypotheses from one underspecified slot, kept separate from recorded pairs.':''} Language counts collapse Glottolog dialects; unknown classifications do not add family support. Source duplicates are not independent confirmations.</p>
          <div id="colex-neighbors"><p>Loading bounded network page…</p></div>
          <p class="sub">“No shared form observed” describes the sampled entries, not a proven lexical absence. Missing usable records are unknown. Comparison coverage requires both meanings within the same source, member and pronunciation scope. Rare and regional connections remain available without the three-family filter.</p>
          <p><a href="${esc(new URL(root.files['edges.csv'].url,base))}" download>Network edges CSV</a> · <a href="${esc(new URL(root.files['quarantines.csv'].url,base))}" download>Quarantined identities CSV</a> · <a href="${esc(base)}" download>Network manifest JSON</a> · <a href="docs/COLEXIFICATION.md">Method and resource limits</a></p>
          <details><summary>Complete evidence and comparison-coverage downloads</summary><p>Gzip CSV shards retain original source IDs; download and decompress the parts needed for your analysis. Coverage records support unknown versus sampled distinctions without a dense all-pairs matrix.</p><ul>${Object.entries(root.files).filter(([name])=>name.endsWith('.csv.gz')||name==='sources.csv').map(([name,file])=>`<li><a href="${esc(new URL(file.url,base))}" download>${esc(name)}</a> · ${(file.bytes/1024/1024).toFixed(2)} MiB</li>`).join('')}</ul></details>`;
        const selector=host.querySelector('#colex-layer');selector.value=layer;selector.onchange=()=>{layer=selector.value;page=0;void update().catch(fail);};
        const evidence=host.querySelector('#colex-kind');evidence.value=kind;evidence.onchange=()=>{kind=evidence.value;page=0;void update().catch(fail);};
        const filter=host.querySelector('#colex-strong');filter.checked=strong;filter.onchange=()=>{strong=filter.checked;page=0;void update().catch(fail);};
        let edges=[];
        if(network.pages.length){const data=await checkedJSON(network.pages[page],base);edges=data.edges;}
        if(!active()||turn!==request)return;
        if(strong)edges=edges.filter(e=>e.families>=recurrence);
        const totalPages=strong?Math.ceil(network.recurrent_neighbors/root.limits.page_edges):network.pages.length;
        const target=host.querySelector('#colex-neighbors');
        if(!edges.length){target.innerHTML='<p>No connections in this representation, evidence type and page/filter selection.</p>';return;}
        target.innerHTML=drawGraph(edges)+`<div class="table-wrap"><table><caption>Connections, with family and comparison coverage</caption><thead><tr><th>Concept</th><th>Known families</th><th>Known language units</th><th>Varieties</th><th>Comparable varieties</th><th>Observed fraction</th><th>Evidence</th></tr></thead><tbody>${edges.map(e=>`<tr><td>${conceptLink(e.concept_id)}</td><td>${e.families}</td><td>${e.languages}</td><td>${e.varieties}</td><td>${e.comparable_varieties??'Not applicable'}</td><td>${e.observed_fraction==null?'Not applicable':(100*e.observed_fraction).toFixed(2)+'%'}</td><td>${example(e)}</td></tr>`).join('')}</tbody></table></div>
          <div class="controls"><button id="colex-prev" ${page===0?'disabled':''}>Previous connections</button><span>Page ${page+1} of ${totalPages}; at most ${root.limits.page_edges} connections per download</span><button id="colex-next" ${page+1>=totalPages?'disabled':''}>Next connections</button></div>`;
        host.querySelector('#colex-prev').onclick=()=>{page--;void update().catch(fail);};host.querySelector('#colex-next').onclick=()=>{page++;void update().catch(fail);};
      }
      function fail(error){if(active())host.innerHTML='<h3>Colexification</h3><p role="alert">'+esc(error.message)+'</p>';}
      await update();
    }catch(error){if(active())host.innerHTML='<h3>Colexification</h3><p role="alert">'+esc(error.message)+'</p>';}
  }
  return {placeholder,render};
})();
