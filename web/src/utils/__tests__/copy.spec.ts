import { describe, expect, it } from "vite-plus/test";

import { apiErrorText, networkErrorText, t, type CopyKey } from "../copy";

describe("German copy catalog", () => {
  it("returns the text for a known catalog key", () => {
    expect(t("filters.retailer")).toBe("Händler");
  });

  it("returns a readable fallback for a missing catalog key", () => {
    expect(t("catalog.missing" as CopyKey)).toBe("Text nicht verfügbar");
  });

  it("maps API error codes to German messages without using HTTP status", () => {
    expect(apiErrorText(4003)).toBe("Ein Import läuft bereits.");
    expect(apiErrorText(4003)).toBe(apiErrorText(4003));
  });

  it("uses a generic German message for unknown or missing API codes", () => {
    expect(apiErrorText(999999)).toBe("Die Anfrage ist fehlgeschlagen.");
    expect(apiErrorText(undefined)).toBe("Die Anfrage ist fehlgeschlagen.");
  });

  it("uses a generic German message for network failures", () => {
    expect(networkErrorText()).toBe("Der Dienst ist nicht erreichbar. Prüfe die Verbindung.");
  });
});
