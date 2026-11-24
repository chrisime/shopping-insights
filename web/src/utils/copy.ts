import germanCopy from "../i18n/de.json";

export type CopyKey = Exclude<keyof typeof germanCopy, "sectionTitleKeys">;

const sectionTitleKeys: Readonly<Partial<Record<string, string>>> = germanCopy.sectionTitleKeys;
export type CopyValues = Record<string, string | number>;

export function t(key: CopyKey, values: CopyValues = {}): string {
  const template = germanCopy[key];
  if (typeof template !== "string") return germanCopy["catalog.missing"];

  return template.replace(/\{\{(\w+)\}\}/g, (placeholder, name: string) =>
    name in values ? String(values[name]) : placeholder,
  );
}

export function dashboardSectionTitle(title: string): string {
  const key = Object.hasOwn(sectionTitleKeys, title) ? sectionTitleKeys[title] : undefined;
  return key && key !== "sectionTitleKeys" && Object.hasOwn(germanCopy, key)
    ? t(key as CopyKey)
    : t("sections.unknown");
}

export function apiErrorText(errorCode?: number): string {
  if (errorCode === undefined) return t("errors.api.generic");

  const key = `errors.api.${errorCode}` as CopyKey;
  return key in germanCopy ? t(key) : t("errors.api.generic");
}

export function networkErrorText(): string {
  return t("errors.network");
}
