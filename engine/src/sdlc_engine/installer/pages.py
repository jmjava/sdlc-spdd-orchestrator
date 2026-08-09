"""HTML templates for the SDLC-SPDD ops console."""

from __future__ import annotations

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>SDLC-SPDD Ops Console</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@500;700;800&family=Source+Sans+3:wght@400;600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet" />
  <style>
    :root {
      --ink: #15231c;
      --muted: #4a5c52;
      --line: #c5d2c9;
      --panel: rgba(255,255,255,0.78);
      --accent: #0d7a5f;
      --accent-ink: #063d30;
      --warn: #9a5b00;
      --ok: #0f6b45;
      --bad: #9b1c1c;
      --bg1: #e8f0ea;
      --bg2: #f7f3e8;
      --mono: "IBM Plex Mono", ui-monospace, monospace;
      --sans: "Source Sans 3", system-ui, sans-serif;
      --display: "Outfit", "Source Sans 3", sans-serif;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      color: var(--ink);
      font-family: var(--sans);
      background:
        radial-gradient(1200px 600px at 10% -10%, #d5ebe0 0%, transparent 55%),
        radial-gradient(900px 500px at 100% 0%, #efe4c8 0%, transparent 50%),
        linear-gradient(160deg, var(--bg1), var(--bg2));
    }
    .wrap { width: min(1080px, calc(100% - 2rem)); margin: 0 auto; padding: 2.25rem 0 4rem; }
    header { margin-bottom: 1.25rem; animation: rise 0.55s ease-out both; }
    .brand {
      font-family: var(--display); font-weight: 800;
      font-size: clamp(1.7rem, 3.8vw, 2.45rem);
      letter-spacing: -0.03em; line-height: 1.05; color: var(--accent-ink);
    }
    .tagline { margin: 0.5rem 0 0; max-width: 40rem; color: var(--muted); font-size: 1.02rem; }
    .panel {
      background: var(--panel); border: 1px solid var(--line);
      backdrop-filter: blur(8px); padding: 1.15rem 1.25rem; margin-bottom: 1rem;
      animation: rise 0.65s ease-out both;
    }
    .panel h2, .panel h3 {
      margin: 0 0 0.75rem; font-family: var(--display);
      font-size: 1.02rem; font-weight: 700; letter-spacing: -0.01em;
    }
    .panel h3 { font-size: 0.95rem; margin-top: 1rem; }
    label.field { display: block; font-size: 0.85rem; font-weight: 600; color: var(--muted); margin-bottom: 0.35rem; }
    .grid-2 {
      display: grid; grid-template-columns: minmax(8rem, 11rem) 1fr;
      gap: 0.45rem 0.75rem; align-items: center; margin-bottom: 0.75rem;
    }
    .grid-2 input { flex: none; width: 100%; min-width: 0; }
    .row { display: flex; gap: 0.6rem; align-items: stretch; flex-wrap: wrap; }
    input[type="text"], input[type="number"], select, textarea {
      flex: 1 1 14rem; min-width: 10rem; border: 1px solid var(--line);
      background: #fff; color: var(--ink); font: 500 0.92rem var(--mono);
      padding: 0.6rem 0.7rem;
    }
    textarea { min-height: 4.5rem; font-family: var(--mono); font-size: 0.82rem; width: 100%; }
    input:focus, select:focus, textarea:focus {
      outline: 2px solid color-mix(in srgb, var(--accent) 45%, white); border-color: var(--accent);
    }
    .tabs { display: flex; flex-wrap: wrap; gap: 0.35rem; margin-bottom: 1rem; }
    .tab {
      font-family: var(--display); font-weight: 700; font-size: 0.88rem;
      padding: 0.5rem 0.85rem; border: 1px solid var(--line); background: #fff;
      color: var(--muted); cursor: pointer;
    }
    .tab.active { background: var(--accent); color: #f4fff9; border-color: var(--accent); }
    .tab-pane { display: none; }
    .tab-pane.active { display: block; animation: rise 0.35s ease-out both; }
    .checks {
      display: grid; grid-template-columns: repeat(auto-fit, minmax(11rem, 1fr));
      gap: 0.55rem 1rem;
    }
    .checks label { display: flex; gap: 0.45rem; align-items: center; font-size: 0.95rem; cursor: pointer; }
    .mode-pill, .stat {
      display: inline-flex; align-items: center; gap: 0.35rem;
      font-family: var(--mono); font-size: 0.75rem; font-weight: 500;
      letter-spacing: 0.02em; text-transform: uppercase;
      padding: 0.28rem 0.55rem; border: 1px solid var(--line); background: #fff; color: var(--muted);
    }
    .mode-pill.install, .stat.ok { color: var(--ok); border-color: color-mix(in srgb, var(--ok) 40%, white); }
    .mode-pill.upgrade, .stat.warn { color: var(--warn); border-color: color-mix(in srgb, var(--warn) 40%, white); }
    .mode-pill.missing, .mode-pill.error, .stat.bad { color: var(--bad); }
    .stats {
      display: grid; grid-template-columns: repeat(auto-fit, minmax(8.5rem, 1fr));
      gap: 0.55rem; margin: 0.75rem 0;
    }
    .stat-card {
      border: 1px solid var(--line); background: #fff; padding: 0.7rem 0.8rem;
    }
    .stat-card .n {
      font-family: var(--display); font-weight: 800; font-size: 1.55rem;
      letter-spacing: -0.03em; color: var(--accent-ink); line-height: 1;
    }
    .stat-card .l { margin-top: 0.25rem; font-size: 0.78rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.04em; }
    .meta { margin-top: 0.75rem; font-size: 0.9rem; color: var(--muted); }
    .meta code, code.inline {
      font-family: var(--mono); font-size: 0.8rem; background: #fff;
      border: 1px solid var(--line); padding: 0.05rem 0.3rem;
    }
    .actions { display: flex; flex-wrap: wrap; gap: 0.55rem; margin-top: 1rem; }
    button {
      appearance: none; border: 1px solid transparent;
      font-family: var(--display); font-weight: 700; font-size: 0.9rem;
      letter-spacing: -0.01em; padding: 0.58rem 0.95rem; cursor: pointer;
      transition: transform 0.12s ease, background 0.15s ease;
    }
    button:hover:not(:disabled) { transform: translateY(-1px); }
    button:disabled { opacity: 0.55; cursor: not-allowed; }
    .btn-primary { background: var(--accent); color: #f4fff9; }
    .btn-primary:hover:not(:disabled) { background: #0a6550; }
    .btn-secondary { background: #fff; color: var(--accent-ink); border-color: var(--line); }
    .btn-ghost { background: transparent; color: var(--muted); border-color: var(--line); }
    .btn-warn { background: #fff8e8; color: var(--warn); border-color: color-mix(in srgb, var(--warn) 35%, white); }
    pre.log, pre.cmd {
      margin: 0; min-height: 8rem; max-height: 22rem; overflow: auto;
      background: #122019; color: #d7ebe0; font: 400 0.78rem/1.45 var(--mono);
      padding: 0.85rem 0.95rem; white-space: pre-wrap; word-break: break-word;
    }
    pre.cmd { min-height: 4rem; max-height: 10rem; }
    table { width: 100%; border-collapse: collapse; font-size: 0.88rem; }
    th, td { text-align: left; padding: 0.4rem 0.45rem; border-bottom: 1px solid var(--line); vertical-align: top; }
    th { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.04em; color: var(--muted); }
    .check-list { list-style: none; padding: 0; margin: 0; }
    .check-list li {
      display: grid; grid-template-columns: 1.2rem 1fr; gap: 0.45rem;
      padding: 0.45rem 0; border-bottom: 1px solid var(--line); font-size: 0.92rem;
    }
    .check-list .mark { font-family: var(--mono); font-weight: 700; }
    .check-list .mark.ok { color: var(--ok); }
    .check-list .mark.bad { color: var(--bad); }
    .check-list .hint { display: block; color: var(--muted); font-size: 0.82rem; margin-top: 0.15rem; }
    .feed-list { list-style: none; padding: 0; margin: 0; max-height: 22rem; overflow: auto; }
    .feed-list li {
      display: grid; grid-template-columns: 5.2rem 1fr; gap: 0.45rem;
      padding: 0.4rem 0; border-bottom: 1px solid var(--line); font-size: 0.88rem;
    }
    .feed-list .src {
      font-family: var(--mono); font-size: 0.7rem; font-weight: 500;
      text-transform: uppercase; color: var(--muted); padding-top: 0.15rem;
    }
    .feed-list .hint { display: block; color: var(--muted); font-size: 0.78rem; margin-top: 0.1rem; }
    .status-line { margin-bottom: 0.55rem; font-family: var(--mono); font-size: 0.78rem; color: var(--muted); }
    .status-line.ok { color: var(--ok); }
    .status-line.bad { color: var(--bad); }
    .browser-list {
      border: 1px solid var(--line); background: #fff; max-height: 16rem; overflow: auto;
      margin: 0.5rem 0 0.75rem;
    }
    .browser-row {
      display: flex; gap: 0.55rem; width: 100%; text-align: left;
      border: 0; border-bottom: 1px solid var(--line); background: transparent;
      padding: 0.45rem 0.65rem; cursor: pointer; font: 500 0.88rem var(--mono); color: var(--ink);
    }
    .browser-row:hover { background: #eef6f1; }
    .browser-row.selected { background: color-mix(in srgb, var(--accent) 14%, white); }
    .browser-row.invalid { color: var(--muted); cursor: default; }
    .browser-row .kind {
      flex: 0 0 2.4rem; font-size: 0.72rem; font-weight: 700; color: var(--muted);
    }
    footer { margin-top: 1.25rem; color: var(--muted); font-size: 0.85rem; }
    footer code { font-family: var(--mono); font-size: 0.8rem; }
    @keyframes rise {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <header>
      <div class="brand">SDLC-SPDD Ops Console <span class="mode-pill warn">experimental</span></div>
      <p class="tagline">Experimental local operator UI — install/upgrade, SQLite cache, upgrade rollback, Embabel Guide + Neo4j, and ADF Viewer launch. Not the stable consumer install path; prefer CLI scripts for production installs.</p>
    </header>

    <section class="panel">
      <h2>Target project</h2>
      <label class="field" for="target">Path</label>
      <div class="row">
        <input id="target" type="text" value="{{ default_target }}" spellcheck="false" autocomplete="off" />
        <button type="button" class="btn-secondary" id="btn-detect">Detect</button>
        <button type="button" class="btn-ghost" id="btn-refresh-all">Refresh panels</button>
      </div>
      <div class="meta" id="detect-meta">
        <span class="mode-pill" id="mode-pill">idle</span>
        <span id="detect-detail"> Choose a path and click Detect.</span>
      </div>
    </section>

    <nav class="tabs" role="tablist">
      <button type="button" class="tab active" data-tab="dashboard">Dashboard</button>
      <button type="button" class="tab" data-tab="install">Install / Upgrade</button>
      <button type="button" class="tab" data-tab="persist">Persistence</button>
      <button type="button" class="tab" data-tab="sqlite">SQLite</button>
      <button type="button" class="tab" data-tab="rollback">Rollback</button>
      <button type="button" class="tab" data-tab="guide">Guide</button>
      <button type="button" class="tab" data-tab="issues">Issues</button>
      <button type="button" class="tab" data-tab="adf">ADF</button>
    </nav>

    <section class="tab-pane active" id="pane-dashboard">
      <div class="panel">
        <h2>Today</h2>
        <p class="meta">Deterministic suggested actions from the ledger, registry, workflow state, and config — no LLM.</p>
        <ul class="check-list" id="dash-suggestions"><li>Refresh to load.</li></ul>
        <div class="actions">
          <button type="button" class="btn-secondary" id="btn-dash-refresh">Refresh dashboard</button>
        </div>
        <div class="status-line" id="dash-status">Ready.</div>
      </div>

      <div class="panel">
        <h2>Active work</h2>
        <div class="stats">
          <div class="stat-card"><div class="n" id="dw-id">—</div><div class="l">work id</div></div>
          <div class="stat-card"><div class="n" id="dw-phase">—</div><div class="l">phase</div></div>
          <div class="stat-card"><div class="n" id="dw-gates">—</div><div class="l">open gates</div></div>
          <div class="stat-card"><div class="n" id="dw-op">—</div><div class="l">next op</div></div>
        </div>
        <h3>Do now</h3>
        <pre class="cmd" id="dash-work-cmd">—</pre>
        <ul class="check-list" id="dash-work-gates"></ul>
        <div class="meta">Claim/advance from the terminal: <code class="inline">./scripts/sdlc.sh next</code></div>
      </div>

      <div class="panel">
        <h2>Memory &amp; backends</h2>
        <div class="stats">
          <div class="stat-card"><div class="n" id="dm-accepted">—</div><div class="l">accepted</div></div>
          <div class="stat-card"><div class="n" id="dm-staged">—</div><div class="l">staged</div></div>
          <div class="stat-card"><div class="n" id="db-sqlite">—</div><div class="l">sqlite cache</div></div>
          <div class="stat-card"><div class="n" id="db-guide">—</div><div class="l">guide</div></div>
        </div>
        <div class="meta" id="dash-memory-meta">—</div>
        <div class="meta" id="dash-backends-meta">—</div>
        <div class="actions">
          <button type="button" class="btn-secondary dash-configure" data-goto-tab="persist">Configure → Persistence (parity buttons)</button>
          <button type="button" class="btn-ghost dash-configure" data-goto-tab="sqlite">Configure → SQLite</button>
          <button type="button" class="btn-ghost dash-configure" data-goto-tab="guide">Configure → Guide</button>
        </div>
      </div>

      <div class="panel">
        <h2>Integrations</h2>
        <ul class="check-list" id="dash-integrations"><li>—</li></ul>
        <div class="actions">
          <button type="button" class="btn-ghost dash-configure" data-goto-tab="issues">Configure → Issues &amp; integrations</button>
          <button type="button" class="btn-ghost dash-configure" data-goto-tab="adf">Configure → ADF / Viewer</button>
          <button type="button" class="btn-ghost dash-configure" data-goto-tab="guide">Configure → Guide</button>
        </div>
      </div>

      <div class="panel">
        <h2>Recent activity — catch up here</h2>
        <ul class="feed-list" id="dash-activity"><li><span class="src">—</span><span>Refresh to load.</span></li></ul>
      </div>
    </section>

    <section class="tab-pane" id="pane-persist">
      <div class="panel">
        <h2>Persistence options</h2>
        <p class="meta">
          Ledger-first ContextStore (storage v3). The committed lessons ledger
          <code class="inline">spdd/memory/lessons.jsonl</code> and registry
          <code class="inline">spdd/memory/registry.jsonl</code> are the system of record;
          captures stage in <code class="inline">.sdlc/staged/lessons.jsonl</code> until accepted.
          SQLite is an opt-in local cache rebuilt from the ledger; Guide soft-fails. Config:
          <code class="inline">.sdlc/persistence-config.json</code>
          (override with <code class="inline">CONTEXT_BACKENDS</code>).
        </p>
        <div class="checks" style="margin-bottom: 0.9rem;">
          <label><input type="checkbox" id="pb-git" checked disabled /> git-pointers — ledger + registry (required)</label>
          <label><input type="checkbox" id="pb-sqlite" checked /> sqlite (opt-in cache)</label>
          <label><input type="checkbox" id="pb-guide" checked /> guide-dice</label>
        </div>
        <div class="row" style="margin-bottom: 0.75rem;">
          <div style="flex:1 1 18rem;">
            <label class="field" for="persist-guide-url">Guide base URL (optional override)</label>
            <input id="persist-guide-url" type="text" spellcheck="false" placeholder="leave blank to use GUIDE_BASE_URL / localhost:21337" />
          </div>
        </div>
        <label class="field" for="persist-notes">Notes</label>
        <textarea id="persist-notes" placeholder="Operator notes for this project's persist fan-out"></textarea>
        <div class="actions">
          <button type="button" class="btn-secondary" id="btn-persist-refresh">Refresh</button>
          <button type="button" class="btn-primary" id="btn-persist-save">Save options</button>
          <button type="button" class="btn-secondary" id="btn-persist-parity">Check ledger parity</button>
          <button type="button" class="btn-warn" id="btn-persist-parity-repair">Parity + repair</button>
        </div>
        <div class="stats" id="persist-stats">
          <div class="stat-card"><div class="n" id="ps-git">—</div><div class="l">git</div></div>
          <div class="stat-card"><div class="n" id="ps-sqlite">—</div><div class="l">sqlite</div></div>
          <div class="stat-card"><div class="n" id="ps-guide">—</div><div class="l">guide</div></div>
          <div class="stat-card"><div class="n" id="ps-source">—</div><div class="l">source</div></div>
        </div>
        <div class="meta" id="persist-meta">Not loaded.</div>
        <div class="status-line" id="persist-status">Ready.</div>
        <pre class="log" id="persist-log">No persistence action yet.</pre>
      </div>
    </section>

    <section class="tab-pane" id="pane-install">
      <div class="panel">
        <h2>Install options</h2>
        <div class="checks" style="margin-bottom: 0.9rem;">
          <label><input type="radio" name="action" value="auto" checked /> Auto (install or upgrade)</label>
          <label><input type="radio" name="action" value="install" /> Force install</label>
          <label><input type="radio" name="action" value="upgrade" /> Force upgrade</label>
        </div>
        <div class="checks" style="margin-bottom: 0.9rem;">
          <label><input type="checkbox" id="as-cursor" checked /> Cursor</label>
          <label><input type="checkbox" id="as-copilot" checked /> GitHub Copilot</label>
          <label><input type="checkbox" id="as-claude" /> Claude Code</label>
          <label><input type="checkbox" id="as-all" /> All assistants</label>
        </div>
        <div class="checks">
          <label><input type="checkbox" id="opt-dry" /> Dry run</label>
          <label><input type="checkbox" id="opt-force" /> Force overwrite (install)</label>
          <label><input type="checkbox" id="opt-nobackup" /> No backup (upgrade)</label>
          <label><input type="checkbox" id="opt-engine" /> Install Python engine</label>
        </div>
        <div class="actions">
          <button type="button" class="btn-primary" id="btn-run">Run</button>
          <button type="button" class="btn-secondary" id="btn-verify">Verify</button>
          <button type="button" class="btn-ghost" id="btn-clear">Clear log</button>
        </div>
      </div>
      <div class="panel">
        <h2>Output</h2>
        <div class="status-line" id="run-status">Ready.</div>
        <pre class="log" id="log">Awaiting action…</pre>
      </div>
    </section>

    <section class="tab-pane" id="pane-sqlite">
      <div class="panel">
        <h2>Local SQLite index</h2>
        <p class="meta">Opt-in cache under <code class="inline">.sdlc/index.sqlite</code>, rebuilt from the committed ledger (<code class="inline">spdd/memory/lessons.jsonl</code>) and registry (<code class="inline">spdd/memory/registry.jsonl</code>). The ledger remains the source of truth.</p>
        <div class="stats" id="sqlite-stats">
          <div class="stat-card"><div class="n" id="sq-work">—</div><div class="l">work items</div></div>
          <div class="stat-card"><div class="n" id="sq-art">—</div><div class="l">artifacts</div></div>
          <div class="stat-card"><div class="n" id="sq-local">—</div><div class="l">local sessions</div></div>
          <div class="stat-card"><div class="n" id="sq-fts">—</div><div class="l">fts mode</div></div>
        </div>
        <div class="meta" id="sqlite-meta">Not loaded.</div>
        <div class="actions">
          <button type="button" class="btn-secondary" id="btn-sqlite-refresh">Refresh</button>
          <button type="button" class="btn-primary" id="btn-sqlite-rebuild">Rebuild index</button>
        </div>
        <h3>Registry breakdown</h3>
        <div id="sqlite-breakdown" class="meta">—</div>
        <h3>Sample work items</h3>
        <div style="overflow:auto;">
          <table>
            <thead><tr><th>Work ID</th><th>Status</th><th>Canvas</th><th>Jira</th><th>Title</th></tr></thead>
            <tbody id="sqlite-rows"><tr><td colspan="5">Refresh to load.</td></tr></tbody>
          </table>
        </div>
      </div>
    </section>

    <section class="tab-pane" id="pane-rollback">
      <div class="panel">
        <h2>Upgrade backups</h2>
        <p class="meta">Backups live in <code class="inline">.sdlc-spdd-upgrade-backups/&lt;timestamp&gt;/</code>. Restore copies those files back over the target; a safety snapshot is taken first unless disabled.</p>
        <div class="actions">
          <button type="button" class="btn-secondary" id="btn-backups-refresh">Refresh backups</button>
        </div>
        <div style="overflow:auto; margin-top: 0.75rem;">
          <table>
            <thead><tr><th>Backup</th><th>Files</th><th>Size</th><th>Actions</th></tr></thead>
            <tbody id="backup-rows"><tr><td colspan="4">Refresh to load.</td></tr></tbody>
          </table>
        </div>
        <label class="checks" style="margin-top: 0.85rem; display:block;">
          <input type="checkbox" id="opt-rollback-dry" /> Dry-run restore
        </label>
        <label class="checks" style="margin-top: 0.35rem; display:block;">
          <input type="checkbox" id="opt-no-safety" /> Skip safety backup
        </label>
        <div class="status-line" id="rollback-status">Ready.</div>
        <pre class="log" id="rollback-log">No restore yet.</pre>
      </div>
    </section>

    <section class="tab-pane" id="pane-guide">
      <div class="panel">
        <h2>Embabel Guide + Neo4j</h2>
        <p class="meta">Pulls from <code class="inline">jmjava/orch-guide</code>, starts Compose Neo4j and Guide on custom ports. Config: <code class="inline">.sdlc/guide-config.json</code> (gitignored).</p>
        <div class="row" style="margin-bottom: 0.65rem;">
          <div style="flex: 2 1 16rem;">
            <label class="field" for="guide-home">Guide home</label>
            <input id="guide-home" type="text" spellcheck="false" />
          </div>
          <div style="flex: 2 1 16rem;">
            <label class="field" for="guide-git">Git URL</label>
            <input id="guide-git" type="text" spellcheck="false" />
          </div>
        </div>
        <div class="row" style="margin-bottom: 0.65rem;">
          <div style="flex: 2 1 18rem;">
            <label class="field" for="guide-ref">Git ref / branch (jmjava/orch-guide)</label>
            <input id="guide-ref" type="text" spellcheck="false" placeholder="sdlc-spdd-projection-v2 (or main)" />
          </div>
          <div style="flex: 1 1 8rem;">
            <label class="field" for="guide-profile">Profile</label>
            <input id="guide-profile" type="text" spellcheck="false" />
          </div>
          <div style="flex: 1 1 8rem;">
            <label class="field" for="guide-host">Guide host</label>
            <input id="guide-host" type="text" spellcheck="false" />
          </div>
          <div style="flex: 1 1 6rem;">
            <label class="field" for="guide-port">Guide port</label>
            <input id="guide-port" type="number" />
          </div>
          <div style="flex: 1 1 8rem;">
            <label class="field" for="guide-mcp">MCP server id</label>
            <input id="guide-mcp" type="text" spellcheck="false" />
          </div>
        </div>
        <div class="row" style="margin-bottom: 0.65rem;">
          <div style="flex: 1 1 6rem;">
            <label class="field" for="neo-bolt">Neo4j Bolt</label>
            <input id="neo-bolt" type="number" />
          </div>
          <div style="flex: 1 1 6rem;">
            <label class="field" for="neo-http">Neo4j HTTP</label>
            <input id="neo-http" type="number" />
          </div>
          <div style="flex: 1 1 6rem;">
            <label class="field" for="neo-https">Neo4j HTTPS</label>
            <input id="neo-https" type="number" />
          </div>
          <div style="flex: 1 1 7rem;">
            <label class="field" for="neo-user">Neo4j user</label>
            <input id="neo-user" type="text" spellcheck="false" />
          </div>
          <div style="flex: 1 1 8rem;">
            <label class="field" for="neo-pass">Neo4j password</label>
            <input id="neo-pass" type="password" autocomplete="off" />
          </div>
        </div>
        <label class="field" for="guide-notes">Notes</label>
        <textarea id="guide-notes"></textarea>
        <div class="actions">
          <button type="button" class="btn-primary" id="btn-guide-save">Save config</button>
          <button type="button" class="btn-secondary" id="btn-guide-ensure">Ensure / pull jmjava/orch-guide</button>
          <button type="button" class="btn-secondary" id="btn-guide-profile">Write Embabel SPDD profile</button>
          <button type="button" class="btn-secondary" id="btn-neo-start">Start Neo4j</button>
          <button type="button" class="btn-ghost" id="btn-neo-stop">Stop Neo4j</button>
          <button type="button" class="btn-primary" id="btn-guide-start">Start Guide (+ingest)</button>
          <button type="button" class="btn-secondary" id="btn-guide-start-noingest">Start Guide (no ingest)</button>
          <button type="button" class="btn-primary" id="btn-proj-load">Load NamedEntity projection</button>
          <button type="button" class="btn-warn" id="btn-guide-stop">Stop Guide</button>
          <button type="button" class="btn-ghost" id="btn-guide-probe">Refresh status</button>
        </div>
        <div class="stats" style="margin-top: 0.85rem;">
          <div class="stat-card"><div class="n" id="st-guide">—</div><div class="l">guide</div></div>
          <div class="stat-card"><div class="n" id="st-neo">—</div><div class="l">neo4j bolt</div></div>
          <div class="stat-card"><div class="n" id="st-pid">—</div><div class="l">guide pid</div></div>
          <div class="stat-card"><div class="n" id="st-port">—</div><div class="l">guide port</div></div>
        </div>
        <div class="meta" id="guide-probe">Status not loaded.</div>
        <div class="status-line" id="guide-action-status">Ready.</div>
        <pre class="log" id="guide-action-log">No runtime action yet.</pre>

        <h3>Neo4j / ingest operators</h3>
        <p class="meta">Requires Guide running. Uses Embabel Guide operator APIs (<code class="inline">load-references</code>, scoped ContentElement purge, git-ingestion revision reset).</p>
        <div class="row" style="margin-bottom: 0.65rem;">
          <div style="flex: 2 1 18rem;">
            <label class="field" for="op-directory">Directory (purge / git-reset scope)</label>
            <input id="op-directory" type="text" spellcheck="false" placeholder="orchestrator root or subdir" />
          </div>
          <div style="flex: 2 1 14rem;">
            <label class="field" for="op-uri-prefix">Or URI prefix (≥ 8 chars)</label>
            <input id="op-uri-prefix" type="text" spellcheck="false" placeholder="file:/… or https://…" />
          </div>
        </div>
        <div class="meta" id="op-dirs-hint">—</div>
        <div class="actions">
          <button type="button" class="btn-secondary" id="btn-guide-stats">Refresh Guide stats</button>
          <button type="button" class="btn-primary" id="btn-ingest-inc">Incremental ingest (load-references)</button>
          <button type="button" class="btn-secondary" id="btn-purge-preview">Purge preview</button>
          <button type="button" class="btn-warn" id="btn-purge">Purge ContentElements</button>
          <button type="button" class="btn-secondary" id="btn-git-reset">Reset git revision (force full re-ingest)</button>
          <button type="button" class="btn-warn" id="btn-purge-all-rag">Purge ALL RAG (docker Neo4j)</button>
        </div>
        <div class="stats" style="margin-top: 0.75rem;">
          <div class="stat-card"><div class="n" id="st-chunks">—</div><div class="l">content elements</div></div>
          <div class="stat-card"><div class="n" id="st-workids">—</div><div class="l">WorkId entities</div></div>
          <div class="stat-card"><div class="n" id="st-canvases">—</div><div class="l">Canvas entities</div></div>
          <div class="stat-card"><div class="n" id="st-areas">—</div><div class="l">Area entities</div></div>
        </div>

        <h3>Embabel mechanics</h3>
        <ul class="check-list" id="embabel-checklist"></ul>
        <h3>Checklist</h3>
        <ul class="check-list" id="guide-checklist"></ul>
        <h3>Equivalent CLI</h3>
        <pre class="cmd" id="guide-cmd">—</pre>
        <h3>Known profiles</h3>
        <div id="guide-profiles" class="meta">—</div>
      </div>
    </section>

    <section class="tab-pane" id="pane-issues">
      <div class="panel">
        <h2>Integrations config</h2>
        <p class="meta">
          Saved to gitignored <code class="inline">.sdlc/integrations-config.json</code>.
          Shell <code class="inline">JIRA_*</code> / <code class="inline">GH_TOKEN</code> env vars override file values.
          Tokens are never echoed back — leave blank to keep an existing saved token.
        </p>
        <div class="grid-2">
          <label class="field" for="int-tracker">Active tracker</label>
          <select id="int-tracker">
            <option value="github">GitHub Issues</option>
            <option value="jira">Jira</option>
            <option value="none">None (link only)</option>
          </select>
          <label class="field" for="int-jira-url">Jira base URL</label>
          <input id="int-jira-url" type="text" spellcheck="false" placeholder="https://yourorg.atlassian.net" />
          <label class="field" for="int-jira-email">Jira email</label>
          <input id="int-jira-email" type="email" spellcheck="false" placeholder="you@yourorg.com" />
          <label class="field" for="int-jira-token">Jira API token</label>
          <input id="int-jira-token" type="password" autocomplete="off" placeholder="Leave blank to keep saved token" />
          <label class="field" for="int-jira-project">Jira project key</label>
          <input id="int-jira-project" type="text" spellcheck="false" placeholder="PROJ" />
          <label class="field" for="int-gh-token">GitHub token</label>
          <input id="int-gh-token" type="password" autocomplete="off" placeholder="ghp_… or leave blank to keep saved" />
          <label class="field" for="int-gh-repo">GitHub repo</label>
          <input id="int-gh-repo" type="text" spellcheck="false" placeholder="owner/repo" />
        </div>
        <div class="actions">
          <button type="button" class="btn-secondary" id="btn-int-refresh">Refresh</button>
          <button type="button" class="btn-primary" id="btn-int-save">Save config</button>
        </div>
        <div class="status-line" id="int-status">Ready.</div>
        <div class="meta" id="int-meta">—</div>
      </div>

      <div class="panel" id="issues-link-jira">
        <h2>Link existing Jira issue</h2>
        <p class="meta">
          Create the Jira issue <strong>manually in Jira</strong>, copy the key
          (e.g. <code class="inline">PROJ-123</code>), then record it here. This
          updates the requirement doc, canvas Metadata, and registry — it does
          <strong>not</strong> create issues in Jira.
        </p>
        <div class="grid-2">
          <label class="field" for="jira-work-id">Work ID</label>
          <input id="jira-work-id" type="text" spellcheck="false" placeholder="FEAT-001-order-status-api" />
          <label class="field" for="jira-key">Jira key (from Jira UI)</label>
          <input id="jira-key" type="text" spellcheck="false" placeholder="PROJ-123" />
          <label class="field" for="jira-summary">Summary (optional, local doc)</label>
          <input id="jira-summary" type="text" spellcheck="false" placeholder="Matches Jira summary if known" />
          <label class="field" for="jira-issue-type">Issue type (optional)</label>
          <input id="jira-issue-type" type="text" spellcheck="false" placeholder="Story" />
        </div>
        <div class="actions">
          <button type="button" class="btn-secondary" id="btn-jira-refresh">Refresh status</button>
          <button type="button" class="btn-secondary" id="btn-jira-link-dry">Preview link</button>
          <button type="button" class="btn-primary" id="btn-jira-link">Apply link</button>
        </div>
        <div class="status-line" id="jira-link-status">Ready.</div>
        <div class="meta" id="jira-link-meta">—</div>
        <pre class="log" id="jira-link-log">No link action yet.</pre>
      </div>

      <div class="panel" id="issues-link-github" style="display:none;">
        <h2>Link existing GitHub issue</h2>
        <p class="meta">
          Create the issue <strong>manually in GitHub</strong>, copy the number
          (e.g. <code class="inline">42</code>), then record it here. Updates the
          requirement doc, canvas, and registry — does not create issues via API.
        </p>
        <div class="grid-2">
          <label class="field" for="gh-work-id">Work ID</label>
          <input id="gh-work-id" type="text" spellcheck="false" placeholder="FEAT-001-order-status-api" />
          <label class="field" for="gh-number">Issue number</label>
          <input id="gh-number" type="text" spellcheck="false" placeholder="42" />
          <label class="field" for="gh-title">Title (optional, local doc)</label>
          <input id="gh-title" type="text" spellcheck="false" placeholder="Matches GitHub title if known" />
          <label class="field" for="gh-url">URL (optional)</label>
          <input id="gh-url" type="text" spellcheck="false" placeholder="https://github.com/org/repo/issues/42" />
        </div>
        <div class="actions">
          <button type="button" class="btn-secondary" id="btn-gh-refresh">Refresh status</button>
          <button type="button" class="btn-secondary" id="btn-gh-link-dry">Preview link</button>
          <button type="button" class="btn-primary" id="btn-gh-link">Apply link</button>
        </div>
        <div class="status-line" id="gh-link-status">Ready.</div>
        <div class="meta" id="gh-link-meta">—</div>
        <pre class="log" id="gh-link-log">No link action yet.</pre>
      </div>

      <div class="panel">
        <h2 id="issues-sync-title">Sync with server</h2>
        <p class="meta" id="issues-sync-meta">
          Configure credentials above. Link an issue first, then pull or push requirement markdown.
        </p>
        <div class="actions">
          <button type="button" class="btn-secondary" id="btn-jira-pull-dry">Prepare pull</button>
          <button type="button" class="btn-primary" id="btn-jira-pull">Pull from server</button>
          <button type="button" class="btn-secondary" id="btn-jira-push-dry">Prepare push</button>
          <button type="button" class="btn-primary" id="btn-jira-push">Push to server</button>
        </div>
        <div class="status-line" id="jira-sync-status">Ready.</div>
        <pre class="cmd" id="jira-sync-cli">—</pre>
        <pre class="log" id="jira-sync-log">No sync yet.</pre>
      </div>
    </section>

    <section class="tab-pane" id="pane-adf">
      <div class="panel">
        <h2>ADF Viewer</h2>
        <p class="meta">Start/stop the viewer for editing and Jira sync. Below: browse a local ADF and init a draft REASONS canvas.</p>
        <div class="row" style="margin-bottom: 0.65rem;">
          <div style="flex: 1 1 10rem;">
            <label class="field" for="adf-host">Host</label>
            <input id="adf-host" type="text" spellcheck="false" value="127.0.0.1" />
          </div>
          <div style="flex: 1 1 6rem;">
            <label class="field" for="adf-port">Port</label>
            <input id="adf-port" type="number" value="5050" />
          </div>
        </div>
        <div class="actions">
          <button type="button" class="btn-primary" id="btn-adf-start">Start viewer</button>
          <button type="button" class="btn-secondary" id="btn-adf-restart">Restart</button>
          <button type="button" class="btn-ghost" id="btn-adf-stop">Stop</button>
          <button type="button" class="btn-secondary" id="btn-adf-refresh">Refresh status</button>
          <button type="button" class="btn-primary" id="btn-adf-open">Open ADF Viewer</button>
        </div>
        <div class="status-line" id="adf-status">Not loaded.</div>
        <div class="meta" id="adf-meta">—</div>
        <h3>Equivalent CLI</h3>
        <pre class="cmd" id="adf-cmd">—</pre>
        <pre class="log" id="adf-log">No action yet.</pre>
      </div>

      <div class="panel">
        <h2>Init SPDD work from ADF</h2>
        <p class="meta">Browse to an <code>.adf.json</code>, then create a draft REASONS canvas + requirement and hand off to analysis.</p>
        <div class="row" style="margin-bottom: 0.45rem;">
          <input id="adf-browse-path" type="text" spellcheck="false" placeholder="Browse path (defaults to target/adf)" />
          <button type="button" class="btn-secondary" id="btn-adf-browse">Browse</button>
          <button type="button" class="btn-ghost" id="btn-adf-browse-home">Target root</button>
          <button type="button" class="btn-ghost" id="btn-adf-browse-adf">adf/</button>
        </div>
        <div class="browser-list" id="adf-browser-list"></div>
        <div class="meta" id="adf-selected">No ADF selected.</div>
        <div class="row" style="margin-top: 0.75rem;">
          <div style="flex: 1 1 8rem;">
            <label class="field" for="adf-work-type">Type</label>
            <select id="adf-work-type">
              <option value="feature">feature</option>
              <option value="spike">spike</option>
              <option value="bug">bug</option>
              <option value="refactor">refactor</option>
              <option value="chore">chore</option>
            </select>
          </div>
          <div style="flex: 2 1 14rem;">
            <label class="field" for="adf-work-title">Title override (optional)</label>
            <input id="adf-work-title" type="text" spellcheck="false" placeholder="Defaults to first heading / filename" />
          </div>
          <div style="flex: 2 1 14rem;">
            <label class="field" for="adf-work-id">Work ID override (optional)</label>
            <input id="adf-work-id" type="text" spellcheck="false" placeholder="FEAT-013-slug" />
          </div>
        </div>
        <div class="actions" style="margin-top: 0.75rem;">
          <button type="button" class="btn-secondary" id="btn-adf-init-dry">Dry run</button>
          <button type="button" class="btn-primary" id="btn-adf-init">Init SPDD work</button>
        </div>
        <div class="status-line" id="adf-init-status">Ready.</div>
        <pre class="log" id="adf-init-log">No init yet.</pre>
      </div>
    </section>

    <footer>
      CLI: <code>./scripts/sdlc.sh installer</code> · <code>db status</code> · <code>db rebuild</code>
      · <code>./scripts/sdlc.sh viewer</code>
      · orchestrator: <code>{{ orchestrator_root }}</code>
    </footer>
  </div>
  <script>
    const $ = (id) => document.getElementById(id);
    let lastDetect = null;

    function target() { return $("target").value.trim(); }

    function assistants() {
      if ($("as-all").checked) return ["all"];
      const out = [];
      if ($("as-cursor").checked) out.push("cursor");
      if ($("as-copilot").checked) out.push("copilot");
      if ($("as-claude").checked) out.push("claude");
      return out.length ? out : ["cursor"];
    }

    function selectedAction() {
      const checked = document.querySelector('input[name="action"]:checked');
      return checked ? checked.value : "auto";
    }

    function setBusy(ids, busy) {
      ids.forEach((id) => { const el = $(id); if (el) el.disabled = busy; });
    }

    document.querySelectorAll(".tab").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".tab").forEach((b) => b.classList.remove("active"));
        document.querySelectorAll(".tab-pane").forEach((p) => p.classList.remove("active"));
        btn.classList.add("active");
        $("pane-" + btn.dataset.tab).classList.add("active");
      });
    });

    async function detect() {
      const t = target();
      if (!t) return;
      setBusy(["btn-detect"], true);
      try {
        const res = await fetch("/api/detect", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ target: t }),
        });
        const data = await res.json();
        lastDetect = data;
        $("mode-pill").textContent = data.mode || "error";
        $("mode-pill").className = "mode-pill " + (data.mode || "error");
        if (data.error) {
          $("detect-detail").textContent = " " + data.error;
          return;
        }
        const markers = (data.markers || []).length
          ? ` markers: ${(data.markers || []).slice(0, 3).join(", ")}${(data.markers || []).length > 3 ? "…" : ""}`
          : " no framework markers";
        $("detect-detail").innerHTML = ` recommendation: <strong>${data.recommendation}</strong> ·${markers}`;
        const a = data.assistants || {};
        if (a.cursor || a.copilot || a.claude) {
          $("as-cursor").checked = !!a.cursor;
          $("as-copilot").checked = !!a.copilot;
          $("as-claude").checked = !!a.claude;
        }
      } catch (err) {
        $("mode-pill").textContent = "error";
        $("mode-pill").className = "mode-pill error";
        $("detect-detail").textContent = " " + err;
      } finally {
        setBusy(["btn-detect"], false);
      }
    }

    async function run(actionOverride) {
      const t = target();
      if (!t) {
        $("run-status").textContent = "Target path required.";
        $("run-status").className = "status-line bad";
        return;
      }
      let action = actionOverride || selectedAction();
      if (action === "auto") {
        await detect();
        const rec = (lastDetect && lastDetect.recommendation) || "install";
        if (rec === "create") {
          $("run-status").textContent = "Target directory does not exist. Create it first.";
          $("run-status").className = "status-line bad";
          return;
        }
        action = rec === "upgrade" ? "upgrade" : "install";
      }
      setBusy(["btn-run", "btn-verify", "btn-detect"], true);
      $("run-status").textContent = `Running ${action}…`;
      $("run-status").className = "status-line";
      $("log").textContent = "";
      try {
        const res = await fetch("/api/run", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            action, target: t, assistants: assistants(),
            dry_run: $("opt-dry").checked,
            force: $("opt-force").checked,
            no_backup: $("opt-nobackup").checked,
            with_python_engine: $("opt-engine").checked,
          }),
        });
        const data = await res.json();
        const cmd = (data.command || []).join(" ");
        $("log").textContent = (cmd ? "$ " + cmd + "\\n\\n" : "") + (data.log || data.error || "");
        if (data.ok) {
          $("run-status").textContent = `${action} succeeded (exit ${data.exit_code}).`;
          $("run-status").className = "status-line ok";
        } else {
          $("run-status").textContent = `${action} failed (exit ${data.exit_code != null ? data.exit_code : "?"}).`;
          $("run-status").className = "status-line bad";
        }
        await detect();
        await loadSqlite();
        await loadBackups();
      } catch (err) {
        $("run-status").textContent = String(err);
        $("run-status").className = "status-line bad";
        $("log").textContent = String(err);
      } finally {
        setBusy(["btn-run", "btn-verify", "btn-detect"], false);
      }
    }

    async function loadSqlite() {
      const t = target();
      if (!t) return;
      const res = await fetch("/api/sqlite/status", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target: t }),
      });
      const data = await res.json();
      if (data.error && !data.path) {
        $("sqlite-meta").textContent = data.error;
        return;
      }
      $("sq-work").textContent = data.exists ? data.work_items : "0";
      $("sq-art").textContent = data.exists ? data.artifacts : "0";
      $("sq-local").textContent = data.exists ? data.local_sessions : "0";
      $("sq-fts").textContent = data.fts || "—";
      $("sqlite-meta").textContent = data.exists
        ? `${data.path} · rebuilt ${data.rebuilt_at || "?"} · commit ${data.source_commit || "?"}`
        : `Missing: ${data.path || "(unknown)"} — rebuild to create.`;
      const br = data.by_registry_status || {};
      const keys = Object.keys(br);
      $("sqlite-breakdown").textContent = keys.length
        ? keys.map((k) => `${k}: ${br[k]}`).join(" · ")
        : "(none)";
      const rows = data.recent || [];
      $("sqlite-rows").innerHTML = rows.length
        ? rows.map((r) => `<tr>
            <td><code class="inline">${r.work_id || ""}</code></td>
            <td>${r.registry_status || ""}</td>
            <td>${r.canvas_status || ""}</td>
            <td>${r.jira_key || ""}</td>
            <td>${(r.title || "").replace(/</g, "&lt;")}</td>
          </tr>`).join("")
        : `<tr><td colspan="5">No rows (rebuild if empty).</td></tr>`;
    }

    async function rebuildSqlite() {
      setBusy(["btn-sqlite-rebuild"], true);
      try {
        const res = await fetch("/api/sqlite/rebuild", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ target: target() }),
        });
        const data = await res.json();
        if (!data.ok) {
          $("sqlite-meta").textContent = data.error || "Rebuild failed";
          return;
        }
        await loadSqlite();
      } finally {
        setBusy(["btn-sqlite-rebuild"], false);
      }
    }

    async function loadBackups() {
      const res = await fetch("/api/backups", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target: target() }),
      });
      const data = await res.json();
      const backups = data.backups || [];
      $("backup-rows").innerHTML = backups.length
        ? backups.map((b) => `<tr>
            <td><code class="inline">${b.id}</code><div class="meta">${(b.files || []).slice(0, 4).join(", ")}${(b.files || []).length > 4 ? "…" : ""}</div></td>
            <td>${b.file_count}</td>
            <td>${Math.round((b.bytes || 0) / 1024)} KB</td>
            <td><button type="button" class="btn-warn" data-restore="${b.id}">Restore</button></td>
          </tr>`).join("")
        : `<tr><td colspan="4">No backups under .sdlc-spdd-upgrade-backups/</td></tr>`;
      document.querySelectorAll("[data-restore]").forEach((btn) => {
        btn.addEventListener("click", () => restoreBackup(btn.dataset.restore));
      });
    }

    async function restoreBackup(backupId) {
      if (!$("opt-rollback-dry").checked) {
        const ok = confirm(`Restore backup ${backupId} into\\n${target()}?`);
        if (!ok) return;
      }
      $("rollback-status").textContent = `Restoring ${backupId}…`;
      $("rollback-status").className = "status-line";
      const res = await fetch("/api/rollback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          target: target(),
          backup_id: backupId,
          dry_run: $("opt-rollback-dry").checked,
          no_safety_backup: $("opt-no-safety").checked,
        }),
      });
      const data = await res.json();
      $("rollback-log").textContent = JSON.stringify(data, null, 2);
      if (data.ok) {
        $("rollback-status").textContent = data.dry_run
          ? `Dry-run: would restore ${data.count} files.`
          : `Restored ${data.count} files.` + (data.safety_backup ? ` Safety: ${data.safety_backup}` : "");
        $("rollback-status").className = "status-line ok";
        await loadBackups();
        await detect();
      } else {
        $("rollback-status").textContent = data.error || "Restore failed";
        $("rollback-status").className = "status-line bad";
      }
    }

    function guideFormBody(extra) {
      return Object.assign({
        target: target(),
        guide_home: $("guide-home").value,
        guide_git_url: $("guide-git").value,
        guide_git_ref: $("guide-ref").value,
        profile: $("guide-profile").value,
        host: $("guide-host").value,
        port: Number($("guide-port").value || 21337),
        neo4j_bolt_port: Number($("neo-bolt").value || 7687),
        neo4j_http_port: Number($("neo-http").value || 7474),
        neo4j_https_port: Number($("neo-https").value || 7473),
        neo4j_username: $("neo-user").value,
        neo4j_password: $("neo-pass").value,
        mcp_server: $("guide-mcp").value,
        notes: $("guide-notes").value,
      }, extra || {});
    }

    function fillGuide(data) {
      const cfg = data.config || {};
      $("guide-home").value = cfg.guide_home || "";
      $("guide-git").value = cfg.guide_git_url || "https://github.com/jmjava/orch-guide.git";
      $("guide-ref").value = cfg.guide_git_ref || "";
      $("guide-profile").value = cfg.profile || "";
      $("guide-host").value = cfg.host || "127.0.0.1";
      $("guide-port").value = cfg.port || 21337;
      $("guide-mcp").value = cfg.mcp_server || "embabel-dev";
      $("neo-bolt").value = cfg.neo4j_bolt_port || 7687;
      $("neo-http").value = cfg.neo4j_http_port || 7474;
      $("neo-https").value = cfg.neo4j_https_port || 7473;
      $("neo-user").value = cfg.neo4j_username || "neo4j";
      if (cfg.neo4j_password) $("neo-pass").value = cfg.neo4j_password;
      $("guide-notes").value = cfg.notes || "";
      const probe = data.probe || {};
      const neo = data.neo4j || {};
      const gp = (data.stack && data.stack.guide_process) || {};
      $("st-guide").textContent = probe.tcp_open ? "UP" : "DOWN";
      $("st-neo").textContent = neo.bolt_open ? "UP" : "DOWN";
      $("st-pid").textContent = gp.pid || "—";
      $("st-port").textContent = cfg.port || "—";
      const gs = (data.guide_stats && data.guide_stats.data) || {};
      const chunkCount = gs.contentElementCount ?? gs.contentElements ?? gs.chunkCount ?? gs.totalContentElements;
      $("st-chunks").textContent = chunkCount != null ? chunkCount : "—";
      const pd = (data.projection && data.projection.data) || {};
      $("st-workids").textContent = pd.workIdCount != null ? pd.workIdCount : "—";
      $("st-canvases").textContent = pd.canvasCount != null ? pd.canvasCount : "—";
      $("st-areas").textContent = pd.areaCount != null ? pd.areaCount : "—";
      const dirs = data.operator_directories || [];
      if (!$("op-directory").value && dirs[0]) $("op-directory").value = dirs[0];
      $("op-dirs-hint").innerHTML = dirs.length
        ? "Quick picks: " + dirs.map((d) => `<code class="inline op-dir" style="cursor:pointer">${d}</code>`).join(" ")
        : "—";
      document.querySelectorAll(".op-dir").forEach((el) => {
        el.addEventListener("click", () => { $("op-directory").value = el.textContent || ""; });
      });
      $("guide-probe").textContent =
        (probe.tcp_open
          ? `Guide UP at ${probe.host}:${probe.port} · SSE ${probe.sse_url}`
          : `Guide DOWN at ${probe.host}:${probe.port}`) +
        " · " +
        (neo.bolt_open
          ? `Neo4j Bolt UP ${neo.bolt_url} · browser ${neo.browser_url}`
          : `Neo4j Bolt DOWN :${neo.bolt_port || "?"}`) +
        (gp.log_path ? ` · log ${gp.log_path}` : "");
      const renderChecks = (items) => (items || []).map((it) => `<li>
          <span class="mark ${it.ok ? "ok" : "bad"}">${it.ok ? "OK" : "!!"}</span>
          <span><strong>${it.label}</strong><span class="hint">${it.hint || ""}</span></span>
        </li>`).join("");
      $("embabel-checklist").innerHTML = renderChecks(data.embabel_mechanics) || "<li>—</li>";
      $("guide-checklist").innerHTML = renderChecks(data.checklist) || "<li>—</li>";
      $("guide-cmd").textContent = data.ingest_command || "—";
      const profiles = (cfg.profiles || []).map((p) => `<div><code class="inline">${p.id}</code> — ${p.purpose}</div>`).join("");
      $("guide-profiles").innerHTML = profiles || "—";
    }

    async function loadGuide() {
      const res = await fetch("/api/guide", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target: target() }),
      });
      fillGuide(await res.json());
    }

    async function saveGuide() {
      const res = await fetch("/api/guide/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(guideFormBody()),
      });
      fillGuide(await res.json());
      $("guide-action-status").textContent = "Config saved.";
      $("guide-action-status").className = "status-line ok";
    }

    async function guideAction(url, extra, label) {
      $("guide-action-status").textContent = label + "…";
      $("guide-action-status").className = "status-line";
      setBusy(["btn-guide-ensure","btn-neo-start","btn-neo-stop","btn-guide-start","btn-guide-start-noingest","btn-guide-stop"], true);
      try {
        const res = await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(guideFormBody(extra)),
        });
        const data = await res.json();
        fillGuide(data);
        const detail = data.ensure || data.result || data;
        $("guide-action-log").textContent = JSON.stringify(detail, null, 2);
        if (data.ok) {
          $("guide-action-status").textContent = label + " OK";
          $("guide-action-status").className = "status-line ok";
        } else {
          $("guide-action-status").textContent = (detail.error || detail.log || label + " failed").toString().slice(0, 200);
          $("guide-action-status").className = "status-line bad";
        }
      } catch (err) {
        $("guide-action-status").textContent = String(err);
        $("guide-action-status").className = "status-line bad";
        $("guide-action-log").textContent = String(err);
      } finally {
        setBusy(["btn-guide-ensure","btn-neo-start","btn-neo-stop","btn-guide-start","btn-guide-start-noingest","btn-guide-stop"], false);
      }
    }

    function adfBody(extra) {
      return Object.assign({
        target: target(),
        host: $("adf-host").value.trim() || "127.0.0.1",
        port: parseInt($("adf-port").value, 10) || 5050,
      }, extra || {});
    }

    function fillAdf(data) {
      const proc = data.process || {};
      const probe = data.probe || {};
      const url = data.url || probe.url || "";
      $("adf-cmd").textContent = data.cli || "—";
      const bits = [
        proc.alive ? "process alive" : "process stopped",
        probe.tcp_open ? "TCP open" : "TCP closed",
        probe.http_ok ? "HTTP ok" : "HTTP down",
        url ? ("url " + url) : "",
        proc.log_path ? ("log " + proc.log_path) : "",
      ].filter(Boolean);
      $("adf-meta").textContent = bits.join(" · ") || "—";
      if (data.ok && (proc.alive || probe.http_ok)) {
        $("adf-status").textContent = "Viewer ready" + (url ? ": " + url : "");
        $("adf-status").className = "status-line ok";
      } else if (data.error) {
        $("adf-status").textContent = data.error;
        $("adf-status").className = "status-line bad";
      } else {
        $("adf-status").textContent = probe.detail || "Viewer not running.";
        $("adf-status").className = "status-line";
      }
      if (data.result) {
        $("adf-log").textContent = JSON.stringify(data.result, null, 2);
      }
      return url;
    }

    async function loadAdf() {
      const res = await fetch("/api/adf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(adfBody()),
      });
      return fillAdf(await res.json());
    }

    async function adfAction(url, label, { openAfter } = {}) {
      $("adf-status").textContent = label + "…";
      $("adf-status").className = "status-line";
      setBusy(["btn-adf-start","btn-adf-stop","btn-adf-restart","btn-adf-open","btn-adf-refresh"], true);
      try {
        const res = await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(adfBody()),
        });
        const data = await res.json();
        const openUrl = fillAdf(data);
        if (!data.ok && data.error) {
          $("adf-status").textContent = data.error;
          $("adf-status").className = "status-line bad";
          return;
        }
        $("adf-status").textContent = label + " OK";
        $("adf-status").className = "status-line ok";
        if (openAfter && openUrl) {
          // Poll briefly so Flask can bind before the new tab loads.
          for (let i = 0; i < 20; i++) {
            await new Promise((r) => setTimeout(r, 250));
            const probeRes = await fetch("/api/adf", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(adfBody()),
            });
            const probeData = await probeRes.json();
            fillAdf(probeData);
            if (probeData.probe && probeData.probe.http_ok) {
              window.open(probeData.url || openUrl, "_blank", "noopener");
              return;
            }
          }
          window.open(openUrl, "_blank", "noopener");
        }
      } catch (err) {
        $("adf-status").textContent = String(err);
        $("adf-status").className = "status-line bad";
        $("adf-log").textContent = String(err);
      } finally {
        setBusy(["btn-adf-start","btn-adf-stop","btn-adf-restart","btn-adf-open","btn-adf-refresh"], false);
      }
    }

    async function openAdfViewer() {
      const statusRes = await fetch("/api/adf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(adfBody()),
      });
      const status = await statusRes.json();
      fillAdf(status);
      if (status.probe && status.probe.http_ok && status.url) {
        window.open(status.url, "_blank", "noopener");
        return;
      }
      await adfAction("/api/adf/start", "Start viewer", { openAfter: true });
    }

    let adfBrowsePath = "";
    let adfSelectedPath = "";
    let adfHome = "";
    let adfDir = "";

    function setAdfSelected(path) {
      adfSelectedPath = path || "";
      $("adf-selected").textContent = adfSelectedPath
        ? ("Selected: " + adfSelectedPath)
        : "No ADF selected.";
    }

    async function loadAdfBrowse(path) {
      const res = await fetch("/api/adf/browse", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(adfBody({ path: path || "" })),
      });
      const data = await res.json();
      if (!data.ok) {
        $("adf-init-status").textContent = data.error || "Browse failed";
        $("adf-init-status").className = "status-line bad";
        $("adf-init-log").textContent = JSON.stringify(data, null, 2);
        return;
      }
      adfBrowsePath = data.path || "";
      adfHome = data.home || target();
      adfDir = data.adf_dir || "";
      $("adf-browse-path").value = adfBrowsePath;
      const list = $("adf-browser-list");
      list.innerHTML = "";
      if (data.parent) {
        const up = document.createElement("button");
        up.type = "button";
        up.className = "browser-row";
        up.innerHTML = '<span class="kind">DIR</span><span>..</span>';
        up.onclick = () => loadAdfBrowse(data.parent);
        list.appendChild(up);
      }
      for (const d of data.dirs || []) {
        const row = document.createElement("button");
        row.type = "button";
        row.className = "browser-row";
        row.innerHTML = '<span class="kind">DIR</span><span></span>';
        row.querySelector("span:last-child").textContent = d.name + "/";
        row.onclick = () => loadAdfBrowse(d.path);
        list.appendChild(row);
      }
      for (const f of data.files || []) {
        const row = document.createElement("button");
        row.type = "button";
        row.className = "browser-row" + (f.valid ? "" : " invalid")
          + (f.path === adfSelectedPath ? " selected" : "");
        row.innerHTML = '<span class="kind">ADF</span><span></span>';
        row.querySelector("span:last-child").textContent = f.name + (f.valid ? "" : " (invalid)");
        if (f.valid) {
          row.onclick = () => {
            setAdfSelected(f.path);
            loadAdfBrowse(adfBrowsePath);
          };
        }
        list.appendChild(row);
      }
      if (!(data.dirs || []).length && !(data.files || []).length) {
        const empty = document.createElement("div");
        empty.className = "meta";
        empty.style.padding = "0.65rem";
        empty.textContent = "No ADF candidates in this folder.";
        list.appendChild(empty);
      }
      $("adf-init-status").textContent = "Browsing " + adfBrowsePath;
      $("adf-init-status").className = "status-line";
    }

    async function initFromAdf(dryRun) {
      if (!adfSelectedPath) {
        $("adf-init-status").textContent = "Select an ADF file first.";
        $("adf-init-status").className = "status-line bad";
        return;
      }
      const label = dryRun ? "Dry run" : "Init SPDD work";
      $("adf-init-status").textContent = label + "…";
      $("adf-init-status").className = "status-line";
      setBusy(["btn-adf-init", "btn-adf-init-dry", "btn-adf-browse"], true);
      try {
        const res = await fetch("/api/adf/init-work", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(adfBody({
            path: adfSelectedPath,
            type: $("adf-work-type").value,
            title: $("adf-work-title").value.trim(),
            work_id: $("adf-work-id").value.trim(),
            dry_run: !!dryRun,
          })),
        });
        const data = await res.json();
        $("adf-init-log").textContent = JSON.stringify(data, null, 2);
        if (!data.ok) {
          $("adf-init-status").textContent = data.error || (label + " failed");
          $("adf-init-status").className = "status-line bad";
          return;
        }
        $("adf-init-status").textContent = (dryRun ? "Would create " : "Created ")
          + data.work_id + " — next: " + data.next_command;
        $("adf-init-status").className = "status-line ok";
      } catch (err) {
        $("adf-init-status").textContent = String(err);
        $("adf-init-status").className = "status-line bad";
        $("adf-init-log").textContent = String(err);
      } finally {
        setBusy(["btn-adf-init", "btn-adf-init-dry", "btn-adf-browse"], false);
      }
    }

    function applyPersist(data) {
      const en = data.enabled || {};
      $("pb-git").checked = true;
      $("pb-sqlite").checked = !!en.sqlite;
      $("pb-guide").checked = !!en["guide-dice"];
      $("persist-guide-url").value = (data.guide && data.guide.base_url) || "";
      $("persist-notes").value = data.notes || "";
      $("ps-git").textContent = en["git-pointers"] ? "ON" : "OFF";
      $("ps-sqlite").textContent = en.sqlite ? (data.sqlite && data.sqlite.exists ? "READY" : "ON") : "OFF";
      $("ps-guide").textContent = en["guide-dice"] ? "ON" : "OFF";
      $("ps-source").textContent = data.source || "—";
      const effective = (data.guide && data.guide.effective_base_url) || "";
      $("persist-meta").textContent =
        "backends=" + (data.backends || []).join(",") +
        " · config=" + (data.config_path || "—") +
        (data.config_exists ? "" : " (defaults)") +
        (effective ? (" · effective guide=" + effective) : "");
      $("persist-log").textContent = JSON.stringify(data, null, 2);
    }

    async function loadPersist() {
      const res = await fetch("/api/persistence/status", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target: target() }),
      });
      const data = await res.json();
      if (!res.ok) {
        $("persist-meta").textContent = data.error || "Failed to load";
        $("persist-status").textContent = "Load failed";
        $("persist-status").className = "status-line bad";
        return;
      }
      applyPersist(data);
      $("persist-status").textContent = "Loaded.";
      $("persist-status").className = "status-line ok";
    }

    async function savePersist() {
      setBusy(["btn-persist-save"], true);
      $("persist-status").textContent = "Saving…";
      $("persist-status").className = "status-line";
      try {
        const backends = ["git-pointers"];
        if ($("pb-sqlite").checked) backends.push("sqlite");
        if ($("pb-guide").checked) backends.push("guide-dice");
        const res = await fetch("/api/persistence/save", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            target: target(),
            backends,
            guide_base_url: $("persist-guide-url").value.trim(),
            notes: $("persist-notes").value,
          }),
        });
        const data = await res.json();
        if (!res.ok) {
          $("persist-status").textContent = data.error || "Save failed";
          $("persist-status").className = "status-line bad";
          $("persist-log").textContent = JSON.stringify(data, null, 2);
          return;
        }
        applyPersist(data);
        $("persist-status").textContent = "Saved persistence options.";
        $("persist-status").className = "status-line ok";
      } catch (err) {
        $("persist-status").textContent = String(err);
        $("persist-status").className = "status-line bad";
      } finally {
        setBusy(["btn-persist-save"], false);
      }
    }

    async function parityPersist(repair) {
      setBusy(["btn-persist-parity", "btn-persist-parity-repair"], true);
      $("persist-status").textContent = repair ? "Checking ledger parity (repair)…" : "Checking ledger parity…";
      $("persist-status").className = "status-line";
      try {
        const res = await fetch("/api/persistence/parity", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ target: target(), repair: !!repair }),
        });
        const data = await res.json();
        $("persist-log").textContent = JSON.stringify(data, null, 2);
        if (!res.ok) {
          $("persist-status").textContent = data.error || "Parity check failed";
          $("persist-status").className = "status-line bad";
          return;
        }
        const parity = data.parity || {};
        const ledger = parity.ledger || {};
        $("persist-status").textContent =
          (parity.ok ? "Parity OK" : "Parity drift") +
          " · ledger " + (ledger.count != null ? ledger.count : "?") + " accepted (" + (ledger.path || "spdd/memory/lessons.jsonl") + ")" +
          (parity.repaired ? " · repair ran (db rebuild / Guide reproject)" : "");
        $("persist-status").className = "status-line " + (parity.ok ? "ok" : "bad");
      } catch (err) {
        $("persist-status").textContent = String(err);
        $("persist-status").className = "status-line bad";
        $("persist-log").textContent = String(err);
      } finally {
        setBusy(["btn-persist-parity", "btn-persist-parity-repair"], false);
      }
    }

    function esc(v) {
      return String(v == null ? "" : v).replace(/&/g, "&amp;").replace(/</g, "&lt;");
    }

    function gotoTab(name) {
      const btn = document.querySelector('.tab[data-tab="' + name + '"]');
      if (btn) btn.click();
    }

    function fillDashboardStatus(data) {
      const work = data.work || {};
      $("dw-id").textContent = work.pointer || "(none)";
      $("dw-phase").textContent = work.phase || "—";
      $("dw-gates").textContent = String((work.open_gates || []).length);
      $("dw-op").textContent = work.operation || "—";
      $("dash-work-cmd").textContent = work.recommended_command
        || (work.pointer ? "—" : "./scripts/sdlc.sh claim <WORK-ID>");
      const gates = work.open_gates || [];
      $("dash-work-gates").innerHTML = gates.length
        ? gates.map((g) => `<li><span class="mark bad">!!</span><span>${esc(g.label || g.gate)}</span></li>`).join("")
        : '<li><span class="mark ok">OK</span><span>No open gates'
          + (work.pointer ? " — ready to advance." : " — no active Work ID.") + "</span></li>";
      const mem = data.memory || {};
      $("dm-accepted").textContent = mem.accepted_count != null ? mem.accepted_count : "—";
      $("dm-staged").textContent = mem.staged_count != null ? mem.staged_count : "—";
      const last = mem.registry_last_event;
      $("dash-memory-meta").textContent =
        "ledger " + (mem.ledger_path || "") +
        (mem.last_accepted_ts ? " · last accepted " + mem.last_accepted_ts : " · nothing accepted yet") +
        (mem.needs_accept ? " · staged records need accept" : "") +
        (last
          ? " · registry: " + [last.event, last.work_id, last.owner ? "by " + last.owner : "", last.ts].filter(Boolean).join(" ")
          : " · registry empty");
      const be = data.backends || {};
      const sq = be.sqlite || {};
      const gd = be.guide || {};
      $("db-sqlite").textContent = sq.enabled ? (sq.exists ? "READY" : "ON") : "OFF";
      $("db-guide").textContent = gd.enabled ? (gd.reachable ? "UP" : "DOWN") : "OFF";
      $("dash-backends-meta").textContent =
        "backends=" + (be.backends || []).join(",") +
        " · source=" + (be.source || "—") +
        (gd.enabled ? " · guide " + (gd.reachable ? "reachable" : "unreachable") + " at " + (gd.host || "?") + ":" + (gd.port || "?") : "") +
        " · " + (be.parity_hint || "");
      const integ = data.integrations || {};
      const jira = integ.jira || {};
      const gh = integ.github || {};
      const viewer = integ.viewer || {};
      const item = (ok, label, hint) => `<li>
          <span class="mark ${ok ? "ok" : "bad"}">${ok ? "OK" : "!!"}</span>
          <span><strong>${esc(label)}</strong><span class="hint">${esc(hint || "")}</span></span>
        </li>`;
      $("dash-integrations").innerHTML = [
        item(jira.configured, "Jira env " + (jira.configured ? "set" : "not set"), jira.hint),
        item(gh.authenticated, "GitHub CLI " + (gh.authenticated ? "authenticated" : "not ready"), gh.detail),
        item(
          viewer.running,
          "ADF Viewer (:" + (viewer.port || 5050) + ") " + (viewer.running ? "running" : "stopped"),
          viewer.running ? viewer.url : "Start it from the ADF tab."
        ),
      ].join("");
    }

    async function loadDashboard() {
      setBusy(["btn-dash-refresh"], true);
      $("dash-status").textContent = "Loading…";
      $("dash-status").className = "status-line";
      try {
        const opts = {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ target: target() }),
        };
        const [statusRes, activityRes, suggestRes] = await Promise.all([
          fetch("/api/dashboard/status", opts),
          fetch("/api/dashboard/activity?limit=20", opts),
          fetch("/api/dashboard/suggestions", opts),
        ]);
        const status = await statusRes.json();
        if (!statusRes.ok) {
          $("dash-status").textContent = status.error || "Dashboard load failed";
          $("dash-status").className = "status-line bad";
        } else {
          fillDashboardStatus(status);
        }
        const activity = await activityRes.json();
        const items = activity.items || [];
        $("dash-activity").innerHTML = items.length
          ? items.map((it) => `<li>
              <span class="src">${esc(it.source)}</span>
              <span>${esc(it.text)}<span class="hint">${esc(it.ts)}${it.work_id ? " · " + esc(it.work_id) : ""}</span></span>
            </li>`).join("")
          : '<li><span class="src">—</span><span>No activity yet (fresh install).</span></li>';
        const sug = await suggestRes.json();
        const list = sug.suggestions || [];
        $("dash-suggestions").innerHTML = list.length
          ? list.map((s) => `<li><span class="mark">[ ]</span><span>${esc(s.text)}</span></li>`).join("")
          : '<li><span class="mark ok">OK</span><span>Nothing pending — all caught up.</span></li>';
        if (statusRes.ok) {
          $("dash-status").textContent = "Loaded.";
          $("dash-status").className = "status-line ok";
        }
      } catch (err) {
        $("dash-status").textContent = String(err);
        $("dash-status").className = "status-line bad";
      } finally {
        setBusy(["btn-dash-refresh"], false);
      }
    }

    function activeTracker() {
      return $("int-tracker").value || "github";
    }

    function activeWorkId() {
      return activeTracker() === "jira"
        ? $("jira-work-id").value.trim()
        : $("gh-work-id").value.trim() || $("jira-work-id").value.trim();
    }

    function applyIssuesPanels() {
      const t = activeTracker();
      $("issues-link-jira").style.display = t === "jira" ? "" : "none";
      $("issues-link-github").style.display = t === "github" ? "" : "none";
      $("issues-sync-title").textContent = t === "jira"
        ? "Sync with Jira server"
        : (t === "github" ? "Sync with GitHub" : "Sync disabled (tracker=none)");
      $("issues-sync-meta").textContent = t === "jira"
        ? "Pull refreshes ## Jira from the server; push sends local markdown → ADF (update only)."
        : (t === "github"
          ? "Pull refreshes ## GitHub from the server; push sends composed GFM markdown (update only)."
          : "Set tracker to Jira or GitHub to enable server sync.");
    }

    async function loadIntegrations() {
      const res = await fetch("/api/integrations/status", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target: target() }),
      });
      const data = await res.json();
      if (!res.ok) {
        $("int-meta").textContent = data.error || "Load failed";
        return;
      }
      $("int-tracker").value = data.effective_tracker || data.tracker || "github";
      const j = data.jira || {};
      const g = data.github || {};
      $("int-jira-url").value = j.base_url || "";
      $("int-jira-email").value = j.email || "";
      $("int-jira-project").value = j.project || "";
      $("int-gh-repo").value = g.repo || "";
      $("int-jira-token").value = "";
      $("int-gh-token").value = "";
      $("int-meta").textContent =
        "tracker=" + (data.effective_tracker || "—")
        + " · jira " + (j.configured ? "ready" : "incomplete")
        + " · github " + (g.configured ? "ready" : "incomplete")
        + " · " + (data.config_path || ".sdlc/integrations-config.json");
      applyIssuesPanels();
    }

    async function saveIntegrations() {
      $("int-status").textContent = "Saving…";
      $("int-status").className = "status-line";
      setBusy(["btn-int-save", "btn-int-refresh"], true);
      try {
        const payload = {
          target: target(),
          tracker: $("int-tracker").value,
          jira: {
            base_url: $("int-jira-url").value.trim(),
            email: $("int-jira-email").value.trim(),
            project: $("int-jira-project").value.trim(),
            api_token: $("int-jira-token").value.trim(),
          },
          github: {
            repo: $("int-gh-repo").value.trim(),
            token: $("int-gh-token").value.trim(),
          },
        };
        const res = await fetch("/api/integrations/save", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const data = await res.json();
        if (!res.ok) {
          $("int-status").textContent = data.error || "Save failed";
          $("int-status").className = "status-line bad";
          return;
        }
        $("int-status").textContent = "Saved.";
        $("int-status").className = "status-line ok";
        applyIssuesPanels();
        await loadIntegrations();
        await loadDashboard();
      } catch (err) {
        $("int-status").textContent = String(err);
        $("int-status").className = "status-line bad";
      } finally {
        setBusy(["btn-int-save", "btn-int-refresh"], false);
      }
    }

    function jiraBody(extra) {
      return Object.assign({
        target: target(),
        system: "jira",
        work_id: $("jira-work-id").value.trim(),
        issue_ref: $("jira-key").value.trim(),
        summary: $("jira-summary").value.trim(),
        issue_type: $("jira-issue-type").value.trim(),
      }, extra || {});
    }

    function ghBody(extra) {
      return Object.assign({
        target: target(),
        system: "github",
        work_id: $("gh-work-id").value.trim(),
        issue_ref: $("gh-number").value.trim(),
        title: $("gh-title").value.trim(),
        url: $("gh-url").value.trim(),
      }, extra || {});
    }

    function fillJiraStatus(data) {
      const bits = [];
      if (data.linked) bits.push("linked " + data.jira_key);
      else if (data.jira_draft) bits.push("Key not set (TBD)");
      else bits.push("not linked");
      if (data.canvas_source_issue) bits.push("canvas " + data.canvas_source_issue);
      if (data.registry_jira) bits.push("registry " + data.registry_jira);
      if (data.jira_url) bits.push(data.jira_url);
      $("jira-link-meta").textContent = bits.join(" · ") || "—";
      if (data.jira_key && !$("jira-key").value.trim()) {
        $("jira-key").value = data.jira_key;
      }
    }

    async function loadJiraStatus() {
      const workId = $("jira-work-id").value.trim();
      if (!workId) {
        $("jira-link-meta").textContent = "Enter a Work ID.";
        return;
      }
      const res = await fetch("/api/issues/status", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target: target(), work_id: workId, system: "jira" }),
      });
      const data = await res.json();
      if (!res.ok) {
        $("jira-link-meta").textContent = data.error || "Status failed";
        return;
      }
      fillJiraStatus(data);
    }

    async function linkJira(dryRun) {
      const workId = $("jira-work-id").value.trim();
      const jiraKey = $("jira-key").value.trim();
      if (!workId || !jiraKey) {
        $("jira-link-status").textContent = "Work ID and Jira key required.";
        $("jira-link-status").className = "status-line bad";
        return;
      }
      const label = dryRun ? "Preview link" : "Apply link";
      $("jira-link-status").textContent = label + "…";
      $("jira-link-status").className = "status-line";
      setBusy(["btn-jira-link", "btn-jira-link-dry", "btn-jira-refresh"], true);
      try {
        const res = await fetch("/api/issues/link", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(jiraBody({ dry_run: dryRun, apply: !dryRun })),
        });
        const data = await res.json();
        $("jira-link-log").textContent = JSON.stringify(data, null, 2);
        if (!res.ok) {
          $("jira-link-status").textContent = data.error || (label + " failed");
          $("jira-link-status").className = "status-line bad";
          return;
        }
        $("jira-link-status").textContent = dryRun
          ? "Preview OK — apply when ready."
          : "Linked " + jiraKey + " to " + workId;
        $("jira-link-status").className = "status-line ok";
        fillJiraStatus(data);
        if (!dryRun) await loadDashboard();
      } catch (err) {
        $("jira-link-status").textContent = String(err);
        $("jira-link-status").className = "status-line bad";
        $("jira-link-log").textContent = String(err);
      } finally {
        setBusy(["btn-jira-link", "btn-jira-link-dry", "btn-jira-refresh"], false);
      }
    }

    async function linkGithub(dryRun) {
      const workId = $("gh-work-id").value.trim();
      const num = $("gh-number").value.trim();
      if (!workId || !num) {
        $("gh-link-status").textContent = "Work ID and issue number required.";
        $("gh-link-status").className = "status-line bad";
        return;
      }
      const label = dryRun ? "Preview link" : "Apply link";
      $("gh-link-status").textContent = label + "…";
      setBusy(["btn-gh-link", "btn-gh-link-dry", "btn-gh-refresh"], true);
      try {
        const res = await fetch("/api/issues/link", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(ghBody({ dry_run: dryRun, apply: !dryRun })),
        });
        const data = await res.json();
        $("gh-link-log").textContent = JSON.stringify(data, null, 2);
        if (!res.ok) {
          $("gh-link-status").textContent = data.error || (label + " failed");
          $("gh-link-status").className = "status-line bad";
          return;
        }
        $("gh-link-status").textContent = dryRun ? "Preview OK" : ("Linked #" + num);
        $("gh-link-status").className = "status-line ok";
        if (!dryRun) await loadDashboard();
      } catch (err) {
        $("gh-link-status").textContent = String(err);
        $("gh-link-status").className = "status-line bad";
      } finally {
        setBusy(["btn-gh-link", "btn-gh-link-dry", "btn-gh-refresh"], false);
      }
    }

    async function syncIssues(direction, apply) {
      const system = activeTracker();
      const workId = activeWorkId();
      if (system === "none") {
        $("jira-sync-status").textContent = "Tracker is none — enable Jira or GitHub above.";
        $("jira-sync-status").className = "status-line bad";
        return;
      }
      if (!workId) {
        $("jira-sync-status").textContent = "Work ID required.";
        $("jira-sync-status").className = "status-line bad";
        return;
      }
      const verb = direction === "pull" ? "Pull" : "Push";
      const label = apply ? verb + " to server" : "Prepare " + direction;
      if (apply && !confirm("Sync " + direction + " for " + workId + " (" + system + ")?")) return;
      $("jira-sync-status").textContent = label + "…";
      setBusy(["btn-jira-pull", "btn-jira-pull-dry", "btn-jira-push", "btn-jira-push-dry"], true);
      try {
        const res = await fetch("/api/issues/sync", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ target: target(), work_id: workId, system, direction, apply }),
        });
        const data = await res.json();
        $("jira-sync-log").textContent = data.report || JSON.stringify(data, null, 2);
        $("jira-sync-cli").textContent = data.cli || "—";
        if (!res.ok) {
          $("jira-sync-status").textContent = data.error || (label + " failed");
          $("jira-sync-status").className = "status-line bad";
          return;
        }
        $("jira-sync-status").textContent = apply ? (verb + " OK") : (verb + " preview OK");
        $("jira-sync-status").className = "status-line ok";
      } catch (err) {
        $("jira-sync-status").textContent = String(err);
        $("jira-sync-log").textContent = String(err);
      } finally {
        setBusy(["btn-jira-pull", "btn-jira-pull-dry", "btn-jira-push", "btn-jira-push-dry"], false);
      }
    }

    async function syncJira(direction, apply) {
      syncIssues(direction, apply);
    }

    async function loadJira() {
      await loadIntegrations();
      const active = $("dw-id").textContent;
      if (active && active !== "(none)" && active !== "—") {
        if (!$("jira-work-id").value.trim()) $("jira-work-id").value = active;
        if (!$("gh-work-id").value.trim()) $("gh-work-id").value = active;
      }
      await loadJiraStatus();
    }

    async function refreshAll() {
      await detect();
      await Promise.all([loadDashboard(), loadPersist(), loadSqlite(), loadBackups(), loadGuide(), loadJira(), loadAdf()]);
      await loadAdfBrowse($("adf-browse-path").value.trim() || adfBrowsePath || "");
    }

    $("btn-detect").addEventListener("click", detect);
    $("btn-refresh-all").addEventListener("click", refreshAll);
    $("btn-dash-refresh").addEventListener("click", loadDashboard);
    document.querySelectorAll(".dash-configure").forEach((el) => {
      el.addEventListener("click", (e) => {
        e.preventDefault();
        gotoTab(el.dataset.gotoTab);
      });
    });
    $("btn-run").addEventListener("click", () => run());
    $("btn-verify").addEventListener("click", () => run("verify"));
    $("btn-clear").addEventListener("click", () => {
      $("log").textContent = "Awaiting action…";
      $("run-status").textContent = "Ready.";
      $("run-status").className = "status-line";
    });
    $("btn-persist-refresh").addEventListener("click", loadPersist);
    $("btn-persist-save").addEventListener("click", savePersist);
    $("btn-persist-parity").addEventListener("click", () => parityPersist(false));
    $("btn-persist-parity-repair").addEventListener("click", () => {
      if (!confirm("Repair re-derives projections (SQLite rebuild + Guide reproject) when parity drifts. Continue?")) return;
      parityPersist(true);
    });
    $("btn-sqlite-refresh").addEventListener("click", loadSqlite);
    $("btn-sqlite-rebuild").addEventListener("click", rebuildSqlite);
    $("btn-backups-refresh").addEventListener("click", loadBackups);
    $("btn-guide-save").addEventListener("click", saveGuide);
    $("btn-guide-probe").addEventListener("click", loadGuide);
    $("btn-guide-ensure").addEventListener("click", () => guideAction("/api/guide/ensure", { save_first: true }, "Ensure/pull guide"));
    $("btn-guide-profile").addEventListener("click", () => guideAction("/api/guide/ensure-profile", {}, "Write Embabel SPDD profile"));
    $("btn-neo-start").addEventListener("click", () => guideAction("/api/guide/neo4j/start", {}, "Start Neo4j"));
    $("btn-neo-stop").addEventListener("click", () => guideAction("/api/guide/neo4j/stop", {}, "Stop Neo4j"));
    $("btn-guide-start").addEventListener("click", () => guideAction("/api/guide/start", {}, "Start Guide + ingest"));
    $("btn-guide-start-noingest").addEventListener("click", () => guideAction("/api/guide/start", { no_ingest: true }, "Start Guide"));
    $("btn-proj-load").addEventListener("click", () => guideAction("/api/guide/projection/load", {}, "Load NamedEntity projection"));
    $("btn-guide-stop").addEventListener("click", () => guideAction("/api/guide/stop", {}, "Stop Guide"));
    $("btn-guide-stats").addEventListener("click", () => guideAction("/api/guide/stats", {}, "Guide stats"));
    $("btn-ingest-inc").addEventListener("click", () => {
      if (!confirm("Run incremental ingest via POST /api/v1/data/load-references? Guide must be up.")) return;
      guideAction("/api/guide/ingest", {}, "Incremental ingest");
    });
    $("btn-purge-preview").addEventListener("click", () => guideAction("/api/guide/purge/preview", {
      directory: $("op-directory").value.trim() || undefined,
      uri_prefix: $("op-uri-prefix").value.trim() || undefined,
    }, "Purge preview"));
    $("btn-purge").addEventListener("click", () => {
      const dir = $("op-directory").value.trim();
      const uri = $("op-uri-prefix").value.trim();
      if (!confirm(`Purge ContentElements for\\n${uri || dir || "(orchestrator root)"}\\n\\nThis deletes matching RAG chunks.`)) return;
      guideAction("/api/guide/purge", {
        confirm: true,
        directory: dir || undefined,
        uri_prefix: uri || undefined,
      }, "Purge ContentElements");
    });
    $("btn-git-reset").addEventListener("click", () => {
      const dir = $("op-directory").value.trim();
      if (!dir) { alert("Directory required for git revision reset"); return; }
      if (!confirm(`Reset git-ingestion revision for\\n${dir}\\n\\nNext ingest will re-scan the full tree.`)) return;
      guideAction("/api/guide/git-revision/reset", { directory: dir }, "Reset git revision");
    });
    $("btn-purge-all-rag").addEventListener("click", () => {
      if (!confirm("WIPE ALL ContentElement RAG nodes in embabel-neo4j via docker cypher-shell?\\n\\nTyped __Entity__ projection nodes are NOT deleted by this.")) return;
      if (!confirm("Type-confirm: really purge ALL RAG chunks?")) return;
      guideAction("/api/guide/purge-all-rag", { confirm: true }, "Purge ALL RAG");
    });
    $("btn-adf-refresh").addEventListener("click", loadAdf);
    $("btn-adf-start").addEventListener("click", () => adfAction("/api/adf/start", "Start viewer"));
    $("btn-adf-stop").addEventListener("click", () => adfAction("/api/adf/stop", "Stop viewer"));
    $("btn-adf-restart").addEventListener("click", () => adfAction("/api/adf/restart", "Restart viewer"));
    $("btn-adf-open").addEventListener("click", openAdfViewer);
    $("btn-adf-browse").addEventListener("click", () => loadAdfBrowse($("adf-browse-path").value.trim()));
    $("btn-adf-browse-home").addEventListener("click", () => loadAdfBrowse(adfHome || target()));
    $("btn-adf-browse-adf").addEventListener("click", () => loadAdfBrowse(adfDir || (target() + "/adf")));
    $("btn-adf-init-dry").addEventListener("click", () => initFromAdf(true));
    $("btn-adf-init").addEventListener("click", () => initFromAdf(false));
    $("adf-browse-path").addEventListener("keydown", (e) => {
      if (e.key === "Enter") loadAdfBrowse($("adf-browse-path").value.trim());
    });
    $("btn-int-refresh").addEventListener("click", loadIntegrations);
    $("btn-int-save").addEventListener("click", saveIntegrations);
    $("int-tracker").addEventListener("change", applyIssuesPanels);
    $("btn-jira-refresh").addEventListener("click", loadJiraStatus);
    $("btn-jira-link-dry").addEventListener("click", () => linkJira(true));
    $("btn-jira-link").addEventListener("click", () => linkJira(false));
    $("btn-gh-link-dry").addEventListener("click", () => linkGithub(true));
    $("btn-gh-link").addEventListener("click", () => linkGithub(false));
    $("btn-jira-pull-dry").addEventListener("click", () => syncIssues("pull", false));
    $("btn-jira-pull").addEventListener("click", () => syncIssues("pull", true));
    $("btn-jira-push-dry").addEventListener("click", () => syncIssues("push", false));
    $("btn-jira-push").addEventListener("click", () => syncIssues("push", true));
    $("jira-work-id").addEventListener("change", loadJiraStatus);
    $("jira-work-id").addEventListener("keydown", (e) => {
      if (e.key === "Enter") loadJiraStatus();
    });
    $("as-all").addEventListener("change", () => {
      if ($("as-all").checked) {
        $("as-cursor").checked = true;
        $("as-copilot").checked = true;
        $("as-claude").checked = true;
      }
    });
    $("target").addEventListener("keydown", (e) => { if (e.key === "Enter") refreshAll(); });
    refreshAll();
  </script>
</body>
</html>
"""
