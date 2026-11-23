import type { DashboardFilters } from "../types/dashboard";
import { apiUrl } from "./http";

export function buildReceiptsExportFilename(filters: DashboardFilters = {}): string {
  const segments = ["shopping-analyzer-receipts"];

  if (filters.retailer) {
    segments.push(filters.retailer);
  }

  if (filters.start_date || filters.end_date) {
    const start = filters.start_date ?? "from-start";
    const end = filters.end_date ?? "to-end";
    segments.push(`${start}-${end}`);
  }

  return `${segments.join("-")}.json`;
}

export async function exportReceiptsJson(filters: DashboardFilters = {}): Promise<void> {
  const response = await fetch(apiUrl("/exports/receipts", filters));
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  const payload = await response.json();
  const blob = new Blob([JSON.stringify(payload, null, 2) + "\n"], {
    type: "application/json;charset=utf-8",
  });
  const objectUrl = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = objectUrl;
  anchor.download = buildReceiptsExportFilename(filters);
  anchor.rel = "noopener";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(objectUrl);
}
