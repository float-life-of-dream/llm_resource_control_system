import { createPinia, setActivePinia } from "pinia";
import { mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

import DashboardView from "../views/DashboardView.vue";

vi.mock("../api/monitor", () => ({
  fetchOverview: vi.fn().mockResolvedValue({
    generatedAt: "2026-04-21T15:00:00Z",
    items: [{ metric: "cpu", label: "CPU", value: 42.5, unit: "%" }],
  }),
  fetchGpuDevices: vi.fn().mockResolvedValue({
    generatedAt: "2026-04-21T15:00:00Z",
    items: [],
  }),
  fetchTimeseries: vi.fn().mockResolvedValue({
    metric: "cpu",
    range: "1h",
    step: "1m",
    series: [{ timestamp: "2026-04-21T14:01:00Z", value: 42.5, unit: "%" }],
  }),
}));

describe("DashboardView", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("renders dashboard shell", async () => {
    const wrapper = mount(DashboardView, {
      global: {
        stubs: {
          AdminLayout: { template: "<div><slot /></div>" },
          PageHeader: { template: "<div>Dashboard</div>" },
          StatCard: { template: "<div>Stat Card</div>" },
          AnalysisPanel: { template: "<div>AI Analysis</div>" },
          MonitorChart: { template: "<div>Monitor Chart</div>" },
          "el-table": { template: "<div><slot /></div>" },
          "el-table-column": true,
          "el-segmented": true,
          "el-alert": true,
        },
      },
    });

    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(wrapper.text()).toContain("Dashboard");
  });
});
