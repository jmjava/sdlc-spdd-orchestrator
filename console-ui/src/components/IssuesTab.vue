<script setup>
import { computed, onMounted, ref } from "vue";
import { postJson } from "../api.js";

const props = defineProps({
  target: { type: String, default: "" },
});

const loading = ref(false);
const tracker = ref("github");
const jiraUrl = ref("");
const jiraEmail = ref("");
const jiraToken = ref("");
const jiraProject = ref("");
const ghToken = ref("");
const ghRepo = ref("");
const intStatus = ref("Ready.");
const intStatusClass = ref("");
const intMeta = ref("—");

const jiraWorkId = ref("");
const jiraKey = ref("");
const jiraSummary = ref("");
const jiraIssueType = ref("");
const jiraLinkStatus = ref("Ready.");
const jiraLinkClass = ref("");
const jiraLinkMeta = ref("—");
const jiraLinkLog = ref("No link action yet.");

const ghWorkId = ref("");
const ghNumber = ref("");
const ghTitle = ref("");
const ghUrl = ref("");
const ghLinkStatus = ref("Ready.");
const ghLinkClass = ref("");
const ghLinkMeta = ref("—");
const ghLinkLog = ref("No link action yet.");

const syncStatus = ref("Ready.");
const syncClass = ref("");
const syncCli = ref("—");
const syncLog = ref("No sync yet.");

const showJira = computed(() => tracker.value === "jira");
const showGithub = computed(() => tracker.value === "github");
const syncTitle = computed(() => {
  if (tracker.value === "jira") return "Sync with Jira server";
  if (tracker.value === "github") return "Sync with GitHub";
  return "Sync disabled (tracker=none)";
});
const syncMeta = computed(() => {
  if (tracker.value === "jira") {
    return "Pull refreshes ## Jira from the server; push sends local markdown → ADF (update only).";
  }
  if (tracker.value === "github") {
    return "Pull refreshes ## GitHub from the server; push sends composed GFM markdown (update only).";
  }
  return "Set tracker to Jira or GitHub to enable server sync.";
});

function applyIntegrations(data) {
  tracker.value = data.effective_tracker || data.tracker || "github";
  const j = data.jira || {};
  const g = data.github || {};
  jiraUrl.value = j.base_url || "";
  jiraEmail.value = j.email || "";
  jiraProject.value = j.project || "";
  ghRepo.value = g.repo || "";
  jiraToken.value = "";
  ghToken.value = "";
  intMeta.value =
    `tracker=${data.effective_tracker || "—"}` +
    ` · jira ${j.configured ? "ready" : "incomplete"}` +
    ` · github ${g.configured ? "ready" : "incomplete"}` +
    ` · ${data.config_path || ".sdlc/integrations-config.json"}`;
}

async function loadIntegrations() {
  loading.value = true;
  try {
    const { ok, status, data } = await postJson("/api/integrations/status", {
      target: props.target,
    });
    if (!ok) {
      intMeta.value = data?.error || `Load failed (${status})`;
      return;
    }
    applyIntegrations(data);
  } catch (err) {
    intMeta.value = String(err?.message || err);
  } finally {
    loading.value = false;
  }
}

async function saveIntegrations() {
  loading.value = true;
  intStatusClass.value = "";
  intStatus.value = "Saving…";
  try {
    const { ok, status, data } = await postJson("/api/integrations/save", {
      target: props.target,
      tracker: tracker.value,
      jira: {
        base_url: jiraUrl.value.trim(),
        email: jiraEmail.value.trim(),
        project: jiraProject.value.trim(),
        api_token: jiraToken.value.trim(),
      },
      github: {
        repo: ghRepo.value.trim(),
        token: ghToken.value.trim(),
      },
    });
    if (!ok) {
      intStatusClass.value = "err";
      intStatus.value = data?.error || `Save failed (${status})`;
      return;
    }
    intStatusClass.value = "ok";
    intStatus.value = "Saved.";
    await loadIntegrations();
  } catch (err) {
    intStatusClass.value = "err";
    intStatus.value = String(err?.message || err);
  } finally {
    loading.value = false;
  }
}

function fillJiraStatus(data) {
  const bits = [];
  if (data.linked) bits.push(`linked ${data.jira_key}`);
  else if (data.jira_draft) bits.push("Key not set (TBD)");
  else bits.push("not linked");
  if (data.canvas_source_issue) bits.push(`canvas ${data.canvas_source_issue}`);
  if (data.registry_jira) bits.push(`registry ${data.registry_jira}`);
  if (data.jira_url) bits.push(data.jira_url);
  jiraLinkMeta.value = bits.join(" · ") || "—";
  if (data.jira_key && !jiraKey.value.trim()) jiraKey.value = data.jira_key;
}

