// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import DashboardSkeleton from "../DashboardSkeleton.vue";
import KpiRow from "../KpiRow.vue";
import TopItemsPanel from "../TopItemsPanel.vue";
import TrendChartPanel from "../TrendChartPanel.vue";
import WeekdayPanel from "../WeekdayPanel.vue";

describe("dashboard panels", () => {
  it("renders the payload fields and skeleton state", () => {
    const kpi = mount(KpiRow, {
      props: { items: [{ label: "REWE Bonus", value: "€10.00" }, { label: "Rabatt-Sparquote", value: "12.5%" }] },
    });

    expect(kpi.text()).toContain("REWE Bonus");
    expect(kpi.text()).toContain("€10.00");
    expect(kpi.find("article").classes()).toEqual(
      expect.arrayContaining(["rounded-2xl", "border", "border-slate-200", "bg-slate-50/80", "shadow-sm"]),
    );

    const trend = mount(TrendChartPanel, {
      props: { items: [{ period: "2024-01", total_spent: 10, receipt_count: 1 }, { period: "2024-02", total_spent: 5, receipt_count: 2 }] },
    });
    expect(trend.text()).toContain("2024-01");
    expect(trend.text()).toContain("€10.00");
    expect(trend.text()).toContain("1 Belege");
    expect(trend.findAll(".bg-indigo-500")).toHaveLength(2);
    expect(trend.findAll(".bg-indigo-500")[0].attributes("style")).toContain("width: 100%");

    const zeroTrend = mount(TrendChartPanel, {
      props: { items: [{ period: "2024-03", total_spent: 0, receipt_count: 0 }] },
    });
    expect(zeroTrend.find(".bg-indigo-500").attributes("style")).toContain("width: 0%");

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
      props: { items: [{ name: "Apfel", total_quantity: 2, total_spent: 4, purchase_count: 1, unit: "pc" }] },
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
      props: { items: [{ name: "Tomaten", total_quantity: 0.696, total_spent: 3.99, purchase_count: 1, unit: "kg" }] },
    });

    expect(topItems.text()).toContain("Tomaten");
    expect(topItems.text()).toContain("0.696 kg");
    expect(topItems.text()).toContain("€3.99");
  });
});
