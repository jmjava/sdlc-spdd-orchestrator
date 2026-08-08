<script setup>
import { computed, onMounted, ref } from "vue";
import { getHealth } from "./api.js";
import PersistenceTab from "./components/PersistenceTab.vue";
import TemplatesTab from "./components/TemplatesTab.vue";

const tabs = [
  { id: "persistence", label: "Persistence" },
  { id: "templates", label: "Templates" },
  { id: "install", label: "Install", stub: true },
  { id: "sqlite", label: "SQLite", stub: true },
  { id: "rollback", label: "Rollback", stub: true },
  { id: "guide", label: "Guide", stub: true },
  { id: "adf", label: "ADF", stub: true },
];

const active = ref("persistence");
const target = ref("");
const health = ref(null);
const healthError = ref("");

const activeMeta = computed(() => tabs.find((t) => t.id === active.value));

async function refreshHealth() {
  healthError.value = "";
  try {
    const res = await getHealth();
    if (!res.ok) {
      healthError.value = `Health check failed (${res.status})`;
      return;
    }
    health.value = res.data;
    if (!target.value && res.data?.default_target) {
      target.value = res.data.default_target;
    }
  } catch (err) {
    healthError.value = String(err?.message || err);
  }
}

onMounted(refreshHealth);
</script>

<template>
  <div class="shell">
    <header class="brand-row">
      <h1 class="brand">SDLC-SPDD</h1>
      <p class="tagline">
        Vue3 ops console — Persistence + ADF Templates first; remaining tabs stubbed
        pending parity port from Flask.
      </p>
    </header>

    <div class="target-bar">
      <input
        v-model="target"
        type="text"
        spellcheck="false"
        placeholder="Target project path"
        aria-label="Target project path"
      />
      <button class="btn btn-secondary" type="button" @click="refreshHealth">
        Refresh health
      </button>
    </div>
    <p v-if="healthError" class="status err">{{ healthError }}</p>
    <p v-else-if="health" class="status ok muted">
      API ok · default {{ health.default_target || "—" }}
    </p>

    <nav class="tabs" aria-label="Console tabs">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        type="button"
        class="tab"
        :class="{ active: active === tab.id }"
        @click="active = tab.id"
      >
        {{ tab.label }}
      </button>
    </nav>

    <PersistenceTab v-if="active === 'persistence'" :target="target" />
    <TemplatesTab v-else-if="active === 'templates'" :target="target" />
    <section v-else class="panel">
      <h2>{{ activeMeta?.label }}</h2>
      <p class="lead">
        Stub — port from Flask <code>installer/pages.py</code> in a later slice. APIs remain on
        the Flask BFF (<code>/api/*</code>).
      </p>
    </section>
  </div>
</template>
