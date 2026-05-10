import { defineStore } from "pinia";

import { fetchGpuDevices, fetchOverview, fetchTimeseries } from "../api/monitor";
import type { GpuDevice, MetricKey, OverviewItem, RangeKey, StepKey, TimeseriesPoint } from "../types/monitor";

const DEFAULT_METRICS: MetricKey[] = [
  "cpu",
  "memory",
  "disk",
  "gpu",
  "gpu_memory_used",
  "gpu_memory_utilization",
  "gpu_utilization",
  "gpu_temperature",
  "gpu_power_usage",
];

export const useMonitorStore = defineStore("monitor", {
  state: () => ({
    range: "1h" as RangeKey,
    step: "1m" as StepKey,
    generatedAt: "",
    overview: [] as OverviewItem[],
    gpuDevices: [] as GpuDevice[],
    seriesMap: {} as Record<MetricKey, TimeseriesPoint[]>,
    isLoading: false,
    error: "",
  }),
  actions: {
    async loadDashboard() {
      this.isLoading = true;
      this.error = "";

      try {
        const [overview, gpuDevices] = await Promise.all([fetchOverview(), fetchGpuDevices()]);
        this.generatedAt = overview.generatedAt;
        this.overview = overview.items;
        this.gpuDevices = gpuDevices.items;

        const responses = await Promise.all(
          DEFAULT_METRICS.map((metric) => fetchTimeseries(metric, this.range, this.step)),
        );
        this.seriesMap = responses.reduce<Record<MetricKey, TimeseriesPoint[]>>(
          (acc, item) => {
            acc[item.metric] = item.series;
            return acc;
          },
          {} as Record<MetricKey, TimeseriesPoint[]>,
        );
      } catch (error) {
        this.error = error instanceof Error ? error.message : "Failed to load monitor data";
      } finally {
        this.isLoading = false;
      }
    },
    async setRange(range: RangeKey) {
      this.range = range;
      await this.loadDashboard();
    },
  },
});
