import type { ReceiptAddress } from "../types/dashboard";
import { t } from "./copy";

const EURO_FORMATTER = new Intl.NumberFormat("de-DE", {
  style: "currency",
  currency: "EUR",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});
const COMPACT_EURO_FORMATTER = new Intl.NumberFormat("de-DE", {
  style: "currency",
  currency: "EUR",
  maximumFractionDigits: 0,
});
const PERCENT_FORMATTER = new Intl.NumberFormat("de-DE", {
  style: "percent",
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});

export function text(value?: string): string {
  return value == null ? t("common.notAvailable") : value;
}

export function euro(value: number, currency = "EUR"): string {
  if (!Number.isFinite(value)) return t("common.notAvailable");
  const code = /^[A-Z]{3}$/.test(currency) ? currency : "EUR";
  try {
    return code === "EUR"
      ? EURO_FORMATTER.format(value)
      : new Intl.NumberFormat("de-DE", {
          style: "currency",
          currency: code,
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        }).format(value);
  } catch {
    return EURO_FORMATTER.format(value);
  }
}

export function compactEuro(value: number): string {
  return Number.isFinite(value) ? COMPACT_EURO_FORMATTER.format(value) : t("common.notAvailable");
}

export function percentage(value: number): string {
  return Number.isFinite(value) ? PERCENT_FORMATTER.format(value / 100) : t("common.notAvailable");
}

export function quantity(value: number, unit: string): string {
  if (!Number.isFinite(value)) return t("common.notAvailable");
  const formatted =
    unit === "kg"
      ? new Intl.NumberFormat("de-DE", {
          minimumFractionDigits: 3,
          maximumFractionDigits: 3,
        }).format(value)
      : new Intl.NumberFormat("de-DE", {
          maximumFractionDigits: 3,
        }).format(value);
  return `${formatted} ${unit}`;
}

export function retailerLabel(value?: string): string {
  if (!value) return t("common.notAvailable");
  const labels: Record<string, string> = {
    lidl: t("retailer.lidl"),
    rewe: t("retailer.rewe"),
    dm: t("retailer.dm"),
    rossmann: t("retailer.rossmann"),
  };
  return labels[value] ?? value;
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
