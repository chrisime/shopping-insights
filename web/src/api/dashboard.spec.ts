import { describe, expect, it, vi } from "vitest";

import { fetchDashboard } from "./dashboard";

describe("fetchDashboard", () => {
  it("requests /ui/dashboard with filters", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ title: "Shopping Analyzer Dashboard", sections: [] }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await fetchDashboard({
      retailer: "lidl",
      start_date: "2024-01-01",
      end_date: "2024-01-31",
      time_granularity: "Monatlich",
      spending_view: "Absolut",
      top_view: "Menge",
      top_limit: 10,
    });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(String(fetchMock.mock.calls[0][0])).toContain("/ui/dashboard");
  });

  it("omits null filter values", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ title: "Shopping Analyzer Dashboard", sections: [] }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await fetchDashboard({
      retailer: null as unknown as string,
      top_limit: 5,
    });

    const url = new URL(String(fetchMock.mock.calls[0][0]));
    expect(url.searchParams.get("retailer")).toBeNull();
    expect(url.searchParams.get("top_limit")).toBe("5");
  });
});
