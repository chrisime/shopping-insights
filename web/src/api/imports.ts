import type { ImportRetailer, ImportStartRequest, ImportStartResponse } from "../types/imports";

const DEFAULT_API_BASE_URL = "http://localhost:8000";

export async function startImportJob(retailer: ImportRetailer): Promise<ImportStartResponse> {
  const baseUrl = import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL;
  const url = new URL("/imports/start", baseUrl);
  const payload: ImportStartRequest = { retailer };

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  return (await response.json()) as ImportStartResponse;
}

export function openImportJobEvents(jobId: string): EventSource {
  const baseUrl = import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL;
  const url = new URL(`/imports/${jobId}/events`, baseUrl);
  return new EventSource(url.toString());
}
