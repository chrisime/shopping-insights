import { afterEach, describe, expect, it, vi } from "vitest";

import { openImportJobEvents, startImportJob } from "./imports";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("import api helpers", () => {
  it("starts an import job for the selected retailer", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ job_id: "job-1", retailer: "lidl" }) });
    vi.stubGlobal("fetch", fetchMock);

    await startImportJob("lidl");

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(String(fetchMock.mock.calls[0][0])).toContain("/imports/start");
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
