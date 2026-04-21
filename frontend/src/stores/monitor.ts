import { defineStore } from "pinia";

import { fetchOverview, fetchTimeseries } from "../api/monitor";
import type { MetricKey, OverviewItem, RangeKey, StepKey, TimeseriesPoint } from "../types/monitor";

const DEFAULT_METRICS: MetricKey[] = ["cpu", "memory", "disk", "gpu"];

export const useMonitorStore = defineStore("monitor", {
  state: () => ({
    range: "1h" as RangeKey,
    step: "1m" as StepKey,
    generatedAt: "",
    overview: [] as OverviewItem[],
    seriesMap: {} as Record<MetricKey, TimeseriesPoint[]>,
    isLoading: false,
    error: "",
  }),
  actions: {
    async loadDashboard() {
      this.isLoading = true;
      this.error = "";

      try {
        const overview = await fetchOverview();
        this.generatedAt = overview.generatedAt;
        this.overview = overview.items;

        const responses = await Promise.all(
          DEFAULT_METRICS.map((metric) => fetchTimeseries(metric, this.range, this.step)),
        );
        this.seriesMap = responses.reduce(
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
