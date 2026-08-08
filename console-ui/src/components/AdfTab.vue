<script setup>
import { onMounted, ref } from "vue";
import { postJson } from "../api.js";

const props = defineProps({
  target: { type: String, default: "" },
});

const host = ref("127.0.0.1");
const port = ref(5050);
const statusText = ref("Not loaded.");
const statusClass = ref("");
const meta = ref("—");
const cmd = ref("—");
const log = ref("No action yet.");
const busy = ref(false);

const browsePath = ref("");
const browseEntries = ref([]);
const selectedPath = ref("");
const adfHome = ref("");
const adfDir = ref("");

const workType = ref("feature");
const workTitle = ref("");
const workId = ref("");
const initStatus = ref("Ready.");
const initStatusClass = ref("");
const initLog = ref("No init yet.");

function adfBody(extra = {}) {
  return {
    target: props.target,
    host: (host.value || "127.0.0.1").trim() || "127.0.0.1",
    port: parseInt(String(port.value), 10) || 5050,
    ...extra,
  };
}

function applyAdf(data) {
  const proc = data?.process || {};
  const probe = data?.probe || {};
  const url = data?.url || probe?.url || "";

  if (proc.host) host.value = proc.host;
  if (proc.port) port.value = proc.port;

  cmd.value = data?.cli || "—";
  const bits = [
    proc.alive ? "process alive" : "process stopped",
    probe.tcp_open ? "TCP open" : "TCP closed",
    probe.http_ok ? "HTTP ok" : "HTTP down",
    url ? `url ${url}` : "",
    proc.log_path ? `log ${proc.log_path}` : "",
  ].filter(Boolean);
  meta.value = bits.join(" · ") || "—";

  if (data?.ok && (proc.alive || probe.http_ok)) {
    statusText.value = "Viewer ready" + (url ? `: ${url}` : "");
    statusClass.value = "ok";
  } else if (data?.error) {
    statusText.value = data.error;
    statusClass.value = "err";
  } else {
    statusText.value = probe.detail || "Viewer not running.";
    statusClass.value = "";
  }

  if (data?.result) {
    log.value = JSON.stringify(data.result, null, 2);
  }
  return url;
}

async function loadAdf() {
  try {
    const { data } = await postJson("/api/adf", adfBody());
    return applyAdf(data);
  } catch (err) {
    statusClass.value = "err";
    statusText.value = String(err?.message || err);
    log.value = String(err);
    return "";
  }
}

async function adfAction(url, label, { openAfter } = {}) {
  busy.value = true;
  statusText.value = `${label}…`;
  statusClass.value = "";
  try {
    const { ok, data } = await postJson(url, adfBody());
    const openUrl = applyAdf(data);
    if (!ok && data?.error) {
      statusText.value = data.error;
      statusClass.value = "err";
      log.value = JSON.stringify(data, null, 2);
      return;
    }
    statusText.value = `${label} OK`;
    statusClass.value = "ok";
    if (data?.result) {
      log.value = JSON.stringify(data.result, null, 2);
    }
    await loadAdf();
    if (openAfter && openUrl) {
      for (let i = 0; i < 20; i++) {
        await new Promise((r) => setTimeout(r, 250));
        const { data: probeData } = await postJson("/api/adf", adfBody());
        applyAdf(probeData);
        if (probeData?.probe?.http_ok) {
          window.open(probeData.url || openUrl, "_blank", "noopener");
          return;
        }
      }
      window.open(openUrl, "_blank", "noopener");
    }
  } catch (err) {
    statusClass.value = "err";
    statusText.value = String(err?.message || err);
    log.value = String(err);
  } finally {
    busy.value = false;
  }
}

async function openAdfViewer() {
  const { data: status } = await postJson("/api/adf", adfBody());
  applyAdf(status);
  if (status?.probe?.http_ok && status.url) {
    window.open(status.url, "_blank", "noopener");
    return;
  }
  await adfAction("/api/adf/start", "Start viewer", { openAfter: true });
}

function setSelected(path) {
  selectedPath.value = path || "";
}

