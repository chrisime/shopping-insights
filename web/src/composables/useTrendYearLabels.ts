import type { ECharts } from "echarts/core";
import { computed, shallowRef, type Ref } from "vue";

import type { TimeSeriesRow } from "../types/dashboard";
import { Y_AXIS_WIDTH } from "../utils/chart";

const YEAR_LABEL_INSET = 4;
const YEAR_LABEL_SPACE = 36;

type YearChart = Pick<ECharts, "getOption" | "convertToPixel">;
type YearRange = { year: string; start: number; end: number };
type VisibleRange = { startValue: number; endValue: number };
type YearLayout = { left: number; width: number; labels: { year: string; left: number }[] };

export const useTrendYearLabels = (
  props: Readonly<{ items: TimeSeriesRow[]; granularity: string }>,
  chartRef: Readonly<Ref<YearChart | null>>,
) => {
  const yearRanges = computed(() => {
    if (props.granularity !== "daily") return [];

    const years: YearRange[] = [];
    for (const [index, { period }] of props.items.entries()) {
      const year = period.slice(0, 4);
      const last = years.at(-1);
      if (last?.year === year) last.end = index;
      else years.push({ year, start: index, end: index });
    }
    return years;
  });

  const yearLayout = shallowRef<YearLayout>();

  const updateYearLabels = () => {
    const chart = chartRef.value;
    if (!chart || !yearRanges.value.length) {
      yearLayout.value = undefined;
      return;
    }

    const zoom = (chart.getOption()?.dataZoom as VisibleRange[] | undefined)?.[0];
    const { startValue = 0, endValue = props.items.length - 1 } = zoom ?? {};
    const first = chart.convertToPixel({ xAxisIndex: 0 }, startValue);
    const last = chart.convertToPixel({ xAxisIndex: 0 }, endValue);
    if (!Number.isFinite(first) || !Number.isFinite(last)) return;

    const slotCount = endValue - startValue + 1;
    const slotWidth = slotCount > 1 ? (last - first) / (slotCount - 1) : 2 * (first - Y_AXIS_WIDTH);
    if (slotWidth <= 0) return;

    const labels = yearRanges.value
      .filter(({ start, end }) => start <= endValue && end >= startValue)
      .map(({ year, start, end }) => ({
        year,
        left: Math.min(
          Math.max(0, start - startValue) * slotWidth + YEAR_LABEL_INSET,
          (end - startValue + 1) * slotWidth - YEAR_LABEL_SPACE,
        ),
      }));
    yearLayout.value = { left: first - slotWidth / 2, width: slotCount * slotWidth, labels };
  };

  return { yearLayout, updateYearLabels };
};
