import { defineStore } from "pinia";

import { fetchAnalysisDetail, fetchAnalysisHistory, runAnalysis } from "../api/analysis";
import type { AnalysisDetail, AnalysisHistoryItem, AnalysisRunResponse } from "../types/analysis";
import type { RangeKey } from "../types/monitor";

export const useAnalysisStore = defineStore("analysis", {
  state: () => ({
    current: null as AnalysisRunResponse | null,
    history: [] as AnalysisHistoryItem[],
    detail: null as AnalysisDetail | null,
    isRunning: false,
    isHistoryLoading: false,
    isDetailLoading: false,
    error: "",
  }),
  actions: {
    async run(payload: { range: RangeKey; logQuery: string; logLimit: number; includeMetrics: boolean }) {
      this.isRunning = true;
      this.error = "";
      try {
        const response = await runAnalysis(payload);
        this.current = response;
        await this.loadHistory();
        return response;
      } catch (error) {
        this.error = error instanceof Error ? error.message : "Failed to run analysis";
        throw error;
      } finally {
        this.isRunning = false;
      }
    },
    async loadHistory() {
      this.isHistoryLoading = true;
      try {
        const response = await fetchAnalysisHistory();
        this.history = response.items;
      } finally {
        this.isHistoryLoading = false;
      }
    },
    async loadDetail(analysisId: string) {
      this.isDetailLoading = true;
      this.error = "";
      try {
        const response = await fetchAnalysisDetail(analysisId);
        this.detail = response;
        return response;
      } catch (error) {
        this.error = error instanceof Error ? error.message : "Failed to load analysis detail";
        throw error;
      } finally {
        this.isDetailLoading = false;
      }
    },
  },
});
