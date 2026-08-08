<script setup>
import { onMounted, ref } from "vue";
import { postJson } from "../api.js";

const props = defineProps({
  target: { type: String, default: "" },
});

const sqliteOn = ref(true);
const guideOn = ref(true);
const guideUrl = ref("");
const notes = ref("");
const statusText = ref("Not loaded.");
const statusClass = ref("");
const meta = ref("Not loaded.");
const log = ref("No persistence action yet.");
const loading = ref(false);
const stats = ref({ git: "—", sqlite: "—", guide: "—", source: "—" });

function applyStatus(data) {
  const en = data.enabled || {};
  sqliteOn.value = !!en.sqlite;
  guideOn.value = !!en["guide-dice"];
  guideUrl.value = (data.guide && data.guide.base_url) || "";
  notes.value = data.notes || "";
  stats.value = {
    git: en["git-pointers"] ? "ON" : "OFF",
    sqlite: en.sqlite ? (data.sqlite && data.sqlite.exists ? "READY" : "ON") : "OFF",
    guide: en["guide-dice"] ? "ON" : "OFF",
    source: data.source || "—",
  };
  const effective = (data.guide && data.guide.effective_base_url) || "";
  meta.value =
    `backends=${(data.backends || []).join(",")}` +
    ` · config=${data.config_path || "—"}` +
    (data.config_exists ? "" : " (defaults)") +
    (effective ? ` · effective guide=${effective}` : "");
  log.value = JSON.stringify(data, null, 2);
}

async function loadStatus() {
  loading.value = true;
  statusClass.value = "";
  statusText.value = "Loading…";
  try {
    const { ok, status, data } = await postJson("/api/persistence/status", {
      target: props.target,
    });
    if (!ok) {
      statusClass.value = "err";
      statusText.value = data?.error || `Request failed (${status})`;
      meta.value = data?.error || "Failed to load";
      log.value = JSON.stringify(data, null, 2);
      return;
    }
    applyStatus(data);
    statusClass.value = "ok";
    statusText.value = "Loaded persistence options.";
  } catch (err) {
    statusClass.value = "err";
    statusText.value = String(err?.message || err);
    log.value = String(err);
  } finally {
    loading.value = false;
  }
}

async function saveOptions() {
  loading.value = true;
  statusClass.value = "";
  statusText.value = "Saving…";
  try {
    const backends = ["git-pointers"];
    if (sqliteOn.value) backends.push("sqlite");
    if (guideOn.value) backends.push("guide-dice");
    const { ok, status, data } = await postJson("/api/persistence/save", {
      target: props.target,
      backends,
      guide_base_url: guideUrl.value.trim(),
      notes: notes.value,
    });
    log.value = JSON.stringify(data, null, 2);
    if (!ok) {
      statusClass.value = "err";
      statusText.value = data?.error || `Save failed (${status})`;
      return;
    }
    applyStatus(data);
    statusClass.value = "ok";
    statusText.value = "Saved persistence options.";
  } catch (err) {
    statusClass.value = "err";
    statusText.value = String(err?.message || err);
    log.value = String(err);
  } finally {
    loading.value = false;
  }
}

onMounted(loadStatus);
</script>

<template>
  <section class="panel" data-testid="persistence-panel">
    <h2>Persistence options</h2>
    <p class="lead">
      Triple-path ContextStore fan-out. Git stay-set is always required. Config:
      <code>.sdlc/persistence-config.json</code>.
    </p>
    <div class="checks" data-testid="persistence-backends">
      <label class="check">
        <input type="checkbox" checked disabled data-testid="pb-git" />
        git-pointers (required)
      </label>
      <label class="check">
        <input v-model="sqliteOn" type="checkbox" data-testid="pb-sqlite" />
        sqlite
      </label>
      <label class="check">
        <input v-model="guideOn" type="checkbox" data-testid="pb-guide" />
        guide-dice
      </label>
    </div>
    <div class="field-row">
      <label>
        Guide base URL (optional override)
        <input
          v-model="guideUrl"
          type="text"
          spellcheck="false"
          placeholder="leave blank for GUIDE_BASE_URL / localhost:21337"
          data-testid="persist-guide-url"
        />
      </label>
    </div>
    <label>
      Notes
      <textarea
        v-model="notes"
        rows="3"
        placeholder="Operator notes for this project's persist fan-out"
        data-testid="persist-notes"
      />
    </label>
    <div class="actions">
      <button
        class="btn btn-secondary"
        type="button"
        data-testid="persistence-load"
        :disabled="loading"
        @click="loadStatus"
      >
        Refresh
      </button>
      <button
        class="btn btn-primary"
        type="button"
        data-testid="persistence-save"
        :disabled="loading"
        @click="saveOptions"
      >
        Save options
      </button>
    </div>
    <div class="stats" data-testid="persist-stats">
      <div class="stat-card"><div class="n" data-testid="ps-git">{{ stats.git }}</div><div class="l">git</div></div>
      <div class="stat-card"><div class="n" data-testid="ps-sqlite">{{ stats.sqlite }}</div><div class="l">sqlite</div></div>
      <div class="stat-card"><div class="n" data-testid="ps-guide">{{ stats.guide }}</div><div class="l">guide</div></div>
      <div class="stat-card"><div class="n" data-testid="ps-source">{{ stats.source }}</div><div class="l">source</div></div>
    </div>
    <p class="meta" data-testid="persist-meta">{{ meta }}</p>
    <p class="status" :class="statusClass" data-testid="persistence-status">{{ statusText }}</p>
    <pre class="log" data-testid="persistence-log">{{ log }}</pre>
  </section>
</template>
