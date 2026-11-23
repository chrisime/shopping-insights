import type { ReceiptAddress } from "../types/dashboard";

export function amount(value: unknown): number {
  return typeof value === "number" ? value : Number(value ?? 0);
}

export function text(value: unknown): string {
  // oxlint-disable-next-line typescript/no-base-to-string -- display fallback for unknown values
  return value == null ? "-" : String(value);
}

export function euro(value: unknown): string {
  const numeric = amount(value);
  return Number.isFinite(numeric) ? `€${numeric.toFixed(2)}` : "-";
}

export function quantity(value: number, unit: string): string {
  if (!Number.isFinite(value)) return "-";
  return `${unit === "kg" ? value.toFixed(3) : Math.trunc(value)} ${unit}`;
}

const RETAILER_LABELS: Record<string, string> = {
  lidl: "Lidl",
  rewe: "REWE",
  dm: "dm",
  rossmann: "Rossmann",
};

export function retailerLabel(value?: string): string {
  if (!value) return "-";
  return RETAILER_LABELS[value] ?? value;
}

export function addressText(address?: ReceiptAddress): string {
  if (!address) return "";

  const street =
    address.street && address.street_no
      ? `${address.street} ${address.street_no}`
      : (address.street ?? "");
  const city =
    address.zip && address.city
      ? `${address.zip} ${address.city}`
      : (address.city ?? address.zip ?? "");

  return [street, city].filter(Boolean).join(", ");
}
