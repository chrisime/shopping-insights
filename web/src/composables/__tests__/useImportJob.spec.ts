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

    await job!.startImport({ retailer: "lidl", browser: "firefox" });
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

    await job!.startImport({ retailer: "lidl", browser: "firefox" });
    await job!.startImport({ retailer: "rewe", cookies_file: "rewe_cookies.json" });

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

    await job!.startImport({ retailer: "lidl", browser: "firefox" });
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

    await job!.startImport({ retailer: "lidl", browser: "firefox" });
    MockEventSource.instances[0].emitEmptyError();

    expect(job!.error.value).toBeNull();
    expect(job!.loading.value).toBe(true);
    expect(MockEventSource.instances[0].close).not.toHaveBeenCalled();

    scope.stop();
  });

  it("surfaces structured backend error details", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ job_id: "job-1", retailer: "lidl" }) });
    vi.stubGlobal("fetch", fetchMock);
    vi.stubGlobal("EventSource", MockEventSource as never);

    const scope = effectScope();
    const job = scope.run(() => useImportJob(() => undefined));
    expect(job).toBeDefined();

    await job!.startImport({ retailer: "lidl", browser: "firefox" });
    MockEventSource.instances[0].emit("error", {
      job_id: "job-1",
      retailer: "lidl",
      status: "error",
      progress: {
        current: 0,
        total: 1,
        added: 0,
        skipped: 0,
        errors: 1,
        items: 0,
        current_receipt: "-",
      },
      error: { error_code: 2102, detail: "Nicht autorisiert (401)" },
      message: "Import fehlgeschlagen",
    });

    expect(job!.technicalError.value).toEqual({ error_code: 2102, detail: "Nicht autorisiert (401)" });
    expect(job!.error.value).toBe("Import fehlgeschlagen");

    scope.stop();
  });

  it("surfaces structured error details in the visible error string", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ job_id: "job-1", retailer: "lidl" }) });
    vi.stubGlobal("fetch", fetchMock);
    vi.stubGlobal("EventSource", MockEventSource as never);

    const scope = effectScope();
    const job = scope.run(() => useImportJob(() => undefined));
    expect(job).toBeDefined();

    await job!.startImport({ retailer: "lidl", browser: "firefox" });
    MockEventSource.instances[0].emit("error", {
      job_id: "job-1",
      retailer: "lidl",
      status: "error",
      progress: {
        current: 0,
        total: 1,
        added: 0,
        skipped: 0,
        errors: 1,
        items: 0,
        current_receipt: "-",
      },
      error: { error_code: 2102, detail: "Nicht autorisiert (401)" },
      message: "Import fehlgeschlagen",
    });

    expect(job!.error.value).toBe("Import fehlgeschlagen");
    expect(job!.technicalError.value?.error_code).toBe(2102);

    scope.stop();
  });

  it("surfaces concurrent import conflicts as a structured start error", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 409,
      json: async () => ({ detail: { error_code: 4091, detail: "Import bereits aktiv" } }),
    });
    vi.stubGlobal("fetch", fetchMock);
    vi.stubGlobal("EventSource", MockEventSource as never);

    const scope = effectScope();
    const job = scope.run(() => useImportJob(() => undefined));
    expect(job).toBeDefined();

    await job!.startImport({ retailer: "lidl", browser: "firefox" });

    expect(job!.error.value).toBe("Import bereits aktiv");
    expect(job!.technicalError.value).toEqual({ error_code: 4091, detail: "Import bereits aktiv" });
    expect(job!.loading.value).toBe(false);
    expect(MockEventSource.instances).toHaveLength(0);

    scope.stop();
  });
});
