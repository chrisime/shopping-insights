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
              title: "Kennzahlen",
              items: [{ label: "Ausgaben gesamt", value: "€10.00" }],
            },
            {
              kind: "bonus_rewe",
              title: "REWE Bonus",
              items: [{ label: "Bonus gesammelt (Zeitraum)", value: "€1.00" }],
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
    expect(html).toContain("Kennzahlen");
    expect(html).toContain("Ausgaben gesamt");
    expect(html).toContain("REWE Bonus");
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

  it("resets the date range when the retailer changes", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          title: "Shopping Analyzer Dashboard",
          min_date: "2024-01-01",
          max_date: "2024-01-31",
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

    dashboard!.retailer.value = "lidl";
    await nextTick();
    await Promise.resolve();
    await Promise.resolve();
    await nextTick();

    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(new URL(String(fetchMock.mock.calls[1][0])).searchParams.get("start_date")).toBeNull();
    expect(new URL(String(fetchMock.mock.calls[1][0])).searchParams.get("end_date")).toBeNull();
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
