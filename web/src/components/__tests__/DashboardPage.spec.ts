import { createSSRApp, nextTick, effectScope } from "vue";
import { renderToString } from "@vue/server-renderer";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("../ImportJobControls.vue", () => ({ default: { template: "<div />" } }));

import DashboardPage from "../DashboardPage.vue";
import { useDashboard } from "../../composables/useDashboard";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("DashboardPage", () => {
  it("renders dashboard sections from the API payload", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          title: "Monatsübersicht",
          min_date: "2024-01-01",
          max_date: "2024-01-31",
          sections: [
            {
              kind: "metrics",
              title: "Allgemeine Informationen",
              items: [
                {
                  spendings: 10.0,
                  spendings_without_discount: 12.0,
                  receipt_count: 1,
                  avg_receipt_amount: 10.0,
                  saved_deposit: 0.0,
                  total_savings: 2.0,
                  total_savings_pct: 16.7,
                },
              ],
            },
            {
              kind: "time_series",
              title: "Ausgaben über Zeit",
              items: [{ period: "2024-01", total_spent: 10, receipt_count: 1 }],
            },
          ],
        }),
      }),
    );

    const html = await renderToString(createSSRApp(DashboardPage));

    expect(html).toContain("Monatsübersicht");
    expect(html).toContain("Allgemeine Informationen");
    expect(html).toContain("Ausgaben gesamt");
    expect(html).toContain("Ausgaben über Zeit");
  });

  it("seeds the dashboard date filters from the first payload", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        title: "Shopping Analyzer Dashboard",
        min_date: "2024-01-01",
        max_date: "2024-01-31",
        sections: [],
      }),
    });
    vi.stubGlobal(
      "fetch",
      fetchMock,
    );

    const scope = effectScope();
    const dashboard = scope.run(() => useDashboard());
    expect(dashboard).toBeDefined();

    await dashboard!.refresh();
    await nextTick();

    expect(dashboard!.startDate.value).toBe("2024-01-01");
    expect(dashboard!.endDate.value).toBe("2024-01-31");
    expect(fetchMock).toHaveBeenCalledTimes(1);

    scope.stop();
  });

  it("includes newly imported dates when the dashboard is using its automatic range", async () => {
    let latestDate = "2024-01-31";
    const fetchMock = vi.fn().mockImplementation(async () => ({
      ok: true,
      json: async () => ({ title: "Dashboard", min_date: "2024-01-01", max_date: latestDate, sections: [] }),
    }));
    vi.stubGlobal("fetch", fetchMock);
    const scope = effectScope();
    const dashboard = scope.run(() => useDashboard())!;

    await dashboard.refresh();
    await nextTick();
    latestDate = "2024-02-01";
    await dashboard.refresh(true);
    await nextTick();
    expect(dashboard.endDate.value).toBe("2024-02-01");
    expect(String(fetchMock.mock.lastCall?.[0])).not.toContain("end_date");

    dashboard.endDate.value = "2024-01-15";
    await nextTick();
    await dashboard.refresh(true);
    expect(dashboard.endDate.value).toBe("2024-01-15");
    expect(String(fetchMock.mock.lastCall?.[0])).toContain("end_date=2024-01-15");
    scope.stop();
  });

  it("shows an empty-state message when the payload reports a dashboard error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          title: "Shopping Analyzer Dashboard",
          min_date: null,
          max_date: null,
          error: { error_code: 101, detail: "missing_database" },
          sections: [],
        }),
      }),
    );

    const html = await renderToString(createSSRApp(DashboardPage));

    expect(html).toContain("Dashboard data is unavailable");
    expect(html).toContain("Shopping Analyzer Dashboard");
  });

  it("preserves the date range and resets pagination/search when the retailer changes", async () => {
    const payload = () => ({
      ok: true,
      json: async () => ({
        title: "Shopping Analyzer Dashboard",
        min_date: "2024-01-01",
        max_date: "2024-01-31",
        sections: [],
      }),
    });
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(payload())
      .mockResolvedValueOnce(payload())
      .mockResolvedValueOnce(payload())
      .mockResolvedValueOnce(payload());
    vi.stubGlobal("fetch", fetchMock);

    const scope = effectScope();
    const dashboard = scope.run(() => useDashboard());
    expect(dashboard).toBeDefined();

    await dashboard!.refresh();
    await nextTick();

    dashboard!.search.value = "lidl";
    dashboard!.page.value = 3;
    await nextTick();
    await Promise.resolve();
    await Promise.resolve();

    dashboard!.retailer.value = "lidl";
    await nextTick();
    await Promise.resolve();
    await Promise.resolve();
    await nextTick();

    const retailerFetch = new URL(String(fetchMock.mock.calls[fetchMock.mock.calls.length - 1][0]));
    expect(retailerFetch.searchParams.get("start_date")).toBe("2024-01-01");
    expect(retailerFetch.searchParams.get("end_date")).toBe("2024-01-31");
    expect(dashboard!.startDate.value).toBe("2024-01-01");
    expect(dashboard!.endDate.value).toBe("2024-01-31");
    expect(dashboard!.search.value).toBe("");
    expect(dashboard!.page.value).toBe(1);

    scope.stop();
  });

  it("seeds the date range from the new retailer payload when no range is set", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          title: "Shopping Analyzer Dashboard",
          min_date: null,
          max_date: null,
          sections: [],
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          title: "Shopping Analyzer Dashboard",
          min_date: "2024-02-01",
          max_date: "2024-02-29",
          sections: [],
        }),
      });
    vi.stubGlobal("fetch", fetchMock);

    const scope = effectScope();
    const dashboard = scope.run(() => useDashboard());
    expect(dashboard).toBeDefined();

    await dashboard!.refresh();
    await nextTick();

    expect(dashboard!.startDate.value).toBe("");
    expect(dashboard!.endDate.value).toBe("");

    dashboard!.retailer.value = "lidl";
    await nextTick();
    await Promise.resolve();
    await Promise.resolve();
    await nextTick();

    expect(dashboard!.startDate.value).toBe("2024-02-01");
    expect(dashboard!.endDate.value).toBe("2024-02-29");

    scope.stop();
  });

  it("refetches when filters change", async () => {
    let resolveFirst: ((value: unknown) => void) | undefined;
    let resolveSecond: ((value: unknown) => void) | undefined;
    const firstResponse = new Promise((resolve) => {
      resolveFirst = resolve;
    });
    const secondResponse = new Promise((resolve) => {
      resolveSecond = resolve;
    });
    const fetchMock = vi
      .fn()
      .mockReturnValueOnce(firstResponse)
      .mockReturnValueOnce(secondResponse);
    vi.stubGlobal("fetch", fetchMock);

    const scope = effectScope();
    const dashboard = scope.run(() => useDashboard());
    expect(dashboard).toBeDefined();

    const firstRefresh = dashboard!.refresh();
    dashboard!.retailer.value = "lidl";
    await nextTick();

    expect(fetchMock).toHaveBeenCalledTimes(2);

    resolveSecond?.({
      ok: true,
      json: async () => ({ title: "Newest", sections: [] }),
    });
    await Promise.resolve();
    await Promise.resolve();
    await nextTick();
    expect(dashboard!.payload.value?.title).toBe("Newest");

    resolveFirst?.({
      ok: true,
      json: async () => ({ title: "Stale", sections: [] }),
    });
    await Promise.resolve();
    await Promise.resolve();
    await nextTick();

    expect(dashboard!.payload.value?.title).toBe("Newest");
    scope.stop();
    await firstRefresh;
  });
});
