import { describe, expect, it } from "vite-plus/test";

import { buildMonthLabels, computePeriod, periodLabel } from "../period";

describe("computePeriod", () => {
  it("maps a daily period to a single day", () => {
    expect(computePeriod("2024-01-15", "Täglich")).toEqual({
      startDate: "2024-01-15",
      endDate: "2024-01-15",
      label: "15. Januar 2024",
    });
  });

  it("maps a monthly period to the full month including leap years", () => {
    expect(computePeriod("2024-02", "Monatlich")).toEqual({
      startDate: "2024-02-01",
      endDate: "2024-02-29",
      label: "Februar 2024",
    });
  });

  it("maps a yearly period to the full year", () => {
    expect(computePeriod("2024", "Jährlich")).toEqual({
      startDate: "2024-01-01",
      endDate: "2024-12-31",
      label: "2024",
    });
  });

  it("falls back to the raw period when a daily period is incomplete", () => {
    expect(computePeriod("2024-01", "Täglich")).toEqual({
      startDate: "2024-01",
      endDate: "2024-01",
      label: "2024-01",
    });
  });

  it("treats a year-only monthly period as a year range", () => {
    expect(computePeriod("2024", "Monatlich")).toEqual({
      startDate: "2024-01-01",
      endDate: "2024-12-31",
      label: "2024",
    });
  });
});

describe("periodLabel", () => {
  it("labels a single day", () => {
    expect(periodLabel("2024-01-15", "2024-01-15")).toBe("15. Januar 2024");
  });

  it("labels a month range", () => {
    expect(periodLabel("2024-01-01", "2024-01-31")).toBe("Januar 2024");
  });

  it("labels a full year with the year only", () => {
    expect(periodLabel("2024-01-01", "2024-12-31")).toBe("2024");
  });

  it("returns an empty label without a start date", () => {
    expect(periodLabel("", "")).toBe("");
  });
});

describe("buildMonthLabels", () => {
  it("returns no labels for empty items", () => {
    expect(buildMonthLabels([])).toEqual([]);
  });

  it("groups consecutive days into one month", () => {
    const items = [{ period: "2024-01-30" }, { period: "2024-01-31" }];
    expect(buildMonthLabels(items)).toEqual([{ label: "Januar 2024", start: 0, end: 1 }]);
  });

  it("splits months across a year boundary", () => {
    const items = [
      { period: "2024-12-30" },
      { period: "2024-12-31" },
      { period: "2025-01-01" },
      { period: "2025-01-02" },
    ];
    expect(buildMonthLabels(items)).toEqual([
      { label: "Dezember 2024", start: 0, end: 1 },
      { label: "Januar 2025", start: 2, end: 3 },
    ]);
  });
});
