<script setup>
import { ref } from "vue";
import { postJson } from "../api.js";

const props = defineProps({
  target: { type: String, default: "" },
});

const statusText = ref("Not loaded.");
const statusClass = ref("");
const log = ref("No persistence probe yet.");
const loading = ref(false);

async function loadStatus() {
  loading.value = true;
  statusClass.value = "";
  statusText.value = "Loading…";
  try {
    const { ok, status, data } = await postJson("/api/persistence/status", {
      target: props.target,
    });
    log.value = JSON.stringify(data, null, 2);
    if (!ok) {
      statusClass.value = "err";
      statusText.value = data?.error || `Request failed (${status})`;
      return;
    }
    statusClass.value = "ok";
    const backends = (data.backends || []).join(", ") || "(defaults)";
    statusText.value = `Persistence ok · backends: ${backends}`;
  } catch (err) {
    statusClass.value = "err";
    statusText.value = String(err?.message || err);
    log.value = String(err);
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <section class="panel">
    <h2>Persistence</h2>
    <p class="lead">
      Triple-path backends (<code>git-pointers</code>, <code>sqlite</code>,
      <code>guide-dice</code>) via <code>POST /api/persistence/status</code>.
    </p>
    <div class="actions">
      <button class="btn btn-primary" type="button" :disabled="loading" @click="loadStatus">
        {{ loading ? "Loading…" : "Load status" }}
      </button>
    </div>
    <p class="status" :class="statusClass">{{ statusText }}</p>
    <pre class="log">{{ log }}</pre>
  </section>
</template>
