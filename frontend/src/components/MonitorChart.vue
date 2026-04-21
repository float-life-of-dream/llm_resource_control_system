<template>
  <div class="chart-card">
    <div class="chart-head">
      <div>
        <span class="label">{{ title }}</span>
        <h3>{{ title }} Trend</h3>
      </div>
      <span class="unit">{{ unit }}</span>
    </div>
    <v-chart class="chart" :option="option" autoresize />
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import VChart from "vue-echarts";
import { CanvasRenderer } from "echarts/renderers";
import { GridComponent, LegendComponent, TooltipComponent } from "echarts/components";
import { LineChart } from "echarts/charts";
import { use } from "echarts/core";

import type { TimeseriesPoint } from "../types/monitor";

use([CanvasRenderer, GridComponent, TooltipComponent, LegendComponent, LineChart]);

const props = defineProps<{
  title: string;
  unit: string;
  series: TimeseriesPoint[];
}>();

const option = computed(() => ({
  tooltip: {
    trigger: "axis",
  },
  grid: {
    top: 24,
    right: 16,
    bottom: 16,
    left: 48,
  },
  xAxis: {
    type: "category",
    boundaryGap: false,
    data: props.series.map((point) => new Date(point.timestamp).toLocaleTimeString("zh-CN")),
    axisLabel: { color: "#8fa3bf" },
  },
  yAxis: {
    type: "value",
    axisLabel: { color: "#8fa3bf" },
    splitLine: {
      lineStyle: { color: "rgba(143, 163, 191, 0.12)" },
    },
  },
  series: [
    {
      data: props.series.map((point) => point.value),
      type: "line",
      smooth: true,
      areaStyle: {
        color: "rgba(75, 192, 192, 0.12)",
      },
      lineStyle: {
        color: "#4bc0c0",
        width: 3,
      },
      showSymbol: false,
    },
  ],
}));
</script>

<style scoped>
.chart-card {
  background: rgba(13, 20, 33, 0.98);
  border: 1px solid rgba(143, 163, 191, 0.18);
  border-radius: 24px;
  padding: 20px;
}

.chart-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.label,
.unit {
  color: #8fa3bf;
}

h3 {
  margin: 6px 0 0;
}

.chart {
  height: 280px;
}
</style>
