import type { MonthLabel, PeriodSelection } from "../types/chart";

export const MONTH_NAMES = [
  "Januar",
  "Februar",
  "März",
  "April",
  "Mai",
  "Juni",
  "Juli",
  "August",
  "September",
  "Oktober",
  "November",
  "Dezember",
];

/** Maps a chart period ("2024", "2024-01", "2024-01-15") to a selectable date range. */
export function computePeriod(period: string, granularity: string): PeriodSelection {
  const parts = period.split("-");

  if (granularity === "Täglich") {
    if (parts.length >= 3) {
      const [year, month, day] = parts.map(Number);
      return {
        startDate: period,
        endDate: period,
        label: `${day}. ${MONTH_NAMES[month - 1]} ${year}`,
      };
    }
    return { startDate: period, endDate: period, label: period };
  }

  if (granularity === "Monatlich" && parts.length >= 2) {
    const [year, month] = parts.map(Number);
    const lastDay = new Date(year, month, 0).getDate();
    return {
      startDate: `${period}-01`,
      endDate: `${period}-${String(lastDay).padStart(2, "0")}`,
      label: `${MONTH_NAMES[month - 1]} ${year}`,
    };
  }

  return {
    startDate: `${period}-01-01`,
    endDate: `${period}-12-31`,
    label: period,
  };
}

/** Human readable headline for a receipt list range. */
export function periodLabel(startDate: string, endDate: string): string {
  if (!startDate) return "";

  if (startDate === endDate) {
    const [year, month, day] = startDate.split("-").map(Number);
    return `${day}. ${MONTH_NAMES[month - 1]} ${year}`;
  }

  if (startDate.endsWith("-01-01") && endDate.endsWith("-12-31")) {
    return startDate.slice(0, 4);
  }

  const [year, month] = startDate.split("-").map(Number);
  return `${MONTH_NAMES[month - 1]} ${year}`;
}

/** Groups consecutive daily periods by month so the chart can label month boundaries. */
export function buildMonthLabels(items: Array<{ period: string }>): MonthLabel[] {
  if (items.length === 0) return [];

  const labels: MonthLabel[] = [];
  let start = 0;
  let currentMonth = items[0].period.slice(5, 7);

  for (let i = 1; i <= items.length; i++) {
    const month = i < items.length ? items[i].period.slice(5, 7) : null;
    if (month === currentMonth) continue;

    const year = items[i - 1].period.slice(0, 4);
    labels.push({
      label: `${MONTH_NAMES[Number(currentMonth) - 1]} ${year}`,
      start,
      end: i - 1,
    });

    if (month !== null) {
      start = i;
      currentMonth = month;
    }
  }

  return labels;
}
