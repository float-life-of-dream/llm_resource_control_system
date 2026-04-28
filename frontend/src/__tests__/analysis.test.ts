import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";

import { useAnalysisStore } from "../stores/analysis";

vi.mock("../api/analysis", () => ({
  runAnalysis: vi.fn().mockResolvedValue({
    analysisId: "a1",
    status: "completed",
    summary: "GPU usage is high.",
    anomalies: ["GPU usage stayed high."],
    recommendations: ["Check backlog."],
    evidenceSummary: { metrics: ["cpu", "gpu"], logCount: 2 },
    model: "llama3.1:8b",
    durationMs: 1500,
  }),
  fetchAnalysisHistory: vi.fn().mockResolvedValue({
    items: [
      {
        analysisId: "a1",
        status: "completed",
        range: "1h",
        logQuery: "timeout",
        logLimit: 50,
        includeMetrics: true,
        model: "llama3.1:8b",
        durationMs: 1500,
        createdAt: "2026-04-21T15:00:00Z",
        completedAt: "2026-04-21T15:00:01Z",
        summary: "GPU usage is high.",
        evidenceSummary: { metrics: ["cpu", "gpu"], logCount: 2 },
      },
    ],
  }),
  fetchAnalysisDetail: vi.fn().mockResolvedValue({
    analysisId: "a1",
    status: "completed",
    range: "1h",
    logQuery: "timeout",
    logLimit: 50,
    includeMetrics: true,
    model: "llama3.1:8b",
    durationMs: 1500,
    createdAt: "2026-04-21T15:00:00Z",
    completedAt: "2026-04-21T15:00:01Z",
    summary: "GPU usage is high.",
    anomalies: ["GPU usage stayed high."],
    recommendations: ["Check backlog."],
    rawModelOutput: "{}",
    evidence: { metricsSnapshot: { cpu: { current: 42.5 } }, logExcerpt: [{ message: "timeout" }] },
    user: { id: "u1", email: "admin@example.local", fullName: "Admin", isSystemAdmin: true },
    tenant: { id: "t1", name: "Default Tenant", slug: "default" },
    evidenceSummary: { metrics: ["cpu", "gpu"], logCount: 2 },
  }),
}));

describe("analysis store", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("runs analysis and loads history", async () => {
    const store = useAnalysisStore();
    await store.run({ range: "1h", logQuery: "timeout", logLimit: 50, includeMetrics: true });
    expect(store.current?.analysisId).toBe("a1");
    expect(store.history[0].analysisId).toBe("a1");
  });
});