async function loadJiraStatus() {
  const workId = jiraWorkId.value.trim();
  if (!workId) {
    jiraLinkMeta.value = "Enter a Work ID.";
    return;
  }
  const { ok, data } = await postJson("/api/issues/status", {
    target: props.target,
    work_id: workId,
    system: "jira",
  });
  if (!ok) {
    jiraLinkMeta.value = data?.error || "Status failed";
    return;
  }
  fillJiraStatus(data);
}

async function loadGithubStatus() {
  const workId = ghWorkId.value.trim();
  if (!workId) {
    ghLinkMeta.value = "Enter a Work ID.";
    return;
  }
  const { ok, data } = await postJson("/api/issues/status", {
    target: props.target,
    work_id: workId,
    system: "github",
  });
  if (!ok) {
    ghLinkMeta.value = data?.error || "Status failed";
    return;
  }
  const bits = [];
  if (data.linked) bits.push(`linked #${data.github_number || data.issue_ref || ""}`);
  else bits.push("not linked");
  if (data.github_url) bits.push(data.github_url);
  ghLinkMeta.value = bits.join(" · ") || "—";
}

async function linkJira(dryRun) {
  const workId = jiraWorkId.value.trim();
  const key = jiraKey.value.trim();
  if (!workId || !key) {
    jiraLinkClass.value = "err";
    jiraLinkStatus.value = "Work ID and Jira key required.";
    return;
  }
  const label = dryRun ? "Preview link" : "Apply link";
  jiraLinkClass.value = "";
  jiraLinkStatus.value = `${label}…`;
  loading.value = true;
  try {
    const { ok, status, data } = await postJson("/api/issues/link", {
      target: props.target,
      system: "jira",
      work_id: workId,
      issue_ref: key,
      summary: jiraSummary.value.trim(),
      issue_type: jiraIssueType.value.trim(),
      dry_run: dryRun,
      apply: !dryRun,
    });
    jiraLinkLog.value = JSON.stringify(data, null, 2);
    if (!ok) {
      jiraLinkClass.value = "err";
      jiraLinkStatus.value = data?.error || `${label} failed (${status})`;
      return;
    }
    jiraLinkClass.value = "ok";
    jiraLinkStatus.value = dryRun ? "Preview OK — apply when ready." : `Linked ${key} to ${workId}`;
    fillJiraStatus(data);
  } catch (err) {
    jiraLinkClass.value = "err";
    jiraLinkStatus.value = String(err?.message || err);
    jiraLinkLog.value = String(err);
  } finally {
    loading.value = false;
  }
}

async function linkGithub(dryRun) {
  const workId = ghWorkId.value.trim();
  const num = ghNumber.value.trim();
  if (!workId || !num) {
    ghLinkClass.value = "err";
    ghLinkStatus.value = "Work ID and issue number required.";
    return;
  }
  const label = dryRun ? "Preview link" : "Apply link";
  ghLinkClass.value = "";
  ghLinkStatus.value = `${label}…`;
  loading.value = true;
  try {
    const { ok, status, data } = await postJson("/api/issues/link", {
      target: props.target,
      system: "github",
      work_id: workId,
      issue_ref: num,
      title: ghTitle.value.trim(),
      url: ghUrl.value.trim(),
      dry_run: dryRun,
      apply: !dryRun,
    });
    ghLinkLog.value = JSON.stringify(data, null, 2);
    if (!ok) {
      ghLinkClass.value = "err";
      ghLinkStatus.value = data?.error || `${label} failed (${status})`;
      return;
    }
    ghLinkClass.value = "ok";
    ghLinkStatus.value = dryRun ? "Preview OK" : `Linked #${num}`;
  } catch (err) {
    ghLinkClass.value = "err";
    ghLinkStatus.value = String(err?.message || err);
    ghLinkLog.value = String(err);
  } finally {
    loading.value = false;
  }
}

function activeWorkId() {
  return tracker.value === "jira"
    ? jiraWorkId.value.trim()
    : ghWorkId.value.trim() || jiraWorkId.value.trim();
}

