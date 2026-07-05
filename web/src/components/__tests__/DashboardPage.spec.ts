import { createSSRApp, nextTick, effectScope } from "vue";
import { renderToString } from "@vue/server-renderer";
import { afterEach, describe, expect, it, vi } from "vitest";

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
