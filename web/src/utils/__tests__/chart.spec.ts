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
      yAxisTicks([{ period: "2024-01", total_spent: 120, receipt_count: 1 }], "Monatlich"),
    ).toEqual([0, 50, 100, 150]);
  });

  it("uses a finer step for daily granularity", () => {
    expect(
      yAxisTicks([{ period: "2024-01-01", total_spent: 12, receipt_count: 1 }], "Täglich"),
    ).toEqual([0, 10, 20]);
  });

  it("returns a single zero tick for empty items", () => {
    expect(yAxisTicks([], "Monatlich")).toEqual([0]);
  });
});

describe("xTickLabel", () => {
  it("shows the day of month when month labels are present", () => {
    expect(xTickLabel("2024-01-15", "Täglich", true)).toBe("15");
  });

  it("shortens monthly periods", () => {
    expect(xTickLabel("2024-01", "Monatlich", false)).toBe("Jan 2024");
  });

  it("keeps yearly and complete daily periods untouched", () => {
    expect(xTickLabel("2024", "Jährlich", false)).toBe("2024");
    expect(xTickLabel("2024-01-15", "Täglich", false)).toBe("2024-01-15");
    expect(xTickLabel("2024", "Monatlich", false)).toBe("2024");
  });
});
