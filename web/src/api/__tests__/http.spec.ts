import { afterEach, describe, expect, it, vi } from "vite-plus/test";

import { apiUrl, ApiRequestError, getJson } from "../http";

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

describe("apiUrl", () => {
  it("builds an url from the default base and skips empty params", () => {
    const url = apiUrl("/ui/dashboard", { retailer: "", top_limit: 5, search: undefined });
    expect(url.pathname).toBe("/ui/dashboard");
    expect(url.searchParams.get("retailer")).toBeNull();
    expect(url.searchParams.get("search")).toBeNull();
    expect(url.searchParams.get("top_limit")).toBe("5");
  });

  it("uses the page origin in production and honors an explicit API base URL", () => {
    vi.stubEnv("PROD", true);
    vi.stubEnv("VITE_API_BASE_URL", undefined);
    vi.stubGlobal("window", { location: { origin: "https://dashboard.example" } });

    expect(apiUrl("/ui/dashboard").origin).toBe("https://dashboard.example");

    vi.stubEnv("VITE_API_BASE_URL", "https://api.example");
    expect(apiUrl("/ui/dashboard").origin).toBe("https://api.example");
  });
});

describe("getJson", () => {
  it("returns the parsed payload", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ title: "ok" }) });
    vi.stubGlobal("fetch", fetchMock);

    await expect(getJson<{ title: string }>("/ui/dashboard")).resolves.toEqual({ title: "ok" });
    expect(String(fetchMock.mock.calls[0][0])).toContain("/ui/dashboard");
  });

  it("throws the backend error code from a failed response", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 503,
        json: async () => ({ error_code: 5001, detail: "diagnostic only" }),
      }),
    );

    await expect(getJson("/ui/dashboard")).rejects.toMatchObject({
      name: "ApiRequestError",
      kind: "api",
      errorCode: 5001,
    });
  });

  it("keeps the same error identity when its HTTP status differs", async () => {
    for (const status of [400, 409]) {
      vi.stubGlobal(
        "fetch",
        vi.fn().mockResolvedValue({
          ok: false,
          status,
          json: async () => ({ error_code: 4003, detail: "diagnostic only" }),
        }),
      );

      await expect(getJson("/ui/dashboard")).rejects.toMatchObject({
        kind: "api",
        errorCode: 4003,
        status,
      });
    }
  });

  it("does not infer error identity from HTTP status when the code is absent", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 503,
        json: async () => ({ detail: "diagnostic only" }),
      }),
    );

    await expect(getJson("/ui/dashboard")).rejects.toMatchObject({
      kind: "api",
      errorCode: undefined,
    });
  });

  it("represents failures without an API response as network failures", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));

    await expect(getJson("/ui/dashboard")).rejects.toBeInstanceOf(ApiRequestError);
    await expect(getJson("/ui/dashboard")).rejects.toMatchObject({ kind: "network" });
  });
});
