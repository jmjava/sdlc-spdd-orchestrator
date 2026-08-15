<script setup>
import { onMounted, ref } from "vue";
import { postJson } from "../api.js";

const props = defineProps({
  target: { type: String, default: "" },
});

const emit = defineEmits(["goto-tab"]);

const loading = ref(false);
const statusText = ref("Ready.");
const statusClass = ref("");
const suggestions = ref([]);
const activity = ref([]);
const work = ref({
  pointer: "",
  phase: "",
  operation: "",
  recommended_command: "",
  open_gates: [],
});
const memory = ref({
  accepted_count: "—",
  staged_count: "—",
  ledger_path: "",
  staged_path: "",
  last_accepted_ts: "",
});
const backends = ref({
  enabled: {},
  sqlite: {},
  guide: {},
  source: "",
  parity_hint: "",
});
const integrations = ref({
  jira: {},
  github: {},
  tracker: "",
  viewer: {},
});

function sqliteLabel() {
  const en = backends.value.enabled || {};
  const sqlite = backends.value.sqlite || {};
  if (!en.sqlite) return "OFF";
  return sqlite.exists ? "READY" : "ON";
}

function guideLabel() {
  const guide = backends.value.guide || {};
  if (!guide.enabled) return "OFF";
  return guide.reachable ? "UP" : "DOWN";
}

function openWork(tab, workId) {
  const id = String(workId || work.value.pointer || "").trim();
  emit("goto-tab", id ? { tab, workId: id } : tab);
}

function openSuggestion(item) {
  openWork(item?.tab || "sqlite", item?.work_id || work.value.pointer || "");
}

function integrationLines() {
  const jira = integrations.value.jira || {};
  const gh = integrations.value.github || {};
  const viewer = integrations.value.viewer || {};
  return [
    `Tracker: ${integrations.value.tracker || "—"}`,
    `Jira: ${jira.configured ? "ready" : "not configured"}`,
    `GitHub: ${gh.authenticated || gh.configured ? "ready" : "not authenticated"}`,
    `ADF viewer: ${viewer.running ? "running" : "stopped"}${viewer.url ? ` · ${viewer.url}` : ""}`,
  ];
}

async function refresh() {
  loading.value = true;
  statusClass.value = "";
  statusText.value = "Loading…";
  try {
    const body = { target: props.target };
    const [statusRes, activityRes, suggestRes] = await Promise.all([
      postJson("/api/dashboard/status", body),
      postJson("/api/dashboard/activity", { ...body, limit: 20 }),
      postJson("/api/dashboard/suggestions", body),
    ]);
    if (!statusRes.ok) {
      statusClass.value = "err";
      statusText.value = statusRes.data?.error || `Status failed (${statusRes.status})`;
      return;
    }
    work.value = statusRes.data.work || work.value;
    memory.value = statusRes.data.memory || memory.value;
    backends.value = statusRes.data.backends || backends.value;
    integrations.value = statusRes.data.integrations || integrations.value;
    activity.value = activityRes.data?.items || [];
    suggestions.value = suggestRes.data?.suggestions || [];
    statusClass.value = "ok";
    statusText.value = "Loaded.";
  } catch (err) {
    statusClass.value = "err";
    statusText.value = String(err?.message || err);
  } finally {
    loading.value = false;
  }
}

onMounted(refresh);
</script>

