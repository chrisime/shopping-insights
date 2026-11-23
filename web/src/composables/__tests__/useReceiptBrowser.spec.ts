import { effectScope, ref } from "vue";
import { flushPromises } from "@vue/test-utils";
import { describe, expect, it, vi } from "vite-plus/test";

import { useReceiptBrowser } from "../useReceiptBrowser";
import type { Receipt } from "../../types/dashboard";

function receipt(id: string): Receipt {
  return { id, retailer: "lidl", purchase_date: "2024-01-15", total_price: 1, items: [] };
}

function setup(load: () => Promise<Receipt[]>) {
  const visible = ref(false);
  const scope = effectScope();
  const browser = scope.run(() => useReceiptBrowser(load, visible))!;
  return { visible, browser, stop: () => scope.stop() };
}

describe("useReceiptBrowser", () => {
  it("does not load while hidden", async () => {
    const load = vi.fn().mockResolvedValue([receipt("r1")]);
    const { browser, stop } = setup(load);

    await flushPromises();
    expect(load).not.toHaveBeenCalled();
    expect(browser.receipts.value).toEqual([]);
    stop();
  });

  it("loads receipts when the modal becomes visible", async () => {
    const load = vi.fn().mockResolvedValue([receipt("r1"), receipt("r2")]);
    const { visible, browser, stop } = setup(load);

    visible.value = true;
    await flushPromises();

    expect(load).toHaveBeenCalledTimes(1);
    expect(browser.loading.value).toBe(false);
    expect(browser.current.value?.id).toBe("r1");
    stop();
  });

  it("discards a stale response after reopening", async () => {
    let resolveFirst: (value: Receipt[]) => void = () => {};
    const load = vi
      .fn()
      .mockImplementationOnce(() => new Promise<Receipt[]>((resolve) => (resolveFirst = resolve)))
      .mockImplementationOnce(() => Promise.resolve([receipt("new")]));

    const { visible, browser, stop } = setup(load);

    visible.value = true;
    await flushPromises();
    visible.value = false;
    await flushPromises();
    visible.value = true;
    await flushPromises();

    resolveFirst([receipt("old")]);
    await flushPromises();

    expect(browser.receipts.value.map((r) => r.id)).toEqual(["new"]);
    expect(browser.loading.value).toBe(false);
    stop();
  });

  it("pages forward and backward within bounds", async () => {
    const load = vi.fn().mockResolvedValue([receipt("r1"), receipt("r2")]);
    const { visible, browser, stop } = setup(load);

    visible.value = true;
    await flushPromises();

    browser.prev();
    expect(browser.currentIndex.value).toBe(0);

    browser.next();
    expect(browser.current.value?.id).toBe("r2");

    browser.next();
    expect(browser.currentIndex.value).toBe(1);

    browser.prev();
    expect(browser.current.value?.id).toBe("r1");
    stop();
  });

  it("exposes a distinct error when loading fails and clears it on a new lookup", async () => {
    const load = vi.fn().mockRejectedValue(new Error("HTTP 500"));
    const { visible, browser, stop } = setup(load);

    visible.value = true;
    await flushPromises();

    expect(browser.receipts.value).toEqual([]);
    expect(browser.loading.value).toBe(false);
    expect(browser.error.value).toBe("Kassenzettel konnten nicht geladen werden.");
    expect(browser.current.value).toBeUndefined();

    load.mockResolvedValueOnce([]);
    visible.value = false;
    await flushPromises();
    visible.value = true;
    await flushPromises();

    expect(browser.error.value).toBeNull();
    stop();
  });
});
