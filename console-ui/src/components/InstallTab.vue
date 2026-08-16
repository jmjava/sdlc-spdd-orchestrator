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
const lastResult = ref(null);

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
    lastResult.value = data;
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

function assistantNames(info) {
  const a = (info && info.assistants) || {};
  return ["cursor", "copilot", "claude"].filter((name) => a[name]);
}

function clearLog() {
  log.value = "Awaiting action…";
  lastResult.value = null;
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
    <div v-if="lastDetect && lastDetect.mode" class="stats" data-testid="detect-stats">
      <div class="stat-card">
        <div class="n" data-testid="detect-mode">{{ lastDetect.mode }}</div>
        <div class="l">mode</div>
      </div>
      <div class="stat-card">
        <div class="n" data-testid="detect-recommendation">{{ lastDetect.recommendation }}</div>
        <div class="l">recommend</div>
      </div>
      <div class="stat-card">
        <div class="n" data-testid="detect-marker-count">{{ (lastDetect.markers || []).length }}</div>
        <div class="l">markers</div>
      </div>
      <div class="stat-card">
        <div class="n" data-testid="detect-assistants">{{ assistantNames(lastDetect).join(", ") || "none" }}</div>
        <div class="l">adapters</div>
      </div>
    </div>
    <ul v-if="lastDetect && (lastDetect.markers || []).length" class="result-list" data-testid="detect-markers">
      <li v-for="m in lastDetect.markers" :key="m">{{ m }}</li>
    </ul>
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
    <section v-if="lastResult && lastResult.summary" class="detail-panel" data-testid="install-summary">
      <h3 data-testid="install-headline">{{ lastResult.summary.headline || lastResult.summary.action }}</h3>
      <div class="stats">
        <div class="stat-card">
          <div class="n" data-testid="install-exit">{{ lastResult.summary.exit_code }}</div>
          <div class="l">exit</div>
        </div>
        <div v-if="lastResult.summary.dry_run" class="stat-card">
          <div class="n" data-testid="install-would-count">{{ lastResult.summary.would_count }}</div>
          <div class="l">would</div>
        </div>
        <div v-if="lastResult.summary.created_count" class="stat-card">
          <div class="n" data-testid="install-created-count">{{ lastResult.summary.created_count }}</div>
          <div class="l">created</div>
        </div>
        <div v-if="lastResult.summary.check_ok_count || lastResult.summary.check_fail_count" class="stat-card">
          <div class="n" data-testid="install-check-counts">
            {{ lastResult.summary.check_ok_count }}/{{ lastResult.summary.check_ok_count + lastResult.summary.check_fail_count }}
          </div>
          <div class="l">checks</div>
        </div>
      </div>
      <p v-if="lastResult.summary.command" class="meta" data-testid="install-command">{{ lastResult.summary.command }}</p>
      <p v-if="lastResult.summary.framework_home" class="meta" data-testid="install-home">{{ lastResult.summary.framework_home }}</p>
      <p v-if="lastResult.summary.checks_summary" class="meta" data-testid="install-checks-summary">{{ lastResult.summary.checks_summary }}</p>
      <ul v-if="lastResult.summary.next_steps.length" class="result-list" data-testid="install-next-steps">
        <li v-for="(step, i) in lastResult.summary.next_steps" :key="i">{{ step }}</li>
      </ul>
      <ul v-if="lastResult.summary.warnings.length" class="result-list" data-testid="install-warnings">
        <li v-for="(w, i) in lastResult.summary.warnings" :key="i">{{ w }}</li>
      </ul>
      <ul v-if="lastResult.summary.would.length" class="result-list" data-testid="install-would">
        <li v-for="(item, i) in lastResult.summary.would" :key="i">{{ item }}</li>
      </ul>
      <ul v-if="lastResult.summary.created.length" class="result-list" data-testid="install-created">
        <li v-for="(item, i) in lastResult.summary.created" :key="i">{{ item }}</li>
      </ul>
      <ul v-if="lastResult.summary.checks_fail.length" class="result-list" data-testid="install-checks-fail">
        <li v-for="(item, i) in lastResult.summary.checks_fail" :key="i">{{ item }}</li>
      </ul>
    </section>
    <pre class="log" data-testid="install-log">{{ log }}</pre>
  </section>
</template>
