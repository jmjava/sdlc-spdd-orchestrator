<script setup>
import { onMounted, ref } from "vue";
import { postJson } from "../api.js";

const props = defineProps({
  target: { type: String, default: "" },
});

const combos = ref([]);
const comboId = ref("feature");
const workId = ref("");
const statusText = ref("Load combos to begin.");
const statusClass = ref("");
const log = ref("No render yet.");
const loading = ref(false);

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
    });
    log.value = JSON.stringify(data, null, 2);
    if (!ok) {
      statusClass.value = "err";
      statusText.value = data?.error || `Render failed (${status})`;
      return;
    }
    statusClass.value = "ok";
    statusText.value = `Rendered ${data.combo_id} for ${data.work_id}`;
  } catch (err) {
    statusClass.value = "err";
    statusText.value = String(err?.message || err);
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
      Compose header/body/footer parts into Jira ADF for a Work ID. Push stays explicit
      (never auto).
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
    <pre class="log" data-testid="templates-log">{{ log }}</pre>
  </section>
</template>
