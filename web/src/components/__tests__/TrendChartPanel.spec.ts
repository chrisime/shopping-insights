// @vitest-environment jsdom

import { describe, expect, it, vi } from "vite-plus/test";
import { mount } from "@vue/test-utils";
import type TrendBarChart from "../TrendBarChart.vue";
import TrendChartPanel from "../TrendChartPanel.vue";

vi.mock("../TrendBarChart.vue", () => ({
  default: {
    props: ["items", "granularity", "monthLabels"],
    template: "<div><slot /></div>",
  },
}));

describe("TrendChartPanel", () => {
  it("computes monthLabels for daily items grouped by month", () => {
    const wrapper = mount(TrendChartPanel, {
      props: {
        timeGranularity: "daily",
        items: [
          { period: "2024-03-01", total_spent: 10, receipt_count: 1 },
          { period: "2024-03-15", total_spent: 20, receipt_count: 1 },
          { period: "2024-04-01", total_spent: 30, receipt_count: 1 },
        ],
      },
    });

    const barChart = wrapper.getComponent<typeof TrendBarChart>("[data-testid=trend-bar-chart]");
    expect(barChart.props("monthLabels")).toEqual([
      { label: "März 2024", start: 0, end: 1 },
      { label: "April 2024", start: 2, end: 2 },
    ]);
  });

  it("returns empty monthLabels for non-daily granularity", () => {
    const wrapper = mount(TrendChartPanel, {
      props: {
        timeGranularity: "monthly",
        items: [
          { period: "2024-03-01", total_spent: 10, receipt_count: 1 },
          { period: "2024-03-15", total_spent: 20, receipt_count: 1 },
        ],
      },
    });

    const barChart = wrapper.getComponent<typeof TrendBarChart>("[data-testid=trend-bar-chart]");
    expect(barChart.props("monthLabels")).toEqual([]);
  });

  it("renders no TrendBarChart for empty items", () => {
    const wrapper = mount(TrendChartPanel, {
      props: {
        timeGranularity: "daily",
        items: [],
      },
    });

    expect(wrapper.findComponent("[data-testid=trend-bar-chart]").exists()).toBe(false);
  });
});
