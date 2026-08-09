"""Inlined HTML templates for the ADF WYSIWYG viewer."""

from __future__ import annotations

# Shared file-browser styles + markup injected into index + edit pages.
_BROWSER_CSS = """
  .browser-backdrop { position:fixed; inset:0; background:rgba(20,30,40,.45); z-index:100;
    display:none; align-items:center; justify-content:center; padding:16px; }
  .browser-backdrop.open { display:flex; }
  .browser-modal { background:#fff; width:min(720px,100%); max-height:min(80vh,640px); display:flex;
    flex-direction:column; border:1px solid #d0d7de; box-shadow:0 12px 40px rgba(0,0,0,.18); }
  .browser-modal header { display:flex; gap:8px; align-items:center; padding:10px 12px; border-bottom:1px solid #d0d7de; }
  .browser-modal header strong { flex:1; font-size:14px; }
  .browser-path { display:flex; gap:6px; padding:8px 12px; border-bottom:1px solid #d0d7de; background:#f6f8fa; }
  .browser-path input { flex:1; padding:6px 8px; border:1px solid #d0d7de; font-family:ui-monospace,monospace; font-size:12px; }
  .browser-list { flex:1; overflow:auto; padding:6px 0; min-height:200px; }
  .browser-row { display:flex; gap:10px; align-items:center; padding:8px 14px; cursor:pointer; border:0; background:transparent;
    width:100%; text-align:left; font:inherit; color:inherit; }
  .browser-row:hover { background:#ddf4ff; }
  .browser-row .kind { font-size:11px; font-weight:700; color:#5a6a7a; width:3.5rem; }
  .browser-row.invalid { opacity:.55; }
  .browser-footer { display:flex; gap:8px; flex-wrap:wrap; padding:10px 12px; border-top:1px solid #d0d7de; }
  .browser-footer input { flex:1; min-width:140px; padding:6px 8px; border:1px solid #d0d7de; }
  .browser-err { color:#cf222e; font-size:12px; padding:0 12px 8px; }
"""

_BROWSER_MODAL = """
<div class="browser-backdrop" id="browserBackdrop" role="dialog" aria-modal="true" aria-label="Browse ADF files">
  <div class="browser-modal">
    <header>
      <strong>Open ADF file</strong>
      <button type="button" id="browserHome">Home</button>
      <button type="button" id="browserAdf">adf/</button>
      <button type="button" id="browserClose">Close</button>
    </header>
    <div class="browser-path">
      <button type="button" id="browserUp" title="Parent folder">↑</button>
      <input id="browserPathInput" spellcheck="false" placeholder="/absolute/or/relative/path">
      <button type="button" id="browserGo">Go</button>
    </div>
    <div class="browser-err" id="browserErr" hidden></div>
    <div class="browser-list" id="browserList"></div>
    <div class="browser-footer">
      <input id="browserNewName" placeholder="NewFile.adf.json">
      <button type="button" id="browserCreate">Create here</button>
    </div>
  </div>
</div>
"""

_BROWSER_JS = r"""
function installFileBrowser(opts) {
  const startPath = opts.startPath || "";
  const backdrop = document.getElementById("browserBackdrop");
  const listEl = document.getElementById("browserList");
  const pathInput = document.getElementById("browserPathInput");
  const errEl = document.getElementById("browserErr");
  let currentPath = startPath;

  function showErr(msg) {
    if (!msg) { errEl.hidden = true; errEl.textContent = ""; return; }
    errEl.hidden = false; errEl.textContent = msg;
  }
  function openBrowser(path) {
    backdrop.classList.add("open");
    loadBrowse(path || currentPath || startPath);
  }
  function closeBrowser() { backdrop.classList.remove("open"); }

  async function loadBrowse(path) {
    showErr("");
    const url = "/api/browse?path=" + encodeURIComponent(path || "");
    const resp = await fetch(url);
    const data = await resp.json();
    if (!data.ok) { showErr(data.error || "browse failed"); return; }
    currentPath = data.path;
    pathInput.value = data.path;
    listEl.innerHTML = "";
    if (data.parent) {
      const up = document.createElement("button");
      up.type = "button";
      up.className = "browser-row";
      up.innerHTML = '<span class="kind">DIR</span><span>..</span>';
      up.onclick = () => loadBrowse(data.parent);
      listEl.appendChild(up);
    }
    for (const d of data.dirs || []) {
      const row = document.createElement("button");
      row.type = "button";
      row.className = "browser-row";
      row.innerHTML = '<span class="kind">DIR</span><span></span>';
      row.querySelector("span:last-child").textContent = d.name + "/";
      row.onclick = () => loadBrowse(d.path);
      listEl.appendChild(row);
    }
    for (const f of data.files || []) {
      const row = document.createElement("button");
      row.type = "button";
      row.className = "browser-row" + (f.valid ? "" : " invalid");
      row.innerHTML = '<span class="kind">ADF</span><span></span>';
      row.querySelector("span:last-child").textContent = f.name + (f.valid ? "" : " (invalid)");
      if (f.valid) row.onclick = () => { location.href = "/edit?path=" + encodeURIComponent(f.path); };
      listEl.appendChild(row);
    }
    if (!(data.dirs || []).length && !(data.files || []).length) {
      const empty = document.createElement("div");
      empty.style.padding = "16px";
      empty.style.color = "#5a6a7a";
      empty.textContent = "No folders or ADF JSON files here.";
      listEl.appendChild(empty);
    }
    window.__browserMeta = data;
  }

  document.getElementById("browserClose").onclick = closeBrowser;
  document.getElementById("browserUp").onclick = () => {
    const meta = window.__browserMeta;
    if (meta && meta.parent) loadBrowse(meta.parent);
  };
  document.getElementById("browserGo").onclick = () => loadBrowse(pathInput.value.trim());
  pathInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") { e.preventDefault(); loadBrowse(pathInput.value.trim()); }
  });
  document.getElementById("browserHome").onclick = async () => {
    const resp = await fetch("/api/browse?path=");
    const data = await resp.json();
    if (data.ok && data.home) loadBrowse(data.home);
  };
  document.getElementById("browserAdf").onclick = async () => {
    const resp = await fetch("/api/browse?path=");
    const data = await resp.json();
    if (data.ok && data.adf_dir) loadBrowse(data.adf_dir);
    else if (data.ok) loadBrowse(data.path);
  };
  document.getElementById("browserCreate").onclick = async () => {
    const name = document.getElementById("browserNewName").value.trim();
    if (!name) { showErr("Enter a filename like ORCH-2.adf.json"); return; }
    const sep = currentPath.includes("\\") && !currentPath.includes("/") ? "\\" : "/";
    const full = currentPath.replace(/[\\/]+$/, "") + sep + name;
    const resp = await fetch("/api/create", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: full }),
    });
    const data = await resp.json();
    if (!data.ok) { showErr(data.error || "create failed"); return; }
    location.href = data.edit_url || ("/edit?path=" + encodeURIComponent(data.path));
  };
  backdrop.addEventListener("click", (e) => { if (e.target === backdrop) closeBrowser(); });
  return { openBrowser, closeBrowser, loadBrowse };
}
"""

INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ADF Ticket Viewer</title>
<style>
  :root { --bg:#eef1f4; --card:#fff; --ink:#1a2332; --muted:#5a6a7a; --accent:#1f6feb; --line:#d0d7de; }
  * { box-sizing: border-box; }
  body { margin:0; font-family: "IBM Plex Sans", "Segoe UI", sans-serif; background:
    radial-gradient(1200px 600px at 10% -10%, #d8e6f8 0%, transparent 55%),
    linear-gradient(180deg, #f7f9fb, var(--bg)); color: var(--ink); min-height:100vh; }
  main { max-width: 820px; margin: 0 auto; padding: 36px 20px 64px; }
  h1 { font-family: "IBM Plex Serif", Georgia, serif; font-size: clamp(1.8rem, 4vw, 2.4rem); margin: 0 0 8px; }
  p.lead { color: var(--muted); margin: 0 0 20px; line-height: 1.5; }
  .actions { display:flex; flex-wrap:wrap; gap:8px; margin-bottom:20px; }
  button, .btn { border:1px solid var(--line); background:#fff; color:var(--ink); padding:8px 12px; cursor:pointer; font: inherit; font-size:14px; }
  button.primary { background: var(--accent); color:#fff; border-color: var(--accent); }
  a.ticket { display:block; padding:12px 14px; margin:0 0 8px; background:var(--card); border:1px solid var(--line);
    text-decoration:none; color:var(--ink); font-weight:600; }
  a.ticket:hover { border-color: var(--accent); }
  .empty { color: var(--muted); padding: 16px; border: 1px dashed var(--line); margin-bottom:16px; }
  code { font-family: "IBM Plex Mono", ui-monospace, monospace; font-size: .9em; }
""" + _BROWSER_CSS + """
</style>
</head>
<body>
<main>
  <h1>ADF Ticket Viewer</h1>
  <p class="lead">Local editor — browse any folder on this machine for <code>*.adf.json</code> / ADF JSON files.
    Start dir: <code>{{ root_label }}</code></p>
  <div class="actions">
    <button type="button" class="primary" id="openBrowserBtn">Browse filesystem…</button>
  </div>
  <h2 style="font-size:1rem;margin:0 0 10px;color:var(--muted)">Quick open — <code>adf/</code></h2>
  {% if files %}
    {% for f in files %}
    <a class="ticket" href="/edit?path={{ (start_path + '/' + f)|urlencode }}">{{ f }}</a>
    {% endfor %}
  {% else %}
    <div class="empty">No files in default <code>adf/</code> yet. Use <strong>Browse filesystem</strong> or create one there.</div>
  {% endif %}
</main>
""" + _BROWSER_MODAL + """
<script>
""" + _BROWSER_JS + """
const browser = installFileBrowser({ startPath: {{ start_path|tojson }} });
document.getElementById("openBrowserBtn").onclick = () => browser.openBrowser();
// Open browser by default so filesystem is front-and-center
browser.openBrowser({{ start_path|tojson }});
</script>
</body>
</html>
"""

EDIT_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Edit {{ filename }}</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/codemirror.min.css">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/theme/idea.min.css">
<style>
  :root {
    --bg:#eef1f4; --card:#fff; --ink:#1a2332; --muted:#5a6a7a; --accent:#1f6feb;
    --line:#d0d7de; --ok:#1a7f37; --warn:#9a6700; --err:#cf222e; --panel:#f6f8fa;
    --raw-bg:#fafbfc; --hi: rgba(31,111,235,.18);
  }
  * { box-sizing: border-box; }
  html, body { height: 100%; }
  body { margin:0; display:flex; flex-direction:column; font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
    background: var(--bg); color: var(--ink); }
  .topbar { flex:0 0 auto; z-index:20; display:flex; flex-wrap:wrap; gap:10px; align-items:center;
    padding:10px 14px; background: rgba(255,255,255,.96); border-bottom:1px solid var(--line); }
  .topbar h1 { font-size:1rem; margin:0; font-weight:700; }
  .file-path { font-family: ui-monospace, monospace; font-size:12px; color:var(--muted); max-width:min(42vw,420px);
    overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
  .actions { margin-left:auto; display:flex; flex-wrap:wrap; gap:8px; align-items:center; }
  .status { font-size:12px; font-weight:700; padding:4px 8px; border-radius:4px; background:#ddf4ff; color:#0969da; }
  .status.warn { background:#fff8c5; color:var(--warn); }
  .status.ok { background:#dafbe1; color:var(--ok); }
  .status.err { background:#ffebe9; color:var(--err); }
  button, .btn { border:1px solid var(--line); background:#fff; color:var(--ink); padding:6px 10px; cursor:pointer; font: inherit; font-size:13px; }
  button:hover, .btn:hover { border-color: var(--accent); }
  button.primary { background: var(--accent); color:#fff; border-color: var(--accent); }
  button:disabled { opacity:.5; cursor:not-allowed; }
  .toolbar { flex:0 0 auto; z-index:15; display:flex; flex-wrap:wrap; gap:6px; padding:8px 14px;
    background: var(--panel); border-bottom:1px solid var(--line); }
  .toolbar .sep { width:1px; background:var(--line); margin:0 4px; align-self: stretch; }
  .toolbar select { padding:4px 6px; border:1px solid var(--line); }
  .toolbar .scenario-btn { background:#1f6feb; color:#fff; border-color:#1f6feb; font-weight:700; }
  .split { flex:1 1 auto; min-height:0; display:flex; flex-direction:row; }
  .pane { min-width: 180px; min-height:0; display:flex; flex-direction:column; background: var(--card); }
  .pane-wysiwyg { flex: 1 1 55%; }
  .pane-raw { flex: 1 1 45%; background: var(--raw-bg); }
  .pane-header { flex:0 0 auto; display:flex; align-items:center; gap:8px; padding:8px 12px;
    font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:.04em; color:var(--muted);
    border-bottom:1px solid var(--line); background: #fff; }
  .pane-header .spacer { flex:1; }
  .pane-body { flex:1 1 auto; min-height:0; overflow:auto; }
  #editor { outline:none; padding:18px 20px 48px; min-height:100%; line-height:1.55; font-size:15px; }
  #editor:focus { box-shadow: inset 0 0 0 2px rgba(31,111,235,.12); }
  #editor .adf-flash { outline: 2px solid var(--accent); background: var(--hi); }
  #editor h1,#editor h2,#editor h3 { margin: 1.1em 0 .4em; line-height:1.25; }
  #editor p { margin: 0 0 .75em; }
  #editor pre.code-block { background:#0d1117; color:#e6edf3; padding:12px 14px; overflow:auto; font-size:13px; }
  #editor blockquote { border-left:3px solid var(--line); margin:0 0 12px; padding-left:12px; color:var(--muted); }
  #editor table.adf-table { border-collapse:collapse; width:100%; margin:0 0 14px; }
  #editor table.adf-table th, #editor table.adf-table td { border:1px solid var(--line); padding:6px 8px; vertical-align:top; }
  #editor figure.media-single img { max-width:100%; height:auto; border:1px solid var(--line); }
  .panel { border-radius:4px; padding:10px 14px; margin:0 0 12px; }
  .panel-info { background:#ddf4ff; border-left:4px solid #0969da; }
  .panel-warning,.panel-note { background:#fff8c5; border-left:4px solid #9a6700; }
  .panel-success { background:#dafbe1; border-left:4px solid #1a7f37; }
  .panel-error { background:#ffebe9; border-left:4px solid #cf222e; }
  .gwt-block { margin:0 0 14px; display:flex; flex-direction:column; gap:10px; }
  .gwt-scenario { position:relative; border:1px solid var(--line); background:#f6f8fa; padding:10px 12px; padding-top:28px;
    margin:0; border-radius:2px; transition: box-shadow .15s, opacity .15s; }
  .gwt-scenario::before { content:"Scenario"; display:inline-block; background:var(--accent); color:#fff; font-size:10px;
    font-weight:700; letter-spacing:.5px; text-transform:uppercase; padding:2px 7px; margin-bottom:6px; border-radius:3px; }
  .gwt-scenario.gwt-dragging { opacity:.45; box-shadow:0 0 0 2px var(--accent); }
  .gwt-scenario.gwt-drag-over { box-shadow: inset 0 3px 0 0 var(--accent); }
  .gwt-chrome { position:absolute; top:6px; right:6px; display:flex; gap:4px; align-items:center;
    z-index:2; user-select:none; }
  .gwt-handle, .gwt-delete { border:1px solid var(--line); background:#fff; color:var(--ink); padding:2px 7px;
    font-size:12px; line-height:1.2; cursor:pointer; border-radius:3px; }
  .gwt-handle { cursor: grab; color:var(--muted); letter-spacing:-1px; }
  .gwt-handle:active { cursor: grabbing; }
  .gwt-delete { color:var(--err); font-weight:700; }
  .gwt-delete:hover { background:#ffebe9; border-color:var(--err); }
  .gwt-line { margin:2px 0; padding-left:8px; border-left:2px solid #d0d7de; line-height:1.6; }
  .gwt-line strong { font-weight:700; }
  .divider { flex:0 0 5px; cursor:col-resize; background:var(--line); }
  .CodeMirror { height: 100%; font-size: 13px; font-family: "IBM Plex Mono", ui-monospace, monospace; }
  .cm-adf-active-line { background: var(--hi) !important; }
  #jsonError { flex:0 0 auto; display:none; color:var(--err); font-size:13px; padding:8px 14px; background:#ffebe9; border-top:1px solid var(--err); }
  .sync-box { flex:0 0 auto; padding:12px 14px; border-top:1px solid var(--line); background:#fff; }
  .sync-box details summary { cursor:pointer; font-weight:700; }
  .sync-box label { display:block; font-size:12px; color:var(--muted); margin:8px 0 4px; }
  .sync-box input, .sync-box select { width:100%; max-width:420px; padding:6px 8px; border:1px solid var(--line); }
  .sync-box .row { display:flex; flex-wrap:wrap; gap:10px; align-items:end; margin-top:10px; }
  .sync-out { margin-top:10px; padding:10px; background:var(--panel); border:1px solid var(--line); font-family: ui-monospace, monospace; font-size:12px; white-space:pre-wrap; }
  @media (max-width:800px) {
    .split { flex-direction: column; }
    .divider { cursor:row-resize; }
    .file-path { max-width:100%; }
  }
""" + _BROWSER_CSS + """
</style>
</head>
<body>
<div class="topbar">
  <h1><a href="/" style="color:inherit;text-decoration:none">ADF Viewer</a></h1>
  <button type="button" id="openBrowserBtn">Open…</button>
  <span class="file-path" title="{{ filename }}">{{ filename }}</span>
  <div class="actions">
    <span id="statusBadge" class="status ok">Loaded</span>
    <button type="button" id="undoBtn">Undo</button>
    <button type="button" id="redoBtn">Redo</button>
    <button type="button" id="saveBtn" class="primary">Save</button>
    <button type="button" id="copyAdf">Copy ADF</button>
  </div>
</div>

<div class="toolbar" role="toolbar" aria-label="Formatting">
  <button type="button" data-cmd="formatBlock" data-val="h1">H1</button>
  <button type="button" data-cmd="formatBlock" data-val="h2">H2</button>
  <button type="button" data-cmd="formatBlock" data-val="h3">H3</button>
  <button type="button" data-cmd="formatBlock" data-val="p">P</button>
  <span class="sep"></span>
  <button type="button" data-cmd="bold"><b>B</b></button>
  <button type="button" data-cmd="italic"><i>I</i></button>
  <button type="button" data-cmd="strikeThrough"><s>S</s></button>
  <button type="button" data-cmd="underline"><u>U</u></button>
  <button type="button" id="btnInlineCode">&lt;/&gt;</button>
  <button type="button" id="btnLink">Link</button>
  <span class="sep"></span>
  <button type="button" data-cmd="insertUnorderedList">• List</button>
  <button type="button" data-cmd="insertOrderedList">1. List</button>
  <span class="sep"></span>
  <button type="button" class="scenario-btn" id="btnScenario" title="Add Given/When/Then scenario (Jira Acceptance Criteria list item)">+ Scenario</button>
  <button type="button" id="btnAcSection" title="Insert Acceptance Criteria heading + empty scenario list">AC section</button>
  <button type="button" id="btnPanel">Panel</button>
  <select id="codeLang" aria-label="Code language">
    <option value="">code-block</option>
    <option value="bash">bash</option>
    <option value="python">python</option>
    <option value="json">json</option>
    <option value="yaml">yaml</option>
  </select>
  <button type="button" id="btnCodeBlock">Insert code</button>
  <button type="button" id="btnTable">Table</button>
  <button type="button" id="btnImage">Image URL</button>
  <button type="button" data-cmd="insertHorizontalRule">Rule</button>
  <button type="button" id="btnQuote">Quote</button>
  <button type="button" id="btnRemoveFormat">Clear fmt</button>
</div>

<div class="split" id="split">
  <div class="pane pane-wysiwyg" id="wysiwygPane">
    <div class="pane-header">WYSIWYG <span class="spacer"></span><span>click a block to jump in raw</span></div>
    <div class="pane-body" id="wysiwygScroll">
      <div id="editor" contenteditable="true" spellcheck="true">{{ preview_html | safe }}</div>
    </div>
  </div>
  <div class="divider" id="divider" title="Drag to resize"></div>
  <div class="pane pane-raw" id="rawPane">
    <div class="pane-header">Raw ADF <span class="spacer"></span><span>edit JSON — cursor jumps in WYSIWYG</span></div>
    <div class="pane-body" id="rawScroll">
      <textarea id="rawEditor">{{ adf_json }}</textarea>
    </div>
  </div>
</div>
<div id="jsonError"></div>

<section class="sync-box">
  <details>
    <summary>Jira sync (explicit apply)</summary>
    <p style="margin:6px 0 0;color:var(--muted);font-size:13px">
      Prepare is dry-run. Apply uses <code>JIRA_*</code> env. Never automatic.
    </p>
    <label for="issueKey">Issue key</label>
    <input id="issueKey" value="{{ issue_key }}" autocomplete="off">
    <label for="descFormat">Upload description format</label>
    <select id="descFormat">
      <option value="adf" selected>raw ADF</option>
      <option value="wiki">wiki shim</option>
    </select>
    <p style="margin:12px 0 4px;font-size:13px;font-weight:700">Local → Jira</p>
    <div class="row">
      <button type="button" id="prepareSync">Prepare upload</button>
      <button type="button" id="applySync">Apply upload</button>
    </div>
    <p style="margin:12px 0 4px;font-size:13px;font-weight:700">Jira → Local</p>
    <p style="margin:0 0 6px;color:var(--muted);font-size:12px">
      Pull hand-edits from Jira into this file (overwrite; git rollback).
    </p>
    <div class="row">
      <button type="button" id="prepareDownload">Prepare download</button>
      <button type="button" id="applyDownload">Apply download</button>
    </div>
    <div class="sync-out" id="syncOut" hidden></div>
  </details>
  <details>
    <summary>GitHub Issue sync (explicit apply)</summary>
    <p style="margin:6px 0 0;color:var(--muted);font-size:13px">
      Prepare is dry-run. Apply uses the <code>gh</code> CLI (<code>gh auth login</code>). Never automatic.
    </p>
    <p style="margin:6px 0 0;color:var(--muted);font-size:12px">
      GitHub stores markdown; complex ADF formatting may flatten.
    </p>
    <label for="ghIssue">GitHub Issue #</label>
    <input id="ghIssue" placeholder="123 or owner/repo#123" autocomplete="off">
    <label for="ghRepo">Repository (optional — defaults to git remote origin)</label>
    <input id="ghRepo" placeholder="owner/repo" autocomplete="off">
    <p style="margin:12px 0 4px;font-size:13px;font-weight:700">GitHub → Local</p>
    <p style="margin:0 0 6px;color:var(--muted);font-size:12px">
      Pull the issue body (markdown → ADF) into this file (overwrite; git rollback).
    </p>
    <div class="row">
      <button type="button" id="ghPullPrepare">Prepare pull</button>
      <button type="button" id="ghPullApply">Apply pull</button>
    </div>
    <p style="margin:12px 0 4px;font-size:13px;font-weight:700">Local → GitHub</p>
    <p style="margin:0 0 6px;color:var(--muted);font-size:12px">
      Push this document (ADF → markdown) as the issue body.
    </p>
    <div class="row">
      <button type="button" id="ghPushPrepare">Prepare push</button>
      <button type="button" id="ghPushApply">Apply push</button>
    </div>
    <div class="sync-out" id="ghSyncOut" hidden></div>
  </details>
</section>
""" + _BROWSER_MODAL + """
<script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/codemirror.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/mode/javascript/javascript.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/addon/edit/matchbrackets.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/addon/edit/closebrackets.min.js"></script>
<script>
""" + _BROWSER_JS + """
(function () {
  const filename = {{ filename|tojson }};
  const editor = document.getElementById("editor");
  const statusBadge = document.getElementById("statusBadge");
  const syncOut = document.getElementById("syncOut");
  const jsonError = document.getElementById("jsonError");
  const wysiwygScroll = document.getElementById("wysiwygScroll");
  const browser = installFileBrowser({ startPath: {{ start_path|tojson }} });
  document.getElementById("openBrowserBtn").onclick = () => browser.openBrowser();

  let dirty = false;
  let saveTimer = null;
  let wysiwygToRawTimer = null;
  let rawToWysiwygTimer = null;
  let applyingHistory = false;
  let syncLock = false;
  let syncSource = null;
  const undoStack = [];
  const redoStack = [];
  const MAX_HIST = 80;

  const cm = CodeMirror.fromTextArea(document.getElementById("rawEditor"), {
    mode: { name: "javascript", json: true },
    theme: "idea",
    lineNumbers: true,
    matchBrackets: true,
    autoCloseBrackets: true,
    lineWrapping: true,
    tabSize: 2,
  });
  cm.setSize("100%", "100%");

  function setStatus(msg, kind) {
    statusBadge.textContent = msg;
    statusBadge.className = "status " + (kind || "ok");
  }
  function markDirty() {
    dirty = true;
    setStatus("Unsaved", "warn");
    scheduleSave();
  }
  function showJsonError(msg) {
    if (!msg) { jsonError.style.display = "none"; jsonError.textContent = ""; return; }
    jsonError.style.display = "block";
    jsonError.textContent = msg;
  }
  function tagBlocks() {
    Array.from(editor.children).forEach((el, i) => el.setAttribute("data-block-index", String(i)));
    enhanceScenarios();
  }

  let dragScenario = null;

  function enhanceScenarios() {
    editor.querySelectorAll(".gwt-scenario").forEach((scenario) => {
      if (scenario.querySelector(":scope > .gwt-chrome")) return;
      scenario.removeAttribute("draggable");
      const chrome = document.createElement("div");
      chrome.className = "gwt-chrome";
      chrome.contentEditable = "false";
      chrome.setAttribute("contenteditable", "false");

      const handle = document.createElement("button");
      handle.type = "button";
      handle.className = "gwt-handle";
      handle.title = "Drag to reorder";
      handle.textContent = "⋮⋮";
      handle.draggable = true;
      handle.setAttribute("contenteditable", "false");

      const del = document.createElement("button");
      del.type = "button";
      del.className = "gwt-delete";
      del.title = "Delete scenario";
      del.textContent = "×";
      del.setAttribute("contenteditable", "false");

      handle.addEventListener("dragstart", (e) => {
        dragScenario = scenario;
        scenario.classList.add("gwt-dragging");
        e.dataTransfer.effectAllowed = "move";
        e.dataTransfer.setData("text/gwt-scenario", "1");
        try {
          e.dataTransfer.setDragImage(scenario, 16, 16);
        } catch (_) { /* some browsers */ }
      });
      handle.addEventListener("dragend", () => {
        if (dragScenario) dragScenario.classList.remove("gwt-dragging");
        editor.querySelectorAll(".gwt-drag-over").forEach((el) => el.classList.remove("gwt-drag-over"));
        dragScenario = null;
        pushHistory();
        markDirty();
        scheduleWysiwygToRaw();
      });

      del.addEventListener("mousedown", (e) => { e.preventDefault(); e.stopPropagation(); });
      del.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (!confirm("Delete this scenario?")) return;
        pushHistory();
        const block = scenario.parentElement;
        scenario.remove();
        if (block && block.classList.contains("gwt-block") && !block.querySelector(".gwt-scenario")) {
          // keep empty list container so + Scenario can refill; optional cleanup:
          // block.remove();
        }
        afterFormat();
      });

      chrome.appendChild(handle);
      chrome.appendChild(del);
      scenario.insertBefore(chrome, scenario.firstChild);

      scenario.addEventListener("dragover", (e) => {
        if (!dragScenario || dragScenario === scenario) return;
        if (dragScenario.parentElement !== scenario.parentElement) return;
        e.preventDefault();
        e.dataTransfer.dropEffect = "move";
        const rect = scenario.getBoundingClientRect();
        const before = e.clientY < rect.top + rect.height / 2;
        scenario.classList.add("gwt-drag-over");
        const block = scenario.parentElement;
        if (before) {
          if (scenario.previousElementSibling !== dragScenario) block.insertBefore(dragScenario, scenario);
        } else if (scenario.nextElementSibling !== dragScenario) {
          block.insertBefore(dragScenario, scenario.nextElementSibling);
        }
      });
      scenario.addEventListener("dragleave", () => scenario.classList.remove("gwt-drag-over"));
      scenario.addEventListener("drop", (e) => {
        e.preventDefault();
        scenario.classList.remove("gwt-drag-over");
      });
    });
  }
  function pushHistory() {
    if (applyingHistory) return;
    const html = editor.innerHTML;
    if (undoStack.length && undoStack[undoStack.length - 1] === html) return;
    undoStack.push(html);
    if (undoStack.length > MAX_HIST) undoStack.shift();
    redoStack.length = 0;
  }
  function flashEl(el) {
    if (!el) return;
    el.classList.add("adf-flash");
    el.scrollIntoView({ block: "center", behavior: "smooth" });
    setTimeout(() => el.classList.remove("adf-flash"), 900);
  }
  function firstTextFromNode(node) {
    if (!node) return "";
    const walk = document.createTreeWalker(node, NodeFilter.SHOW_TEXT);
    let n;
    while ((n = walk.nextNode())) {
      const t = (n.textContent || "").trim();
      if (t) return t.slice(0, 80);
    }
    return "";
  }
  function blockFromEventTarget(target) {
    let el = target;
    while (el && el !== editor) {
      if (el.getAttribute && el.hasAttribute("data-block-index")) return el;
      el = el.parentElement;
    }
    el = target;
    while (el && el.parentElement !== editor) el = el.parentElement;
    return el && el.parentElement === editor ? el : null;
  }
  function scrollRawToText(needle) {
    if (!needle) return;
    const hay = cm.getValue();
    const escaped = JSON.stringify(needle).slice(1, -1);
    let idx = hay.indexOf(escaped);
    if (idx < 0) idx = hay.indexOf(needle);
    if (idx < 0) return;
    const pos = cm.posFromIndex(idx);
    cm.setCursor(pos);
    cm.scrollIntoView(pos, 80);
    cm.addLineClass(pos.line, "background", "cm-adf-active-line");
    setTimeout(() => cm.removeLineClass(pos.line, "background", "cm-adf-active-line"), 1200);
  }
  function scrollWysiwygToText(needle) {
    if (!needle) return;
    for (const el of editor.querySelectorAll("[data-block-index],h1,h2,h3,p,li,pre,.gwt-scenario,.panel")) {
      if ((el.textContent || "").includes(needle)) { flashEl(el); return; }
    }
  }
  function textNearRawCursor() {
    const cur = cm.getCursor();
    for (let d = 0; d <= 8; d++) {
      for (const ln of [cur.line - d, cur.line + d]) {
        if (ln < 0 || ln >= cm.lineCount()) continue;
        const L = cm.getLine(ln) || "";
        const m = L.match(/"text"\\s*:\\s*"((?:\\\\.|[^"\\\\])*)"/);
        if (m) {
          try { return JSON.parse('"' + m[1] + '"'); } catch (e) { return m[1]; }
        }
      }
    }
    return "";
  }

  async function htmlToAdf() {
    const resp = await fetch("/api/html-to-adf", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ html: editor.innerHTML }),
    });
    const data = await resp.json();
    if (!data.ok) throw new Error(data.error || "html-to-adf failed");
    return data.adf;
  }
  async function refreshRawFromWysiwyg() {
    if (syncSource === "raw") return;
    try {
      const adf = await htmlToAdf();
      const text = JSON.stringify(adf, null, 2);
      syncSource = "wysiwyg";
      const cursor = cm.getCursor();
      const scroll = cm.getScrollInfo();
      if (cm.getValue() !== text) {
        cm.setValue(text);
        cm.setCursor(cursor);
        cm.scrollTo(scroll.left, scroll.top);
      }
      showJsonError("");
      tagBlocks();
    } catch (e) {
      showJsonError("WYSIWYG→ADF: " + e.message);
    } finally {
      setTimeout(() => { if (syncSource === "wysiwyg") syncSource = null; }, 50);
    }
  }
  async function refreshWysiwygFromRaw() {
    if (syncSource === "wysiwyg") return;
    let parsed;
    try {
      parsed = JSON.parse(cm.getValue());
      showJsonError("");
    } catch (e) {
      showJsonError("JSON parse error: " + e.message);
      setStatus("JSON error", "err");
      return;
    }
    try {
      const resp = await fetch("/api/render", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(parsed),
      });
      const data = await resp.json();
      if (!data.ok && data.error) throw new Error(data.error);
      syncSource = "raw";
      applyingHistory = true;
      editor.innerHTML = data.html || "<p><br></p>";
      tagBlocks();
      applyingHistory = false;
      setStatus(dirty ? "Unsaved" : "Preview synced", dirty ? "warn" : "ok");
    } catch (e) {
      showJsonError("ADF→HTML: " + e.message);
    } finally {
      setTimeout(() => { if (syncSource === "raw") syncSource = null; }, 50);
    }
  }
  function scheduleWysiwygToRaw() {
    clearTimeout(wysiwygToRawTimer);
    wysiwygToRawTimer = setTimeout(refreshRawFromWysiwyg, 350);
  }
  function scheduleRawToWysiwyg() {
    clearTimeout(rawToWysiwygTimer);
    rawToWysiwygTimer = setTimeout(refreshWysiwygFromRaw, 400);
  }

  async function saveNow() {
    setStatus("Saving…", "warn");
    try {
      let body = { path: filename };
      try {
        Object.assign(body, JSON.parse(cm.getValue()));
      } catch (e) {
        body = { path: filename, html: editor.innerHTML };
      }
      const resp = await fetch("/api/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await resp.json();
      if (!data.ok) throw new Error(data.error || "save failed");
      dirty = false;
      syncSource = "wysiwyg";
      cm.setValue(JSON.stringify(data.adf, null, 2));
      const ren = await fetch("/api/render", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data.adf),
      });
      const rh = await ren.json();
      applyingHistory = true;
      editor.innerHTML = rh.html || "";
      tagBlocks();
      applyingHistory = false;
      syncSource = null;
      showJsonError("");
      setStatus("Saved", "ok");
    } catch (e) {
      setStatus("Save failed: " + e.message, "err");
    }
  }
  function scheduleSave() {
    clearTimeout(saveTimer);
    saveTimer = setTimeout(saveNow, 1500);
  }
  function undo() {
    if (undoStack.length < 2) return;
    applyingHistory = true;
    redoStack.push(undoStack.pop());
    editor.innerHTML = undoStack[undoStack.length - 1];
    tagBlocks();
    applyingHistory = false;
    markDirty();
    scheduleWysiwygToRaw();
  }
  function redo() {
    if (!redoStack.length) return;
    applyingHistory = true;
    const html = redoStack.pop();
    undoStack.push(html);
    editor.innerHTML = html;
    tagBlocks();
    applyingHistory = false;
    markDirty();
    scheduleWysiwygToRaw();
  }

  editor.addEventListener("input", () => {
    if (applyingHistory || syncSource === "raw") return;
    pushHistory();
    markDirty();
    scheduleWysiwygToRaw();
  });
  editor.addEventListener("click", (e) => {
    const block = blockFromEventTarget(e.target);
    tagBlocks();
    const needle = firstTextFromNode(block) || firstTextFromNode(e.target);
    if (needle) scrollRawToText(needle);
  });
  editor.addEventListener("keydown", (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "s") {
      e.preventDefault(); clearTimeout(saveTimer); saveNow();
    }
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "z" && !e.shiftKey) {
      e.preventDefault(); undo();
    }
    if ((e.metaKey || e.ctrlKey) && (e.key.toLowerCase() === "y" || (e.key.toLowerCase() === "z" && e.shiftKey))) {
      e.preventDefault(); redo();
    }
  });
  cm.on("change", (_i, change) => {
    if (syncSource === "wysiwyg" || change.origin === "setValue") return;
    markDirty();
    scheduleRawToWysiwyg();
  });
  cm.on("cursorActivity", () => {
    if (syncSource === "wysiwyg") return;
    const needle = textNearRawCursor();
    if (needle) scrollWysiwygToText(needle);
  });
  wysiwygScroll.addEventListener("scroll", () => {
    if (syncLock) return;
    syncLock = true;
    const pct = wysiwygScroll.scrollTop / Math.max(1, wysiwygScroll.scrollHeight - wysiwygScroll.clientHeight);
    const info = cm.getScrollInfo();
    cm.scrollTo(0, pct * Math.max(0, info.height - info.clientHeight));
    requestAnimationFrame(() => { syncLock = false; });
  });
  cm.on("scroll", () => {
    if (syncLock) return;
    syncLock = true;
    const info = cm.getScrollInfo();
    const pct = info.top / Math.max(1, info.height - info.clientHeight);
    wysiwygScroll.scrollTop = pct * Math.max(0, wysiwygScroll.scrollHeight - wysiwygScroll.clientHeight);
    requestAnimationFrame(() => { syncLock = false; });
  });

  const divider = document.getElementById("divider");
  const wysiwygPane = document.getElementById("wysiwygPane");
  const rawPane = document.getElementById("rawPane");
  let dragging = false;
  divider.addEventListener("mousedown", (e) => { dragging = true; e.preventDefault(); });
  window.addEventListener("mousemove", (e) => {
    if (!dragging) return;
    const split = document.getElementById("split");
    const rect = split.getBoundingClientRect();
    const vertical = window.matchMedia("(max-width:800px)").matches;
    if (vertical) {
      const pct = ((e.clientY - rect.top) / rect.height) * 100;
      wysiwygPane.style.flex = "none";
      wysiwygPane.style.height = Math.min(85, Math.max(15, pct)) + "%";
      rawPane.style.flex = "1";
    } else {
      const pct = ((e.clientX - rect.left) / rect.width) * 100;
      wysiwygPane.style.flex = "none";
      wysiwygPane.style.width = Math.min(85, Math.max(15, pct)) + "%";
      rawPane.style.flex = "1";
    }
    cm.refresh();
  });
  window.addEventListener("mouseup", () => { dragging = false; });

  document.getElementById("saveBtn").onclick = () => { clearTimeout(saveTimer); saveNow(); };
  document.getElementById("undoBtn").onclick = undo;
  document.getElementById("redoBtn").onclick = redo;
  document.getElementById("copyAdf").onclick = async () => {
    await navigator.clipboard.writeText(cm.getValue());
    setStatus("ADF copied", "ok");
  };

  function afterFormat() {
    tagBlocks();
    markDirty();
    scheduleWysiwygToRaw();
  }
  document.querySelector(".toolbar").addEventListener("click", (e) => {
    const btn = e.target.closest("button[data-cmd]");
    if (!btn) return;
    e.preventDefault();
    editor.focus();
    pushHistory();
    const cmd = btn.getAttribute("data-cmd");
    if (cmd === "formatBlock") document.execCommand("formatBlock", false, btn.getAttribute("data-val"));
    else document.execCommand(cmd, false, null);
    afterFormat();
  });
  document.getElementById("btnInlineCode").onclick = () => {
    editor.focus(); pushHistory();
    const sel = window.getSelection();
    const t = sel && !sel.isCollapsed ? sel.toString() : "code";
    document.execCommand("insertHTML", false, "<code>" + t.replace(/</g, "&lt;") + "</code>");
    afterFormat();
  };
  document.getElementById("btnLink").onclick = () => {
    const href = prompt("Link URL:", "https://");
    if (!href) return;
    editor.focus(); pushHistory();
    document.execCommand("createLink", false, href);
    afterFormat();
  };
  document.getElementById("btnRemoveFormat").onclick = () => {
    editor.focus(); pushHistory();
    document.execCommand("removeFormat", false, null);
    afterFormat();
  };
  document.getElementById("btnQuote").onclick = () => {
    editor.focus(); pushHistory();
    document.execCommand("formatBlock", false, "blockquote");
    afterFormat();
  };
  /** One scenario = one ADF bulletList listItem (Given/When/Then + hardBreaks). */
  function makeScenarioEl(given, when, then) {
    const wrap = document.createElement("div");
    wrap.className = "gwt-scenario";
    wrap.setAttribute("contenteditable", "true");
    [["Given ", given || "precondition"], ["When ", when || "action"], ["Then ", then || "outcome"]].forEach(([kw, rest]) => {
      const line = document.createElement("div");
      line.className = "gwt-line";
      const strong = document.createElement("strong");
      strong.textContent = kw;
      line.appendChild(strong);
      line.appendChild(document.createTextNode(rest));
      wrap.appendChild(line);
    });
    return wrap;
  }
  function findGwtBlockNearSelection() {
    const sel = window.getSelection();
    let node = sel && sel.anchorNode;
    if (node && node.nodeType === 3) node = node.parentElement;
    while (node && node !== editor) {
      if (node.classList && node.classList.contains("gwt-block")) return node;
      node = node.parentElement;
    }
    const blocks = editor.querySelectorAll(".gwt-block");
    return blocks.length ? blocks[blocks.length - 1] : null;
  }
  function placeCaretInScenario(scenarioEl) {
    const line = scenarioEl.querySelector(".gwt-line");
    if (!line) return;
    const range = document.createRange();
    const sel = window.getSelection();
    // caret after "Given "
    const strong = line.querySelector("strong");
    if (strong && strong.nextSibling) {
      range.setStart(strong.nextSibling, 0);
    } else {
      range.selectNodeContents(line);
      range.collapse(true);
    }
    range.collapse(true);
    sel.removeAllRanges();
    sel.addRange(range);
  }
  document.getElementById("btnScenario").onclick = () => {
    editor.focus();
    pushHistory();
    const scenario = makeScenarioEl("precondition", "action", "expected result");
    let block = findGwtBlockNearSelection();
    if (!block) {
      block = document.createElement("div");
      block.className = "gwt-block";
      // Prefer insert after Acceptance Criteria heading when present
      const headings = Array.from(editor.querySelectorAll("h2"));
      const ac = headings.find((h) => /acceptance criteria/i.test(h.textContent || ""));
      if (ac && ac.parentElement === editor) {
        if (ac.nextSibling) editor.insertBefore(block, ac.nextSibling);
        else editor.appendChild(block);
      } else {
        document.execCommand("insertHTML", false, '<div class="gwt-block"></div><p><br></p>');
        block = findGwtBlockNearSelection() || editor.querySelector(".gwt-block:last-of-type");
        if (!block) {
          block = document.createElement("div");
          block.className = "gwt-block";
          editor.appendChild(block);
        }
      }
    }
    block.appendChild(scenario);
    placeCaretInScenario(scenario);
    afterFormat();
  };
  document.getElementById("btnAcSection").onclick = () => {
    editor.focus();
    pushHistory();
    const hasAc = Array.from(editor.querySelectorAll("h2")).some((h) =>
      /acceptance criteria/i.test(h.textContent || "")
    );
    const block = document.createElement("div");
    block.className = "gwt-block";
    block.appendChild(makeScenarioEl("precondition", "action", "expected result"));
    if (!hasAc) {
      const h = document.createElement("h2");
      h.textContent = "Acceptance Criteria";
      const sel = window.getSelection();
      let inserted = false;
      if (sel && sel.rangeCount) {
        const range = sel.getRangeAt(0);
        range.deleteContents();
        range.insertNode(block);
        range.insertNode(h);
        inserted = true;
      }
      if (!inserted) {
        editor.appendChild(h);
        editor.appendChild(block);
      }
      const br = document.createElement("p");
      br.innerHTML = "<br>";
      block.after(br);
    } else {
      const headings = Array.from(editor.querySelectorAll("h2"));
      const ac = headings.find((h) => /acceptance criteria/i.test(h.textContent || ""));
      let existing = ac && ac.nextElementSibling;
      while (existing && existing.tagName === "P" && !(existing.textContent || "").trim()) {
        existing = existing.nextElementSibling;
      }
      if (existing && existing.classList && existing.classList.contains("gwt-block")) {
        existing.appendChild(makeScenarioEl("precondition", "action", "expected result"));
        placeCaretInScenario(existing.querySelector(".gwt-scenario:last-child"));
      } else if (ac) {
        ac.after(block);
      } else {
        editor.appendChild(block);
      }
    }
    const last = editor.querySelector(".gwt-scenario:last-of-type");
    if (last) placeCaretInScenario(last);
    afterFormat();
  };
  document.getElementById("btnPanel").onclick = () => {
    editor.focus(); pushHistory();
    const type = prompt("Panel type (info|warning|note|success|error):", "info") || "info";
    document.execCommand(
      "insertHTML", false,
      '<div class="panel panel-' + type + '" data-panel-type="' + type + '"><p>Panel text</p></div><p><br></p>'
    );
    afterFormat();
  };
  document.getElementById("btnCodeBlock").onclick = () => {
    editor.focus(); pushHistory();
    const lang = document.getElementById("codeLang").value || "";
    document.execCommand(
      "insertHTML", false,
      '<pre class="code-block" data-language="' + lang + '"><code>// code</code></pre><p><br></p>'
    );
    afterFormat();
  };
  document.getElementById("btnTable").onclick = () => {
    editor.focus(); pushHistory();
    document.execCommand(
      "insertHTML", false,
      '<table class="adf-table"><tbody>' +
        '<tr><th><p>Column A</p></th><th><p>Column B</p></th></tr>' +
        '<tr><td><p>1</p></td><td><p>2</p></td></tr>' +
      '</tbody></table><p><br></p>'
    );
    afterFormat();
  };
  document.getElementById("btnImage").onclick = () => {
    const url = prompt("Image URL:");
    if (!url) return;
    editor.focus(); pushHistory();
    const alt = prompt("Alt text:", "") || "";
    document.execCommand(
      "insertHTML", false,
      '<figure class="media-single" data-layout="center"><img src="' +
        url.replace(/"/g, "&quot;") + '" alt="' + alt.replace(/"/g, "&quot;") +
        '"></figure><p><br></p>'
    );
    afterFormat();
  };

  async function sync(apply) {
    const issueKey = document.getElementById("issueKey").value.trim();
    const fmt = document.getElementById("descFormat").value;
    if (apply && !confirm("Apply upload to Jira issue " + issueKey + " as " + fmt + "?")) return;
    if (dirty) await saveNow();
    syncOut.hidden = false;
    syncOut.textContent = apply ? "Applying upload…" : "Preparing upload dry-run…";
    const resp = await fetch("/api/sync", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: filename, apply: !!apply, issue_key: issueKey, description_format: fmt }),
    });
    const data = await resp.json();
    const lines = [];
    if (data.cli) lines.push("CLI: " + data.cli);
    if (data.message) lines.push(data.message);
    if (data.error) lines.push("Error: " + data.error);
    syncOut.textContent = lines.join("\\n\\n");
    setStatus(data.ok ? (apply ? "Uploaded" : "Upload prepared") : "Sync error", data.ok ? "ok" : "err");
  }
  async function downloadFromJira(apply) {
    const issueKey = document.getElementById("issueKey").value.trim();
    if (apply && !confirm("Overwrite local file with Jira description for " + issueKey + "?")) return;
    syncOut.hidden = false;
    syncOut.textContent = apply ? "Applying download…" : "Preparing download dry-run…";
    const resp = await fetch("/api/download", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: filename, apply: !!apply, issue_key: issueKey }),
    });
    const data = await resp.json();
    const lines = [];
    if (data.cli) lines.push("CLI: " + data.cli);
    if (data.message) lines.push(data.message);
    if (data.error) lines.push("Error: " + data.error);
    syncOut.textContent = lines.join("\\n\\n");
    if (data.ok && apply && data.adf) {
      applyingHistory = true;
      cm.setValue(JSON.stringify(data.adf, null, 2));
      if (data.html) editor.innerHTML = data.html;
      else await refreshWysiwygFromRaw();
      tagBlocks();
      dirty = false;
      undoStack.length = 0;
      redoStack.length = 0;
      pushHistory();
      applyingHistory = false;
      setStatus("Downloaded", "ok");
    } else {
      setStatus(data.ok ? (apply ? "Downloaded" : "Download prepared") : "Download error", data.ok ? "ok" : "err");
    }
  }
  document.getElementById("prepareSync").onclick = () => sync(false);
  document.getElementById("applySync").onclick = () => sync(true);
  document.getElementById("prepareDownload").onclick = () => downloadFromJira(false);
  document.getElementById("applyDownload").onclick = () => downloadFromJira(true);

  const ghSyncOut = document.getElementById("ghSyncOut");
  function ghParams() {
    return {
      issue: document.getElementById("ghIssue").value.trim(),
      repo: document.getElementById("ghRepo").value.trim(),
    };
  }
  function ghReport(data) {
    const lines = [];
    if (data.message) lines.push(data.message);
    if (data.note) lines.push("Note: " + data.note);
    if (data.error) lines.push("Error: " + data.error);
    ghSyncOut.textContent = lines.join("\\n\\n");
  }
  async function githubPull(apply) {
    const { issue, repo } = ghParams();
    ghSyncOut.hidden = false;
    if (!issue) { ghSyncOut.textContent = "Enter a GitHub issue number (123 or owner/repo#123)."; return; }
    if (apply && !confirm("Overwrite local file with GitHub issue " + issue + " body?")) return;
    ghSyncOut.textContent = apply ? "Applying pull…" : "Preparing pull dry-run…";
    const resp = await fetch("/api/github/pull", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ issue, repo, path: filename, apply: !!apply }),
    });
    const data = await resp.json();
    ghReport(data);
    if (data.ok && apply && data.adf) {
      applyingHistory = true;
      cm.setValue(JSON.stringify(data.adf, null, 2));
      if (data.html) editor.innerHTML = data.html;
      else await refreshWysiwygFromRaw();
      tagBlocks();
      dirty = false;
      undoStack.length = 0;
      redoStack.length = 0;
      pushHistory();
      applyingHistory = false;
      setStatus("Pulled from GitHub", "ok");
    } else {
      setStatus(data.ok ? (apply ? "Pulled from GitHub" : "GitHub pull prepared") : "GitHub pull error", data.ok ? "ok" : "err");
    }
  }
  async function githubPush(apply) {
    const { issue, repo } = ghParams();
    ghSyncOut.hidden = false;
    if (!issue) { ghSyncOut.textContent = "Enter a GitHub issue number (123 or owner/repo#123)."; return; }
    if (apply && !confirm("Update GitHub issue " + issue + " body with this document (ADF → markdown)?")) return;
    if (dirty) await saveNow();
    ghSyncOut.textContent = apply ? "Applying push…" : "Preparing push dry-run…";
    const resp = await fetch("/api/github/push", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ issue, repo, path: filename, apply: !!apply }),
    });
    const data = await resp.json();
    ghReport(data);
    setStatus(data.ok ? (apply ? "Pushed to GitHub" : "GitHub push prepared") : "GitHub push error", data.ok ? "ok" : "err");
  }
  document.getElementById("ghPullPrepare").onclick = () => githubPull(false);
  document.getElementById("ghPullApply").onclick = () => githubPull(true);
  document.getElementById("ghPushPrepare").onclick = () => githubPush(false);
  document.getElementById("ghPushApply").onclick = () => githubPush(true);

  tagBlocks();
  pushHistory();
  window.addEventListener("beforeunload", (e) => {
    if (dirty) { e.preventDefault(); e.returnValue = ""; }
  });
  window.addEventListener("resize", () => cm.refresh());
})();
</script>
</body>
</html>
"""