<template>
  <div data-testid="dashboard-panel">
    <section class="panel">
      <h2>Today</h2>
      <p class="lead">
        Deterministic suggested actions from the ledger, registry, workflow state, and config — no LLM.
      </p>
      <ul class="check-list" data-testid="dash-suggestions">
        <li v-if="!suggestions.length && statusText === 'Ready.'">Refresh to load.</li>
        <li v-else-if="!suggestions.length">
          <span class="mark ok">OK</span>
          <span>Nothing pending — all caught up.</span>
        </li>
        <li v-for="item in suggestions" :key="item.id" :data-suggestion-id="item.id">
          <span class="mark">[ ]</span>
          <button
            class="suggestion-link"
            type="button"
            :data-testid="`dash-suggestion-${item.id}`"
            @click="openSuggestion(item)"
          >
            {{ item.text }}
          </button>
        </li>
      </ul>
      <div class="actions">
        <button
          class="btn btn-secondary"
          type="button"
          data-testid="btn-dash-refresh"
          :disabled="loading"
          @click="refresh"
        >
          Refresh dashboard
        </button>
      </div>
      <p class="status" :class="statusClass" data-testid="dash-status">{{ statusText }}</p>
    </section>

    <section class="panel">
      <h2>Active work</h2>
      <div class="stats" data-testid="dash-work-stats">
        <div class="stat-card">
          <button
            class="n work-id-link"
            type="button"
            data-testid="dw-id"
            :disabled="!work.pointer"
            @click="openWork('sqlite', work.pointer)"
          >
            {{ work.pointer || "(none)" }}
          </button>
          <div class="l">work id</div>
        </div>
        <div class="stat-card">
          <div class="n" data-testid="dw-phase">{{ work.phase || "—" }}</div>
          <div class="l">phase</div>
        </div>
        <div class="stat-card">
          <div class="n" data-testid="dw-gates">{{ (work.open_gates || []).length }}</div>
          <div class="l">open gates</div>
        </div>
        <div class="stat-card">
          <div class="n" data-testid="dw-op">{{ work.operation || "—" }}</div>
          <div class="l">next op</div>
        </div>
      </div>
      <h3>Do now</h3>
      <pre class="cmd" data-testid="dash-work-cmd">{{ work.recommended_command || "—" }}</pre>
      <ul class="check-list" data-testid="dash-work-gates">
        <li v-for="gate in work.open_gates || []" :key="gate.gate">
          {{ gate.label || gate.gate }}
        </li>
      </ul>
      <div class="actions" v-if="work.pointer">
        <button class="btn btn-secondary" type="button" data-testid="dash-open-sqlite" @click="openWork('sqlite', work.pointer)">
          Open in SQLite
        </button>
        <button class="btn btn-ghost" type="button" data-testid="dash-open-templates" @click="openWork('templates', work.pointer)">
          Templates
        </button>
        <button class="btn btn-ghost" type="button" data-testid="dash-open-issues" @click="openWork('issues', work.pointer)">
          Issues
        </button>
        <button class="btn btn-ghost" type="button" data-testid="dash-open-adf" @click="openWork('adf', work.pointer)">
          ADF
        </button>
      </div>
      <p class="meta">Claim/advance from the terminal: <code>./scripts/sdlc.sh next</code></p>
    </section>

    <section class="panel">
      <h2>Memory &amp; backends</h2>
      <div class="stats" data-testid="dash-memory-stats">
        <div class="stat-card">
          <div class="n" data-testid="dm-accepted">{{ memory.accepted_count }}</div>
          <div class="l">accepted</div>
        </div>
        <div class="stat-card">
          <div class="n" data-testid="dm-staged">{{ memory.staged_count }}</div>
          <div class="l">staged</div>
        </div>
        <div class="stat-card">
          <div class="n" data-testid="db-sqlite">{{ sqliteLabel() }}</div>
          <div class="l">sqlite cache</div>
        </div>
        <div class="stat-card">
          <div class="n" data-testid="db-guide">{{ guideLabel() }}</div>
          <div class="l">guide</div>
        </div>
      </div>
      <p class="meta" data-testid="dash-memory-meta">
        ledger {{ memory.ledger_path || "—" }}
        · staged {{ memory.staged_path || "—" }}
        <template v-if="memory.last_accepted_ts"> · last accepted {{ memory.last_accepted_ts }}</template>
      </p>
      <p class="meta" data-testid="dash-backends-meta">
        {{ backends.parity_hint || "Run parity from the Persistence tab." }}
      </p>
      <div class="actions">
        <button class="btn btn-secondary" type="button" data-testid="dash-goto-persistence" @click="emit('goto-tab', 'persistence')">
          Configure → Persistence
        </button>
        <button class="btn btn-ghost" type="button" data-testid="dash-goto-sqlite" @click="openWork('sqlite', work.pointer)">
          Configure → SQLite
        </button>
        <button class="btn btn-ghost" type="button" data-testid="dash-goto-guide" @click="emit('goto-tab', 'guide')">
          Configure → Guide
        </button>
      </div>
    </section>

    <section class="panel">
      <h2>Integrations</h2>
      <ul class="check-list" data-testid="dash-integrations">
        <li v-for="line in integrationLines()" :key="line">{{ line }}</li>
      </ul>
      <div class="actions">
        <button class="btn btn-ghost" type="button" data-testid="dash-goto-issues" @click="openWork('issues', work.pointer)">
          Configure → Issues
        </button>
        <button class="btn btn-ghost" type="button" data-testid="dash-goto-adf" @click="openWork('adf', work.pointer)">
          Configure → ADF / Viewer
        </button>
      </div>
    </section>

    <section class="panel">
      <h2>Recent activity — catch up here</h2>
      <ul class="feed-list" data-testid="dash-activity">
        <li v-if="!activity.length">
          <span class="src">—</span>
          <span>{{ statusText === 'Ready.' ? 'Refresh to load.' : 'No activity yet (fresh install).' }}</span>
        </li>
        <li v-for="(item, idx) in activity" :key="idx">
          <span class="src">{{ item.source }}</span>
          <span>
            {{ item.text }}
            <button
              v-if="item.work_id"
              class="suggestion-link"
              type="button"
              data-testid="dash-activity-work"
              @click="openWork('sqlite', item.work_id)"
            >
              {{ item.work_id }}
            </button>
            <span class="hint">{{ item.ts }}</span>
          </span>
        </li>
      </ul>
    </section>
  </div>
</template>
