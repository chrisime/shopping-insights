// @vitest-environment jsdom

import { effectScope, nextTick } from "vue";
import { afterEach, describe, expect, it, vi } from "vitest";

import { useImportJob } from "../useImportJob";

class MockEventSource {
  static instances: MockEventSource[] = [];

  listeners = new Map<string, Array<(event: MessageEvent<string>) => void>>();
  onerror: ((event: Event) => void) | null = null;
  close = vi.fn();

  constructor(public url: string) {
    MockEventSource.instances.push(this);
  }

  addEventListener(type: string, listener: (event: MessageEvent<string>) => void) {
    const listeners = this.listeners.get(type) ?? [];
    listeners.push(listener);
    this.listeners.set(type, listeners);
  }

  emit(type: string, payload: object) {
    const event = { data: JSON.stringify(payload) } as MessageEvent<string>;
    for (const listener of this.listeners.get(type) ?? []) {
      listener(event);
    }
  }

  emitEmptyError() {
    const event = { data: "" } as MessageEvent<string>;
    for (const listener of this.listeners.get("error") ?? []) {
      listener(event);
    }
  }
}

afterEach(() => {
  vi.unstubAllGlobals();
  MockEventSource.instances = [];
});

describe("useImportJob", () => {
  it("updates progress from SSE events and refreshes on success", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ job_id: "job-1", retailer: "lidl" }) });
    const refreshDashboard = vi.fn().mockResolvedValue(undefined);

    vi.stubGlobal("fetch", fetchMock);
    vi.stubGlobal("EventSource", MockEventSource as never);

    const scope = effectScope();
    const job = scope.run(() => useImportJob(refreshDashboard));
    expect(job).toBeDefined();

    await job!.startImport("lidl");
    expect(job!.loading.value).toBe(true);
    expect(MockEventSource.instances).toHaveLength(1);

    MockEventSource.instances[0].emit("progress", {
      job_id: "job-1",
      retailer: "lidl",
      status: "running",
      progress: {
        current: 1,
        total: 2,
        added: 1,
        skipped: 0,
        errors: 0,
        items: 3,
        current_receipt: "r1",
      },
      message: null,
    });

    expect(job!.progress.value.current).toBe(1);
    expect(job!.progress.value.current_receipt).toBe("r1");

    MockEventSource.instances[0].emit("success", {
      job_id: "job-1",
      retailer: "lidl",
      status: "success",
      progress: {
        current: 2,
        total: 2,
        added: 2,
        skipped: 0,
        errors: 0,
        items: 6,
        current_receipt: "r2",
      },
      message: null,
    });

    await nextTick();

    expect(refreshDashboard).toHaveBeenCalledTimes(1);
    expect(job!.loading.value).toBe(false);
    expect(MockEventSource.instances[0].close).toHaveBeenCalledTimes(1);

    scope.stop();
  });

  it("closes the previous event source when starting a new import", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ job_id: "job-1", retailer: "lidl" }) });
    vi.stubGlobal("fetch", fetchMock);
    vi.stubGlobal("EventSource", MockEventSource as never);

    const scope = effectScope();
    const job = scope.run(() => useImportJob(() => undefined));
    expect(job).toBeDefined();

    await job!.startImport("lidl");
    await job!.startImport("rewe");

    expect(MockEventSource.instances).toHaveLength(2);
    expect(MockEventSource.instances[0].close).toHaveBeenCalledTimes(1);

    scope.stop();
  });

  it("closes the active event source when the scope is disposed", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ job_id: "job-1", retailer: "lidl" }) });
    vi.stubGlobal("fetch", fetchMock);
    vi.stubGlobal("EventSource", MockEventSource as never);

    const scope = effectScope();
    const job = scope.run(() => useImportJob(() => undefined));
    expect(job).toBeDefined();

    await job!.startImport("lidl");
    scope.stop();

    expect(MockEventSource.instances).toHaveLength(1);
    expect(MockEventSource.instances[0].close).toHaveBeenCalledTimes(1);
  });

  it("ignores transport error events and keeps the stream open", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ job_id: "job-1", retailer: "lidl" }) });
    vi.stubGlobal("fetch", fetchMock);
    vi.stubGlobal("EventSource", MockEventSource as never);

    const scope = effectScope();
    const job = scope.run(() => useImportJob(() => undefined));
    expect(job).toBeDefined();

    await job!.startImport("lidl");
    MockEventSource.instances[0].emitEmptyError();

    expect(job!.error.value).toBeNull();
    expect(job!.loading.value).toBe(true);
    expect(MockEventSource.instances[0].close).not.toHaveBeenCalled();

    scope.stop();
  });
});