async function syncIssues(direction, apply) {
  if (tracker.value === "none") {
    syncClass.value = "err";
    syncStatus.value = "Tracker is none — enable Jira or GitHub above.";
    return;
  }
  const workId = activeWorkId();
  if (!workId) {
    syncClass.value = "err";
    syncStatus.value = "Work ID required.";
    return;
  }
  const verb = direction === "pull" ? "Pull" : "Push";
  const label = apply ? `${verb} to server` : `Prepare ${direction}`;
  if (apply && !window.confirm(`Sync ${direction} for ${workId} (${tracker.value})?`)) return;
  syncClass.value = "";
  syncStatus.value = `${label}…`;
  loading.value = true;
  try {
    const { ok, status, data } = await postJson("/api/issues/sync", {
      target: props.target,
      work_id: workId,
      system: tracker.value,
      direction,
      apply,
    });
    syncLog.value = data?.report || JSON.stringify(data, null, 2);
    syncCli.value = data?.cli || "—";
    if (!ok) {
      syncClass.value = "err";
      syncStatus.value = data?.error || `${label} failed (${status})`;
      return;
    }
    syncClass.value = "ok";
    syncStatus.value = apply ? `${verb} OK` : `${verb} preview OK`;
  } catch (err) {
    syncClass.value = "err";
    syncStatus.value = String(err?.message || err);
    syncLog.value = String(err);
  } finally {
    loading.value = false;
  }
}

onMounted(loadIntegrations);
</script>

