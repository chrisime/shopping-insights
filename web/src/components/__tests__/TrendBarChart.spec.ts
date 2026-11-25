// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vite-plus/test";

import TrendBarChart from "../TrendBarChart.vue";

describe("TrendBarChart", () => {
  it("renders SVG elements for y-axis and bars", () => {
    const wrapper = mount(TrendBarChart, {
      props: {
        items: [{ period: "2024-01", total_spent: 10, receipt_count: 1 }],
        granularity: "monthly",
      },
    });
    expect(wrapper.find("[data-testid=trend-chart-svg]").exists()).toBe(true);
    expect(wrapper.find("[data-testid=trend-chart-y-axis-svg]").exists()).toBe(true);
  });

  it("renders monthly labels", () => {
    const wrapper = mount(TrendBarChart, {
      props: {
        items: [
          { period: "2024-01", total_spent: 10, receipt_count: 1 },
          { period: "2024-02", total_spent: 20, receipt_count: 2 },
        ],
        granularity: "monthly",
      },
    });
    expect(wrapper.text()).toContain("Jan 2024");
    expect(wrapper.text()).toContain("Feb 2024");
  });

  it("wraps chart in scrollable container for monthly granularity", () => {
    const wrapper = mount(TrendBarChart, {
      props: {
        items: [{ period: "2024-01", total_spent: 10, receipt_count: 1 }],
        granularity: "monthly",
      },
    });
    expect(wrapper.find("[data-testid=trend-chart-scroll]").classes("overflow-x-auto")).toBe(true);
  });

  it("renders yearly labels", () => {
    const wrapper = mount(TrendBarChart, {
      props: {
        items: [
          { period: "2024", total_spent: 100, receipt_count: 12 },
          { period: "2025", total_spent: 200, receipt_count: 24 },
        ],
        granularity: "yearly",
      },
    });
    expect(wrapper.text()).toContain("2024");
    expect(wrapper.text()).toContain("2025");
  });

  it("keeps the year above day-only labels until the next year pushes it out", async () => {
    const wrapper = mount(TrendBarChart, {
      props: {
        items: [
          { period: "2024-01-15", total_spent: 10, receipt_count: 1 },
          { period: "2024-02-20", total_spent: 20, receipt_count: 2 },
          { period: "2025-01-10", total_spent: 10, receipt_count: 1 },
        ],
        granularity: "daily",
        monthLabels: [
          { label: "Januar 2024", start: 0, end: 0 },
          { label: "Februar 2024", start: 1, end: 1 },
          { label: "Januar 2025", start: 2, end: 2 },
        ],
      },
    });
    const years = wrapper.findAll(".year-label");
    const months = wrapper.findAll(".month-label");
    expect(years.map((label) => label.text())).toEqual(["2024", "2025"]);
    expect(months.map((label) => label.text())).toEqual(["Jan", "Feb", "Jan"]);
    expect(Number(years[0].attributes("y"))).toBeLessThan(Number(months[0].attributes("y")));
    expect(wrapper.text()).toContain("15");
    expect(wrapper.text()).toContain("20");
    expect(wrapper.text()).not.toContain("2024-01-15");
    expect(wrapper.text()).not.toContain("2024-02-20");

    const scroll = wrapper.get<HTMLDivElement>('[data-testid="trend-chart-scroll"]');
    scroll.element.scrollLeft = 50;
    await scroll.trigger("scroll");
    expect(years[0].attributes("x")).toBe("54");

    const nextYearX = Number(years[1].attributes("x"));
    scroll.element.scrollLeft = nextYearX - 15;
    await scroll.trigger("scroll");
    expect(Number(years[0].attributes("x"))).toBeLessThan(scroll.element.scrollLeft);

    scroll.element.scrollLeft = nextYearX + 8;
    await scroll.trigger("scroll");
    expect(Number(years[1].attributes("x"))).toBe(scroll.element.scrollLeft + 4);
  });

  it("shows full labels when monthLabels is not provided", () => {
    const wrapper = mount(TrendBarChart, {
      props: {
        items: [{ period: "2024-01-15", total_spent: 10, receipt_count: 1 }],
        granularity: "daily",
      },
    });
    expect(wrapper.text()).toContain("2024-01-15");
  });

  it("emits select-period with monthly boundaries", async () => {
    const wrapper = mount(TrendBarChart, {
      props: {
        granularity: "monthly",
        items: [{ period: "2024-01", total_spent: 10, receipt_count: 1 }],
      },
    });

    const rect = wrapper.find("[data-testid=trend-chart-bar]");
    await rect.trigger("click");

    expect(wrapper.emitted("select-period")).toHaveLength(1);
    expect(wrapper.emitted("select-period")![0]).toEqual([
      { startDate: "2024-01-01", endDate: "2024-01-31", label: "Januar 2024" },
    ]);
  });

  it("emits select-period with daily boundaries", async () => {
    const wrapper = mount(TrendBarChart, {
      props: {
        granularity: "daily",
        items: [{ period: "2024-01-15", total_spent: 10, receipt_count: 1 }],
      },
    });

    const rect = wrapper.find("[data-testid=trend-chart-bar]");
    await rect.trigger("click");

    expect(wrapper.emitted("select-period")![0]).toEqual([
      { startDate: "2024-01-15", endDate: "2024-01-15", label: "15. Januar 2024" },
    ]);
  });

  it("emits select-period with yearly boundaries", async () => {
    const wrapper = mount(TrendBarChart, {
      props: {
        granularity: "yearly",
        items: [{ period: "2024", total_spent: 100, receipt_count: 12 }],
      },
    });

    const rect = wrapper.find("[data-testid=trend-chart-bar]");
    await rect.trigger("click");

    expect(wrapper.emitted("select-period")![0]).toEqual([
      { startDate: "2024-01-01", endDate: "2024-12-31", label: "2024" },
    ]);
  });

  it("shows tooltip on bar mouseenter", async () => {
    const wrapper = mount(TrendBarChart, {
      props: {
        granularity: "monthly",
        items: [
          {
            period: "2024-01",
            total_spent: 1234.5,
            receipt_count: 5,
            retailers: ["lidl"],
          },
        ],
      },
    });

    const rect = wrapper.find("[data-testid=trend-chart-bar]");
    await rect.trigger("mouseenter");

    const tooltipGroup = wrapper.find("[data-testid=trend-chart-tooltip]");
    expect(tooltipGroup.exists()).toBe(true);
    expect(tooltipGroup.attributes("style")).not.toContain("display: none");
  });

  it("tooltip contains period, total, count, avg, and retailers", async () => {
    const wrapper = mount(TrendBarChart, {
      props: {
        granularity: "monthly",
        items: [
          {
            period: "2024-01",
            total_spent: 1234.5,
            receipt_count: 5,
            retailers: ["lidl", "rewe"],
          },
        ],
      },
    });

    const rect = wrapper.find("[data-testid=trend-chart-bar]");
    await rect.trigger("mouseenter");

    expect(wrapper.text()).toContain("Januar 2024");
    expect(wrapper.text()).toContain("1.234,50 €");
    expect(wrapper.text()).toContain("5 Belege");
    expect(wrapper.text()).toContain("246,90 €");
    expect(wrapper.text()).toContain("Lidl");
    expect(wrapper.text()).toContain("REWE");
  });

  it("hides tooltip on bar mouseleave after delay", async () => {
    vi.useFakeTimers();
    const wrapper = mount(TrendBarChart, {
      props: {
        granularity: "monthly",
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

    const rect = wrapper.find("[data-testid=trend-chart-bar]");
    await rect.trigger("mouseenter");
    await rect.trigger("mouseleave");

    // Immediately after leave, tooltip should still be visible (200ms delay)
    const tooltipGroup = wrapper.find("[data-testid=trend-chart-tooltip]");
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
        granularity: "monthly",
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

    const rect = wrapper.find("[data-testid=trend-chart-bar]");
    await rect.trigger("mouseenter");
    await rect.trigger("mouseleave");

    // Re-enter before delay expires
    await rect.trigger("mouseenter");
    vi.advanceTimersByTime(201);
    await wrapper.vm.$nextTick();

    const tooltipGroup = wrapper.find("[data-testid=trend-chart-tooltip]");
    // Tooltip should still be visible because re-enter cancelled the timer
    expect(tooltipGroup.attributes("style")).not.toContain("display: none");

    // Now leave for real
    await rect.trigger("mouseleave");
    vi.advanceTimersByTime(201);
    await wrapper.vm.$nextTick();

    expect(tooltipGroup.attributes("style")).toContain("display: none");
    vi.useRealTimers();
  });

  it("replaces the SVGs and binds selection to the new data after a props update", async () => {
    const wrapper = mount(TrendBarChart, {
      props: {
        granularity: "monthly",
        items: [{ period: "2024-01", total_spent: 10, receipt_count: 1 }],
      },
    });

    try {
      await wrapper.setProps({
        granularity: "yearly",
        items: [{ period: "2025", total_spent: 0, receipt_count: 0 }],
      });

      expect(wrapper.findAll("svg")).toHaveLength(2);
      expect(wrapper.text()).toContain("2025");
      expect(wrapper.text()).not.toContain("Jan 2024");
      const bar = wrapper.get('[data-testid="trend-chart-bar"]');
      expect(bar.attributes("height")).toBe("0");
      await bar.trigger("click");
      expect(wrapper.emitted("select-period")).toEqual([
        [{ startDate: "2025-01-01", endDate: "2025-12-31", label: "2025" }],
      ]);

      await bar.trigger("mouseenter");
      const { x, y, width } = bar.attributes();
      expect(wrapper.get('[data-testid="trend-chart-tooltip"]').attributes("transform")).toBe(
        `translate(${Number(x) + Number(width) / 2}, ${y})`,
      );

      await wrapper.setProps({ items: [] });
      expect(wrapper.findAll("svg")).toHaveLength(0);
    } finally {
      wrapper.unmount();
    }
  });

  it.each(["redraw", "unmount"])("clears the pending tooltip timer on %s", async (action) => {
    const wrapper = mount(TrendBarChart, {
      props: {
        granularity: "monthly",
        items: [{ period: "2024-01", total_spent: 10, receipt_count: 1 }],
      },
    });
    vi.useFakeTimers();
    let unmounted = false;

    try {
      const bar = wrapper.get('[data-testid="trend-chart-bar"]');
      await bar.trigger("mouseenter");
      await bar.trigger("mouseleave");
      expect(vi.getTimerCount()).toBe(1);

      if (action === "redraw") {
        await wrapper.setProps({ items: [] });
      } else {
        wrapper.unmount();
        unmounted = true;
      }
      expect(vi.getTimerCount()).toBe(0);
    } finally {
      if (!unmounted) wrapper.unmount();
      vi.useRealTimers();
    }
  });
});
