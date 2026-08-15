<script setup>
import { onMounted, ref } from "vue";
import { postJson } from "../api.js";

const props = defineProps({
  target: { type: String, default: "" },
});

const guideHome = ref("");
const guideGit = ref("https://github.com/jmjava/guide.git");
const guideRef = ref("");
const guideProfile = ref("");
const guideHost = ref("127.0.0.1");
const guidePort = ref(21337);
const guideMcp = ref("embabel-dev");
const neoBolt = ref(7687);
const neoHttp = ref(7474);
const neoHttps = ref(7473);
const neoUser = ref("neo4j");
const neoPass = ref("");
const guideNotes = ref("");

const stGuide = ref("—");
const stNeo = ref("—");
const stPid = ref("—");
const stPort = ref("—");
const stChunks = ref("—");
const stWorkIds = ref("—");
const stCanvases = ref("—");
const stAreas = ref("—");
const guideProbe = ref("Status not loaded.");
const actionStatus = ref("Ready.");
const actionStatusClass = ref("");
const actionLog = ref("No runtime action yet.");
const busy = ref(false);
const opDirectory = ref("");
const opUriPrefix = ref("");
const formTouched = ref(false);

function markFormTouched() {
  formTouched.value = true;
}

function formBody(extra = {}) {
  return {
    target: props.target,
    guide_home: guideHome.value,
    guide_git_url: guideGit.value,
    guide_git_ref: guideRef.value,
    profile: guideProfile.value,
    host: guideHost.value,
    port: Number(guidePort.value || 21337),
    neo4j_bolt_port: Number(neoBolt.value || 7687),
    neo4j_http_port: Number(neoHttp.value || 7474),
    neo4j_https_port: Number(neoHttps.value || 7473),
    neo4j_username: neoUser.value,
    neo4j_password: neoPass.value,
    mcp_server: guideMcp.value,
    notes: guideNotes.value,
    ...extra,
  };
}

function checklistText(items) {
  if (!items?.length) return "";
  return items
    .map((it) => `${it.ok ? "OK" : "!!"} ${it.label}${it.hint ? ` — ${it.hint}` : ""}`)
    .join("\n");
}

function applyGuide(data, { forceForm = false } = {}) {
  const cfg = data?.config || {};
  if (forceForm || !formTouched.value) {
    guideHome.value = cfg.guide_home || "";
    guideGit.value = cfg.guide_git_url || "https://github.com/jmjava/guide.git";
    guideRef.value = cfg.guide_git_ref || "";
    guideProfile.value = cfg.profile || "";
    guideHost.value = cfg.host || "127.0.0.1";
    guidePort.value = cfg.port || 21337;
    guideMcp.value = cfg.mcp_server || "embabel-dev";
    neoBolt.value = cfg.neo4j_bolt_port || 7687;
    neoHttp.value = cfg.neo4j_http_port || 7474;
    neoHttps.value = cfg.neo4j_https_port || 7473;
    neoUser.value = cfg.neo4j_username || "neo4j";
    if (cfg.neo4j_password) neoPass.value = cfg.neo4j_password;
    guideNotes.value = cfg.notes || "";
  }

  const probe = data?.probe || {};
  const neo = data?.neo4j || {};
  const gp = data?.stack?.guide_process || data?.runtime?.guide_process || {};
  stGuide.value = probe.tcp_open ? "UP" : "DOWN";
  stNeo.value = neo.bolt_open ? "UP" : "DOWN";
  stPid.value = gp.pid || "—";
  stPort.value = cfg.port || "—";

  const gs = data?.guide_stats?.data || {};
  const chunkCount =
    gs.contentElementCount ?? gs.contentElements ?? gs.chunkCount ?? gs.totalContentElements;
  stChunks.value = chunkCount != null ? String(chunkCount) : "—";
  const pd = data?.projection?.data || {};
  stWorkIds.value = pd.workIdCount != null ? String(pd.workIdCount) : "—";
  stCanvases.value = pd.canvasCount != null ? String(pd.canvasCount) : "—";
  stAreas.value = pd.areaCount != null ? String(pd.areaCount) : "—";
  const dirs = data?.operator_directories || [];
  if (!opDirectory.value && dirs[0]) opDirectory.value = dirs[0];

  guideProbe.value =
    (probe.tcp_open
      ? `Guide UP at ${probe.host}:${probe.port} · SSE ${probe.sse_url}`
      : `Guide DOWN at ${probe.host || guideHost.value}:${probe.port || guidePort.value}`) +
    " · " +
    (neo.bolt_open
      ? `Neo4j Bolt UP ${neo.bolt_url} · browser ${neo.browser_url}`
      : `Neo4j Bolt DOWN :${neo.bolt_port || "?"}`) +
    (gp.log_path ? ` · log ${gp.log_path}` : "");

  const checks = [
    checklistText(data?.embabel_mechanics),
    checklistText(data?.checklist),
  ]
    .filter(Boolean)
    .join("\n\n");
  if (checks) {
    actionLog.value = checks;
  }
}

