<script setup>
import { onMounted, ref } from "vue";
import { getHealth } from "./api.js";
import DashboardTab from "./components/DashboardTab.vue";
import PersistenceTab from "./components/PersistenceTab.vue";
import TemplatesTab from "./components/TemplatesTab.vue";
import InstallTab from "./components/InstallTab.vue";
import SqliteTab from "./components/SqliteTab.vue";
import RollbackTab from "./components/RollbackTab.vue";
import GuideTab from "./components/GuideTab.vue";
import IssuesTab from "./components/IssuesTab.vue";
import AdfTab from "./components/AdfTab.vue";

const tabs = [
  { id: "dashboard", label: "Dashboard" },
  { id: "persistence", label: "Persistence" },
  { id: "templates", label: "Templates" },
  { id: "install", label: "Install" },
  { id: "sqlite", label: "SQLite" },
  { id: "rollback", label: "Rollback" },
  { id: "guide", label: "Guide" },
  { id: "issues", label: "Issues" },
  { id: "adf", label: "ADF" },
];

const active = ref("dashboard");
const target = ref("");
const health = ref(null);
const healthError = ref("");

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
  <div class="shell" data-testid="console-shell">
    <header class="brand-row">
      <h1 class="brand" data-testid="console-brand">SDLC-SPDD</h1>
      <p class="tagline">
        Vue3 ops console — Dashboard, Persistence, Templates, Install, SQLite, Rollback, Guide, Issues, and ADF.
      </p>
    </header>

    <div class="target-bar">
      <input
        v-model="target"
        type="text"
        spellcheck="false"
        placeholder="Target project path"
        aria-label="Target project path"
        data-testid="target-input"
      />
      <button
        class="btn btn-secondary"
        type="button"
        data-testid="refresh-health"
        @click="refreshHealth"
      >
        Refresh health
      </button>
    </div>
    <p v-if="healthError" class="status err" data-testid="health-status">{{ healthError }}</p>
    <p v-else-if="health" class="status ok muted" data-testid="health-status">
      API ok · default {{ health.default_target || "—" }}
      <template v-if="health.playground"> · playground</template>
    </p>
    <p
      v-if="health && health.playground"
      class="status"
      data-testid="playground-banner"
    >
      Playground target — disposable seed. Guide, Jira, and GitHub are in-process
      fakes (no network). Regenerate with <code>sdlc.sh console --playground</code>.
    </p>

    <nav class="tabs" aria-label="Console tabs" data-testid="console-tabs">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        type="button"
        class="tab"
        :class="{ active: active === tab.id }"
        :data-testid="`tab-${tab.id}`"
        :data-tab="tab.id"
        @click="active = tab.id"
      >
        {{ tab.label }}
      </button>
    </nav>

    <DashboardTab v-if="active === 'dashboard'" :target="target" @goto-tab="active = $event" />
    <PersistenceTab v-else-if="active === 'persistence'" :target="target" />
    <TemplatesTab v-else-if="active === 'templates'" :target="target" />
    <InstallTab v-else-if="active === 'install'" :target="target" />
    <SqliteTab v-else-if="active === 'sqlite'" :target="target" />
    <RollbackTab v-else-if="active === 'rollback'" :target="target" />
    <GuideTab v-else-if="active === 'guide'" :target="target" />
    <IssuesTab v-else-if="active === 'issues'" :target="target" />
    <AdfTab v-else-if="active === 'adf'" :target="target" />
  </div>
</template>
