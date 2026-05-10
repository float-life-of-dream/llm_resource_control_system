import { defineStore } from "pinia";

import { fetchPrometheusHealth, fetchPrometheusMetrics, fetchPrometheusTargets } from "../api/prometheus";
import type {
  PrometheusHealthResponse,
  PrometheusMetricGroup,
  PrometheusTarget,
} from "../types/prometheus";

export const usePrometheusStore = defineStore("prometheus", {
  state: () => ({
    health: null as PrometheusHealthResponse | null,
    targets: [] as PrometheusTarget[],
    metricGroups: [] as PrometheusMetricGroup[],
    generatedAt: "",
    isLoading: false,
    error: "",
  }),
  getters: {
    targetSummary(state) {
      return state.targets.reduce(
        (summary, target) => {
          if (target.health === "up") {
            summary.up += 1;
          } else {
            summary.down += 1;
          }
          return summary;
        },
        { up: 0, down: 0 },
      );
    },
  },
  actions: {
    async loadPrometheusStatus() {
      this.isLoading = true;
      this.error = "";

      try {
        const [health, targets, metrics] = await Promise.all([
          fetchPrometheusHealth(),
          fetchPrometheusTargets(),
          fetchPrometheusMetrics(),
        ]);
        this.health = health;
        this.targets = targets.items;
        this.metricGroups = metrics.groups;
        this.generatedAt = targets.generatedAt || health.generatedAt;
      } catch (error) {
        this.error = error instanceof Error ? error.message : "Failed to load Prometheus status";
      } finally {
        this.isLoading = false;
      }
    },
  },
});
