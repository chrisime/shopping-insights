import type { ImportStartRequest, ImportStartResponse } from "../types/imports";
import { apiUrl } from "./http";
import { apiErrorText, networkErrorText, t } from "../utils/copy";

const UNKNOWN_API_CODE = 4004;

export class ImportStartError extends Error {
  constructor(
    message: string,
    public errorCode: number,
    public network = false,
  ) {
    super(message);
    this.name = "ImportStartError";
  }
}

export async function startImportJob(payload: ImportStartRequest): Promise<ImportStartResponse> {
  const url = apiUrl("/imports/start");
  if (
    payload.user_login &&
    url.protocol !== "https:" &&
    !(url.protocol === "http:" && ["localhost", "127.0.0.1", "[::1]"].includes(url.hostname))
  ) {
    throw new ImportStartError(t("import.secureConnectionRequired"), 4001);
  }

  let response: Response;
  try {
    response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
      ...(payload.user_login && { redirect: "error", cache: "no-store" }),
    });
  } catch {
    throw new ImportStartError(networkErrorText(), UNKNOWN_API_CODE, true);
  }

  if (!response.ok) {
    let errorCode: number | undefined;
    try {
      const body = (await response.json()) as { error_code?: unknown };
      if (typeof body.error_code === "number") errorCode = body.error_code;
    } catch {
      // Use the generic API error fallback.
    }
    const code = errorCode ?? UNKNOWN_API_CODE;
    throw new ImportStartError(apiErrorText(code), code);
  }

  return (await response.json()) as ImportStartResponse;
}

export function openImportJobEvents(jobId: string): EventSource {
  return new EventSource(apiUrl(`/imports/${jobId}/events`).toString());
}
