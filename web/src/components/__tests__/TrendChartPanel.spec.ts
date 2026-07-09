// @vitest-environment jsdom

import { describe, expect, it, vi } from "vitest";
import { mount } from "@vue/test-utils";
import TrendChartPanel from "../TrendChartPanel.vue";

vi.mock("vue-chartjs", () => ({
  Bar: {
    props: ["data", "options"],
    template:
      "<canvas data-testid='mock-bar-chart' /><div class='mock-labels'>{{ data?.labels?.join(', ') }}</div>",
  },
}));

vi.mock("../TrendBarChart.vue", () => ({
  default: {
    props: ["items", "granularity", "monthLabels"],
    template: "<div data-testid='trend-bar-chart'><slot /></div>",
  },
}));

describe("TrendChartPanel", () => {
  it("computes monthLabels for daily items grouped by month", () => {
    const wrapper = mount(TrendChartPanel, {
      props: {
        timeGranularity: "Täglich",
        items: [
          { period: "2024-03-01", total_spent: 10, receipt_count: 1 },
          { period: "2024-03-15", total_spent: 20, receipt_count: 1 },
          { period: "2024-04-01", total_spent: 30, receipt_count: 1 },
        ],
      },
    });

    const barChart = wrapper.findComponent({ name: "TrendBarChart" });
    expect(barChart.props("monthLabels")).toEqual([
      { label: "März 2024", start: 0, end: 1 },
      { label: "April 2024", start: 2, end: 2 },
    ]);
  });

  it("returns empty monthLabels for non-daily granularity", () => {
    const wrapper = mount(TrendChartPanel, {
      props: {
        timeGranularity: "Monatlich",
        items: [
          { period: "2024-03-01", total_spent: 10, receipt_count: 1 },
          { period: "2024-03-15", total_spent: 20, receipt_count: 1 },
        ],
      },
    });

    const barChart = wrapper.findComponent({ name: "TrendBarChart" });
    expect(barChart.props("monthLabels")).toEqual([]);
  });

  it("renders no TrendBarChart for empty items", () => {
    const wrapper = mount(TrendChartPanel, {
      props: {
        timeGranularity: "Täglich",
        items: [],
      },
    });

    expect(wrapper.findComponent({ name: "TrendBarChart" }).exists()).toBe(false);
  });
});
