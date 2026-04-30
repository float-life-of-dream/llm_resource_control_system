import { defineStore } from "pinia";

import { fetchModelList, fetchModelMonitorOverview, fetchModelMonitorTimeseries } from "../api/modelMonitor";
import type { RangeKey, StepKey, TimeseriesPoint } from "../types/monitor";
import type { ModelInfo, ModelMonitorMetricKey, ModelMonitorOverviewItem } from "../types/modelMonitor";

const DEFAULT_METRICS: ModelMonitorMetricKey[] = [
  "request_rate",
  "latency",
  "concurrency",
  "tokens_per_second",
  "error_rate",
  "loaded_models",
];

export const useModelMonitorStore = defineStore("modelMonitor", {
  state: () => ({
    range: "1h" as RangeKey,
    step: "1m" as StepKey,
    generatedAt: "",
    overview: [] as ModelMonitorOverviewItem[],
    models: [] as ModelInfo[],
    seriesMap: {} as Record<ModelMonitorMetricKey, TimeseriesPoint[]>,
    isLoading: false,
    error: "",
  }),
  actions: {
    async loadModelMonitor() {
      this.isLoading = true;
      this.error = "";

      try {
        const [overview, models] = await Promise.all([fetchModelMonitorOverview(), fetchModelList()]);
        this.generatedAt = overview.generatedAt;
        this.overview = overview.items;
        this.models = models.items;

        const responses = await Promise.all(
          DEFAULT_METRICS.map((metric) => fetchModelMonitorTimeseries(metric, this.range, this.step)),
        );
        this.seriesMap = responses.reduce<Record<ModelMonitorMetricKey, TimeseriesPoint[]>>(
          (acc, item) => {
            acc[item.metric] = item.series;
            return acc;
          },
          {} as Record<ModelMonitorMetricKey, TimeseriesPoint[]>,
        );
      } catch (error) {
        this.error = error instanceof Error ? error.message : "Failed to load model monitor data";
      } finally {
        this.isLoading = false;
      }
    },
    async setRange(range: RangeKey) {
      this.range = range;
      await this.loadModelMonitor();
    },
  },
});
