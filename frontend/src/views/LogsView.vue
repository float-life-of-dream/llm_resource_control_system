<template>
  <AdminLayout>
    <section class="logs-page">
      <div class="page-head">
        <div>
          <span class="eyebrow">Elasticsearch</span>
          <h1>Logs</h1>
        </div>
        <el-segmented :model-value="store.range" :options="rangeOptions" @change="handleRangeChange" />
      </div>

      <section class="filter-panel">
        <el-input v-model="store.query" clearable placeholder="Search messages, services, exceptions..." @keyup.enter="load" />
        <el-select v-model="store.level" placeholder="Level" clearable>
          <el-option label="All levels" value="" />
          <el-option label="Error" value="error" />
          <el-option label="Warn" value="warn" />
          <el-option label="Info" value="info" />
          <el-option label="Debug" value="debug" />
        </el-select>
        <el-select v-model="store.service" placeholder="Service" clearable filterable>
          <el-option label="All services" value="" />
          <el-option v-for="service in store.serviceOptions" :key="service" :label="service" :value="service" />
        </el-select>
        <el-button type="primary" :loading="store.isLoading" @click="load">Search</el-button>
      </section>

      <el-alert
        v-if="store.error"
        title="Log data failed to load"
        :description="store.error"
        type="error"
        show-icon
        :closable="false"
      />

      <div class="summary-grid">
        <div class="summary-card">
          <span>Total</span>
          <strong>{{ store.total }}</strong>
        </div>
        <div v-for="level in store.levels" :key="level.key" class="summary-card">
          <span>{{ level.key }}</span>
          <strong>{{ level.count }}</strong>
        </div>
      </div>

      <section class="table-panel">
        <div class="section-head">
          <h2>Log Events</h2>
          <span>{{ store.items.length }} shown</span>
        </div>
        <el-table v-loading="store.isLoading" :data="store.items" class="logs-table">
          <el-table-column prop="timestamp" label="Time" min-width="190" />
          <el-table-column label="Level" width="110">
            <template #default="{ row }">
              <el-tag :type="levelTagType(row.level)" effect="dark">{{ row.level }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="service" label="Service" width="160" />
          <el-table-column prop="message" label="Message" min-width="360" show-overflow-tooltip />
          <el-table-column prop="traceId" label="Trace" width="160" />
          <el-table-column prop="host" label="Host" width="140" />
        </el-table>
        <div v-if="!store.isLoading && !store.items.length" class="state-panel">No logs matched the current filters.</div>
      </section>
    </section>
  </AdminLayout>
</template>

<script setup lang="ts">
import { onMounted } from "vue";

import AdminLayout from "../layouts/AdminLayout.vue";
import { useLogsStore } from "../stores/logs";
import type { RangeKey } from "../types/monitor";

const store = useLogsStore();
const rangeOptions = [
  { label: "1h", value: "1h" },
  { label: "6h", value: "6h" },
  { label: "24h", value: "24h" },
];

onMounted(() => {
  void store.loadLogs();
});

function load() {
  void store.loadLogs();
}

function handleRangeChange(value: string | number | boolean) {
  void store.setRange(value as RangeKey);
}

function levelTagType(level: string) {
  const normalized = level.toLowerCase();
  if (normalized === "error") {
    return "danger";
  }
  if (normalized === "warn" || normalized === "warning") {
    return "warning";
  }
  if (normalized === "debug") {
    return "info";
  }
  return "success";
}
</script>

<style scoped>
.logs-page {
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
.summary-card span,
.section-head span {
  color: #8fa3bf;
}

h1,
h2 {
  margin: 6px 0 0;
}

.filter-panel,
.table-panel,
.summary-card {
  background: rgba(13, 20, 33, 0.98);
  border: 1px solid rgba(143, 163, 191, 0.18);
  border-radius: 16px;
}

.filter-panel {
  display: grid;
  grid-template-columns: minmax(240px, 1fr) 160px 180px auto;
  gap: 12px;
  padding: 18px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 16px;
}

.summary-card {
  min-height: 112px;
  display: grid;
  gap: 8px;
  padding: 18px;
}

.summary-card strong {
  font-size: 32px;
}

.table-panel {
  padding: 20px;
}

.logs-table {
  margin-top: 16px;
}

.state-panel {
  min-height: 120px;
  display: grid;
  place-items: center;
  border-radius: 16px;
  border: 1px dashed rgba(143, 163, 191, 0.3);
  color: #8fa3bf;
  margin-top: 16px;
}

@media (max-width: 960px) {
  .filter-panel {
    grid-template-columns: 1fr;
  }
}
</style>
