<template>
  <AdminLayout>
    <section class="dashboard">
      <PageHeader :generated-at="store.generatedAt" />

      <el-segmented
        :model-value="store.range"
        :options="rangeOptions"
        class="range-switch"
        @change="handleRangeChange"
      />

      <el-alert
        v-if="store.error"
        title="Monitor data failed to load"
        :description="store.error"
        type="error"
        show-icon
        :closable="false"
      />

      <div v-if="store.isLoading" class="state-panel">Loading monitor data...</div>

      <template v-else>
        <div v-if="store.overview.length" class="stats-grid">
          <StatCard v-for="item in store.overview" :key="item.metric" :item="item" />
        </div>
        <div v-else class="state-panel">No overview data available.</div>

        <AnalysisPanel :range="store.range" />

        <section class="gpu-panel">
          <div class="section-head">
            <div>
              <span class="eyebrow">NVIDIA DCGM</span>
              <h2>GPU Devices</h2>
            </div>
            <span>{{ store.gpuDevices.length }} detected</span>
          </div>
          <el-table v-if="store.gpuDevices.length" :data="store.gpuDevices" class="gpu-table">
            <el-table-column prop="name" label="Device" min-width="180" />
            <el-table-column prop="uuid" label="UUID" min-width="180" show-overflow-tooltip />
            <el-table-column label="Memory" width="180">
              <template #default="{ row }">{{ row.memoryUsedMiB }} / {{ row.memoryTotalMiB }} MiB</template>
            </el-table-column>
            <el-table-column label="Memory %" width="120">
              <template #default="{ row }">{{ row.memoryUtilizationPercent }}%</template>
            </el-table-column>
            <el-table-column label="GPU %" width="110">
              <template #default="{ row }">{{ row.utilizationPercent }}%</template>
            </el-table-column>
            <el-table-column label="Temp" width="110">
              <template #default="{ row }">{{ row.temperatureCelsius }} C</template>
            </el-table-column>
            <el-table-column label="Power" width="110">
              <template #default="{ row }">{{ row.powerUsageWatts }} W</template>
            </el-table-column>
            <el-table-column prop="status" label="Status" width="120" />
          </el-table>
          <div v-else class="state-panel compact">
            No GPU devices detected. Enable dcgm-exporter on an NVIDIA host to populate this table.
          </div>
        </section>

        <div class="charts-grid">
          <MonitorChart
            v-for="metric in metrics"
            :key="metric.metric"
            :title="metric.label"
            :unit="metric.unit"
            :series="store.seriesMap[metric.metric] ?? []"
          />
        </div>
      </template>
    </section>
  </AdminLayout>
</template>

<script setup lang="ts">
import { onMounted } from "vue";

import AdminLayout from "../layouts/AdminLayout.vue";
import AnalysisPanel from "../components/AnalysisPanel.vue";
import MonitorChart from "../components/MonitorChart.vue";
import PageHeader from "../components/PageHeader.vue";
import StatCard from "../components/StatCard.vue";
import { useMonitorStore } from "../stores/monitor";
import type { RangeKey } from "../types/monitor";

const store = useMonitorStore();
const rangeOptions = [
  { label: "1h", value: "1h" },
  { label: "6h", value: "6h" },
  { label: "24h", value: "24h" },
];

const metrics = [
  { metric: "cpu", label: "CPU", unit: "%" },
  { metric: "memory", label: "Memory", unit: "GiB" },
  { metric: "disk", label: "Disk", unit: "%" },
  { metric: "gpu", label: "GPU", unit: "MiB" },
  { metric: "gpu_utilization", label: "GPU Utilization", unit: "%" },
  { metric: "gpu_memory_used", label: "GPU Memory", unit: "MiB" },
  { metric: "gpu_memory_utilization", label: "GPU Memory %", unit: "%" },
  { metric: "gpu_temperature", label: "GPU Temperature", unit: "C" },
  { metric: "gpu_power_usage", label: "GPU Power", unit: "W" },
] as const;

onMounted(() => {
  void store.loadDashboard();
});

function handleRangeChange(value: string | number | boolean) {
  void store.setRange(value as RangeKey);
}
</script>

<style scoped>
.dashboard {
  display: grid;
  gap: 24px;
}

.range-switch {
  width: fit-content;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}

.gpu-panel {
  background: rgba(13, 20, 33, 0.98);
  border: 1px solid rgba(143, 163, 191, 0.18);
  border-radius: 24px;
  padding: 20px;
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.eyebrow,
.section-head span {
  color: #8fa3bf;
}

.section-head h2 {
  margin: 6px 0 0;
}

.gpu-table {
  margin-top: 8px;
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
  border-radius: 24px;
  border: 1px dashed rgba(143, 163, 191, 0.3);
  color: #8fa3bf;
}

.state-panel.compact {
  min-height: 96px;
}
</style>
