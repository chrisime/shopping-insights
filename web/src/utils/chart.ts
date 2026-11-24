import type { TimeSeriesRow } from "../types/dashboard";
import { MONTH_NAMES } from "./period";

export const CHART_HEIGHT = 500;
export const Y_AXIS_WIDTH = 64;

const BAR_SLOT_WIDTH = 56;
const RIGHT_MARGIN = 16;
const STEP_SIZES: Record<string, number> = {
  daily: 10,
  monthly: 50,
  yearly: 500,
};

export function chartWidth(itemCount: number): number {
  return itemCount * BAR_SLOT_WIDTH + RIGHT_MARGIN;
}

/** Round tick values covering the largest spending value for the given granularity. */
export function yAxisTicks(items: TimeSeriesRow[], granularity: string): number[] {
  const step = STEP_SIZES[granularity] ?? STEP_SIZES.yearly;
  const max = Math.max(...items.map((item) => item.total_spent), 0);
  const roundedMax = Math.ceil(max / step) * step;

  const ticks: number[] = [];
  for (let value = 0; value <= roundedMax; value += step) {
    ticks.push(value);
  }
  return ticks;
}

/** X-axis caption: day of month when months are labelled above, otherwise a short period. */
export function xTickLabel(period: string, granularity: string, hasMonthLabels: boolean): string {
  if (hasMonthLabels) return period.slice(8, 10);

  if (granularity === "monthly") {
    const [year, month] = period.split("-").map(Number);
    if (month) return `${MONTH_NAMES[month - 1].slice(0, 3)} ${year}`;
  }

  return period;
}
