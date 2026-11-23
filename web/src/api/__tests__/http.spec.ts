import { afterEach, describe, expect, it, vi } from "vite-plus/test";

import { apiUrl, getJson } from "../http";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("apiUrl", () => {
  it("builds an url from the default base and skips empty params", () => {
    const url = apiUrl("/ui/dashboard", { retailer: "", top_limit: 5, search: undefined });
    expect(url.pathname).toBe("/ui/dashboard");
    expect(url.searchParams.get("retailer")).toBeNull();
    expect(url.searchParams.get("search")).toBeNull();
    expect(url.searchParams.get("top_limit")).toBe("5");
  });
});

describe("getJson", () => {
  it("returns the parsed payload", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ title: "ok" }) });
    vi.stubGlobal("fetch", fetchMock);

    await expect(getJson<{ title: string }>("/ui/dashboard")).resolves.toEqual({ title: "ok" });
    expect(String(fetchMock.mock.calls[0][0])).toContain("/ui/dashboard");
  });

  it("throws with the status code on a failed response", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 503 }));

    await expect(getJson("/ui/dashboard")).rejects.toThrow("HTTP 503");
  });
});
