import { effectScope, nextTick } from "vue";
import { flushPromises } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vite-plus/test";

import { useDashboard } from "../useDashboard";

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

function stubFetch() {
  const fetchMock = vi.fn().mockResolvedValue({
    ok: true,
    json: async () => ({ title: "Shopping Analyzer Dashboard", sections: [] }),
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function response(title: string) {
  return { ok: true, json: async () => ({ title, sections: [] }) };
}

describe("useDashboard", () => {
  it("debounces search refreshes", async () => {
    vi.useFakeTimers();
    const fetchMock = stubFetch();
    const scope = effectScope();
    const dashboard = scope.run(() => useDashboard())!;

    dashboard.search.value = "milch";
    await nextTick();
    expect(fetchMock).not.toHaveBeenCalled();

    vi.advanceTimersByTime(400);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    scope.stop();
  });

  it("cancels a pending search refresh when the scope is disposed", async () => {
    vi.useFakeTimers();
    const fetchMock = stubFetch();
    const scope = effectScope();
    const dashboard = scope.run(() => useDashboard())!;

    dashboard.search.value = "milch";
    await nextTick();
    scope.stop();

    vi.advanceTimersByTime(400);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("debounces one search refresh when search resets a later page", async () => {
    vi.useFakeTimers();
    const fetchMock = stubFetch();
    const scope = effectScope();
    const dashboard = scope.run(() => useDashboard())!;

    dashboard.page.value = 3;
    await nextTick();
    await flushPromises();
    fetchMock.mockClear();

    dashboard.search.value = "milk";
    await nextTick();
    expect(dashboard.page.value).toBe(1);
    expect(fetchMock).not.toHaveBeenCalled();

    vi.advanceTimersByTime(400);
    await flushPromises();

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const requestUrl = new URL(String(fetchMock.mock.calls[0][0]));
    expect(requestUrl.searchParams.get("search")).toBe("milk");
    expect(requestUrl.searchParams.get("page")).toBeNull();
    scope.stop();
  });

  it("cancels the pending search refresh when retailer change clears search", async () => {
    vi.useFakeTimers();
    const fetchMock = stubFetch();
    const scope = effectScope();
    const dashboard = scope.run(() => useDashboard())!;
    await dashboard.refresh();
    fetchMock.mockClear();

    dashboard.search.value = "milk";
    await nextTick();
    dashboard.retailer.value = "rewe";
    await nextTick();

    vi.advanceTimersByTime(400);
    await flushPromises();

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const requestUrl = new URL(String(fetchMock.mock.calls[0][0]));
    expect(requestUrl.searchParams.get("retailer")).toBe("rewe");
    expect(requestUrl.searchParams.get("search")).toBeNull();
    scope.stop();
  });

  it("coalesces rapid successive search edits into the final debounced request", async () => {
    vi.useFakeTimers();
    const fetchMock = stubFetch();
    const scope = effectScope();
    const dashboard = scope.run(() => useDashboard())!;

    dashboard.search.value = "mil";
    await nextTick();
    vi.advanceTimersByTime(250);
    dashboard.search.value = "milk";
    await nextTick();
    vi.advanceTimersByTime(399);
    expect(fetchMock).not.toHaveBeenCalled();

    vi.advanceTimersByTime(1);
    await flushPromises();

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(new URL(String(fetchMock.mock.calls[0][0])).searchParams.get("search")).toBe("milk");
    scope.stop();
  });

  it("does not let an older request replace a newer dashboard response", async () => {
    let resolveFirst!: (value: ReturnType<typeof response>) => void;
    let resolveSecond!: (value: ReturnType<typeof response>) => void;
    const first = new Promise<ReturnType<typeof response>>((resolve) => {
      resolveFirst = resolve;
    });
    const second = new Promise<ReturnType<typeof response>>((resolve) => {
      resolveSecond = resolve;
    });
    const fetchMock = vi.fn().mockReturnValueOnce(first).mockReturnValueOnce(second);
    vi.stubGlobal("fetch", fetchMock);
    const scope = effectScope();
    const dashboard = scope.run(() => useDashboard())!;

    const firstRequest = dashboard.refresh();
    const secondRequest = dashboard.refresh();
    resolveSecond(response("new response"));
    await secondRequest;
    expect(dashboard.payload.value?.title).toBe("new response");
    expect(dashboard.loading.value).toBe(false);

    resolveFirst(response("old response"));
    await firstRequest;
    expect(dashboard.payload.value?.title).toBe("new response");
    expect(dashboard.loading.value).toBe(false);
    scope.stop();
  });
});