async function loadAdfBrowse(path) {
  busy.value = true;
  try {
    const { ok, data } = await postJson("/api/adf/browse", adfBody({ path: path || "" }));
    if (!ok) {
      initStatus.value = data?.error || "Browse failed";
      initStatusClass.value = "err";
      initLog.value = JSON.stringify(data, null, 2);
      return;
    }
    browsePath.value = data.path || "";
    adfHome.value = data.home || props.target;
    adfDir.value = data.adf_dir || "";

    const entries = [];
    if (data.parent) {
      entries.push({ kind: "DIR", name: "..", path: data.parent, navigate: true });
    }
    for (const d of data.dirs || []) {
      entries.push({
        kind: "DIR",
        name: `${d.name}/`,
        path: d.path,
        navigate: true,
      });
    }
    for (const f of data.files || []) {
      // Browse returns ADF candidates (*.adf.json); valid rows are selectable.
      const selectable = !!f.valid;
      entries.push({
        kind: "ADF",
        name: f.name + (f.valid ? "" : " (invalid)"),
        path: f.path,
        navigate: false,
        selectable,
        selected: f.path === selectedPath.value,
        invalid: !f.valid,
      });
    }
    browseEntries.value = entries;
    initStatus.value = `Browsing ${browsePath.value}`;
    initStatusClass.value = "";
  } catch (err) {
    initStatusClass.value = "err";
    initStatus.value = String(err?.message || err);
    initLog.value = String(err);
  } finally {
    busy.value = false;
  }
}

function onBrowseRow(entry) {
  if (entry.navigate) {
    loadAdfBrowse(entry.path);
    return;
  }
  if (entry.selectable) {
    setSelected(entry.path);
    loadAdfBrowse(browsePath.value);
  }
}

async function initFromAdf(dryRun) {
  if (!selectedPath.value) {
    initStatus.value = "Select an ADF file first";
    initStatusClass.value = "err";
    return;
  }
  const label = dryRun ? "Dry run" : "Init SPDD work";
  busy.value = true;
  initStatus.value = `${label}…`;
  initStatusClass.value = "";
  try {
    const { ok, data } = await postJson(
      "/api/adf/init-work",
      adfBody({
        path: selectedPath.value,
        type: workType.value,
        title: workTitle.value.trim(),
        work_id: workId.value.trim(),
        dry_run: !!dryRun,
      }),
    );
    initLog.value = JSON.stringify(data, null, 2);
    if (!ok) {
      initStatus.value = data?.error || `${label} failed`;
      initStatusClass.value = "err";
      return;
    }
    initStatus.value =
      (dryRun ? "Would create " : "Created ") +
      data.work_id +
      " — next: " +
      data.next_command;
    initStatusClass.value = "ok";
  } catch (err) {
    initStatusClass.value = "err";
    initStatus.value = String(err?.message || err);
    initLog.value = String(err);
  } finally {
    busy.value = false;
  }
}

onMounted(async () => {
  await loadAdf();
  await loadAdfBrowse(browsePath.value || "");
});
</script>

