import { describe, expect, it } from "vite-plus/test";

import { chartWidth, xTickLabel, yAxisTicks } from "../chart";

describe("chartWidth", () => {
  it("reserves one slot per bar plus the right margin", () => {
    expect(chartWidth(0)).toBe(16);
    expect(chartWidth(2)).toBe(128);
  });
});

describe("yAxisTicks", () => {
  it("rounds up to the monthly step size", () => {
    expect(
      yAxisTicks([{ period: "2024-01", total_spent: 120, receipt_count: 1 }], "monthly"),
    ).toEqual([0, 50, 100, 150]);
  });

  it("uses a finer step for daily granularity", () => {
    expect(
      yAxisTicks([{ period: "2024-01-01", total_spent: 12, receipt_count: 1 }], "daily"),
    ).toEqual([0, 10, 20]);
  });

  it("returns a single zero tick for empty items", () => {
    expect(yAxisTicks([], "monthly")).toEqual([0]);
  });
});

describe("xTickLabel", () => {
  it("shows the day of month when month labels are present", () => {
    expect(xTickLabel("2024-01-15", "daily", true)).toBe("15");
  });

  it("shortens monthly periods", () => {
    expect(xTickLabel("2024-01", "monthly", false)).toBe("Jan 2024");
  });

  it("keeps yearly and complete daily periods untouched", () => {
    expect(xTickLabel("2024", "yearly", false)).toBe("2024");
    expect(xTickLabel("2024-01-15", "daily", false)).toBe("2024-01-15");
    expect(xTickLabel("2024", "monthly", false)).toBe("2024");
  });
});
