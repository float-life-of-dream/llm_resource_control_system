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
        title="监控数据加载失败"
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
</style>
