import type { ImportRetailer, ImportStartRequest, ImportStartResponse } from "../types/imports";

const CONCURRENT_IMPORT_MESSAGE = "Import bereits aktiv";
const CONCURRENT_IMPORT_CODE = 4091;

export class ImportStartError extends Error {
  constructor(
    message: string,
    public errorCode: number,
  ) {
    super(message);
    this.name = "ImportStartError";
  }
}

const DEFAULT_API_BASE_URL = "http://localhost:8000";

export async function startImportJob(payload: ImportStartRequest): Promise<ImportStartResponse> {
  const baseUrl = import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL;
  const url = new URL("/imports/start", baseUrl);

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    if (response.status === 409) {
      const payload = (await response.json()) as { detail?: { error_code?: number; detail?: string } };
      throw new ImportStartError(payload.detail?.detail ?? CONCURRENT_IMPORT_MESSAGE, payload.detail?.error_code ?? CONCURRENT_IMPORT_CODE);
    }
    throw new Error(`HTTP ${response.status}`);
  }

  return (await response.json()) as ImportStartResponse;
}

export function openImportJobEvents(jobId: string): EventSource {
  const baseUrl = import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL;
  const url = new URL(`/imports/${jobId}/events`, baseUrl);
  return new EventSource(url.toString());
}
