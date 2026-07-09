// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

import TrendBarChart from "../TrendBarChart.vue";

// Mock vue-chartjs Bar component since canvas rendering isn't available in jsdom
vi.mock("vue-chartjs", () => ({
  Bar: {
    props: ["data", "options"],
    template:
      "<canvas data-testid='mock-bar-chart' /><div class='mock-labels'>{{ data?.labels?.join(', ') }}</div>",
  },
}));

describe("TrendBarChart", () => {
  it("renders a canvas element", () => {
    const wrapper = mount(TrendBarChart, {
      props: {
        items: [{ period: "2024-01", total_spent: 10, receipt_count: 1 }],
        granularity: "Monatlich",
      },
    });
    expect(wrapper.find("canvas").exists()).toBe(true);
  });

  it("renders monthly labels", () => {
    const wrapper = mount(TrendBarChart, {
      props: {
        items: [
          { period: "2024-01", total_spent: 10, receipt_count: 1 },
          { period: "2024-02", total_spent: 20, receipt_count: 2 },
        ],
        granularity: "Monatlich",
      },
    });
    expect(wrapper.text()).toContain("2024-01");
    expect(wrapper.text()).toContain("2024-02");
  });

  it("wraps chart in scrollable container for monthly granularity", () => {
    const wrapper = mount(TrendBarChart, {
      props: {
        items: [{ period: "2024-01", total_spent: 10, receipt_count: 1 }],
        granularity: "Monatlich",
      },
    });
    expect(wrapper.find(".overflow-x-auto").exists()).toBe(true);
  });

  it("renders yearly labels", () => {
    const wrapper = mount(TrendBarChart, {
      props: {
        items: [
          { period: "2024", total_spent: 100, receipt_count: 12 },
          { period: "2025", total_spent: 200, receipt_count: 24 },
        ],
        granularity: "Jährlich",
      },
    });
    expect(wrapper.text()).toContain("2024");
    expect(wrapper.text()).toContain("2025");
  });
});
