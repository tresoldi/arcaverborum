"use strict";

let db = null;
let BUILD = {};
let coreOnly = false;
let view = "varieties";

const $ = (sel) => document.querySelector(sel);
const app = () => $("#app");
const esc = (s) => String(s == null ? "" : s).replace(/[&<>"]/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

function q(sql, params = []) {
  const st = db.prepare(sql);
  st.bind(params);
  const rows = [];
  while (st.step()) rows.push(st.getAsObject());
  st.free();
  return rows;
}
function one(sql, params = []) { const r = q(sql, params); return r[0] || null; }
const coreClause = (alias = "") => coreOnly ? ` AND ${alias}is_core_concept='true'` : "";
const fmt = (n) => Number(n).toLocaleString();

// ---- rendering helpers ----
function table(cols, rows, rowAttrs) {
  if (!rows.length) return `<p class="empty">No results.</p>`;
  const head = cols.map((c) => `<th${c.num ? ' class="num"' : ""}>${esc(c.label)}</th>`).join("");
  const body = rows.map((r) => {
    const attrs = rowAttrs ? rowAttrs(r) : "";
    const tds = cols.map((c) => {
      const v = c.render ? c.render(r) : esc(r[c.key]);
      const cls = [c.num ? "num" : "", c.seg ? "seg" : ""].filter(Boolean).join(" ");
      return `<td${cls ? ` class="${cls}"` : ""}>${v}</td>`;
    }).join("");
    return `<tr${attrs}>${tds}</tr>`;
  }).join("");
  return `<div class="scroll"><table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`;
}
const coreToggle = () =>
  `<label class="toggle"><input type="checkbox" id="coretoggle"${coreOnly ? " checked" : ""}> basic-vocabulary core only</label>`;
function wireCoreToggle(rerender) {
  const t = $("#coretoggle");
  if (t) t.onchange = () => { coreOnly = t.checked; rerender(); };
}
const cognacyCell = (r) => r.Cognacy
  ? `<span class="clink" data-cog="${esc(r.Cognacy)}" data-pid="${esc(r.Parameter_ID)}">${esc(r.Cognacy)}</span>`
  : "";
function wireDrill() {
  app().querySelectorAll("[data-av]").forEach((e) => e.onclick = () => showVariety(e.dataset.av));
  app().querySelectorAll("[data-cid]").forEach((e) => e.onclick = () => showConcept(e.dataset.cid));
  app().querySelectorAll("[data-cog]").forEach((e) => e.onclick = () => showCognate(e.dataset.cog, e.dataset.pid));
}

// ---- views ----
function showVarieties() {
  view = "varieties"; setNav();
  const families = q("SELECT DISTINCT Family FROM languages WHERE Family<>'' ORDER BY Family");
  const st = window._vstate || (window._vstate = { fam: "", tier: "", search: "" });
  const render = () => {
    const where = [], p = [];
    if (st.fam) { where.push("l.Family=?"); p.push(st.fam); }
    if (st.tier) { where.push("l.tier=?"); p.push(st.tier); }
    if (st.search) { where.push("l.Name LIKE ?"); p.push("%" + st.search + "%"); }
    const wsql = where.length ? " WHERE " + where.join(" AND ") : "";
    const rows = q(
      `SELECT l.ID, l.Name, l.Family, l.Macroarea, l.tier,
        COUNT(f.ID) AS nf
       FROM languages l LEFT JOIN forms f ON f.Language_ID=l.ID${coreOnly ? " AND f.is_core_concept='true'" : ""}
       ${wsql} GROUP BY l.ID ORDER BY nf DESC, l.Name`, p);
    $("#vresults").innerHTML =
      `<p class="sub">${rows.length} varieties${coreOnly ? " (core forms counted)" : ""}</p>` +
      table([
        { key: "Name", label: "Variety" },
        { key: "Family", label: "Family" },
        { key: "Macroarea", label: "Macroarea" },
        { key: "tier", label: "Tier", render: (r) => `<span class="tier">${esc(r.tier)}</span>` },
        { key: "nf", label: "Forms", num: true, render: (r) => fmt(r.nf) },
      ], rows, (r) => ` class="rowlink" data-av="${esc(r.ID)}"`);
    wireDrill();
  };
  app().innerHTML = `
    <div class="controls">
      <input type="text" id="vsearch" placeholder="Search variety name…" value="${esc(st.search)}">
      <select id="vfam"><option value="">All families</option>${families.map((f) =>
        `<option${st.fam === f.Family ? " selected" : ""}>${esc(f.Family)}</option>`).join("")}</select>
      <select id="vtier"><option value="">All tiers</option>${["gold","silver","bronze","copper"].map((t) =>
        `<option${st.tier === t ? " selected" : ""}>${t}</option>`).join("")}</select>
      ${coreToggle()}
    </div>
    <div id="vresults"></div>`;
  $("#vsearch").oninput = (e) => { st.search = e.target.value.trim(); render(); };
  $("#vfam").onchange = (e) => { st.fam = e.target.value; render(); };
  $("#vtier").onchange = (e) => { st.tier = e.target.value; render(); };
  wireCoreToggle(render);
  render();
}

function showVariety(id) {
  destroyMap();
  const L = one("SELECT * FROM languages WHERE ID=?", [id]);
  if (!L) return;
  const rows = q(
    `SELECT * FROM forms WHERE Language_ID=?${coreClause()} ORDER BY concept_label`, [id]);
  app().innerHTML = `
    <p class="crumb"><a id="back">← Varieties</a></p>
    <h2 class="view-title">${esc(L.Name)}</h2>
    <p class="sub">${esc(L.Family)} · ${esc(L.Macroarea || "—")} · Glottocode ${esc(L.Glottocode || "—")}
      · tier ${esc(L.tier)} · ${rows.length} forms${coreOnly ? " (core only)" : ""}</p>
    <div class="controls">${coreToggle()}</div>
    <div id="vd"></div>`;
  $("#vd").innerHTML = table([
    { key: "concept_label", label: "Concept",
      render: (r) => `<span class="clink" data-cid="${esc(r.Parameter_ID)}">${esc(r.concept_label)}</span>${
        r.is_core_concept === "true" ? ' <span class="chip core">core</span>' : ""}` },
    { key: "Form", label: "Form" },
    { key: "Segments", label: "Segments", seg: true },
    { key: "Cognacy", label: "Cognate", render: cognacyCell },
  ], rows);
  $("#back").onclick = showVarieties;
  wireCoreToggle(() => showVariety(id));
  wireDrill();
}

function showConcepts() {
  view = "concepts"; setNav();
  const st = window._cstate || (window._cstate = { search: "" });
  const render = () => {
    const where = [], p = [];
    if (st.search) { where.push("(p.Name LIKE ? OR p.ID LIKE ?)"); p.push("%" + st.search + "%", "%" + st.search + "%"); }
    const wsql = where.length ? " WHERE " + where.join(" AND ") : "";
    const rows = q(
      `SELECT p.ID, p.Name, p.semantic_field, p.pos, p.is_core,
        COUNT(f.ID) AS nf, COUNT(DISTINCT f.Language_ID) AS nv
       FROM parameters p LEFT JOIN forms f ON f.Parameter_ID=p.ID
       ${wsql} GROUP BY p.ID ORDER BY nv DESC, nf DESC`, p);
    $("#cresults").innerHTML = `<p class="sub">${rows.length} concepts</p>` + table([
      { key: "Name", label: "Concept",
        render: (r) => `${esc(r.Name)}${r.is_core === "true" ? ' <span class="chip core">core</span>' : ""}` },
      { key: "semantic_field", label: "Field" },
      { key: "pos", label: "POS" },
      { key: "nv", label: "Varieties", num: true, render: (r) => fmt(r.nv) },
      { key: "nf", label: "Forms", num: true, render: (r) => fmt(r.nf) },
    ], rows, (r) => ` class="rowlink" data-cid="${esc(r.ID)}"`);
    wireDrill();
  };
  app().innerHTML = `
    <div class="controls">
      <input type="text" id="csearch" placeholder="Search concept…" value="${esc(st.search)}">
    </div><div id="cresults"></div>`;
  $("#csearch").oninput = (e) => { st.search = e.target.value.trim(); render(); };
  render();
}

function showConcept(cid) {
  destroyMap();
  const P = one("SELECT * FROM parameters WHERE ID=?", [cid]);
  if (!P) return;
  const rows = q(
    `SELECT f.*, l.Family AS Family, l.Name AS LangName, l.Latitude AS Latitude, l.Longitude AS Longitude
     FROM forms f JOIN languages l ON l.ID=f.Language_ID
     WHERE f.Parameter_ID=? ORDER BY l.Family, l.Name`, [cid]);
  app().innerHTML = `
    <p class="crumb"><a id="back">← Concepts</a></p>
    <h2 class="view-title">${esc(P.Name)} ${P.is_core === "true" ? '<span class="chip core">core</span>' : ""}</h2>
    <p class="sub">${esc(P.semantic_field)} · ${esc(P.pos || "")} · Concepticon ${esc(P.Concepticon_ID || "—")}
      · ${rows.length} forms across ${new Set(rows.map((r) => r.Language_ID)).size} varieties</p>
    <div id="conceptmap"></div>
    ${table([
      { key: "Family", label: "Family" },
      { key: "LangName", label: "Variety", render: (r) => `<span class="clink" data-av="${esc(r.Language_ID)}">${esc(r.LangName)}</span>` },
      { key: "Form", label: "Form" },
      { key: "Segments", label: "Segments", seg: true },
      { key: "Cognacy", label: "Cognate", render: cognacyCell },
    ], rows)}`;
  $("#back").onclick = showConcepts;
  wireDrill();
  loadWorld().then(() => conceptMap(cid, rows));
}

function showCognate(code, pid) {
  destroyMap();
  const rows = q(
    `SELECT f.*, l.Family AS Family, l.Name AS LangName
     FROM forms f JOIN languages l ON l.ID=f.Language_ID
     WHERE f.Cognacy=? AND f.Parameter_ID=? ORDER BY l.Family, l.Name`, [code, pid]);
  const P = one("SELECT Name FROM parameters WHERE ID=?", [pid]);
  app().innerHTML = `
    <p class="crumb"><a id="back">← Concept</a></p>
    <h2 class="view-title">Cognate set ${esc(code)}</h2>
    <p class="sub">Concept “${esc(P ? P.Name : pid)}” · ${rows.length} members</p>
    ${table([
      { key: "Family", label: "Family" },
      { key: "LangName", label: "Variety", render: (r) => `<span class="clink" data-av="${esc(r.Language_ID)}">${esc(r.LangName)}</span>` },
      { key: "Form", label: "Form" },
      { key: "Segments", label: "Segments", seg: true },
    ], rows)}`;
  $("#back").onclick = () => showConcept(pid);
  wireDrill();
}

function showSearch() {
  view = "search"; setNav();
  const st = window._sstate || (window._sstate = { term: "" });
  const render = () => {
    let html = "";
    if (st.term) {
      const like = "%" + st.term + "%";
      const rows = q(
        `SELECT f.*, l.Name AS LangName, l.Family AS Family
         FROM forms f JOIN languages l ON l.ID=f.Language_ID
         WHERE (f.Form LIKE ? OR f.Segments LIKE ?)${coreClause("f.")}
         ORDER BY l.Family, l.Name LIMIT 500`, [like, like]);
      html = `<p class="sub">${rows.length} matching forms${rows.length === 500 ? " (showing first 500)" : ""}</p>` +
        table([
          { key: "Form", label: "Form" },
          { key: "Segments", label: "Segments", seg: true },
          { key: "concept_label", label: "Concept", render: (r) => `<span class="clink" data-cid="${esc(r.Parameter_ID)}">${esc(r.concept_label)}</span>` },
          { key: "LangName", label: "Variety", render: (r) => `<span class="clink" data-av="${esc(r.Language_ID)}">${esc(r.LangName)}</span>` },
          { key: "Family", label: "Family" },
        ], rows);
    } else {
      html = `<p class="empty">Type a form or segment sequence to search (e.g. <code>aqua</code>, <code>w a</code>).</p>`;
    }
    $("#sresults").innerHTML = html;
    wireDrill();
  };
  app().innerHTML = `
    <div class="controls">
      <input type="text" id="sterm" placeholder="Search Form or Segments…" value="${esc(st.term)}" style="min-width:280px">
      ${coreToggle()}
    </div><div id="sresults"></div>`;
  $("#sterm").oninput = (e) => { st.term = e.target.value.trim(); render(); };
  wireCoreToggle(render);
  render();
}

function showStats() {
  view = "stats"; setNav();
  const tot = one("SELECT COUNT(*) AS f FROM forms");
  const core = one("SELECT COUNT(*) AS f FROM forms WHERE is_core_concept='true'");
  const nl = one("SELECT COUNT(*) AS n FROM languages");
  const np = one("SELECT COUNT(*) AS n FROM parameters");
  const fam = q(
    `SELECT l.Family AS Family, COUNT(DISTINCT l.ID) AS nv, COUNT(f.ID) AS nf,
      SUM(CASE WHEN f.is_core_concept='true' THEN 1 ELSE 0 END) AS ncore
     FROM languages l LEFT JOIN forms f ON f.Language_ID=l.ID
     GROUP BY l.Family ORDER BY nf DESC`);
  app().innerHTML = `
    <h2 class="view-title">Statistics</h2>
    <p class="sub">${fmt(tot.f)} forms · ${fmt(core.f)} basic-vocab core · ${fmt(nl.n)} varieties · ${fmt(np.n)} concepts</p>
    ${table([
      { key: "Family", label: "Family" },
      { key: "nv", label: "Varieties", num: true, render: (r) => fmt(r.nv) },
      { key: "nf", label: "Forms", num: true, render: (r) => fmt(r.nf) },
      { key: "ncore", label: "Core forms", num: true, render: (r) => fmt(r.ncore) },
    ], fam)}`;
}

function showSQL() {
  view = "sql"; setNav();
  const example = "SELECT l.Family, COUNT(*) AS forms\nFROM forms f JOIN languages l ON l.ID=f.Language_ID\nGROUP BY l.Family\nORDER BY forms DESC;";
  app().innerHTML = `
    <p class="sub">Read-only <code>SELECT</code> / <code>WITH</code> / <code>PRAGMA</code> over tables
      <code>forms</code>, <code>languages</code>, <code>parameters</code>.</p>
    <textarea id="sqlbox">${esc(example)}</textarea>
    <div class="controls" style="margin-top:8px"><button class="primary" id="run">Run</button></div>
    <div id="sqlout"></div>`;
  $("#run").onclick = () => {
    const sql = $("#sqlbox").value.trim().replace(/;+\s*$/, "");
    if (!/^\s*(select|with|pragma|explain)\b/i.test(sql)) {
      $("#sqlout").innerHTML = `<p class="err">Only SELECT / WITH / PRAGMA / EXPLAIN are allowed.</p>`;
      return;
    }
    try {
      const rows = q(sql);
      if (!rows.length) { $("#sqlout").innerHTML = `<p class="empty">No rows.</p>`; return; }
      const cols = Object.keys(rows[0]).map((k) => ({ key: k, label: k }));
      $("#sqlout").innerHTML = `<p class="sub">${rows.length} rows</p>` + table(cols, rows.slice(0, 1000));
    } catch (e) {
      $("#sqlout").innerHTML = `<p class="err">${esc(e.message)}</p>`;
    }
  };
}

// ---- maps ----
const MPAL = ["#4e79a7","#f28e2b","#e15759","#76b7b2","#59a14f","#edc948","#b07aa1",
  "#ff9da7","#9c755f","#8cd17d","#1f77b4","#d62728","#9467bd","#e377c2","#17becf",
  "#bcbd22","#8c564b","#7f7f7f","#aec7e8","#ffbb78"];
const TIER_COLORS = { gold: "#d9a441", silver: "#9aa0a6", bronze: "#a8703e", copper: "#7a4b2e" };
const COV_BINS = [[0, 50], [50, 150], [150, 350], [350, 600], [600, 1e12]];
const COV_LABELS = ["< 50", "50–150", "150–350", "350–600", "600+"];
const COV_SHADES = ["#e7d7cf", "#d3a892", "#c07a5c", "#9c5236", "#6f2f1c"];
const keyColors = (keys) => { const m = {}; keys.forEach((k, i) => m[k] = MPAL[i % MPAL.length]); return m; };
let _map = null, _world = null;
function destroyMap() { if (_map) { _map.remove(); _map = null; } }
async function loadWorld() {
  if (!_world) _world = await fetch("vendor/world.geo.json").then((r) => r.json());
  return _world;
}
function baseMap(el, center, zoom) {
  const m = L.map(el, { worldCopyJump: true, attributionControl: false }).setView(center, zoom);
  L.geoJSON(_world, { style: { fillColor: "#ece7dd", fillOpacity: 1, color: "#c9beb0", weight: 0.6 }, interactive: false }).addTo(m);
  return m;
}
function mapCtl(map, pos, cls, html) {
  const c = L.control({ position: pos });
  c.onAdd = () => { const d = L.DomUtil.create("div", cls); d.innerHTML = html; return d; };
  c.addTo(map);
}
const legendHTML = (title, entries) => `<b>${esc(title)}</b>` +
  entries.map((e) => `<div><i style="background:${e.color}"></i>${esc(e.label)}</div>`).join("");

function showMap() {
  view = "map"; setNav();
  app().innerHTML = `
    <div class="controls">
      <label class="toggle">Colour by
        <select id="mmode">
          <option value="family">Family</option>
          <option value="macroarea">Macroarea</option>
          <option value="tier">Tier</option>
          <option value="coverage">Coverage (form count)</option>
        </select></label>
    </div>
    <div id="mapc" class="map"></div>`;
  loadWorld().then(() => {
    const langs = q(
      `SELECT l.ID, l.Name, l.Family, l.Macroarea, l.tier, l.Latitude, l.Longitude,
        COUNT(f.ID) AS nf
       FROM languages l LEFT JOIN forms f ON f.Language_ID=l.ID
       WHERE l.Latitude<>'' AND l.Longitude<>'' GROUP BY l.ID`);
    const render = () => {
      destroyMap();
      _map = baseMap($("#mapc"), [15, 15], 2);
      const mode = $("#mmode").value;
      let color, entries, title;
      if (mode === "tier") {
        color = (d) => TIER_COLORS[d.tier] || "#bbb";
        entries = ["gold", "silver", "bronze", "copper"].map((t) => ({ color: TIER_COLORS[t], label: t }));
        title = "Tier";
      } else if (mode === "coverage") {
        const binOf = (n) => COV_BINS.findIndex(([a, b]) => n >= a && n < b);
        color = (d) => COV_SHADES[binOf(+d.nf)];
        entries = COV_LABELS.map((l, i) => ({ color: COV_SHADES[i], label: l + " forms" }));
        title = "Coverage";
      } else {
        const field = mode === "macroarea" ? "Macroarea" : "Family";
        const counts = {};
        langs.forEach((d) => { const k = d[field] || "—"; counts[k] = (counts[k] || 0) + 1; });
        const top = Object.entries(counts).sort((a, b) => b[1] - a[1])
          .slice(0, mode === "family" ? 12 : 20).map((e) => e[0]);
        const cm = keyColors(top);
        color = (d) => top.includes(d[field] || "—") ? cm[d[field] || "—"] : "#b8b0a6";
        entries = top.map((k) => ({ color: cm[k], label: `${k} (${counts[k]})` }));
        if (Object.keys(counts).length > top.length) entries.push({ color: "#b8b0a6", label: "other" });
        title = field;
      }
      langs.forEach((d) => {
        L.circleMarker([+d.Latitude, +d.Longitude],
          { radius: 4, weight: 0.6, color: "#fff", fillColor: color(d), fillOpacity: 0.9 })
          .addTo(_map)
          .bindTooltip(`${esc(d.Name)} — ${esc(d.Family)} · ${fmt(d.nf)} forms`)
          .on("click", () => showVariety(d.ID));
      });
      mapCtl(_map, "bottomleft", "legend", legendHTML(title, entries));
      mapCtl(_map, "topright", "titlebox",
        `<b>${fmt(langs.length)} varieties</b><br>Click a point for the variety's forms.`);
    };
    $("#mmode").onchange = render;
    render();
  });
}

function conceptMap(cid, rows) {
  const withxy = rows.filter((r) => r.Latitude && r.Longitude);
  if (withxy.length < 2) return;
  const fams = [...new Set(withxy.map((r) => r.Family))].sort();
  const byFam = {}; withxy.forEach((r) => (byFam[r.Family] = (byFam[r.Family] || 0) + 1));
  const defFam = fams.slice().sort((a, b) => byFam[b] - byFam[a])[0];
  const host = document.getElementById("conceptmap");
  if (!host) return;
  host.innerHTML = `
    <div class="controls">
      <label class="toggle">Cognate map — family
        <select id="cmfam">${fams.map((f) =>
          `<option${f === defFam ? " selected" : ""}>${esc(f)} (${byFam[f]})</option>`).join("")}</select></label>
    </div>
    <div id="cmap" class="map small"></div>`;
  const cog = (r) => r.Cognacy || "";   // full cognate coding (may be "X;Y" for partial cognacy)
  const draw = () => {
    destroyMap();
    const fam = $("#cmfam").value.replace(/\s+\(\d+\)$/, "");
    const pts = withxy.filter((r) => r.Family === fam);
    _map = baseMap($("#cmap"), [20, 0], 2);
    const classes = [...new Set(pts.map(cog).filter(Boolean))]
      .sort((a, b) => (+a.replace(/\D+/g, "") || 0) - (+b.replace(/\D+/g, "") || 0));
    const cm = keyColors(classes);
    const rep = {}; pts.forEach((p) => { const k = cog(p); if (k && !rep[k]) rep[k] = p.Form; });
    const ll = [];
    pts.forEach((p) => {
      const c = [+p.Latitude, +p.Longitude]; ll.push(c); const k = cog(p);
      L.circleMarker(c, { radius: 6, weight: 0.8, color: "#333",
        fillColor: k ? cm[k] : "#ccc", fillOpacity: 0.92 })
        .addTo(_map)
        .bindTooltip(`${esc(p.LangName)}: ${esc(p.Form)}${k ? " (set " + esc(k) + ")" : ""}`)
        .on("click", () => showVariety(p.Language_ID));
    });
    if (ll.length) _map.fitBounds(L.latLngBounds(ll).pad(0.25));
    mapCtl(_map, "bottomleft", "legend",
      legendHTML(`Cognate set — ${classes.length}`,
        classes.map((c) => ({ color: cm[c], label: `${c} · ${rep[c] || ""}` }))));
  };
  $("#cmfam").onchange = draw;
  draw();
}

// ---- nav / boot ----
const VIEWS = { varieties: showVarieties, concepts: showConcepts, map: showMap, search: showSearch, stats: showStats, sql: showSQL };
function setNav() {
  destroyMap();
  document.querySelectorAll("#nav button").forEach((b) =>
    b.classList.toggle("active", b.dataset.view === view));
}
function route(hash) {
  const h = (hash || "").replace(/^#/, "");
  if (h.startsWith("concept:")) return showConcept(h.slice(8)), true;
  if (h.startsWith("variety:")) return showVariety(h.slice(8)), true;
  if (VIEWS[h]) return VIEWS[h](), true;
  return false;
}
function wireNav() {
  document.querySelectorAll("#nav button").forEach((b) =>
    b.onclick = () => { if (location.hash !== "#" + b.dataset.view) location.hash = b.dataset.view; else VIEWS[b.dataset.view](); });
  window.onhashchange = () => route(location.hash);
}

async function boot() {
  try {
    const SQL = await initSqlJs({ locateFile: (f) => "vendor/" + f });
    $("#status-detail").textContent = "(fetching data…)";
    const [gz, info] = await Promise.all([
      fetch("arca-core.sqlite.gz"),
      fetch("BUILD_INFO").then((r) => r.ok ? r.json() : {}).catch(() => ({})),
    ]);
    if (!gz.ok) throw new Error("could not fetch dataset (" + gz.status + ")");
    BUILD = info || {};
    const buf = await new Response(gz.body.pipeThrough(new DecompressionStream("gzip"))).arrayBuffer();
    db = new SQL.Database(new Uint8Array(buf));
    const c = BUILD.counts || {};
    $("#ver").textContent = BUILD.version ? "v" + BUILD.version : "";
    $("#counts").textContent = c.forms
      ? `${fmt(c.forms)} forms · ${fmt(c.languages)} varieties · ${fmt(c.parameters)} concepts · merkmal ${BUILD.merkmal_version || "?"}`
      : "";
    $("#status").hidden = true;
    app().hidden = false;
    wireNav();
    if (!route(location.hash)) showVarieties();
  } catch (e) {
    $("#status").innerHTML = `<p class="err">Failed to load: ${esc(e.message)}</p>`;
  }
}
boot();
