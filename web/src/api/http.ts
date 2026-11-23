const DEFAULT_API_BASE_URL = "http://localhost:8000";

export type QueryParams = Record<string, string | number | null | undefined>;

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
  const response = await fetch(apiUrl(path, params));
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return (await response.json()) as T;
}