<template>
  <div data-testid="issues-panel">
    <section class="panel">
      <h2>Integrations config</h2>
      <p class="lead">
        Saved to gitignored <code>.sdlc/integrations-config.json</code>.
        Shell <code>JIRA_*</code> / <code>GH_TOKEN</code> env vars override file values.
        Tokens are never echoed back — leave blank to keep an existing saved token.
      </p>
      <div class="field-row">
        <label>
          Active tracker
          <select
            :value="tracker"
            data-testid="int-tracker"
            @change="tracker = $event.target.value"
          >
            <option value="github">GitHub Issues</option>
            <option value="jira">Jira</option>
            <option value="none">None (link only)</option>
          </select>
        </label>
        <label>
          Jira base URL
          <input v-model="jiraUrl" type="text" spellcheck="false" placeholder="https://yourorg.atlassian.net" data-testid="int-jira-url" />
        </label>
        <label>
          Jira email
          <input v-model="jiraEmail" type="email" spellcheck="false" placeholder="you@yourorg.com" data-testid="int-jira-email" />
        </label>
        <label>
          Jira API token
          <input v-model="jiraToken" type="password" autocomplete="off" placeholder="Leave blank to keep saved token" data-testid="int-jira-token" />
        </label>
        <label>
          Jira project key
          <input v-model="jiraProject" type="text" spellcheck="false" placeholder="PROJ" data-testid="int-jira-project" />
        </label>
        <label>
          GitHub token
          <input v-model="ghToken" type="password" autocomplete="off" placeholder="ghp_… or leave blank to keep saved" data-testid="int-gh-token" />
        </label>
        <label>
          GitHub repo
          <input v-model="ghRepo" type="text" spellcheck="false" placeholder="owner/repo" data-testid="int-gh-repo" />
        </label>
      </div>
      <div class="actions">
        <button class="btn btn-secondary" type="button" data-testid="btn-int-refresh" :disabled="loading" @click="loadIntegrations">
          Refresh
        </button>
        <button class="btn btn-primary" type="button" data-testid="btn-int-save" :disabled="loading" @click="saveIntegrations">
          Save config
        </button>
      </div>
      <p class="status" :class="intStatusClass" data-testid="int-status">{{ intStatus }}</p>
      <p class="meta" data-testid="int-meta">{{ intMeta }}</p>
    </section>

    <section v-show="showJira" class="panel" data-testid="issues-link-jira">
      <h2>Link existing Jira issue</h2>
      <p class="lead">
        Create the Jira issue <strong>manually in Jira</strong>, copy the key
        (e.g. <code>PROJ-123</code>), then record it here. Updates the requirement
        doc, canvas Metadata, and registry — it does <strong>not</strong> create issues in Jira.
      </p>
      <div class="field-row">
        <label>
          Work ID
          <input v-model="jiraWorkId" type="text" spellcheck="false" placeholder="FEAT-001-order-status-api" data-testid="jira-work-id" />
        </label>
        <label>
          Jira key (from Jira UI)
          <input v-model="jiraKey" type="text" spellcheck="false" placeholder="PROJ-123" data-testid="jira-key" />
        </label>
        <label>
          Summary (optional, local doc)
          <input v-model="jiraSummary" type="text" spellcheck="false" placeholder="Matches Jira summary if known" data-testid="jira-summary" />
        </label>
        <label>
          Issue type (optional)
          <input v-model="jiraIssueType" type="text" spellcheck="false" placeholder="Story" data-testid="jira-issue-type" />
        </label>
      </div>
      <div class="actions">
        <button class="btn btn-secondary" type="button" data-testid="btn-jira-refresh" :disabled="loading" @click="loadJiraStatus">
          Refresh status
        </button>
        <button class="btn btn-secondary" type="button" data-testid="btn-jira-link-dry" :disabled="loading" @click="linkJira(true)">
          Preview link
        </button>
        <button class="btn btn-primary" type="button" data-testid="btn-jira-link" :disabled="loading" @click="linkJira(false)">
          Apply link
        </button>
      </div>
      <p class="status" :class="jiraLinkClass" data-testid="jira-link-status">{{ jiraLinkStatus }}</p>
      <p class="meta" data-testid="jira-link-meta">{{ jiraLinkMeta }}</p>
      <pre class="log" data-testid="jira-link-log">{{ jiraLinkLog }}</pre>
    </section>

    <section v-show="showGithub" class="panel" data-testid="issues-link-github">
      <h2>Link existing GitHub issue</h2>
      <p class="lead">
        Create the issue <strong>manually in GitHub</strong>, copy the number
        (e.g. <code>42</code>), then record it here. Updates the requirement doc,
        canvas, and registry — does not create issues via API.
      </p>
      <div class="field-row">
        <label>
          Work ID
          <input v-model="ghWorkId" type="text" spellcheck="false" placeholder="FEAT-001-order-status-api" data-testid="gh-work-id" />
        </label>
        <label>
          Issue number
          <input v-model="ghNumber" type="text" spellcheck="false" placeholder="42" data-testid="gh-number" />
        </label>
        <label>
          Title (optional, local doc)
          <input v-model="ghTitle" type="text" spellcheck="false" placeholder="Matches GitHub title if known" data-testid="gh-title" />
        </label>
        <label>
          URL (optional)
          <input v-model="ghUrl" type="text" spellcheck="false" placeholder="https://github.com/org/repo/issues/42" data-testid="gh-url" />
        </label>
      </div>
      <div class="actions">
        <button class="btn btn-secondary" type="button" data-testid="btn-gh-refresh" :disabled="loading" @click="loadGithubStatus">
          Refresh status
        </button>
        <button class="btn btn-secondary" type="button" data-testid="btn-gh-link-dry" :disabled="loading" @click="linkGithub(true)">
          Preview link
        </button>
        <button class="btn btn-primary" type="button" data-testid="btn-gh-link" :disabled="loading" @click="linkGithub(false)">
          Apply link
        </button>
      </div>
      <p class="status" :class="ghLinkClass" data-testid="gh-link-status">{{ ghLinkStatus }}</p>
      <p class="meta" data-testid="gh-link-meta">{{ ghLinkMeta }}</p>
      <pre class="log" data-testid="gh-link-log">{{ ghLinkLog }}</pre>
    </section>

    <section class="panel" data-testid="issues-sync-panel">
      <h2 data-testid="issues-sync-title">{{ syncTitle }}</h2>
      <p class="meta" data-testid="issues-sync-meta">{{ syncMeta }}</p>
      <div class="actions">
        <button class="btn btn-secondary" type="button" data-testid="btn-jira-pull-dry" :disabled="loading" @click="syncIssues('pull', false)">
          Prepare pull
        </button>
        <button class="btn btn-primary" type="button" data-testid="btn-jira-pull" :disabled="loading" @click="syncIssues('pull', true)">
          Pull from server
        </button>
        <button class="btn btn-secondary" type="button" data-testid="btn-jira-push-dry" :disabled="loading" @click="syncIssues('push', false)">
          Prepare push
        </button>
        <button class="btn btn-primary" type="button" data-testid="btn-jira-push" :disabled="loading" @click="syncIssues('push', true)">
          Push to server
        </button>
      </div>
      <p class="status" :class="syncClass" data-testid="jira-sync-status">{{ syncStatus }}</p>
      <pre class="cmd" data-testid="jira-sync-cli">{{ syncCli }}</pre>
      <pre class="log" data-testid="jira-sync-log">{{ syncLog }}</pre>
    </section>
  </div>
</template>
