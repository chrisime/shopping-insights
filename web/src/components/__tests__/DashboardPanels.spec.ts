// @vitest-environment jsdom

import { mount, shallowMount } from "@vue/test-utils";
import { describe, expect, it } from "vite-plus/test";

import DashboardSkeleton from "../DashboardSkeleton.vue";
import TrendChartPanel from "../TrendChartPanel.vue";
import WeekdayPanel from "../WeekdayPanel.vue";

describe("dashboard panels", () => {
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

  it("renders absolute time-series summary stats", () => {
    const trend = shallowMount(TrendChartPanel, {
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
