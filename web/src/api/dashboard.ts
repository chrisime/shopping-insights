import { getJson } from "./http";
import type { DashboardFilters, DashboardPayload, Receipt } from "../types/dashboard";

export function fetchDashboard(filters: DashboardFilters = {}): Promise<DashboardPayload> {
  return getJson<DashboardPayload>("/ui/dashboard", filters);
}

export function fetchReceiptsByDateRange(
  startDate: string,
  endDate: string,
  retailer?: string,
): Promise<Receipt[]> {
  return getJson<Receipt[]>("/receipts/by-date", {
    start_date: startDate,
    end_date: endDate,
    retailer,
  });
}

export function fetchReceiptsByItem(name: string, retailer?: string): Promise<Receipt[]> {
  return getJson<Receipt[]>("/receipts/by-item", { name, retailer });
}