async function loadGuide({ forceForm = false } = {}) {
  try {
    const { data } = await postJson("/api/guide", { target: props.target });
    applyGuide(data, { forceForm });
  } catch (err) {
    actionStatusClass.value = "err";
    actionStatus.value = String(err?.message || err);
    actionLog.value = String(err);
  }
}

async function saveGuide() {
  busy.value = true;
  try {
    const { ok, data } = await postJson("/api/guide/save", formBody());
    applyGuide(data, { forceForm: true });
    formTouched.value = false;
    actionStatus.value = ok ? "Config saved." : data?.error || "Save failed";
    actionStatusClass.value = ok ? "ok" : "err";
    actionLog.value = JSON.stringify(data, null, 2);
  } catch (err) {
    actionStatusClass.value = "err";
    actionStatus.value = String(err?.message || err);
    actionLog.value = String(err);
  } finally {
    busy.value = false;
  }
}

async function guideAction(url, extra, label) {
  busy.value = true;
  actionStatus.value = `${label}…`;
  actionStatusClass.value = "";
  try {
    const { ok, data } = await postJson(url, formBody(extra));
    applyGuide(data);
    const detail = data?.ensure || data?.result || data;
    actionLog.value = JSON.stringify(detail, null, 2);
    if (ok) {
      actionStatus.value = `${label} OK`;
      actionStatusClass.value = "ok";
    } else {
      actionStatus.value = String(detail?.error || detail?.log || `${label} failed`).slice(0, 200);
      actionStatusClass.value = "err";
    }
    await loadGuide();
  } catch (err) {
    actionStatusClass.value = "err";
    actionStatus.value = String(err?.message || err);
    actionLog.value = String(err);
  } finally {
    busy.value = false;
  }
}

function confirmPurge() {
  const dir = opDirectory.value.trim();
  const uri = opUriPrefix.value.trim();
  const scope = uri || dir || "(orchestrator root)";
  if (
    !window.confirm(
      `Purge ContentElements for\n${scope}\n\nThis deletes matching RAG chunks.`,
    )
  ) {
    return;
  }
  guideAction(
    "/api/guide/purge",
    { confirm: true, directory: dir || undefined, uri_prefix: uri || undefined },
    "Purge ContentElements",
  );
}

function confirmGitReset() {
  const dir = opDirectory.value.trim();
  if (!dir) {
    window.alert("Directory required for git revision reset");
    return;
  }
  if (
    !window.confirm(
      `Reset git-ingestion revision for\n${dir}\n\nNext ingest will re-scan the full tree.`,
    )
  ) {
    return;
  }
  guideAction("/api/guide/git-revision/reset", { directory: dir }, "Reset git revision");
}

function confirmPurgeAllRag() {
  if (
    !window.confirm(
      "WIPE ALL ContentElement RAG nodes in embabel-neo4j via docker cypher-shell?\n\nTyped __Entity__ projection nodes are NOT deleted by this.",
    )
  ) {
    return;
  }
  if (!window.confirm("Type-confirm: really purge ALL RAG chunks?")) {
    return;
  }
  guideAction("/api/guide/purge-all-rag", { confirm: true }, "Purge ALL RAG");
}

onMounted(loadGuide);
</script>

