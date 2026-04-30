import { describe, expect, it, vi } from "vitest";

import { fetchModelList, fetchModelMonitorOverview, fetchModelMonitorTimeseries } from "../api/modelMonitor";
import { http } from "../api/http";

vi.mock("../api/http", () => ({
  http: {
    get: vi.fn(),
  },
}));

describe("model monitor api", () => {
  it("fetches overview", async () => {
    vi.mocked(http.get).mockResolvedValueOnce({ data: { generatedAt: "now", items: [] } });

    const response = await fetchModelMonitorOverview();

    expect(http.get).toHaveBeenCalledWith("/model-monitor/overview");
    expect(response.items).toEqual([]);
  });

  it("fetches models", async () => {
    vi.mocked(http.get).mockResolvedValueOnce({ data: { generatedAt: "now", items: [] } });

    const response = await fetchModelList();

    expect(http.get).toHaveBeenCalledWith("/model-monitor/models");
    expect(response.items).toEqual([]);
  });

  it("fetches timeseries", async () => {
    vi.mocked(http.get).mockResolvedValueOnce({ data: { metric: "latency", range: "1h", step: "1m", series: [] } });

    await fetchModelMonitorTimeseries("latency", "1h", "1m");

    expect(http.get).toHaveBeenCalledWith("/model-monitor/timeseries", {
      params: { metric: "latency", range: "1h", step: "1m" },
    });
  });

  it("fetches extended inference metric timeseries", async () => {
    vi.mocked(http.get).mockResolvedValueOnce({
      data: { metric: "tokens_per_second", range: "1h", step: "1m", series: [] },
    });

    await fetchModelMonitorTimeseries("tokens_per_second", "1h", "1m");

    expect(http.get).toHaveBeenCalledWith("/model-monitor/timeseries", {
      params: { metric: "tokens_per_second", range: "1h", step: "1m" },
    });
  });
});
