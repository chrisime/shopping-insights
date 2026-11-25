// @vitest-environment jsdom

import { enableAutoUnmount, flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vite-plus/test";

import TrendChartPanel from "../TrendChartPanel.vue";

enableAutoUnmount(afterEach);

describe("TrendChartPanel", () => {
  beforeEach(() => {
    vi.spyOn(HTMLElement.prototype, "clientWidth", "get").mockReturnValue(800);
    vi.spyOn(HTMLElement.prototype, "clientHeight", "get").mockReturnValue(500);
    vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockReturnValue(null);
    vi.stubGlobal(
      "ResizeObserver",
      class {
        observe() {}
        disconnect() {}
      },
    );
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it("renders the default monthly chart and updates the SVG for daily data", async () => {
    const items = [{ period: "2025-01", total_spent: 10, receipt_count: 1 }];
    const wrapper = mount(TrendChartPanel, { props: { items } });
    await vi.dynamicImportSettled();
    await flushPromises();
    expect(wrapper.get("h3").text()).toBe("Monate");
    expect(wrapper.get('[data-testid="trend-bar-chart"] svg').text()).toContain("Jan 2025");

    await wrapper.setProps({
      timeGranularity: "daily",
      items: [
        { ...items[0], period: "2024-12-31" },
        { ...items[0], period: "2025-01-01" },
      ],
    });

    expect(wrapper.get("h3").text()).toBe("Tage");
    const chart = wrapper.get('[data-testid="trend-bar-chart"] svg');
    expect(chart.text()).toContain("Dezember 2024");
    expect(chart.text()).toContain("Januar 2025");
    expect(wrapper.get('[data-testid="trend-year-overlay"]').text()).toBe("20242025");
  });

  it("renders no chart for empty items", () => {
    const wrapper = mount(TrendChartPanel, { props: { items: [] } });

    expect(wrapper.find('[data-testid="trend-bar-chart"]').exists()).toBe(false);
    expect(wrapper.find("h3").exists()).toBe(false);
  });
});
