<script setup>
import { ref } from "vue";
import { postJson } from "../api.js";

const props = defineProps({
  target: { type: String, default: "" },
});

const action = ref("auto");
const asCursor = ref(true);
const asCopilot = ref(true);
const asClaude = ref(false);
const asAll = ref(false);
const dryRun = ref(false);
const force = ref(false);
const noBackup = ref(false);
const withEngine = ref(false);
const modePill = ref("idle");
const detectDetail = ref("Detect to recommend install vs upgrade.");
const statusText = ref("Ready.");
const statusClass = ref("");
const log = ref("Awaiting action…");
const loading = ref(false);
const lastDetect = ref(null);

function assistants() {
  if (asAll.value) return ["all"];
  const out = [];
  if (asCursor.value) out.push("cursor");
  if (asCopilot.value) out.push("copilot");
  if (asClaude.value) out.push("claude");
  return out.length ? out : ["cursor"];
}

async function detect() {
  if (!props.target.trim()) {
    statusClass.value = "err";
    statusText.value = "Target path required.";
    return;
  }
  loading.value = true;
  try {
    const { ok, data } = await postJson("/api/detect", { target: props.target });
    lastDetect.value = data;
    modePill.value = data.mode || "error";
    if (!ok || data.error) {
      detectDetail.value = data.error || "Detect failed";
      return;
    }
    const markers = (data.markers || []).length
      ? ` markers: ${(data.markers || []).slice(0, 3).join(", ")}`
      : " no framework markers";
    detectDetail.value = `recommendation: ${data.recommendation} ·${markers}`;
    const a = data.assistants || {};
    if (a.cursor || a.copilot || a.claude) {
      asCursor.value = !!a.cursor;
      asCopilot.value = !!a.copilot;
      asClaude.value = !!a.claude;
    }
  } catch (err) {
    modePill.value = "error";
    detectDetail.value = String(err?.message || err);
  } finally {
    loading.value = false;
  }
}

async function run(actionOverride) {
  if (!props.target.trim()) {
    statusClass.value = "err";
    statusText.value = "Target path required.";
    return;
  }
  let next = actionOverride || action.value;
  if (next === "auto") {
    await detect();
    const rec = (lastDetect.value && lastDetect.value.recommendation) || "install";
    if (rec === "create") {
      statusClass.value = "err";
      statusText.value = "Target directory does not exist. Create it first.";
      return;
    }
    next = rec === "upgrade" ? "upgrade" : "install";
  }
  loading.value = true;
  statusClass.value = "";
  statusText.value = `Running ${next}…`;
  log.value = "";
  try {
    const { ok, data } = await postJson("/api/run", {
      action: next,
      target: props.target,
      assistants: assistants(),
      dry_run: dryRun.value,
      force: force.value,
      no_backup: noBackup.value,
      with_python_engine: withEngine.value,
    });
    const cmd = (data.command || []).join(" ");
    log.value = (cmd ? `$ ${cmd}\n\n` : "") + (data.log || data.error || "");
    if (ok && data.ok !== false) {
      statusClass.value = "ok";
      statusText.value = `${next} succeeded (exit ${data.exit_code}).`;
    } else {
      statusClass.value = "err";
      statusText.value = `${next} failed (exit ${data.exit_code != null ? data.exit_code : "?"}).`;
    }
    await detect();
  } catch (err) {
    statusClass.value = "err";
    statusText.value = String(err?.message || err);
    log.value = String(err);
  } finally {
    loading.value = false;
  }
}

function clearLog() {
  log.value = "Awaiting action…";
  statusText.value = "Ready.";
  statusClass.value = "";
}
</script>

<template>
  <section class="panel" data-testid="install-panel">
    <h2>Install / Upgrade</h2>
    <p class="lead">Detect target mode, then install or upgrade assistant adapters.</p>
    <div class="actions">
      <button
        class="btn btn-secondary"
        type="button"
        data-testid="btn-detect"
        :disabled="loading"
        @click="detect"
      >
        Detect
      </button>
      <span class="mode-pill" :data-mode="modePill" data-testid="mode-pill">{{ modePill }}</span>
    </div>
    <p class="meta" data-testid="detect-detail">{{ detectDetail }}</p>
    <div class="checks">
      <label class="check"><input v-model="action" type="radio" value="auto" data-testid="action-auto" /> Auto</label>
      <label class="check"><input v-model="action" type="radio" value="install" data-testid="action-install" /> Force install</label>
      <label class="check"><input v-model="action" type="radio" value="upgrade" data-testid="action-upgrade" /> Force upgrade</label>
    </div>
    <div class="checks">
      <label class="check"><input v-model="asCursor" type="checkbox" data-testid="as-cursor" /> Cursor</label>
      <label class="check"><input v-model="asCopilot" type="checkbox" data-testid="as-copilot" /> GitHub Copilot</label>
      <label class="check"><input v-model="asClaude" type="checkbox" data-testid="as-claude" /> Claude Code</label>
      <label class="check"><input v-model="asAll" type="checkbox" data-testid="as-all" /> All assistants</label>
    </div>
    <div class="checks">
      <label class="check"><input v-model="dryRun" type="checkbox" data-testid="opt-dry" /> Dry run</label>
      <label class="check"><input v-model="force" type="checkbox" data-testid="opt-force" /> Force overwrite</label>
      <label class="check"><input v-model="noBackup" type="checkbox" data-testid="opt-nobackup" /> No backup</label>
      <label class="check"><input v-model="withEngine" type="checkbox" data-testid="opt-engine" /> Install Python engine</label>
    </div>
    <div class="actions">
      <button class="btn btn-primary" type="button" data-testid="btn-run" :disabled="loading" @click="run()">
        Run
      </button>
      <button class="btn btn-secondary" type="button" data-testid="btn-verify" :disabled="loading" @click="run('verify')">
        Verify
      </button>
      <button class="btn btn-ghost" type="button" data-testid="btn-clear" @click="clearLog">Clear log</button>
    </div>
    <p class="status" :class="statusClass" data-testid="run-status">{{ statusText }}</p>
    <pre class="log" data-testid="install-log">{{ log }}</pre>
  </section>
</template>
