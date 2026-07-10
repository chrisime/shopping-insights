// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import DashboardSkeleton from "../DashboardSkeleton.vue";
import TopItemsPanel from "../TopItemsPanel.vue";
import TrendChartPanel from "../TrendChartPanel.vue";
import WeekdayPanel from "../WeekdayPanel.vue";

describe("dashboard panels", () => {
  it("renders the new vertical bar charts", () => {
    const monthly = mount(TrendChartPanel, {
      props: {
        timeGranularity: "Monatlich",
        items: [
          { period: "2023-01", total_spent: 10, receipt_count: 1 },
          { period: "2023-02", total_spent: 20, receipt_count: 2 },
          { period: "2024-01", total_spent: 30, receipt_count: 3 },
        ],
      },
    });

    expect(monthly.text()).toContain("2023");
    expect(monthly.text()).toContain("Jan 2023");
    expect(monthly.text()).toContain("€10.00");
    expect(monthly.findAll("svg").length).toBeGreaterThanOrEqual(2);
    expect(monthly.findAll("details")).toHaveLength(0);

    const daily = mount(TrendChartPanel, {
      props: {
        timeGranularity: "Täglich",
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
    expect(daily.findAll("svg").length).toBeGreaterThanOrEqual(2);

    const trend = mount(TrendChartPanel, {
      props: { items: [{ period: "2024-01", total_spent: 10, receipt_count: 1 }, { period: "2024-02", total_spent: 5, receipt_count: 2 }] },
    });
    expect(trend.text()).toContain("Jan 2024");
    expect(trend.text()).toContain("Feb 2024");
    expect(trend.findAll("svg").length).toBeGreaterThanOrEqual(2);

    const yearly = mount(TrendChartPanel, {
      props: {
        timeGranularity: "Jährlich",
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
    expect(yearly.findAll("svg").length).toBeGreaterThanOrEqual(2);
  });

  it("renders weekday, top items, and skeleton", () => {
    const weekday = mount(WeekdayPanel, {
      props: {
        items: [
          { weekday_name: "Montag", trip_count: 1, avg_spent: 10, total_spent: 10 },
          { weekday_name: "Dienstag", trip_count: 2, avg_spent: 5, total_spent: 10 },
        ],
      },
    });
    expect(weekday.text()).toContain("Montag");
    expect(weekday.text()).toContain("Anzahl Einkäufe");
    expect(weekday.text()).toContain("Ø Ausgaben pro Einkauf");
    expect(weekday.findAll(".bg-indigo-500")).toHaveLength(4);

    const topItems = mount(TopItemsPanel, {
      props: { items: [{ name: "Apfel", total_quantity: 2, total_spent: 4, purchase_count: 1, unit: "pc" }], page: 1, pageSize: 20, totalCount: 1, topLimit: 20 },
    });
    expect(topItems.find("table").exists()).toBe(true);
    expect(topItems.text()).toContain("Artikel");
    expect(topItems.text()).toContain("Gesamtmenge");
    expect(topItems.text()).toContain("Ausgaben");
    expect(topItems.text()).toContain("Einkäufe");
    expect(topItems.text()).toContain("Apfel");
    expect(topItems.text()).toContain("2");
    expect(topItems.text()).toContain("€4.00");
    expect(topItems.text()).toContain("1");
    expect(topItems.text()).toContain("pc");

    const skeleton = mount(DashboardSkeleton);
    expect(skeleton.text()).toBe("");
    expect(skeleton.findAll(".dashboard-skeleton__block")).toHaveLength(4);
    expect(skeleton.find(".dashboard-skeleton__block--wide").classes()).toEqual(
      expect.arrayContaining(["h-32", "animate-pulse"]),
    );
  });

  it("handles year boundary for daily granularity (Dec 2024 → Jan 2025)", () => {
    const daily = mount(TrendChartPanel, {
      props: {
        timeGranularity: "Täglich",
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
    expect(daily.findAll("svg").length).toBeGreaterThanOrEqual(2);
    expect(daily.text()).toContain("Tage");
  });

  it("renders absolute time-series summary stats and top-item quantities", () => {
    const trend = mount(TrendChartPanel, {
      props: {
        spendingView: "Absolut",
        items: [
          { period: "2024-01", total_spent: 10, receipt_count: 1 },
          { period: "2024-02", total_spent: 5, receipt_count: 2 },
        ],
      },
    });

    expect(trend.text()).toContain("Ø Ausgaben pro Zeitraum");
    expect(trend.text()).toContain("€7.50");
    expect(trend.text()).toContain("€10.00");
    expect(trend.text()).toContain("€5.00");

    const topItems = mount(TopItemsPanel, {
      props: { items: [{ name: "Tomaten", total_quantity: 0.696, total_spent: 3.99, purchase_count: 1, unit: "kg" }], page: 1, pageSize: 20, totalCount: 1, topLimit: 20 },
    });

    expect(topItems.text()).toContain("Tomaten");
    expect(topItems.text()).toContain("0.696 kg");
    expect(topItems.text()).toContain("€3.99");
  });
});
