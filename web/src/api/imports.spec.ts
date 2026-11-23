import { afterEach, describe, expect, it, vi } from "vite-plus/test";

import { openImportJobEvents, startImportJob } from "./imports";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("import api helpers", () => {
  it("starts an import job for the selected retailer", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue({ ok: true, json: async () => ({ job_id: "job-1", retailer: "lidl" }) });
    vi.stubGlobal("fetch", fetchMock);

    await startImportJob({ retailer: "lidl", browser: "firefox" });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledWith(expect.any(URL), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ retailer: "lidl", browser: "firefox" }),
    });
    expect(String(fetchMock.mock.calls[0][0])).toContain("/imports/start");
  });

  it("surfaces structured conflict details for a concurrent import", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 409,
      json: async () => ({ error_code: 4003, detail: "Import already running" }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await expect(startImportJob({ retailer: "rewe", browser: "firefox" })).rejects.toMatchObject({
      name: "ImportStartError",
      errorCode: 4003,
      message: "Ein Import läuft bereits.",
    });
  });

  it("uses a generic German message when an API error has no numeric code", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 409,
        json: async () => ({ detail: "diagnostic only" }),
      }),
    );

    await expect(startImportJob({ retailer: "rewe" })).rejects.toMatchObject({
      errorCode: 4004,
      message: "Die Anfrage ist fehlgeschlagen.",
    });
  });

  it("uses the German network fallback when import start cannot reach the API", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));

    await expect(startImportJob({ retailer: "rewe" })).rejects.toMatchObject({
      network: true,
      message: "Der Dienst ist nicht erreichbar. Prüfe die Verbindung.",
    });
  });

  it("opens the import event stream for a job", () => {
    const openMock = vi.fn();

    class MockEventSource {
      constructor(url: string) {
        openMock(url);
      }
    }

    vi.stubGlobal("EventSource", MockEventSource as never);

    openImportJobEvents("job-1");

    expect(openMock).toHaveBeenCalledTimes(1);
    expect(openMock).toHaveBeenCalledWith("http://localhost:8000/imports/job-1/events");
  });
});
