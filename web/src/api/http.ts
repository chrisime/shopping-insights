const DEFAULT_API_BASE_URL = "http://localhost:8000";

export type QueryParams = Record<string, string | number | null | undefined>;

export class ApiRequestError extends Error {
  constructor(
    public kind: "api" | "network",
    public errorCode?: number,
    public status?: number,
  ) {
    super(
      kind === "api"
        ? `API request failed (${status ?? "unknown status"})`
        : "Network request failed",
    );
    this.name = "ApiRequestError";
  }
}

export function apiUrl(path: string, params: QueryParams = {}): URL {
  const baseUrl = import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL;
  const url = new URL(path, baseUrl);

  for (const [key, value] of Object.entries(params)) {
    if (value != null && value !== "") {
      url.searchParams.set(key, String(value));
    }
  }

  return url;
}

export async function getJson<T>(path: string, params: QueryParams = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(apiUrl(path, params));
  } catch {
    throw new ApiRequestError("network");
  }
  if (!response.ok) {
    let errorCode: number | undefined;
    try {
      const body = (await response.json()) as { error_code?: unknown };
      if (typeof body.error_code === "number") errorCode = body.error_code;
    } catch {
      // The generic API fallback is used when an error response has no JSON body.
    }
    throw new ApiRequestError("api", errorCode, response.status);
  }
  return (await response.json()) as T;
}
