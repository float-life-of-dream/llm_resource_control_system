import { describe, expect, it, vi } from "vitest";

import { fetchLogServices, fetchLogSummary, searchLogs } from "../api/logs";
import { http } from "../api/http";

vi.mock("../api/http", () => ({
  http: {
    get: vi.fn(),
  },
}));

describe("logs api", () => {
  it("searches logs with filters", async () => {
    vi.mocked(http.get).mockResolvedValueOnce({ data: { generatedAt: "now", range: "1h", total: 0, items: [] } });

    const response = await searchLogs({
      range: "1h",
      query: "timeout",
      level: "error",
      service: "backend",
      limit: 100,
    });

    expect(http.get).toHaveBeenCalledWith("/logs/search", {
      params: { range: "1h", query: "timeout", level: "error", service: "backend", limit: 100 },
    });
    expect(response.items).toEqual([]);
  });

  it("fetches log summary", async () => {
    vi.mocked(http.get).mockResolvedValueOnce({ data: { generatedAt: "now", total: 0, levels: [], services: [] } });

    await fetchLogSummary("6h", "exception");

    expect(http.get).toHaveBeenCalledWith("/logs/summary", { params: { range: "6h", query: "exception" } });
  });

  it("fetches log service options", async () => {
    vi.mocked(http.get).mockResolvedValueOnce({ data: { generatedAt: "now", items: ["backend"] } });

    const response = await fetchLogServices("24h");

    expect(http.get).toHaveBeenCalledWith("/logs/services", { params: { range: "24h" } });
    expect(response.items).toEqual(["backend"]);
  });
});
