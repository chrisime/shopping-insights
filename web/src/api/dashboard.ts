import type { DashboardFilters, DashboardPayload } from "../types/dashboard";

const DEFAULT_API_BASE_URL = "http://localhost:8000";

export async function fetchDashboard(filters: DashboardFilters = {}): Promise<DashboardPayload> {
  const baseUrl = import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL;
  const url = new URL("/ui/dashboard", baseUrl);

  for (const [key, value] of Object.entries(filters)) {
    if (value != null && value !== "") {
      url.searchParams.set(key, String(value));
    }
  }

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  return (await response.json()) as DashboardPayload;
}

export async function fetchReceiptsByItem(
  name: string,
  retailer?: string,
): Promise<Array<Record<string, unknown>>> {
  const baseUrl = import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL;
  const url = new URL("/receipts/by-item", baseUrl);
  url.searchParams.set("name", name);
  if (retailer) url.searchParams.set("retailer", retailer);
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Failed to fetch receipts: ${res.status}`);
  return res.json();
}