<template>
  <section class="panel" data-testid="adf-panel">
    <h2>ADF Viewer</h2>
    <p class="lead">
      Start/stop the viewer for editing and Jira sync. Browse a local ADF and init a draft
      REASONS canvas.
    </p>

    <div class="field-row">
      <label>
        Host
        <input v-model="host" data-testid="adf-host" type="text" spellcheck="false" />
      </label>
      <label>
        Port
        <input v-model.number="port" data-testid="adf-port" type="number" />
      </label>
    </div>

    <div class="actions">
      <button
        class="btn btn-primary"
        type="button"
        data-testid="btn-adf-start"
        :disabled="busy"
        @click="adfAction('/api/adf/start', 'Start viewer')"
      >
        Start viewer
      </button>
      <button
        class="btn btn-secondary"
        type="button"
        data-testid="btn-adf-restart"
        :disabled="busy"
        @click="adfAction('/api/adf/restart', 'Restart viewer')"
      >
        Restart
      </button>
      <button
        class="btn btn-ghost"
        type="button"
        data-testid="btn-adf-stop"
        :disabled="busy"
        @click="adfAction('/api/adf/stop', 'Stop viewer')"
      >
        Stop
      </button>
      <button
        class="btn btn-secondary"
        type="button"
        data-testid="btn-adf-refresh"
        :disabled="busy"
        @click="loadAdf"
      >
        Refresh status
      </button>
      <button
        class="btn btn-primary"
        type="button"
        data-testid="btn-adf-open"
        :disabled="busy"
        @click="openAdfViewer"
      >
        Open ADF Viewer
      </button>
    </div>

    <p class="status" :class="statusClass" data-testid="adf-status">{{ statusText }}</p>
    <div class="meta" data-testid="adf-meta">{{ meta }}</div>
    <pre class="log" data-testid="adf-log">{{ log }}</pre>
    <pre class="meta" data-testid="adf-cmd">{{ cmd }}</pre>

    <div class="panel" data-testid="adf-init-panel">
      <h3>Browse &amp; init from ADF</h3>
      <div class="field-row">
        <label style="flex: 1 1 auto">
          Browse path
          <input
            v-model="browsePath"
            data-testid="adf-browse-path"
            type="text"
            spellcheck="false"
            placeholder="Browse path (defaults to target/adf)"
            @keydown.enter="loadAdfBrowse(browsePath.trim())"
          />
        </label>
      </div>
      <div class="actions">
        <button
          class="btn btn-secondary"
          type="button"
          data-testid="btn-adf-browse"
          :disabled="busy"
          @click="loadAdfBrowse(browsePath.trim())"
        >
          Browse
        </button>
        <button
          class="btn btn-ghost"
          type="button"
          data-testid="btn-adf-browse-home"
          :disabled="busy"
          @click="loadAdfBrowse(adfHome || target)"
        >
          Target root
        </button>
        <button
          class="btn btn-ghost"
          type="button"
          data-testid="btn-adf-browse-adf"
          :disabled="busy"
          @click="loadAdfBrowse(adfDir || (target ? `${target}/adf` : 'adf'))"
        >
          adf/
        </button>
      </div>

      <div class="browser-list" data-testid="adf-browser-list">
        <button
          v-for="(entry, idx) in browseEntries"
          :key="`${entry.kind}-${entry.path}-${idx}`"
          type="button"
          class="browser-row"
          :class="{ selected: entry.selected, invalid: entry.invalid }"
          @click="onBrowseRow(entry)"
        >
          <span class="kind">{{ entry.kind }}</span>
          <span>{{ entry.name }}</span>
        </button>
        <div v-if="!browseEntries.length" class="meta">No ADF candidates in this folder.</div>
      </div>
      <div class="meta" data-testid="adf-selected">
        {{ selectedPath ? `Selected: ${selectedPath}` : "No ADF selected." }}
      </div>

      <div class="field-row">
        <label>
          Work type
          <select v-model="workType" data-testid="adf-work-type">
            <option value="feature">feature</option>
            <option value="spike">spike</option>
            <option value="bug">bug</option>
            <option value="refactor">refactor</option>
            <option value="chore">chore</option>
          </select>
        </label>
        <label>
          Title
          <input
            v-model="workTitle"
            data-testid="adf-work-title"
            type="text"
            spellcheck="false"
            placeholder="Defaults to first heading / filename"
          />
        </label>
        <label>
          Work ID
          <input
            v-model="workId"
            data-testid="adf-work-id"
            type="text"
            spellcheck="false"
            placeholder="FEAT-013-slug"
          />
        </label>
      </div>

      <div class="actions">
        <button
          class="btn btn-secondary"
          type="button"
          data-testid="btn-adf-init-dry"
          :disabled="busy"
          @click="initFromAdf(true)"
        >
          Dry run
        </button>
        <button
          class="btn btn-primary"
          type="button"
          data-testid="btn-adf-init"
          :disabled="busy"
          @click="initFromAdf(false)"
        >
          Init SPDD work
        </button>
      </div>
      <p class="status" :class="initStatusClass" data-testid="adf-init-status">
        {{ initStatus }}
      </p>
      <pre class="log" data-testid="adf-init-log">{{ initLog }}</pre>
    </div>
  </section>
</template>
