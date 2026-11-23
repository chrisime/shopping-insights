import germanCopy from "../locales/de.json";

export type CopyKey = keyof typeof germanCopy;
export type CopyValues = Record<string, string | number>;

export function t(key: CopyKey, values: CopyValues = {}): string {
  const template = germanCopy[key];
  if (typeof template !== "string") return germanCopy["catalog.missing"];

  return template.replace(/\{\{(\w+)\}\}/g, (placeholder, name: string) =>
    name in values ? String(values[name]) : placeholder,
  );
}

export function apiErrorText(errorCode?: number): string {
  if (errorCode === undefined) return t("errors.api.generic");

  const key = `errors.api.${errorCode}` as CopyKey;
  return key in germanCopy ? t(key) : t("errors.api.generic");
}

export function networkErrorText(): string {
  return t("errors.network");
}
