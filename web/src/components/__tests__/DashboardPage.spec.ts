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
          title: "Shopping Analyzer Dashboard",
          sections: [
            {
              kind: "metrics",
              title: "Kennzahlen",
              items: [{ label: "Ausgaben gesamt", value: "€10.00" }],
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

    expect(html).toContain("Shopping Analyzer Dashboard");
    expect(html).toContain("Kennzahlen");
    expect(html).toContain("Ausgaben gesamt");
    expect(html).toContain("Ausgaben über Zeit");
  });

  it("refetches when filters change", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ title: "Shopping Analyzer Dashboard", sections: [] }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const scope = effectScope();
    const dashboard = scope.run(() => useDashboard());
    expect(dashboard).toBeDefined();

    await dashboard!.refresh();
    expect(fetchMock).toHaveBeenCalledTimes(1);

    dashboard!.retailer.value = "lidl";
    await nextTick();

    expect(fetchMock).toHaveBeenCalledTimes(2);
    scope.stop();
  });
});
