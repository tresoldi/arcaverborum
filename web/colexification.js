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
      const graphSpec=spec.subgraphs;
      let graphNode=null;
      if(graphSpec){
        const graphRoot=await checkedJSON(graphSpec,location.href,MAX_ROOT);
        if(graphRoot.parent_build_id!==root.build_id)throw Error('Local subgraph and colexification snapshots differ.');
        graphNode=await checkedJSON(graphRoot.nodes[concept.concept_id],new URL(graphSpec.url,location.href));
        if(!active())return;
      }
      let layer=['segmented','written','reduced'].includes(networkState.colexLayer)?networkState.colexLayer:'segmented',
        kind=['observed','inferred'].includes(networkState.colexKind)?networkState.colexKind:'observed',
        page=Number.isInteger(networkState.colexPage)&&networkState.colexPage>=0?networkState.colexPage:0,
        strong=networkState.colexStrong===true,request=0;
      let weight=['families','languages','varieties'].includes(networkState.colexWeight)?networkState.colexWeight:'families';
      const weightNames={families:'known family lineages',languages:'known language units',varieties:'accepted varieties'},weightIndex={families:2,languages:3,varieties:4};
      const strengthWidth=n=>1+.8*Math.log2(1+Math.max(0,n));
      const recurrence=root.policy.recurrence_families;
      const label=cid=>concepts.get(cid)?.label||cid;
      const conceptLink=cid=>`<a href="${esc(href({view:'concept',cid,page:0,columns:[]}))}">${esc(label(cid))}</a>`;
      const recordLink=(id,text)=>`<a href="${esc(href({view:'form',id,page:0,columns:[]}))}">${esc(text)}</a>`;
      function drawGraph(graph){
        if(!graph||graph.nodes.length<2)return '';
        const nodes=graph.nodes.map((cid,i)=>({cid,x:i?400+190*Math.cos(i*2*Math.PI/(graph.nodes.length-1)):400,y:i?240+160*Math.sin(i*2*Math.PI/(graph.nodes.length-1)):240}));
        // Fixed-size deterministic relaxation; no animation loop or unbounded force graph.
        for(let tick=0;tick<220;tick++){
          const forces=nodes.map(n=>({x:(400-n.x)*.008,y:(240-n.y)*.008}));
          for(let i=0;i<nodes.length;i++)for(let j=i+1;j<nodes.length;j++){
            const dx=nodes[i].x-nodes[j].x,dy=nodes[i].y-nodes[j].y,d2=Math.max(64,dx*dx+dy*dy),f=180/d2;
            forces[i].x+=dx*f;forces[i].y+=dy*f;forces[j].x-=dx*f;forces[j].y-=dy*f;
            if(Math.abs(dx)<95&&Math.abs(dy)<27){const separate=(dy||((i+j)%2?1:-1))>0?1:-1,push=(27-Math.abs(dy))*.25;forces[i].y+=separate*push;forces[j].y-=separate*push;}
          }
          for(const [a,b,families] of graph.edges){
            const dx=nodes[b].x-nodes[a].x,dy=nodes[b].y-nodes[a].y,d=Math.max(1,Math.hypot(dx,dy)),f=(d-85)*.018*(1+Math.log1p(families)*.25);
            forces[a].x+=dx/d*f;forces[a].y+=dy/d*f;forces[b].x-=dx/d*f;forces[b].y-=dy/d*f;
          }
          const cooling=1-tick/260;
          nodes.forEach((n,i)=>{n.x+=Math.max(-10,Math.min(10,forces[i].x))*cooling;n.y+=Math.max(-10,Math.min(10,forces[i].y))*cooling;});
        }
        const xs=nodes.map(n=>n.x),ys=nodes.map(n=>n.y),left=Math.min(...xs),right=Math.max(...xs),top=Math.min(...ys),bottom=Math.max(...ys),scale=Math.min(580/Math.max(1,right-left),350/Math.max(1,bottom-top));
        nodes.forEach(n=>{n.x=400+(n.x-(left+right)/2)*scale;n.y=230+(n.y-(top+bottom)/2)*scale;});
        const lines=graph.edges.map(([a,b,families,languages,varieties])=>`<line data-a="${a}" data-b="${b}" class="${a===0||b===0?'colex-focal-edge':'colex-neighbor-edge'}" x1="${nodes[a].x}" y1="${nodes[a].y}" x2="${nodes[b].x}" y2="${nodes[b].y}" data-strength="${({families,languages,varieties})[weight]}" stroke-width="${strengthWidth(({families,languages,varieties})[weight])}" stroke-dasharray="${({families,languages,varieties})[weight]===0?'3 3':'none'}" tabindex="0" role="button" aria-label="${esc(label(nodes[a].cid))} to ${esc(label(nodes[b].cid))}: ${({families,languages,varieties})[weight]} ${weightNames[weight]}"><title>${esc(label(nodes[a].cid))} ↔ ${esc(label(nodes[b].cid))}: ${families} known families; ${languages} languages; ${varieties} varieties</title></line>`).join('');
        const points=nodes.map((n,i)=>`<a data-node="${i}" href="${esc(href({view:'concept',cid:n.cid,colexPage:0,page:0,columns:[]}))}" transform="translate(${n.x} ${n.y})"><title>${esc(label(n.cid))}${i===0?' (selected concept)':''}. Drag to move; click to open concept.</title><circle class="${i===0?'colex-center':''}" r="${i===0?13:8}"/><text y="${i===0?29:23}" text-anchor="middle">${esc([...label(n.cid)].slice(0,28).join(''))}</text></a>`).join('');
        const legend=[0,1,3,10,100].map(n=>`<span><svg viewBox="0 0 64 16" aria-hidden="true"><line x1="3" x2="61" y1="8" y2="8" stroke-width="${strengthWidth(n)}" stroke-dasharray="${n===0?'3 3':'none'}"/></svg>${n}</span>`).join('');
        const strengths=graph.edges.map(e=>e[weightIndex[weight]]);
        return `<figure class="colex-graph"><div class="colex-strength-legend" aria-label="Connection strength legend"><strong>Line width: ${weightNames[weight]}</strong><div class="colex-width-samples">${legend}</div><p>Displayed support: ${Math.min(...strengths)}–${Math.max(...strengths)}. Width = 1 + 0.8 × log₂(1 + count), on the same scale across concepts. Dashed zero means no known classified units; supporting varieties may be unclassified. Counts measure sampled support, not probability or coverage-adjusted association.</p></div><div class="controls"><button id="colex-zoom-in" aria-label="Zoom network in">+</button><button id="colex-zoom-out" aria-label="Zoom network out">−</button><button id="colex-reset">Reset network view</button></div><svg class="colex-network" viewBox="0 0 800 480" role="img" aria-label="Interconnected colexification subgraph for ${esc(concept.label)}"><g class="colex-viewport"><g class="colex-edges">${lines}</g><g class="colex-nodes">${points}</g></g></svg><figcaption>${nodes.length} concepts and ${graph.edges.length} ${kind==='observed'?'recorded':'inferred'} links, including ${graph.neighbor_links} links among neighbors. Up to ${graph.max_neighbors} strongest direct neighbors, with every eligible edge among the selected concepts; this bounded subgraph is independent of the table page. Line width reflects ${weightNames[weight]}; orange links touch the selected concept, blue links join neighbors. Neighbor selection remains ranked by family support. Layout distance has no statistical interpretation. Drag nodes or the background; use buttons or the wheel to zoom. Click a concept to explore its network.</figcaption><p id="colex-graph-selection" aria-live="polite"></p></figure>`;
      }
      function wireGraph(graph){
        const svg=host.querySelector('.colex-network');if(!svg||!graph)return;
        const viewport=svg.querySelector('.colex-viewport'),points=[...svg.querySelectorAll('[data-node]')],lines=[...svg.querySelectorAll('line[data-a]')];
        const positions=points.map(p=>{const m=p.transform.baseVal.consolidate().matrix;return {x:m.e,y:m.f};});
        let zoom=1,panX=0,panY=0,drag=null,moved=false;
        const transform=()=>viewport.setAttribute('transform',`translate(${panX} ${panY}) scale(${zoom})`);
        const coords=e=>new DOMPoint(e.clientX,e.clientY).matrixTransform(svg.getScreenCTM().inverse());
        const applyZoom=f=>{const next=Math.max(.5,Math.min(3,zoom*f)),ratio=next/zoom;panX=400-(400-panX)*ratio;panY=240-(240-panY)*ratio;zoom=next;transform();};
        host.querySelector('#colex-zoom-in').onclick=()=>applyZoom(1.25);host.querySelector('#colex-zoom-out').onclick=()=>applyZoom(.8);
        host.querySelector('#colex-reset').onclick=()=>{zoom=1;panX=panY=0;transform();};
        svg.addEventListener('wheel',e=>{e.preventDefault();applyZoom(e.deltaY<0?1.1:1/1.1);},{passive:false});
        svg.addEventListener('pointerdown',e=>{if(e.button!==0)return;const p=coords(e),anchor=e.target.closest('[data-node]');moved=false;drag={node:anchor?Number(anchor.dataset.node):null,x:p.x,y:p.y,panX,panY};(anchor||e.target.closest('line[data-a]')||svg).setPointerCapture(e.pointerId);});
        svg.addEventListener('pointermove',e=>{if(!drag)return;const p=coords(e);if(Math.hypot(p.x-drag.x,p.y-drag.y)>3)moved=true;if(drag.node===null){panX=drag.panX+p.x-drag.x;panY=drag.panY+p.y-drag.y;transform();return;}const n=positions[drag.node];n.x=(p.x-panX)/zoom;n.y=(p.y-panY)/zoom;points[drag.node].setAttribute('transform',`translate(${n.x} ${n.y})`);for(const line of lines){const a=positions[Number(line.dataset.a)],b=positions[Number(line.dataset.b)];line.setAttribute('x1',a.x);line.setAttribute('y1',a.y);line.setAttribute('x2',b.x);line.setAttribute('y2',b.y);}});
        const end=e=>{drag=null;const holder=e.target.closest('[data-node],line[data-a]')||svg;if(holder.hasPointerCapture(e.pointerId))holder.releasePointerCapture(e.pointerId);};svg.addEventListener('pointerup',end);svg.addEventListener('pointercancel',end);
        svg.addEventListener('keydown',e=>{if(e.target.matches('line[data-a]')&&(e.key==='Enter'||e.key===' ')){e.preventDefault();e.target.dispatchEvent(new MouseEvent('click',{bubbles:true}));}});
        svg.addEventListener('click',e=>{if(moved){e.preventDefault();e.stopPropagation();moved=false;return;}const line=e.target.closest('line[data-a]');if(!line)return;const a=Number(line.dataset.a),b=Number(line.dataset.b),edge=graph.edges.find(row=>row[0]===a&&row[1]===b);host.querySelector('#colex-graph-selection').innerHTML=conceptLink(graph.nodes[a])+' ↔ '+conceptLink(graph.nodes[b])+`: ${edge[2]} known families, ${edge[3]} known language units, ${edge[4]} varieties. Open either concept to inspect its source examples.`;},true);
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
        if(onState)onState({colexLayer:layer,colexKind:kind,colexStrong:strong,colexPage:page,colexWeight:weight});
        host.innerHTML=`<h3>Colexification</h3><p class="colex-status">Segmented-data status: ${esc(({observed:'Recorded whole-form connections',no_shared_form_observed:'Usable records present; no recorded segmented connections',no_comparable_segmented_data:'No usable segmented records',merged:'Merged concept; excluded from inference'})[node.status]||node.status)}.</p>
          <p class="sub">Whole-form identity is neutral between polysemy and homophony. These precomputed networks cover all accepted varieties; the lexical filters do not change their counts. WordNet associations do not create network edges.</p>
          <div class="controls"><label>Representation <select id="colex-layer"><option value="segmented">Supplied / profile segments</option><option value="written">Citation forms (not phonetic evidence)</option><option value="reduced">ASJP / GLED reduced representations</option></select></label>
          <label>Evidence <select id="colex-kind"><option value="observed">Recorded meaning pairs</option><option value="inferred">Broad-concept inferences</option></select></label>
          <label>Line width <select id="colex-weight"><option value="families">Known family lineages</option><option value="languages">Known language units</option><option value="varieties">Accepted varieties</option></select></label>
          <label><input type="checkbox" id="colex-strong"> At least ${recurrence} known family lineages</label></div>
          ${root.concept_expansions[concept.concept_id]?'<p>This catalog slot is underspecified. Separately labelled inferences link '+root.concept_expansions[concept.concept_id].map(pair=>conceptLink(pair.a)+' and '+conceptLink(pair.b)).join('; ')+'. Open either target and choose “Broad-concept inferences” to inspect the evidence. The original meaning is unchanged.</p>':''}
          <p id="colex-counts">${info.usable_varieties} varieties with usable records for this concept; ${network.neighbors} connections, ${network.recurrent_neighbors} supported by at least ${recurrence} known family lineages.</p>
          <p class="sub">${esc(root.policy.layers[layer])}. ${kind==='inferred'?'Broad-concept inferences are hypotheses from one underspecified slot, kept separate from recorded pairs.':''} Language counts collapse Glottolog dialects; unknown classifications do not add family support. Source duplicates are not independent confirmations.</p>
          <div id="colex-neighbors"><p>Loading bounded network page…</p></div>
          <p class="sub">“No shared form observed” describes the sampled entries, not a proven lexical absence. Missing usable records are unknown. Comparison coverage requires both meanings within the same source, member and pronunciation scope. Rare and regional connections remain available without the three-family filter.</p>
          <p><a href="${esc(new URL(root.files['edges.csv'].url,base))}" download>Network edges CSV</a> · <a href="${esc(new URL(root.files['quarantines.csv'].url,base))}" download>Quarantined identities CSV</a> · <a href="${esc(base)}" download>Network manifest JSON</a> · <a href="docs/COLEXIFICATION.md">Method and resource limits</a> · <a href="docs/CLICS_COMPARISON.md">Comparison with CLICS</a></p>
          <details><summary>Complete evidence and comparison-coverage downloads</summary><p>Gzip CSV shards retain original source IDs; download and decompress the parts needed for your analysis. Coverage records support unknown versus sampled distinctions without a dense all-pairs matrix.</p><ul>${Object.entries(root.files).filter(([name])=>name.endsWith('.csv.gz')||name==='sources.csv').map(([name,file])=>`<li><a href="${esc(new URL(file.url,base))}" download>${esc(name)}</a> · ${(file.bytes/1024/1024).toFixed(2)} MiB</li>`).join('')}</ul></details>`;
        const selector=host.querySelector('#colex-layer');selector.value=layer;selector.onchange=()=>{layer=selector.value;page=0;void update().catch(fail);};
        const evidence=host.querySelector('#colex-kind');evidence.value=kind;evidence.onchange=()=>{kind=evidence.value;page=0;void update().catch(fail);};
        const weighting=host.querySelector('#colex-weight');weighting.value=weight;weighting.onchange=()=>{weight=weighting.value;void update().catch(fail);};
        const filter=host.querySelector('#colex-strong');filter.checked=strong;filter.onchange=()=>{strong=filter.checked;page=0;void update().catch(fail);};
        let edges=[];
        if(network.pages.length){const data=await checkedJSON(network.pages[page],base);edges=data.edges;}
        if(!active()||turn!==request)return;
        if(strong)edges=edges.filter(e=>e.families>=recurrence);
        const totalPages=strong?Math.ceil(network.recurrent_neighbors/root.limits.page_edges):network.pages.length;
        const target=host.querySelector('#colex-neighbors');
        if(!edges.length){target.innerHTML='<p>No connections in this representation, evidence type and page/filter selection.</p>';return;}
        const graph=graphNode?.views[`${layer}:${kind}:${strong?'recurrent':'all'}`];
        target.innerHTML=drawGraph(graph)+`<div class="table-wrap"><table><caption>Connections, with family and comparison coverage</caption><thead><tr><th>Concept</th><th>Known families</th><th>Known language units</th><th>Varieties</th><th>Comparable varieties</th><th>Observed fraction</th><th>Evidence</th></tr></thead><tbody>${edges.map(e=>`<tr><td>${conceptLink(e.concept_id)}</td><td>${e.families}</td><td>${e.languages}</td><td>${e.varieties}</td><td>${e.comparable_varieties??'Not applicable'}</td><td>${e.observed_fraction==null?'Not applicable':(100*e.observed_fraction).toFixed(2)+'%'}</td><td>${example(e)}</td></tr>`).join('')}</tbody></table></div>
          <div class="controls"><button id="colex-prev" ${page===0?'disabled':''}>Previous connections</button><span>Page ${page+1} of ${totalPages}; at most ${root.limits.page_edges} connections per download</span><button id="colex-next" ${page+1>=totalPages?'disabled':''}>Next connections</button></div>`;
        wireGraph(graph);
        host.querySelector('#colex-prev').onclick=()=>{page--;void update().catch(fail);};host.querySelector('#colex-next').onclick=()=>{page++;void update().catch(fail);};
      }
      function fail(error){if(active())host.innerHTML='<h3>Colexification</h3><p role="alert">'+esc(error.message)+'</p>';}
      await update();
    }catch(error){if(active())host.innerHTML='<h3>Colexification</h3><p role="alert">'+esc(error.message)+'</p>';}
  }
  return {placeholder,render};
})();
