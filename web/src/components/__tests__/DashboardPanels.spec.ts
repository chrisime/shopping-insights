// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vite-plus/test";

import DashboardSkeleton from "../DashboardSkeleton.vue";
import TrendChartPanel from "../TrendChartPanel.vue";
import WeekdayPanel from "../WeekdayPanel.vue";

describe("dashboard panels", () => {
  it("renders the new vertical bar charts", () => {
    const monthly = mount(TrendChartPanel, {
      props: {
        timeGranularity: "monthly",
        items: [
          { period: "2023-01", total_spent: 10, receipt_count: 1 },
          { period: "2023-02", total_spent: 20, receipt_count: 2 },
          { period: "2024-01", total_spent: 30, receipt_count: 3 },
        ],
      },
    });

    expect(monthly.text()).toContain("2023");
    expect(monthly.text()).toContain("Jan 2023");
    expect(monthly.text()).toContain("10,00 €");
    expect(monthly.find("[data-testid=trend-chart-svg]").exists()).toBe(true);
    expect(monthly.find("[data-testid=trend-chart-y-axis-svg]").exists()).toBe(true);
    expect(monthly.html()).not.toMatch(/<details[\s>]/);

    const daily = mount(TrendChartPanel, {
      props: {
        timeGranularity: "daily",
        items: [
          { period: "2024-01-01", total_spent: 10, receipt_count: 1 },
          { period: "2024-01-02", total_spent: 20, receipt_count: 2 },
          { period: "2024-02-01", total_spent: 30, receipt_count: 3 },
        ],
      },
    });

    expect(daily.text()).toContain("01");
    expect(daily.text()).toContain("02");
    expect(daily.text()).toContain("Tage");
    expect(daily.find("[data-testid=trend-chart-svg]").exists()).toBe(true);
    expect(daily.find("[data-testid=trend-chart-y-axis-svg]").exists()).toBe(true);

    const trend = mount(TrendChartPanel, {
      props: {
        items: [
          { period: "2024-01", total_spent: 10, receipt_count: 1 },
          { period: "2024-02", total_spent: 5, receipt_count: 2 },
        ],
      },
    });
    expect(trend.text()).toContain("Jan 2024");
    expect(trend.text()).toContain("Feb 2024");
    expect(trend.find("[data-testid=trend-chart-svg]").exists()).toBe(true);
    expect(trend.find("[data-testid=trend-chart-y-axis-svg]").exists()).toBe(true);

    const yearly = mount(TrendChartPanel, {
      props: {
        timeGranularity: "yearly",
        items: [
          { period: "2023", total_spent: 100, receipt_count: 12 },
          { period: "2024", total_spent: 200, receipt_count: 24 },
          { period: "2025", total_spent: 150, receipt_count: 18 },
        ],
      },
    });

    expect(yearly.text()).toContain("2023");
    expect(yearly.text()).toContain("2024");
    expect(yearly.text()).toContain("2025");
    expect(yearly.find("[data-testid=trend-chart-svg]").exists()).toBe(true);
    expect(yearly.find("[data-testid=trend-chart-y-axis-svg]").exists()).toBe(true);
  });

  it("renders weekday and skeleton", () => {
    const weekday = mount(WeekdayPanel, {
      props: {
        items: [
          { weekday: 0, weekday_name: "Montag", trip_count: 1, avg_spent: 10, total_spent: 10 },
          { weekday: 1, weekday_name: "Dienstag", trip_count: 2, avg_spent: 5, total_spent: 10 },
        ],
      },
    });
    expect(weekday.text()).toContain("Montag");
    expect(weekday.text()).toContain("Anzahl Einkäufe");
    expect(weekday.text()).toContain("Ø Ausgaben pro Einkauf");
    expect(weekday.findAll("[data-testid=weekday-bar]")).toHaveLength(4);

    const skeleton = mount(DashboardSkeleton);
    expect(skeleton.text()).toBe("");
    const blocks = skeleton.element.children;
    expect(blocks).toHaveLength(4);
    expect(blocks[0]?.classList.contains("h-32")).toBe(true);
    expect(blocks[0]?.classList.contains("animate-pulse")).toBe(true);
  });

  it("handles year boundary for daily granularity (Dec 2024 → Jan 2025)", () => {
    const daily = mount(TrendChartPanel, {
      props: {
        timeGranularity: "daily",
        items: [
          { period: "2024-12-30", total_spent: 10, receipt_count: 1 },
          { period: "2024-12-31", total_spent: 15, receipt_count: 2 },
          { period: "2025-01-01", total_spent: 20, receipt_count: 1 },
          { period: "2025-01-02", total_spent: 25, receipt_count: 3 },
        ],
      },
    });

    expect(daily.text()).toContain("30");
    expect(daily.text()).toContain("31");
    expect(daily.text()).toContain("01");
    expect(daily.text()).toContain("02");
    expect(daily.find("[data-testid=trend-chart-svg]").exists()).toBe(true);
    expect(daily.find("[data-testid=trend-chart-y-axis-svg]").exists()).toBe(true);
    expect(daily.text()).toContain("Tage");
  });

  it("renders absolute time-series summary stats", () => {
    const trend = mount(TrendChartPanel, {
      props: {
        items: [
          { period: "2024-01", total_spent: 10, receipt_count: 1 },
          { period: "2024-02", total_spent: 5, receipt_count: 2 },
        ],
      },
    });

    expect(trend.text()).toContain("Ø Ausgaben pro Zeitraum");
    expect(trend.text()).toContain("7,50 €");
    expect(trend.text()).toContain("10,00 €");
    expect(trend.text()).toContain("5,00 €");
  });
});
