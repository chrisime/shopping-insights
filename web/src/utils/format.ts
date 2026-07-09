export function amount(value: unknown): number {
  return typeof value === "number" ? value : Number(value ?? 0);
}

export function text(value: unknown): string {
  return value == null ? "-" : String(value);
}

export function euro(value: unknown): string {
  const numeric = amount(value);
  return Number.isFinite(numeric) ? `€${numeric.toFixed(2)}` : "-";
}
