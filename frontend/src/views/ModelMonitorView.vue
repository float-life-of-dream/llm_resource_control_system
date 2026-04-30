<template>
  <AdminLayout>
    <section class="model-monitor">
      <div class="page-head">
        <div>
          <span class="eyebrow">Ollama Runtime</span>
          <h1>Model Monitor</h1>
        </div>
        <el-segmented :model-value="store.range" :options="rangeOptions" @change="handleRangeChange" />
      </div>

      <el-alert
        v-if="store.error"
        title="Model monitor data failed to load"
        :description="store.error"
        type="error"
        show-icon
        :closable="false"
      />

      <div v-if="store.isLoading" class="state-panel">Loading model telemetry...</div>

      <template v-else>
        <div class="stats-grid">
          <div v-for="item in store.overview" :key="item.metric" class="stat-card">
            <span class="label">{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
            <span class="unit">{{ item.unit }}</span>
          </div>
        </div>

        <section class="table-panel">
          <div class="section-head">
            <h2>Loaded Models</h2>
            <span>{{ store.models.length }} active</span>
          </div>
          <el-table v-if="store.models.length" :data="store.models" class="model-table">
            <el-table-column prop="name" label="Model" min-width="220" />
            <el-table-column prop="parameterSize" label="Parameters" width="140" />
            <el-table-column prop="quantization" label="Quantization" width="140" />
            <el-table-column label="Context" width="120">
              <template #default="{ row }">{{ row.contextWindow || "-" }}</template>
            </el-table-column>
            <el-table-column label="Memory" width="140">
              <template #default="{ row }">{{ formatBytes(row.memoryBytes) }}</template>
            </el-table-column>
            <el-table-column prop="status" label="Status" width="120" />
          </el-table>
          <div v-else class="state-panel compact">No loaded Ollama models detected.</div>
        </section>

        <div class="charts-grid">
          <MonitorChart title="Request Rate" unit="req/s" :series="store.seriesMap.request_rate ?? []" />
          <MonitorChart title="Avg Latency" unit="s" :series="store.seriesMap.latency ?? []" />
          <MonitorChart title="Concurrency" unit="" :series="store.seriesMap.concurrency ?? []" />
          <MonitorChart title="Tokens/sec" unit="tok/s" :series="store.seriesMap.tokens_per_second ?? []" />
          <MonitorChart title="Error Rate" unit="err/s" :series="store.seriesMap.error_rate ?? []" />
          <MonitorChart title="Loaded Models" unit="" :series="store.seriesMap.loaded_models ?? []" />
        </div>
      </template>
    </section>
  </AdminLayout>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from "vue";

import AdminLayout from "../layouts/AdminLayout.vue";
import MonitorChart from "../components/MonitorChart.vue";
import { useModelMonitorStore } from "../stores/modelMonitor";
import type { RangeKey } from "../types/monitor";

const store = useModelMonitorStore();
const rangeOptions = [
  { label: "1h", value: "1h" },
  { label: "6h", value: "6h" },
  { label: "24h", value: "24h" },
];

let refreshTimer: number | undefined;

onMounted(() => {
  void store.loadModelMonitor();
  refreshTimer = window.setInterval(() => {
    void store.loadModelMonitor();
  }, 30_000);
});

onUnmounted(() => {
  if (refreshTimer) {
    window.clearInterval(refreshTimer);
  }
});

function handleRangeChange(value: string | number | boolean) {
  void store.setRange(value as RangeKey);
}

function formatBytes(value: number) {
  if (!value) {
    return "-";
  }
  const units = ["B", "KiB", "MiB", "GiB"];
  let size = value;
  let unitIndex = 0;
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex += 1;
  }
  return `${size.toFixed(unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`;
}
</script>

<style scoped>
.model-monitor {
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
h2 {
  margin: 6px 0 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}

.stat-card,
.table-panel {
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
}

.model-table {
  margin-top: 16px;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
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
