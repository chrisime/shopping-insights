// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import DashboardSkeleton from "../DashboardSkeleton.vue";
import KpiRow from "../KpiRow.vue";
import TopItemsPanel from "../TopItemsPanel.vue";
import TrendChartPanel from "../TrendChartPanel.vue";
import WeekdayPanel from "../WeekdayPanel.vue";

describe("dashboard panels", () => {
  it("uses the shared panel shell classes", () => {
    const kpi = mount(KpiRow, {
      props: { items: [{ label: "Ausgaben gesamt", value: "€10.00" }] },
    });

    expect(kpi.classes()).toEqual(expect.arrayContaining(["grid", "gap-3", "sm:grid-cols-2", "xl:grid-cols-4"]));
    expect(kpi.find("article").classes()).toEqual(
      expect.arrayContaining(["rounded-2xl", "border", "border-sky-200", "bg-sky-50/80", "shadow-sm"]),
    );

    const trend = mount(TrendChartPanel, {
      props: { items: [{ period: "2024-01", total_spent: 10, receipt_count: 1 }] },
    });
    expect(trend.classes()).toEqual(expect.arrayContaining(["grid", "gap-3"]));
    expect(trend.find("li").classes()).toEqual(
      expect.arrayContaining(["rounded-2xl", "border", "border-slate-200", "bg-slate-50/80"]),
    );

    const weekday = mount(WeekdayPanel, {
      props: { items: [{ weekday_name: "Montag", trip_count: 1, avg_spent: 10, total_spent: 10 }] },
    });
    expect(weekday.find("li").classes()).toEqual(
      expect.arrayContaining(["rounded-2xl", "border", "border-slate-200", "bg-slate-50/80"]),
    );

    const topItems = mount(TopItemsPanel, {
      props: { items: [{ name: "Apfel", total_quantity: 2, total_spent: 4, purchase_count: 1, unit: "pc" }] },
    });
    expect(topItems.find("li").classes()).toEqual(
      expect.arrayContaining(["rounded-2xl", "border", "border-slate-200", "bg-slate-50/80"]),
    );

    const skeleton = mount(DashboardSkeleton);
    expect(skeleton.classes()).toContain("grid");
    expect(skeleton.findAll(".dashboard-skeleton__block")).toHaveLength(4);
    expect(skeleton.find(".dashboard-skeleton__block--wide").classes()).toContain("h-32");
  });
});
