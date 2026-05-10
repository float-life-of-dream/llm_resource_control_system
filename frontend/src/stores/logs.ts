import { defineStore } from "pinia";

import { fetchLogServices, fetchLogSummary, searchLogs } from "../api/logs";
import type { LogBucket, LogItem, LogLevel } from "../types/logs";
import type { RangeKey } from "../types/monitor";

export const useLogsStore = defineStore("logs", {
  state: () => ({
    range: "1h" as RangeKey,
    query: "",
    level: "" as LogLevel,
    service: "",
    limit: 100,
    generatedAt: "",
    total: 0,
    items: [] as LogItem[],
    levels: [] as LogBucket[],
    services: [] as LogBucket[],
    serviceOptions: [] as string[],
    isLoading: false,
    error: "",
  }),
  actions: {
    async loadLogs() {
      this.isLoading = true;
      this.error = "";

      try {
        const [search, summary, services] = await Promise.all([
          searchLogs({
            range: this.range,
            query: this.query,
            level: this.level,
            service: this.service,
            limit: this.limit,
          }),
          fetchLogSummary(this.range, this.query),
          fetchLogServices(this.range),
        ]);
        this.generatedAt = search.generatedAt;
        this.total = search.total;
        this.items = search.items;
        this.levels = summary.levels;
        this.services = summary.services;
        this.serviceOptions = services.items;
      } catch (error) {
        this.error = error instanceof Error ? error.message : "Failed to load logs";
      } finally {
        this.isLoading = false;
      }
    },
    async setRange(range: RangeKey) {
      this.range = range;
      await this.loadLogs();
    },
  },
});
