import { beforeEach, describe, expect, it, vi } from "vitest";

import { fetchOverview, fetchTimeseries } from "../api/monitor";
import { http } from "../api/http";

vi.mock("../api/http", () => ({
  http: {
    get: vi.fn(),
  },
}));

describe("monitor api", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("parses overview response", async () => {
    vi.mocked(http.get).mockResolvedValueOnce({
      data: {
        generatedAt: "2026-04-21T15:00:00Z",
        items: [{ metric: "cpu", label: "CPU", value: 42.5, unit: "%" }],
      },
    });

    const result = await fetchOverview();
    expect(result.items[0].metric).toBe("cpu");
  });

  it("parses timeseries response", async () => {
    vi.mocked(http.get).mockResolvedValueOnce({
      data: {
        metric: "gpu",
        range: "1h",
        step: "1m",
        series: [{ timestamp: "2026-04-21T14:01:00Z", value: 8192, unit: "MiB" }],
      },
    });

    const result = await fetchTimeseries("gpu", "1h", "1m");
    expect(result.series[0].unit).toBe("MiB");
  });

  it("fetches gpu depth timeseries", async () => {
    vi.mocked(http.get).mockResolvedValueOnce({
      data: {
        metric: "gpu_utilization",
        range: "1h",
        step: "1m",
        series: [],
      },
    });

    await fetchTimeseries("gpu_utilization", "1h", "1m");

    expect(http.get).toHaveBeenCalledWith("/monitor/timeseries", {
      params: { metric: "gpu_utilization", range: "1h", step: "1m" },
    });
  });
});
