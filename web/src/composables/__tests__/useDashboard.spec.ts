import { effectScope, nextTick } from "vue";
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
});
