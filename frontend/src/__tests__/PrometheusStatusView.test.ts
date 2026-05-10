import { createPinia, setActivePinia } from "pinia";
import { mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

import PrometheusStatusView from "../views/PrometheusStatusView.vue";

vi.mock("../api/prometheus", () => ({
  fetchPrometheusHealth: vi.fn().mockResolvedValue({
    status: "up",
    baseUrl: "http://prometheus:9090",
    generatedAt: "2026-04-30T10:00:00Z",
  }),
  fetchPrometheusTargets: vi.fn().mockResolvedValue({
    generatedAt: "2026-04-30T10:00:00Z",
    items: [{ job: "backend", instance: "backend:5000", health: "up", scrapeUrl: "http://backend:5000/metrics", lastScrape: null, lastError: "" }],
  }),
  fetchPrometheusMetrics: vi.fn().mockResolvedValue({
    generatedAt: "2026-04-30T10:00:00Z",
    groups: [{ key: "host", label: "Host Metrics", items: [{ key: "cpu", label: "CPU", unit: "%" }] }],
  }),
}));

describe("PrometheusStatusView", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("renders prometheus status shell", async () => {
    const wrapper = mount(PrometheusStatusView, {
      global: {
        stubs: {
          AdminLayout: { template: "<div><slot /></div>" },
          "el-alert": true,
          "el-button": { template: "<button><slot /></button>" },
          "el-table": { template: "<div><slot /></div>" },
          "el-table-column": true,
          "el-tag": { template: "<span><slot /></span>" },
        },
      },
    });

    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(wrapper.text()).toContain("Prometheus Status");
    expect(wrapper.text()).toContain("Whitelist only");
  });
});
