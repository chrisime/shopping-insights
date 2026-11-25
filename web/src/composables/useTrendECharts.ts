import { computed } from "vue";
import { format, type ComposeOption } from "echarts/core";
import type { BarSeriesOption } from "echarts/charts";
import type {
  DataZoomComponentOption,
  GridComponentOption,
  TooltipComponentOption,
} from "echarts/components";

import type { PeriodSelection } from "../types/chart";
import type { TimeSeriesRow } from "../types/dashboard";
import { TREND_PLOT_TOP, Y_AXIS_WIDTH, xTickLabel, yAxisTicks } from "../utils/chart";
import { t } from "../utils/copy";
import { compactEuro, euro, retailerLabel } from "../utils/format";
import { buildMonthLabels, computePeriod } from "../utils/period";

const WINDOW_SIZE = 12;
const AMOUNT_LABEL_FONT_SIZE = 12;
const AMOUNT_LABEL_FONT_FAMILY = "sans-serif";
const AMOUNT_LABEL_PADDING = 4;
type ChartOption = ComposeOption<
  BarSeriesOption | DataZoomComponentOption | GridComponentOption | TooltipComponentOption
>;

const formatTooltip = (row: TimeSeriesRow, granularity: string): string => {
  const count = row.receipt_count;
  const average = count > 0 ? row.total_spent / count : 0;
  return [
    computePeriod(row.period, granularity).label,
    t("chart.total", { amount: euro(row.total_spent) }),
    t("chart.receipts", { count }),
    t("chart.averagePerReceipt", { amount: euro(average) }),
    ...(row.retailers?.length ? [row.retailers.map(retailerLabel).join(", ")] : []),
  ].join("\n");
};

const barSeries = (items: TimeSeriesRow[]): BarSeriesOption => ({
  type: "bar",
  data: items.map(({ total_spent }) => total_spent),
  itemStyle: { color: "#6366f1", borderRadius: [4, 4, 0, 0] },
  label: {
    show: true,
    position: "top",
    overflow: "truncate",
    fontSize: AMOUNT_LABEL_FONT_SIZE,
    fontFamily: AMOUNT_LABEL_FONT_FAMILY,
    formatter: ({ dataIndex }) => euro(items[dataIndex].total_spent),
  },
  // Keep the full amount within its own bar's width, or leave it to the tooltip.
  labelLayout: ({ rect, text }) => {
    const font = `${AMOUNT_LABEL_FONT_SIZE}px ${AMOUNT_LABEL_FONT_FAMILY}`;
    const textWidth = format.getTextRect(text, font).width;
    return { width: textWidth + AMOUNT_LABEL_PADDING <= rect.width ? rect.width : 0 };
  },
});

type TrendEChartsProps = { items: TimeSeriesRow[]; granularity: string };

export const useTrendECharts = (
  props: Readonly<TrendEChartsProps>,
  onSelectPeriod: (period: PeriodSelection) => void,
) => {
  const option = computed<ChartOption>(() => {
    const { items, granularity } = props;
    const months = granularity === "daily" ? buildMonthLabels(items) : [];
    const monthStarts = new Map(months.map(({ start, label }) => [items[start].period, label]));
    const ticks = yAxisTicks(items, granularity);
    const hasSlider = granularity !== "yearly" && items.length > WINDOW_SIZE;

    return {
      animation: false,
      grid: { left: Y_AXIS_WIDTH, right: 16, top: TREND_PLOT_TOP, bottom: hasSlider ? 100 : 62 },
      xAxis: {
        type: "category",
        data: items.map(({ period }) => period),
        axisLabel: {
          formatter: (period: string) => {
            const dayOrPeriod = xTickLabel(period, granularity, months.length > 0);
            const month = monthStarts.get(period);
            return month ? dayOrPeriod + "\n" + month : dayOrPeriod;
          },
        },
      },
      yAxis: {
        type: "value",
        min: 0,
        max: ticks.at(-1) || 10,
        interval: ticks[1],
        axisLabel: { formatter: (value: number) => compactEuro(value) },
      },
      dataZoom: hasSlider
        ? [
            {
              type: "slider",
              xAxisIndex: 0,
              startValue: 0,
              endValue: WINDOW_SIZE - 1,
            },
          ]
        : [],
      tooltip: {
        trigger: "item",
        renderMode: "richText",
        hideDelay: 200,
        formatter: (params) => {
          if (Array.isArray(params)) return "";
          const row = items[params.dataIndex];
          if (!row) return "";
          return formatTooltip(row, granularity);
        },
      },
      series: [barSeries(items)],
    };
  });

  const selectBar = ({
    componentType,
    seriesType,
    dataIndex,
  }: {
    componentType?: string;
    seriesType?: string;
    dataIndex?: number;
  }) => {
    if (componentType !== "series" || seriesType !== "bar" || dataIndex === undefined) return;
    const row = props.items[dataIndex];
    if (row) onSelectPeriod(computePeriod(row.period, props.granularity));
  };

  return { option, selectBar };
};
