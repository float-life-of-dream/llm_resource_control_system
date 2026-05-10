import { describe, expect, it, vi } from "vitest";

import { fetchPrometheusHealth, fetchPrometheusMetrics, fetchPrometheusTargets } from "../api/prometheus";
import { http } from "../api/http";

vi.mock("../api/http", () => ({
  http: {
    get: vi.fn(),
  },
}));

describe("prometheus api", () => {
  it("fetches health", async () => {
    vi.mocked(http.get).mockResolvedValueOnce({
      data: { status: "up", baseUrl: "http://prometheus:9090", generatedAt: "now" },
    });

    const response = await fetchPrometheusHealth();

    expect(http.get).toHaveBeenCalledWith("/prometheus/health");
    expect(response.status).toBe("up");
  });

  it("fetches targets", async () => {
    vi.mocked(http.get).mockResolvedValueOnce({ data: { generatedAt: "now", items: [] } });

    const response = await fetchPrometheusTargets();

    expect(http.get).toHaveBeenCalledWith("/prometheus/targets");
    expect(response.items).toEqual([]);
  });

  it("fetches whitelist metric catalog", async () => {
    vi.mocked(http.get).mockResolvedValueOnce({ data: { generatedAt: "now", groups: [] } });

    const response = await fetchPrometheusMetrics();

    expect(http.get).toHaveBeenCalledWith("/prometheus/metrics");
    expect(response.groups).toEqual([]);
  });
});
