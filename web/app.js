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
  const P = one("SELECT * FROM parameters WHERE ID=?", [cid]);
  if (!P) return;
  const rows = q(
    `SELECT f.*, l.Family AS Family, l.Name AS LangName
     FROM forms f JOIN languages l ON l.ID=f.Language_ID
     WHERE f.Parameter_ID=? ORDER BY l.Family, l.Name`, [cid]);
  app().innerHTML = `
    <p class="crumb"><a id="back">← Concepts</a></p>
    <h2 class="view-title">${esc(P.Name)} ${P.is_core === "true" ? '<span class="chip core">core</span>' : ""}</h2>
    <p class="sub">${esc(P.semantic_field)} · ${esc(P.pos || "")} · Concepticon ${esc(P.Concepticon_ID || "—")}
      · ${rows.length} forms across ${new Set(rows.map((r) => r.Language_ID)).size} varieties</p>
    ${table([
      { key: "Family", label: "Family" },
      { key: "LangName", label: "Variety", render: (r) => `<span class="clink" data-av="${esc(r.Language_ID)}">${esc(r.LangName)}</span>` },
      { key: "Form", label: "Form" },
      { key: "Segments", label: "Segments", seg: true },
      { key: "Cognacy", label: "Cognate", render: cognacyCell },
    ], rows)}`;
  $("#back").onclick = showConcepts;
  wireDrill();
}

function showCognate(code, pid) {
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

// ---- nav / boot ----
const VIEWS = { varieties: showVarieties, concepts: showConcepts, search: showSearch, stats: showStats, sql: showSQL };
function setNav() {
  document.querySelectorAll("#nav button").forEach((b) =>
    b.classList.toggle("active", b.dataset.view === view));
}
function wireNav() {
  document.querySelectorAll("#nav button").forEach((b) =>
    b.onclick = () => { if (location.hash !== "#" + b.dataset.view) location.hash = b.dataset.view; else VIEWS[b.dataset.view](); });
  window.onhashchange = () => {
    const v = location.hash.replace("#", "");
    if (VIEWS[v]) VIEWS[v]();
  };
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
    const initial = location.hash.replace("#", "");
    (VIEWS[initial] || showVarieties)();
  } catch (e) {
    $("#status").innerHTML = `<p class="err">Failed to load: ${esc(e.message)}</p>`;
  }
}
boot();
