import { reactive } from "vue";
import { describe, expect, it, vi } from "vite-plus/test";

import { useTrendECharts } from "../useTrendECharts";

const dailyItems = [
  ...Array.from({ length: 12 }, (_, index) => ({
    period: `2024-12-${20 + index}`,
    total_spent: index,
    receipt_count: 1,
  })),
  { period: "2025-01-02", total_spent: 92, receipt_count: 2 },
];

describe("useTrendECharts", () => {
  it("builds a slider and scales the full daily series", () => {
    const { option } = useTrendECharts({ items: dailyItems, granularity: "daily" }, vi.fn());

    expect(option.value).toMatchObject({
      xAxis: { data: dailyItems.map(({ period }) => period) },
      yAxis: { min: 0, max: 100, interval: 10 },
      dataZoom: [{ type: "slider", startValue: 0, endValue: 11 }],
      series: [{ type: "bar", data: dailyItems.map(({ total_spent }) => total_spent) }],
    });
  });

  it("rebuilds the chart when the data and granularity change", () => {
    const props = reactive({ items: dailyItems, granularity: "daily" });
    const { option } = useTrendECharts(props, vi.fn());
    expect(option.value.dataZoom).toHaveLength(1);

    props.items = [{ period: "2025", total_spent: 0, receipt_count: 0 }];
    props.granularity = "yearly";

    expect(option.value).toMatchObject({
      xAxis: { data: ["2025"] },
      yAxis: { min: 0, max: 10 },
      dataZoom: [],
      series: [{ type: "bar", data: [0] }],
    });
  });

  it("selects only valid bar events and uses the current period data", () => {
    const props = reactive({ items: dailyItems, granularity: "daily" });
    const onSelectPeriod = vi.fn();
    const { selectBar } = useTrendECharts(props, onSelectPeriod);

    selectBar({ componentType: "xAxis", dataIndex: 0 });
    selectBar({ componentType: "series", seriesType: "custom", dataIndex: 0 });
    selectBar({ componentType: "series", seriesType: "bar" });
    selectBar({ componentType: "series", seriesType: "bar", dataIndex: dailyItems.length });
    expect(onSelectPeriod).not.toHaveBeenCalled();

    selectBar({ componentType: "series", seriesType: "bar", dataIndex: 12 });
    props.items = [{ period: "2024-02", total_spent: 10, receipt_count: 1 }];
    props.granularity = "monthly";
    selectBar({ componentType: "series", seriesType: "bar", dataIndex: 0 });

    expect(onSelectPeriod.mock.calls).toEqual([
      [{ startDate: "2025-01-02", endDate: "2025-01-02", label: "2. Januar 2025" }],
      [{ startDate: "2024-02-01", endDate: "2024-02-29", label: "Februar 2024" }],
    ]);
  });
});
