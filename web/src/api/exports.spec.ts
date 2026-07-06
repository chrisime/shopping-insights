// @vitest-environment jsdom

import { afterEach, describe, expect, it, vi } from "vitest";

import { buildReceiptsExportFilename, exportReceiptsJson } from "./exports";

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("exportReceiptsJson", () => {
  it("requests the export endpoint with filters and downloads the json", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ data: [{ id: "r1" }] }),
    });
    const click = vi.fn();
    const remove = vi.fn();
    const anchor = { href: "", download: "", rel: "", click, remove } as unknown as HTMLAnchorElement;
    const createObjectURL = vi.fn(() => "blob:receipt-export");
    const revokeObjectURL = vi.fn();

    vi.stubGlobal("fetch", fetchMock);
    vi.stubGlobal("URL", Object.assign(URL, { createObjectURL, revokeObjectURL }));
    vi.spyOn(document, "createElement").mockReturnValue(anchor);
    vi.spyOn(document.body, "appendChild").mockImplementation(() => anchor);

    await exportReceiptsJson({ retailer: "lidl", start_date: "2024-01-01", end_date: "2024-01-31" });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(String(fetchMock.mock.calls[0][0])).toContain("/exports/receipts");
    expect(String(fetchMock.mock.calls[0][0])).toContain("retailer=lidl");
    expect(anchor.download).toBe("shopping-analyzer-receipts-lidl-2024-01-01-2024-01-31.json");
    expect(click).toHaveBeenCalledTimes(1);
    expect(revokeObjectURL).toHaveBeenCalledWith("blob:receipt-export");
  });

  it("builds stable filenames without filters", () => {
    expect(buildReceiptsExportFilename()).toBe("shopping-analyzer-receipts.json");
    expect(buildReceiptsExportFilename({ retailer: "rewe" })).toBe("shopping-analyzer-receipts-rewe.json");
  });
});