<template>
  <section class="panel" data-testid="guide-panel" @input="markFormTouched">
    <h2>Embabel Guide + Neo4j</h2>
    <p class="lead">
      Pulls from <code>jmjava/guide</code>, starts Compose Neo4j and Guide on custom ports.
      Config: <code>.sdlc/guide-config.json</code>.
    </p>

    <div class="field-row">
      <label>
        Guide home
        <input v-model="guideHome" data-testid="guide-home" type="text" spellcheck="false" />
      </label>
      <label>
        Git URL
        <input v-model="guideGit" data-testid="guide-git" type="text" spellcheck="false" />
      </label>
    </div>

    <div class="field-row">
      <label>
        Git ref
        <input
          v-model="guideRef"
          data-testid="guide-ref"
          type="text"
          spellcheck="false"
          placeholder="sdlc-spdd-projection-v1"
        />
      </label>
      <label>
        Profile
        <input v-model="guideProfile" data-testid="guide-profile" type="text" spellcheck="false" />
      </label>
      <label>
        Guide host
        <input v-model="guideHost" data-testid="guide-host" type="text" spellcheck="false" />
      </label>
      <label>
        Guide port
        <input v-model.number="guidePort" data-testid="guide-port" type="number" />
      </label>
      <label>
        MCP server id
        <input v-model="guideMcp" data-testid="guide-mcp" type="text" spellcheck="false" />
      </label>
    </div>

    <div class="field-row">
      <label>
        Neo4j Bolt
        <input v-model.number="neoBolt" data-testid="neo-bolt" type="number" />
      </label>
      <label>
        Neo4j HTTP
        <input v-model.number="neoHttp" data-testid="neo-http" type="number" />
      </label>
      <label>
        Neo4j HTTPS
        <input v-model.number="neoHttps" data-testid="neo-https" type="number" />
      </label>
      <label>
        Neo4j user
        <input v-model="neoUser" data-testid="neo-user" type="text" spellcheck="false" />
      </label>
      <label>
        Neo4j password
        <input v-model="neoPass" data-testid="neo-pass" type="password" autocomplete="off" />
      </label>
    </div>

    <label>
      Notes
      <textarea v-model="guideNotes" data-testid="guide-notes"></textarea>
    </label>

    <div class="actions">
      <button
        class="btn btn-primary"
        type="button"
        data-testid="btn-guide-save"
        :disabled="busy"
        @click="saveGuide"
      >
        Save config
      </button>
      <button
        class="btn btn-secondary"
        type="button"
        data-testid="btn-guide-probe"
        :disabled="busy"
        @click="loadGuide({ forceForm: true })"
      >
        Refresh status
      </button>
      <button
        class="btn btn-secondary"
        type="button"
        data-testid="btn-guide-ensure"
        :disabled="busy"
        @click="guideAction('/api/guide/ensure', { save_first: true }, 'Ensure/pull guide')"
      >
        Ensure / pull
      </button>
      <button
        class="btn btn-secondary"
        type="button"
        data-testid="btn-guide-profile"
        :disabled="busy"
        @click="guideAction('/api/guide/ensure-profile', {}, 'Write Embabel SPDD profile')"
      >
        Write profile
      </button>
      <button
        class="btn btn-secondary"
        type="button"
        data-testid="btn-neo-start"
        :disabled="busy"
        @click="guideAction('/api/guide/neo4j/start', {}, 'Start Neo4j')"
      >
        Start Neo4j
      </button>
      <button
        class="btn btn-ghost"
        type="button"
        data-testid="btn-neo-stop"
        :disabled="busy"
        @click="guideAction('/api/guide/neo4j/stop', {}, 'Stop Neo4j')"
      >
        Stop Neo4j
      </button>
      <button
        class="btn btn-primary"
        type="button"
        data-testid="btn-guide-start"
        :disabled="busy"
        @click="guideAction('/api/guide/start', {}, 'Start Guide + ingest')"
      >
        Start Guide (+ingest)
      </button>
      <button
        class="btn btn-secondary"
        type="button"
        data-testid="btn-guide-start-noingest"
        :disabled="busy"
        @click="guideAction('/api/guide/start', { no_ingest: true }, 'Start Guide')"
      >
        Start Guide (no ingest)
      </button>
      <button
        class="btn btn-primary"
        type="button"
        data-testid="btn-proj-load"
        :disabled="busy"
        @click="guideAction('/api/guide/projection/load', {}, 'Load NamedEntity projection')"
      >
        Load projection
      </button>
      <button
        class="btn btn-warn"
        type="button"
        data-testid="btn-guide-stop"
        :disabled="busy"
        @click="guideAction('/api/guide/stop', {}, 'Stop Guide')"
      >
        Stop Guide
      </button>
    </div>

    <div class="stats">
      <div class="stat-card">
        <div class="n" data-testid="st-guide">{{ stGuide }}</div>
        <div class="l">guide</div>
      </div>
      <div class="stat-card">
        <div class="n" data-testid="st-neo">{{ stNeo }}</div>
        <div class="l">neo4j bolt</div>
      </div>
      <div class="stat-card">
        <div class="n" data-testid="st-pid">{{ stPid }}</div>
        <div class="l">guide pid</div>
      </div>
      <div class="stat-card">
        <div class="n" data-testid="st-port">{{ stPort }}</div>
        <div class="l">guide port</div>
      </div>
    </div>

    <div class="meta" data-testid="guide-probe">{{ guideProbe }}</div>
    <p class="status" :class="actionStatusClass" data-testid="guide-action-status">
      {{ actionStatus }}
    </p>
    <pre class="log" data-testid="guide-action-log">{{ actionLog }}</pre>

    <h3>Neo4j / ingest operators</h3>
    <p class="lead">Requires Guide running. Purge stays explicit (preview first).</p>
    <div class="field-row">
      <label>
        Directory (purge / git-reset scope)
        <input
          v-model="opDirectory"
          type="text"
          spellcheck="false"
          data-testid="op-directory"
          placeholder="orchestrator root or subdir"
        />
      </label>
      <label>
        Or URI prefix (≥ 8 chars)
        <input
          v-model="opUriPrefix"
          type="text"
          spellcheck="false"
          data-testid="op-uri-prefix"
          placeholder="file:/… or https://…"
        />
      </label>
    </div>
    <div class="actions">
      <button
        class="btn btn-secondary"
        type="button"
        data-testid="btn-guide-stats"
        :disabled="busy"
        @click="guideAction('/api/guide/stats', {}, 'Refresh Guide stats')"
      >
        Refresh Guide stats
      </button>
      <button
        class="btn btn-primary"
        type="button"
        data-testid="btn-ingest-inc"
        :disabled="busy"
        @click="guideAction('/api/guide/ingest', {}, 'Incremental ingest')"
      >
        Incremental ingest
      </button>
      <button
        class="btn btn-secondary"
        type="button"
        data-testid="btn-purge-preview"
        :disabled="busy"
        @click="
          guideAction(
            '/api/guide/purge/preview',
            { directory: opDirectory, uri_prefix: opUriPrefix },
            'Purge preview',
          )
        "
      >
        Purge preview
      </button>
      <button
        class="btn btn-warn"
        type="button"
        data-testid="btn-purge"
        :disabled="busy"
        @click="confirmPurge"
      >
        Purge ContentElements
      </button>
      <button
        class="btn btn-secondary"
        type="button"
        data-testid="btn-git-reset"
        :disabled="busy"
        @click="confirmGitReset"
      >
        Reset git revision
      </button>
      <button
        class="btn btn-warn"
        type="button"
        data-testid="btn-purge-all-rag"
        :disabled="busy"
        @click="confirmPurgeAllRag"
      >
        Purge ALL RAG
      </button>
    </div>
    <div class="stats">
      <div class="stat-card">
        <div class="n" data-testid="st-chunks">{{ stChunks }}</div>
        <div class="l">content elements</div>
      </div>
      <div class="stat-card">
        <div class="n" data-testid="st-workids">{{ stWorkIds }}</div>
        <div class="l">WorkId entities</div>
      </div>
      <div class="stat-card">
        <div class="n" data-testid="st-canvases">{{ stCanvases }}</div>
        <div class="l">Canvas entities</div>
      </div>
      <div class="stat-card">
        <div class="n" data-testid="st-areas">{{ stAreas }}</div>
        <div class="l">Area entities</div>
      </div>
    </div>
  </section>
</template>
