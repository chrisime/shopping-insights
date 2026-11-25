// @vitest-environment jsdom

import { flushPromises, mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vite-plus/test";
import { init } from "echarts/core";
import { nextTick } from "vue";
import VChart from "vue-echarts";

import "../trendEChartsSetup";
import TrendChartPanel from "../TrendChartPanel.vue";
import TrendChartRenderer from "../TrendChartRenderer.vue";

const chartMethods = vi.hoisted(() => ({
  getDom: vi.fn(),
  getOption: vi.fn(),
  convertToPixel: vi.fn(),
  getWidth: vi.fn(),
  containPixel: vi.fn(),
  dispatchAction: vi.fn(),
}));

vi.mock("vue-echarts", () => ({
  default: {
    props: ["option", "initOptions"],
    emits: ["click", "datazoom", "updated"],
    template: "<div />",
    methods: chartMethods,
  },
}));

const items = [
  ...Array.from({ length: 12 }, (_, index) => ({
    period: `2024-12-${20 + index}`,
    total_spent: 0,
    receipt_count: 0,
  })),
  { period: "2025-01-01", total_spent: 92, receipt_count: 2, retailers: ["lidl"] },
  ...Array.from({ length: 11 }, (_, index) => ({
    period: `2025-01-${String(index + 2).padStart(2, "0")}`,
    total_spent: 0,
    receipt_count: 0,
  })),
];

function mountDailyChart() {
  return mount(TrendChartRenderer, { props: { items, granularity: "daily" } });
}

type PrototypeOption = Parameters<ReturnType<typeof init>["setOption"]>[0] & {
  xAxis: { data: string[]; axisLabel: { formatter: (period: string) => string } };
  tooltip: { hideDelay: number; formatter: (params: { dataIndex: number }) => string };
};

function chartOption(chart: ReturnType<typeof mountDailyChart>) {
  return chart.getComponent(VChart).props("option") as PrototypeOption;
}

describe("TrendChartRenderer", () => {
  it("uses a slider across the year boundary and scales to the full data range", () => {
    const wrapper = mountDailyChart();
    const chart = wrapper.getComponent(VChart);
    const option = chartOption(wrapper);

    expect(chart.props("initOptions")).toEqual({ renderer: "svg" });
    expect(option.dataZoom).toEqual([
      { type: "slider", xAxisIndex: 0, startValue: 0, endValue: 11 },
    ]);
    expect(option.yAxis).toMatchObject({ min: 0, max: 100, interval: 10 });
    expect(option.xAxis.data[12]).toBe("2025-01-01");
    expect(option.xAxis.axisLabel.formatter("2024-12-31")).toBe("31");
    expect(option.xAxis.axisLabel.formatter("2025-01-01")).toBe("01\nJanuar 2025");
    wrapper.unmount();
  });

  it("pins and pushes the year overlay as the ECharts range crosses into the next year", async () => {
    const wrapper = mountDailyChart();
    const canvas = vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockReturnValue(null);
    const chart = init(null, undefined, { renderer: "svg", ssr: true, width: 440, height: 500 });
    chartMethods.getOption.mockImplementation(() => chart.getOption());
    chartMethods.convertToPixel.mockImplementation(chart.convertToPixel.bind(chart));
    chart.on("updated", () => wrapper.getComponent(VChart).vm.$emit("updated"));

    const yearLabels = () => {
      const overlay = wrapper.get('[data-testid="trend-year-overlay"]');
      const plotLeft = Number.parseFloat((overlay.element as HTMLElement).style.left);
      return Object.fromEntries(
        overlay
          .findAll("span")
          .map((label) => [label.text(), plotLeft + Number.parseFloat(label.element.style.left)]),
      );
    };

    const moveRange = async (startValue: number, endValue: number) => {
      chart.dispatchAction({ type: "dataZoom", startValue, endValue });
      await nextTick();
    };

    try {
      chart.setOption(chartOption(wrapper));
      await nextTick();
      const pinnedX = yearLabels()["2024"];
      expect(pinnedX).toBeCloseTo(68);

      await moveRange(1, 10);
      expect(Object.keys(yearLabels())).toEqual(["2024"]);
      expect(yearLabels()["2024"]).toBeCloseTo(pinnedX);

      await moveRange(1, 12);
      const bothYears = yearLabels();
      expect(bothYears["2024"]).toBeCloseTo(pinnedX);
      expect(bothYears["2025"]).toBeGreaterThan(pinnedX);
      expect(chart.renderToSVGString()).toContain(">Januar 2025<");

      await moveRange(11, 22);
      const pushedYear = yearLabels();
      expect(pushedYear["2024"]).toBeLessThan(pinnedX);
      expect(pushedYear["2025"]).toBeGreaterThan(pinnedX);
      expect(pushedYear["2025"]).toBeLessThan(bothYears["2025"]);

      await moveRange(12, 23);
      expect(Object.keys(yearLabels())).toEqual(["2025"]);
      expect(yearLabels()["2025"]).toBeCloseTo(pinnedX);

      await moveRange(0, 11);
      expect(Object.keys(yearLabels())).toEqual(["2024"]);
      expect(yearLabels()["2024"]).toBeCloseTo(pinnedX);
    } finally {
      chart.dispose();
      canvas.mockRestore();
      wrapper.unmount();
      for (const method of Object.values(chartMethods)) method.mockReset();
    }
  });

  it.each(["mouse wheel", "horizontal trackpad"])(
    "pans with %s in proportion to the accumulated movement",
    (input) => {
      const wrapper = mountDailyChart();
      const canvas = vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockReturnValue(null);
      const host = document.createElement("div");
      const chart = init(host, undefined, { renderer: "svg", width: 800, height: 500 });
      chartMethods.getDom.mockImplementation(() => host);
      chartMethods.getOption.mockImplementation(() => chart.getOption());
      chartMethods.getWidth.mockImplementation(() => chart.getWidth());
      chartMethods.containPixel.mockImplementation(chart.containPixel.bind(chart));
      chartMethods.dispatchAction.mockImplementation(chart.dispatchAction.bind(chart));
      chart.on("datazoom", () => wrapper.getComponent(VChart).vm.$emit("datazoom"));
      const range = () =>
        (chart.getOption().dataZoom as { startValue: number; endValue: number }[])[0];
      const wheel = (delta: WheelEventInit) =>
        wrapper.element.dispatchEvent(
          new WheelEvent("wheel", {
            bubbles: true,
            cancelable: true,
            clientX: 200,
            clientY: 150,
            ...delta,
          }),
        );

      try {
        chart.setOption(chartOption(wrapper));
        expect(range()).toMatchObject({ startValue: 0, endValue: 11 });

        if (input === "horizontal trackpad") {
          for (let index = 0; index < 3; index++) wheel({ deltaX: 8 });
          expect(range()).toMatchObject({ startValue: 0, endValue: 11 });
          expect(chartMethods.getOption).toHaveBeenCalledTimes(1);
          wheel({ deltaX: 8 });
          expect(range()).toMatchObject({ startValue: 1, endValue: 12 });
          wheel({ deltaX: 40 });
          expect(range()).toMatchObject({ startValue: 2, endValue: 13 });
          wheel({ deltaX: 24 });
          expect(range()).toMatchObject({ startValue: 3, endValue: 14 });
          wheel({ deltaX: -32 });
          expect(range()).toMatchObject({ startValue: 2, endValue: 13 });
          expect(wheel({ deltaX: 96, ctrlKey: true })).toBe(true);
          expect(range()).toMatchObject({ startValue: 2, endValue: 13 });
        } else {
          wheel({ deltaY: 96 });
          expect(range()).toMatchObject({ startValue: 3, endValue: 14 });
          wheel({ deltaY: 800 });
          expect(range()).toMatchObject({ startValue: 12, endValue: 23 });
          expect(wheel({ deltaY: 96 })).toBe(true);

          chart.dispatchAction({ type: "dataZoom", startValue: 5, endValue: 10 });
          wheel({ deltaY: 32 });
          expect(range()).toMatchObject({ startValue: 6, endValue: 11 });
        }
      } finally {
        chart.dispose();
        canvas.mockRestore();
        wrapper.unmount();
        for (const method of Object.values(chartMethods)) method.mockReset();
      }
    },
  );

  it.each(["slider range", "chart width"])(
    "hides and restores the full amount label when the %s changes",
    (change) => {
      const wrapper = mountDailyChart();
      const canvas = vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockReturnValue(null);
      const chart = init(document.createElement("div"), undefined, {
        renderer: "svg",
        width: 1100,
        height: 500,
      });
      const amountLabels = () => {
        const svg = new DOMParser().parseFromString(chart.renderToSVGString(), "image/svg+xml");
        return [...svg.querySelectorAll("text")]
          .map((node) => node.textContent)
          .filter((text) => /,\d{2}\s*€$/.test(text));
      };

      const setRange = (endValue: number) =>
        chart.dispatchAction({ type: "dataZoom", dataZoomIndex: 0, startValue: 1, endValue });

      try {
        chart.setOption(chartOption(wrapper));
        setRange(12);
        expect(amountLabels()).toContain("92,00 €");

        if (change === "slider range") setRange(23);
        else chart.resize({ width: 420 });
        expect(amountLabels()).toEqual([]);
        expect(chartOption(wrapper).tooltip.formatter({ dataIndex: 12 })).toContain("92,00 €");

        if (change === "slider range") setRange(12);
        else chart.resize({ width: 1100 });
        expect(amountLabels()).toContain("92,00 €");
      } finally {
        chart.dispose();
        canvas.mockRestore();
        wrapper.unmount();
      }
    },
  );

  it("formats a tooltip using the original row index beyond the initial slider window", () => {
    const wrapper = mountDailyChart();
    const { tooltip } = chartOption(wrapper);
    const content = tooltip.formatter({ dataIndex: 12 });

    expect(tooltip.hideDelay).toBe(200);
    expect(content).toContain("1. Januar 2025");
    expect(content).toContain("92,00");
    expect(content).toContain("2 Belege");
    expect(content).toContain("46,00");
    expect(content).toContain("Lidl");
    wrapper.unmount();
  });

  it("updates the configuration for yearly data and emits only valid bar selections", async () => {
    const wrapper = mountDailyChart();
    const chart = wrapper.getComponent(VChart);
    chart.vm.$emit("click", { componentType: "xAxis", seriesType: "bar", dataIndex: 0 });
    chart.vm.$emit("click", { componentType: "series", seriesType: "bar", dataIndex: 99 });
    expect(wrapper.emitted("select-period")).toBeUndefined();

    chart.vm.$emit("click", { componentType: "series", seriesType: "bar", dataIndex: 12 });
    await wrapper.setProps({
      items: [{ period: "2025", total_spent: 0, receipt_count: 0 }],
      granularity: "yearly",
    });
    expect(chartOption(wrapper).dataZoom).toEqual([]);
    expect(chartOption(wrapper).yAxis).toMatchObject({ max: 10 });
    chart.vm.$emit("click", { componentType: "series", seriesType: "bar", dataIndex: 0 });
    expect(wrapper.emitted("select-period")).toEqual([
      [{ startDate: "2025-01-01", endDate: "2025-01-01", label: "1. Januar 2025" }],
      [{ startDate: "2025-01-01", endDate: "2025-12-31", label: "2025" }],
    ]);
    wrapper.unmount();
  });

  it("loads the chart in the panel and forwards a period selection", async () => {
    const wrapper = mount(TrendChartPanel, { props: { items, timeGranularity: "daily" } });
    await vi.dynamicImportSettled();
    await flushPromises();

    expect(wrapper.find('[data-testid="trend-bar-chart"]').exists()).toBe(true);
    wrapper.getComponent(VChart).vm.$emit("click", {
      componentType: "series",
      seriesType: "bar",
      dataIndex: 12,
    });
    expect(wrapper.emitted("select-period")).toEqual([
      [{ startDate: "2025-01-01", endDate: "2025-01-01", label: "1. Januar 2025" }],
    ]);
    wrapper.unmount();
  });
});
