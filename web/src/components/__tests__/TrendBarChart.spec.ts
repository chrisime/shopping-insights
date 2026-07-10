// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

import TrendBarChart from "../TrendBarChart.vue";

describe("TrendBarChart", () => {
  it("renders SVG elements for y-axis and bars", () => {
    const wrapper = mount(TrendBarChart, {
      props: {
        items: [{ period: "2024-01", total_spent: 10, receipt_count: 1 }],
        granularity: "Monatlich",
      },
    });
    expect(wrapper.findAll("svg").length).toBe(2);
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

  it("shows day-only labels when monthLabels is provided", () => {
    const wrapper = mount(TrendBarChart, {
      props: {
        items: [
          { period: "2024-01-15", total_spent: 10, receipt_count: 1 },
          { period: "2024-02-20", total_spent: 20, receipt_count: 2 },
        ],
        granularity: "Täglich",
        monthLabels: [
          { label: "Januar 2024", start: 0, end: 0 },
          { label: "Februar 2024", start: 1, end: 1 },
        ],
      },
    });
    expect(wrapper.text()).toContain("15");
    expect(wrapper.text()).toContain("20");
    expect(wrapper.text()).not.toContain("2024-01-15");
    expect(wrapper.text()).not.toContain("2024-02-20");
  });

  it("shows full labels when monthLabels is not provided", () => {
    const wrapper = mount(TrendBarChart, {
      props: {
        items: [
          { period: "2024-01-15", total_spent: 10, receipt_count: 1 },
        ],
        granularity: "Täglich",
      },
    });
    expect(wrapper.text()).toContain("2024-01-15");
  });

  it("emits select-period with monthly boundaries", () => {
    const wrapper = mount(TrendBarChart, {
      props: {
        granularity: "Monatlich",
        items: [{ period: "2024-01", total_spent: 10, receipt_count: 1 }],
      },
    });

    const rect = wrapper.find("rect.bar");
    rect.trigger("click");

    expect(wrapper.emitted("select-period")).toHaveLength(1);
    expect(wrapper.emitted("select-period")![0]).toEqual([
      { startDate: "2024-01-01", endDate: "2024-01-31", label: "Januar 2024" },
    ]);
  });

  it("emits select-period with daily boundaries", () => {
    const wrapper = mount(TrendBarChart, {
      props: {
        granularity: "Täglich",
        items: [{ period: "2024-01-15", total_spent: 10, receipt_count: 1 }],
      },
    });

    const rect = wrapper.find("rect.bar");
    rect.trigger("click");

    expect(wrapper.emitted("select-period")![0]).toEqual([
      { startDate: "2024-01-15", endDate: "2024-01-15", label: "15. Januar 2024" },
    ]);
  });

  it("emits select-period with yearly boundaries", () => {
    const wrapper = mount(TrendBarChart, {
      props: {
        granularity: "Jährlich",
        items: [{ period: "2024", total_spent: 100, receipt_count: 12 }],
      },
    });

    const rect = wrapper.find("rect.bar");
    rect.trigger("click");

    expect(wrapper.emitted("select-period")![0]).toEqual([
      { startDate: "2024-01-01", endDate: "2024-12-31", label: "2024" },
    ]);
  });

  it("shows tooltip on bar mouseenter", () => {
    const wrapper = mount(TrendBarChart, {
      props: {
        granularity: "Monatlich",
        items: [
          {
            period: "2024-01",
            total_spent: 100,
            receipt_count: 5,
            retailers: ["lidl"],
          },
        ],
      },
    });

    const rect = wrapper.find("rect.bar");
    rect.trigger("mouseenter");

    const tooltipGroup = wrapper.find(".tooltip-group");
    expect(tooltipGroup.exists()).toBe(true);
    expect(tooltipGroup.attributes("style")).not.toContain("display: none");
  });

  it("tooltip contains period, total, count, avg, and retailers", () => {
    const wrapper = mount(TrendBarChart, {
      props: {
        granularity: "Monatlich",
        items: [
          {
            period: "2024-01",
            total_spent: 100,
            receipt_count: 5,
            retailers: ["lidl", "rewe"],
          },
        ],
      },
    });

    const rect = wrapper.find("rect.bar");
    rect.trigger("mouseenter");

    expect(wrapper.text()).toContain("Januar 2024");
    expect(wrapper.text()).toContain("€100.00");
    expect(wrapper.text()).toContain("5 Belege");
    expect(wrapper.text()).toContain("€20.00");
    expect(wrapper.text()).toContain("lidl");
    expect(wrapper.text()).toContain("rewe");
  });

  it("hides tooltip on bar mouseleave after delay", async () => {
    vi.useFakeTimers();
    const wrapper = mount(TrendBarChart, {
      props: {
        granularity: "Monatlich",
        items: [
          {
            period: "2024-01",
            total_spent: 100,
            receipt_count: 5,
            retailers: ["lidl"],
          },
        ],
      },
    });

    const rect = wrapper.find("rect.bar");
    rect.trigger("mouseenter");
    rect.trigger("mouseleave");

    // Immediately after leave, tooltip should still be visible (200ms delay)
    const tooltipGroup = wrapper.find(".tooltip-group");
    expect(tooltipGroup.attributes("style")).not.toContain("display: none");

    // Advance past the 200ms delay
    vi.advanceTimersByTime(201);
    await wrapper.vm.$nextTick();

    expect(tooltipGroup.attributes("style")).toContain("display: none");
    vi.useRealTimers();
  });

  it("cancel hide timeout on re-enter", async () => {
    vi.useFakeTimers();
    const wrapper = mount(TrendBarChart, {
      props: {
        granularity: "Monatlich",
        items: [
          {
            period: "2024-01",
            total_spent: 100,
            receipt_count: 5,
            retailers: ["lidl"],
          },
        ],
      },
    });

    const rect = wrapper.find("rect.bar");
    rect.trigger("mouseenter");
    rect.trigger("mouseleave");

    // Re-enter before delay expires
    rect.trigger("mouseenter");
    vi.advanceTimersByTime(201);
    await wrapper.vm.$nextTick();

    const tooltipGroup = wrapper.find(".tooltip-group");
    // Tooltip should still be visible because re-enter cancelled the timer
    expect(tooltipGroup.attributes("style")).not.toContain("display: none");

    // Now leave for real
    rect.trigger("mouseleave");
    vi.advanceTimersByTime(201);
    await wrapper.vm.$nextTick();

    expect(tooltipGroup.attributes("style")).toContain("display: none");
    vi.useRealTimers();
  });
});
