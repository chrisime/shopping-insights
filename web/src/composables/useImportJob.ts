import { computed, onScopeDispose, ref } from "vue";

import { ImportStartError, openImportJobEvents, startImportJob } from "../api/imports";
import type {
  ImportJobEventPayload,
  ImportProgressState,
  ImportStartRequest,
  ImportTechnicalError,
} from "../types/imports";

const EMPTY_PROGRESS: ImportProgressState = {
  current: 0,
  total: 0,
  added: 0,
  skipped: 0,
  errors: 0,
  items: 0,
  current_receipt: "-",
};

export function useImportJob(refreshDashboard: () => Promise<void> | void) {
  const progress = ref<ImportProgressState>({ ...EMPTY_PROGRESS });
  const loading = ref(false);
  const error = ref<string | null>(null);
  const technicalError = ref<ImportTechnicalError | null>(null);
  const message = ref<string | null>(null);

  const streaming = ref(false);
  let eventSource: EventSource | null = null;
  let activeToken = 0;
  let disposed = false;

  function closeEventSource() {
    if (eventSource) {
      eventSource.close();
      eventSource = null;
    }
    streaming.value = false;
  }

  function applyEventPayload(data: ImportJobEventPayload) {
    progress.value = { ...data.progress };
    message.value = data.message;
    technicalError.value = data.error;
    error.value = data.error ? (data.message ?? data.error.detail) : null;
  }

  function readPayload(event: Event): ImportJobEventPayload | null {
    if (!("data" in event) || typeof event.data !== "string" || event.data.length === 0) {
      return null;
    }
    try {
      return JSON.parse(event.data) as ImportJobEventPayload;
    } catch {
      return null;
    }
  }

  async function handleSuccess(event: Event, token: number) {
    if (token !== activeToken) return;

    const payload = readPayload(event);
    if (payload) applyEventPayload(payload);
    closeEventSource();
    loading.value = false;

    try {
      await refreshDashboard();
    } catch (cause) {
      error.value = cause instanceof Error ? cause.message : "Failed to refresh dashboard";
    }
  }

  function attachStreamHandlers(stream: EventSource, token: number) {
    stream.addEventListener("progress", (event) => {
      if (token !== activeToken) return;
      const payload = readPayload(event);
      if (payload) applyEventPayload(payload);
    });

    stream.addEventListener("success", (event) => {
      void handleSuccess(event, token);
    });

    stream.addEventListener("error", (event) => {
      if (token !== activeToken) return;
      if (!("data" in event) || typeof event.data !== "string" || event.data.length === 0) {
        return;
      }

      try {
        const payload = JSON.parse(event.data) as Partial<ImportJobEventPayload>;
        technicalError.value = payload.error ?? {
          error_code: 2103,
          detail: payload.message ?? "Import stream failed",
        };
        error.value = payload.message ?? technicalError.value.detail;
      } catch {
        error.value = "Import stream failed";
      }
      loading.value = false;
      closeEventSource();
    });
  }

  async function startImport(payload: ImportStartRequest) {
    const token = ++activeToken;
    closeEventSource();
    loading.value = true;
    error.value = null;
    progress.value = { ...EMPTY_PROGRESS };
    message.value = null;

    try {
      const response = await startImportJob(payload);
      if (disposed || token !== activeToken) {
        return;
      }

      eventSource = openImportJobEvents(response.job_id);
      streaming.value = true;
      attachStreamHandlers(eventSource, token);
    } catch (cause) {
      if (disposed || token !== activeToken) {
        return;
      }

      if (cause instanceof ImportStartError) {
        technicalError.value = { error_code: cause.errorCode, detail: cause.message };
        error.value = cause.message;
      } else {
        error.value = cause instanceof Error ? cause.message : "Failed to start import";
      }
      loading.value = false;
      closeEventSource();
    }
  }

  const running = computed(() => loading.value || streaming.value);

  onScopeDispose(() => {
    disposed = true;
    activeToken += 1;
    closeEventSource();
  });

  return {
    progress,
    loading,
    running,
    error,
    technicalError,
    message,
    startImport,
  };
}
