import type { ImportStartRequest, ImportStartResponse } from "../types/imports";
import { apiUrl } from "./http";

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

export async function startImportJob(payload: ImportStartRequest): Promise<ImportStartResponse> {
  const url = apiUrl("/imports/start");
  if (
    payload.rossmann_login &&
    url.protocol !== "https:" &&
    !(url.protocol === "http:" && ["localhost", "127.0.0.1", "[::1]"].includes(url.hostname))
  ) {
    throw new Error(
      "Die Rossmann-Anmeldung benötigt eine lokale oder verschlüsselte API-Verbindung.",
    );
  }

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
    ...(payload.rossmann_login && { redirect: "error", cache: "no-store" }),
  });

  if (!response.ok) {
    if (response.status === 409) {
      const body = (await response.json()) as {
        detail?: { error_code?: number; detail?: string };
      };
      throw new ImportStartError(
        body.detail?.detail ?? CONCURRENT_IMPORT_MESSAGE,
        body.detail?.error_code ?? CONCURRENT_IMPORT_CODE,
      );
    }
    throw new Error(`HTTP ${response.status}`);
  }

  return (await response.json()) as ImportStartResponse;
}

export function openImportJobEvents(jobId: string): EventSource {
  return new EventSource(apiUrl(`/imports/${jobId}/events`).toString());
}
