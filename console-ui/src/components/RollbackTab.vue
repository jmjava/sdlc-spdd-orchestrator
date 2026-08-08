<script setup>
import { onMounted, ref } from "vue";
import { postJson } from "../api.js";

const props = defineProps({
  target: { type: String, default: "" },
});

const backups = ref([]);
const dryRun = ref(true);
const noSafety = ref(false);
const statusText = ref("Ready.");
const statusClass = ref("");
const log = ref("No restore yet.");
const loading = ref(false);

async function loadBackups() {
  loading.value = true;
  try {
    const { data } = await postJson("/api/backups", { target: props.target });
    backups.value = data.backups || [];
    statusClass.value = "ok";
    statusText.value = backups.value.length
      ? `${backups.value.length} backup(s) found.`
      : "No backups under .sdlc-spdd-upgrade-backups/";
  } catch (err) {
    statusClass.value = "err";
    statusText.value = String(err?.message || err);
  } finally {
    loading.value = false;
  }
}

async function restoreBackup(backupId) {
  if (!dryRun.value) {
    const ok = window.confirm(`Restore backup ${backupId} into\n${props.target}?`);
    if (!ok) return;
  }
  loading.value = true;
  statusClass.value = "";
  statusText.value = `Restoring ${backupId}…`;
  try {
    const { ok, data } = await postJson("/api/rollback", {
      target: props.target,
      backup_id: backupId,
      dry_run: dryRun.value,
      no_safety_backup: noSafety.value,
    });
    log.value = JSON.stringify(data, null, 2);
    if (ok && data.ok !== false) {
      statusClass.value = "ok";
      statusText.value = data.dry_run
        ? `Dry-run: would restore ${data.count} files.`
        : `Restored ${data.count} files.`;
      await loadBackups();
    } else {
      statusClass.value = "err";
      statusText.value = data?.error || "Restore failed";
    }
  } catch (err) {
    statusClass.value = "err";
    statusText.value = String(err?.message || err);
    log.value = String(err);
  } finally {
    loading.value = false;
  }
}

onMounted(loadBackups);
</script>

<template>
  <section class="panel" data-testid="rollback-panel">
    <h2>Upgrade backups</h2>
    <p class="lead">
      Backups live in <code>.sdlc-spdd-upgrade-backups/&lt;timestamp&gt;/</code>.
    </p>
    <div class="actions">
      <button
        class="btn btn-secondary"
        type="button"
        data-testid="btn-backups-refresh"
        :disabled="loading"
        @click="loadBackups"
      >
        Refresh backups
      </button>
    </div>
    <div class="checks">
      <label class="check">
        <input v-model="dryRun" type="checkbox" data-testid="opt-rollback-dry" />
        Dry-run restore
      </label>
      <label class="check">
        <input v-model="noSafety" type="checkbox" data-testid="opt-no-safety" />
        Skip safety backup
      </label>
    </div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr><th>Backup</th><th>Files</th><th>Size</th><th>Actions</th></tr>
        </thead>
        <tbody data-testid="backup-rows">
          <tr v-if="!backups.length">
            <td colspan="4">No backups under .sdlc-spdd-upgrade-backups/</td>
          </tr>
          <tr v-for="b in backups" :key="b.id">
            <td>
              <code>{{ b.id }}</code>
              <div class="meta">{{ (b.files || []).slice(0, 4).join(", ") }}</div>
            </td>
            <td>{{ b.file_count }}</td>
            <td>{{ Math.round((b.bytes || 0) / 1024) }} KB</td>
            <td>
              <button
                class="btn btn-warn"
                type="button"
                :data-testid="`btn-restore-${b.id}`"
                :disabled="loading"
                @click="restoreBackup(b.id)"
              >
                Restore
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <p class="status" :class="statusClass" data-testid="rollback-status">{{ statusText }}</p>
    <pre class="log" data-testid="rollback-log">{{ log }}</pre>
  </section>
</template>
