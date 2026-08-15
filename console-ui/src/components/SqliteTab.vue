<script setup>
import { onMounted, ref } from "vue";
import { postJson } from "../api.js";

const props = defineProps({
  target: { type: String, default: "" },
});

const emit = defineEmits(["open-work"]);

const workItems = ref("—");
const artifacts = ref("—");
const localSessions = ref("—");
const fts = ref("—");
const meta = ref("Not loaded.");
const breakdown = ref("—");
const rows = ref([]);
const query = ref("");
const statusFilter = ref("");
const loading = ref(false);
const statusText = ref("");
const statusClass = ref("");

async function loadStatus() {
  if (!props.target.trim()) return;
  loading.value = true;
  statusText.value = "";
  try {
    const { ok, data } = await postJson("/api/sqlite/status", { target: props.target });
    if (!ok && data?.error && !data.path) {
      meta.value = data.error;
      statusClass.value = "err";
      statusText.value = data.error;
      return;
    }
    workItems.value = data.exists ? String(data.work_items) : "0";
    artifacts.value = data.exists ? String(data.artifacts) : "0";
    localSessions.value = data.exists ? String(data.local_sessions) : "0";
    fts.value = data.fts || "—";
    meta.value = data.exists
      ? `${data.path} · rebuilt ${data.rebuilt_at || "?"} · commit ${data.source_commit || "?"}`
      : `Missing: ${data.path || "(unknown)"} — rebuild to create.`;
    const br = data.by_registry_status || {};
    const keys = Object.keys(br);
    breakdown.value = keys.length ? keys.map((k) => `${k}: ${br[k]}`).join(" · ") : "(none)";
    statusClass.value = "ok";
    statusText.value = "SQLite status loaded.";
    await loadWorks();
  } catch (err) {
    statusClass.value = "err";
    statusText.value = String(err?.message || err);
    meta.value = statusText.value;
  } finally {
    loading.value = false;
  }
}

async function loadWorks() {
  if (!props.target.trim()) return;
  const { ok, data } = await postJson("/api/sqlite/works", {
    target: props.target,
    q: query.value.trim(),
    status: statusFilter.value.trim(),
    limit: 100,
  });
  if (!ok && data?.error) {
    statusClass.value = "err";
    statusText.value = data.error;
    rows.value = [];
    return;
  }
  rows.value = data.works || [];
  if (data.exists === false) {
    statusText.value = "Index missing — rebuild to browse works.";
  } else {
    statusText.value = `${rows.value.length} work(s)`;
    statusClass.value = "ok";
  }
}

async function rebuild() {
  loading.value = true;
  try {
    const { ok, data } = await postJson("/api/sqlite/rebuild", { target: props.target });
    if (!ok) {
      statusClass.value = "err";
      statusText.value = data?.error || "Rebuild failed";
      meta.value = statusText.value;
      return;
    }
    await loadStatus();
    statusClass.value = "ok";
    statusText.value = "Index rebuilt.";
  } catch (err) {
    statusClass.value = "err";
    statusText.value = String(err?.message || err);
  } finally {
    loading.value = false;
  }
}

function openWork(workId, tab) {
  emit("open-work", { tab, workId });
}

onMounted(loadStatus);
</script>

<template>
  <section class="panel" data-testid="sqlite-panel">
    <h2>Local SQLite index</h2>
    <p class="lead">
      Regenerable cache under <code>.sdlc/index.sqlite</code>. Filter the work list and jump to
      Templates, Issues, or ADF. Git remains source of truth.
    </p>
    <div class="stats" data-testid="sqlite-stats">
      <div class="stat-card"><div class="n" data-testid="sq-work">{{ workItems }}</div><div class="l">work items</div></div>
      <div class="stat-card"><div class="n" data-testid="sq-art">{{ artifacts }}</div><div class="l">artifacts</div></div>
      <div class="stat-card"><div class="n" data-testid="sq-local">{{ localSessions }}</div><div class="l">local sessions</div></div>
      <div class="stat-card"><div class="n" data-testid="sq-fts">{{ fts }}</div><div class="l">fts mode</div></div>
    </div>
    <p class="meta" data-testid="sqlite-meta">{{ meta }}</p>
    <div class="actions">
      <button class="btn btn-secondary" type="button" data-testid="btn-sqlite-refresh" :disabled="loading" @click="loadStatus">
        Refresh
      </button>
      <button class="btn btn-primary" type="button" data-testid="btn-sqlite-rebuild" :disabled="loading" @click="rebuild">
        Rebuild index
      </button>
    </div>
    <p class="status" :class="statusClass" data-testid="sqlite-status">{{ statusText }}</p>
    <h3>Registry breakdown</h3>
    <p class="meta" data-testid="sqlite-breakdown">{{ breakdown }}</p>
    <h3>Work browser</h3>
    <div class="field-row">
      <label>
        Search
        <input
          v-model="query"
          type="search"
          spellcheck="false"
          placeholder="Work ID, title, Jira, GitHub…"
          data-testid="sqlite-filter"
          @keydown.enter="loadWorks"
        />
      </label>
      <label>
        Status
        <input
          v-model="statusFilter"
          type="text"
          spellcheck="false"
          placeholder="registry / canvas status"
          data-testid="sqlite-status-filter"
          @keydown.enter="loadWorks"
        />
      </label>
    </div>
    <div class="actions">
      <button class="btn btn-secondary" type="button" data-testid="sqlite-filter-apply" :disabled="loading" @click="loadWorks">
        Apply filter
      </button>
    </div>
    <div class="table-wrap">
      <table data-testid="sqlite-table">
        <thead>
          <tr>
            <th>Work ID</th>
            <th>Status</th>
            <th>Canvas</th>
            <th>Jira</th>
            <th>GitHub</th>
            <th>Title</th>
            <th>Open</th>
          </tr>
        </thead>
        <tbody data-testid="sqlite-rows">
          <tr v-if="!rows.length"><td colspan="7">Refresh or rebuild to load.</td></tr>
          <tr v-for="r in rows" :key="r.work_id" :data-work-id="r.work_id">
            <td><code>{{ r.work_id }}</code></td>
            <td>{{ r.registry_status }}</td>
            <td>{{ r.canvas_status }}</td>
            <td>{{ r.jira_key }}</td>
            <td>{{ r.github_number }}</td>
            <td>{{ r.title }}</td>
            <td class="row-actions">
              <button class="btn btn-ghost" type="button" data-testid="sqlite-open-templates" @click="openWork(r.work_id, 'templates')">
                Templates
              </button>
              <button class="btn btn-ghost" type="button" data-testid="sqlite-open-issues" @click="openWork(r.work_id, 'issues')">
                Issues
              </button>
              <button class="btn btn-ghost" type="button" data-testid="sqlite-open-adf" @click="openWork(r.work_id, 'adf')">
                ADF
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
