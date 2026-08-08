<script setup>
import { onMounted, ref } from "vue";
import { postJson } from "../api.js";

const props = defineProps({
  target: { type: String, default: "" },
});

const workItems = ref("—");
const artifacts = ref("—");
const localSessions = ref("—");
const fts = ref("—");
const meta = ref("Not loaded.");
const breakdown = ref("—");
const rows = ref([]);
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
    rows.value = data.recent || [];
    statusClass.value = "ok";
    statusText.value = "SQLite status loaded.";
  } catch (err) {
    statusClass.value = "err";
    statusText.value = String(err?.message || err);
    meta.value = statusText.value;
  } finally {
    loading.value = false;
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

onMounted(loadStatus);
</script>

<template>
  <section class="panel" data-testid="sqlite-panel">
    <h2>Local SQLite index</h2>
    <p class="lead">
      Regenerable cache under <code>.sdlc/index.sqlite</code>. Git remains source of truth.
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
    <h3>Sample work items</h3>
    <div class="table-wrap">
      <table data-testid="sqlite-table">
        <thead>
          <tr><th>Work ID</th><th>Status</th><th>Canvas</th><th>Jira</th><th>Title</th></tr>
        </thead>
        <tbody data-testid="sqlite-rows">
          <tr v-if="!rows.length"><td colspan="5">Refresh to load.</td></tr>
          <tr v-for="r in rows" :key="r.work_id">
            <td><code>{{ r.work_id }}</code></td>
            <td>{{ r.registry_status }}</td>
            <td>{{ r.canvas_status }}</td>
            <td>{{ r.jira_key }}</td>
            <td>{{ r.title }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
