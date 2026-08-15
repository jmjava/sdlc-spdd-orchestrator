<script setup>
import { onMounted, ref, watch } from "vue";
import { postJson } from "../api.js";

const props = defineProps({
  target: { type: String, default: "" },
  focusWorkId: { type: String, default: "" },
});

const combos = ref([]);
const comboId = ref("feature");
const workId = ref("");
const writeAdf = ref(false);
const openViewer = ref(false);
const markdown = ref("");
const viewerUrl = ref("");
const statusText = ref("Load combos to begin.");
const statusClass = ref("");
const log = ref("No render yet.");
const loading = ref(false);

watch(
  () => props.focusWorkId,
  (id) => {
    if (id) workId.value = id;
  },
  { immediate: true },
);

async function loadCombos() {
  loading.value = true;
  try {
    const { ok, data, status } = await postJson("/api/templates", {});
    if (!ok) {
      statusClass.value = "err";
      statusText.value = data?.error || `List failed (${status})`;
      return;
    }
    combos.value = data.combos || [];
    if (combos.value.length && !combos.value.some((c) => c.id === comboId.value)) {
      comboId.value = combos.value[0].id;
    }
    statusClass.value = "ok";
    statusText.value = `${combos.value.length} combo(s) available`;
    log.value = JSON.stringify(combos.value, null, 2);
  } catch (err) {
    statusClass.value = "err";
    statusText.value = String(err?.message || err);
  } finally {
    loading.value = false;
  }
}

function applyRender(data) {
  markdown.value = data?.markdown || "";
  const adf = data?.adf ? JSON.stringify(data.adf, null, 2) : "";
  log.value = adf || JSON.stringify(data, null, 2);
  viewerUrl.value = data?.viewer?.edit_url || "";
}

async function renderCombo() {
  if (!workId.value.trim()) {
    statusClass.value = "err";
    statusText.value = "Work ID is required";
    return;
  }
  loading.value = true;
  try {
    const { ok, data, status } = await postJson("/api/templates/render", {
      target: props.target,
      work_id: workId.value.trim(),
      combo: comboId.value,
      write: writeAdf.value || openViewer.value,
      open_viewer: openViewer.value,
    });
    applyRender(data);
    if (!ok) {
      statusClass.value = "err";
      statusText.value = data?.error || `Render failed (${status})`;
      return;
    }
    statusClass.value = "ok";
    const written = data.output_path ? ` · wrote ${data.output_path}` : "";
    const opened = data.viewer?.edit_url ? " · viewer URL ready" : "";
    statusText.value = `Rendered ${data.combo_id} for ${data.work_id}${written}${opened}`;
    if (data.viewer?.edit_url) {
      window.open(data.viewer.edit_url, "_blank", "noopener");
    }
  } catch (err) {
    statusClass.value = "err";
    statusText.value = String(err?.message || err);
    log.value = String(err);
  } finally {
    loading.value = false;
  }
}

onMounted(loadCombos);
</script>

<template>
  <section class="panel" data-testid="templates-panel">
    <h2>Templates</h2>
    <p class="lead">
      Compose header/body/footer parts into Jira ADF for a Work ID. Preview here; push stays
      explicit (never auto). Write + open viewer starts the ADF editor on the file.
    </p>
    <div class="field-row">
      <label>
        Combo
        <select v-model="comboId" data-testid="templates-combo">
          <option v-for="c in combos" :key="c.id" :value="c.id">
            {{ c.id }} — {{ c.title }}
          </option>
        </select>
      </label>
      <label>
        Work ID
        <input
          v-model="workId"
          type="text"
          spellcheck="false"
          placeholder="FEAT-001-shared-script-library"
          data-testid="templates-work-id"
        />
      </label>
    </div>
    <div class="checks">
      <label class="check">
        <input v-model="writeAdf" type="checkbox" data-testid="templates-write" />
        Write ADF to <code>adf/&lt;work-id&gt;.adf.json</code>
      </label>
      <label class="check">
        <input v-model="openViewer" type="checkbox" data-testid="templates-open-viewer" />
        Open in ADF Viewer after write
      </label>
    </div>
    <div class="actions">
      <button
        class="btn btn-secondary"
        type="button"
        data-testid="templates-refresh"
        :disabled="loading"
        @click="loadCombos"
      >
        Refresh combos
      </button>
      <button
        class="btn btn-primary"
        type="button"
        data-testid="templates-render"
        :disabled="loading"
        @click="renderCombo"
      >
        Render ADF
      </button>
    </div>
    <p class="status" :class="statusClass" data-testid="templates-status">{{ statusText }}</p>
    <p v-if="viewerUrl" class="meta" data-testid="templates-viewer-url">
      Viewer: <a :href="viewerUrl" target="_blank" rel="noopener">{{ viewerUrl }}</a>
    </p>
    <h3 v-if="markdown">Markdown preview</h3>
    <pre v-if="markdown" class="preview" data-testid="templates-preview">{{ markdown }}</pre>
    <h3>ADF JSON</h3>
    <pre class="log" data-testid="templates-log">{{ log }}</pre>
  </section>
</template>
