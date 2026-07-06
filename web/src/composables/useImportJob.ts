import { computed, onScopeDispose, ref } from "vue";

import { openImportJobEvents, startImportJob } from "../api/imports";
import type { ImportJobEventPayload, ImportProgressState, ImportRetailer } from "../types/imports";

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

  let eventSource: EventSource | null = null;
  let activeToken = 0;

  function closeEventSource() {
    if (eventSource) {
      eventSource.close();
      eventSource = null;
    }
  }

  function applyEventPayload(data: ImportJobEventPayload) {
    progress.value = { ...data.progress };
  }

  function parseEventPayload(event: MessageEvent<string>) {
    return JSON.parse(event.data) as ImportJobEventPayload;
  }

  function attachStreamHandlers(stream: EventSource, token: number) {
    const handleProgress = (event: MessageEvent<string>) => {
      if (token !== activeToken) {
        return;
      }
      applyEventPayload(parseEventPayload(event));
    };

    const handleSuccess = async (event: MessageEvent<string>) => {
      if (token !== activeToken) {
        return;
      }

      applyEventPayload(parseEventPayload(event));
      closeEventSource();
      loading.value = false;
      await refreshDashboard();
    };

    const handleError = () => {
      if (token !== activeToken) {
        return;
      }

      error.value = "Import stream failed";
      loading.value = false;
      closeEventSource();
    };

    stream.addEventListener("progress", handleProgress as EventListener);
    stream.addEventListener("success", handleSuccess as EventListener);
    stream.addEventListener("error", handleError as EventListener);
  }

  async function startImport(retailer: ImportRetailer) {
    const token = ++activeToken;
    closeEventSource();
    loading.value = true;
    error.value = null;
    progress.value = { ...EMPTY_PROGRESS };

    try {
      const response = await startImportJob(retailer);
      if (token !== activeToken) {
        return;
      }

      eventSource = openImportJobEvents(response.job_id);
      attachStreamHandlers(eventSource, token);
    } catch (cause) {
      if (token !== activeToken) {
        return;
      }

      error.value = cause instanceof Error ? cause.message : "Failed to start import";
      loading.value = false;
      closeEventSource();
    }
  }

  const running = computed(() => loading.value || eventSource !== null);

  onScopeDispose(() => {
    closeEventSource();
  });

  return {
    progress,
    loading,
    running,
    error,
    startImport,
    closeEventSource,
  };
}
