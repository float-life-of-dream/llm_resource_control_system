<template>
  <AdminLayout>
    <section class="prometheus-status">
      <div class="page-head">
        <div>
          <span class="eyebrow">Observability Control Plane</span>
          <h1>Prometheus Status</h1>
        </div>
        <el-button type="primary" :loading="store.isLoading" @click="load">Refresh</el-button>
      </div>

      <el-alert
        v-if="store.error"
        title="Prometheus status failed to load"
        :description="store.error"
        type="error"
        show-icon
        :closable="false"
      />

      <div v-if="store.isLoading" class="state-panel">Loading Prometheus status...</div>

      <template v-else>
        <div class="stats-grid">
          <div class="stat-card">
            <span class="label">Connection</span>
            <strong :class="store.health?.status === 'up' ? 'ok' : 'bad'">{{ store.health?.status ?? "unknown" }}</strong>
            <span class="unit">{{ store.health?.baseUrl ?? "Prometheus URL unavailable" }}</span>
          </div>
          <div class="stat-card">
            <span class="label">Targets Up</span>
            <strong class="ok">{{ store.targetSummary.up }}</strong>
            <span class="unit">healthy scrape targets</span>
          </div>
          <div class="stat-card">
            <span class="label">Targets Down</span>
            <strong :class="store.targetSummary.down > 0 ? 'bad' : 'ok'">{{ store.targetSummary.down }}</strong>
            <span class="unit">dcgm-exporter may be down on non-GPU hosts</span>
          </div>
        </div>

        <section class="panel">
          <div class="section-head">
            <h2>Scrape Targets</h2>
            <span>{{ store.targets.length }} targets</span>
          </div>
          <el-table v-if="store.targets.length" :data="store.targets" class="targets-table">
            <el-table-column prop="job" label="Job" width="180" />
            <el-table-column prop="instance" label="Instance" min-width="180" />
            <el-table-column label="Health" width="110">
              <template #default="{ row }">
                <el-tag :type="row.health === 'up' ? 'success' : 'danger'">{{ row.health }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="scrapeUrl" label="Scrape URL" min-width="240" />
            <el-table-column label="Last Error" min-width="220">
              <template #default="{ row }">{{ row.lastError || "-" }}</template>
            </el-table-column>
          </el-table>
          <div v-else class="state-panel compact">No scrape targets reported by Prometheus.</div>
        </section>

        <section class="panel">
          <div class="section-head">
            <h2>Supported Metrics</h2>
            <span>Whitelist only, raw PromQL is not exposed</span>
          </div>
          <div class="metric-groups">
            <div v-for="group in store.metricGroups" :key="group.key" class="metric-group">
              <h3>{{ group.label }}</h3>
              <div class="metric-list">
                <el-tag v-for="metric in group.items" :key="metric.key" effect="plain">
                  {{ metric.key }} · {{ metric.unit || "count" }}
                </el-tag>
              </div>
            </div>
          </div>
        </section>
      </template>
    </section>
  </AdminLayout>
</template>

<script setup lang="ts">
import { onMounted } from "vue";

import AdminLayout from "../layouts/AdminLayout.vue";
import { usePrometheusStore } from "../stores/prometheus";

const store = usePrometheusStore();

onMounted(() => {
  void load();
});

function load() {
  return store.loadPrometheusStatus();
}
</script>

<style scoped>
.prometheus-status {
  display: grid;
  gap: 24px;
}

.page-head,
.section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.eyebrow,
.label,
.unit,
.section-head span {
  color: #8fa3bf;
}

h1,
h2,
h3 {
  margin: 6px 0 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
}

.stat-card,
.panel,
.metric-group {
  background: rgba(13, 20, 33, 0.98);
  border: 1px solid rgba(143, 163, 191, 0.18);
  border-radius: 16px;
  padding: 20px;
}

.stat-card {
  min-height: 132px;
  display: grid;
  gap: 10px;
}

strong {
  font-size: 36px;
  line-height: 1;
  text-transform: uppercase;
}

.ok {
  color: #4bc0c0;
}

.bad {
  color: #ff7d7d;
}

.targets-table {
  margin-top: 16px;
}

.metric-groups {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
  margin-top: 16px;
}

.metric-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 14px;
}

.state-panel {
  min-height: 160px;
  display: grid;
  place-items: center;
  border-radius: 16px;
  border: 1px dashed rgba(143, 163, 191, 0.3);
  color: #8fa3bf;
}

.state-panel.compact {
  margin-top: 16px;
  min-height: 96px;
}
</style>
