import { describe, expect, it } from "vite-plus/test";

import {
  addressText,
  compactEuro,
  euro,
  percentage,
  quantity,
  retailerLabel,
  text,
} from "../format";

describe("format helpers", () => {
  it("renders missing values as a dash", () => {
    expect(text(undefined)).toBe("–");
    expect(text("Apfel")).toBe("Apfel");
  });

  it("formats euro amounts with German separators and a non-breaking space", () => {
    expect(euro(4)).toBe("4,00 €");
    expect(euro(1234.5)).toBe("1.234,50 €");
    expect(euro(Number.NaN)).toBe("–");
  });

  it("formats compact chart-axis values as whole German euros", () => {
    expect(compactEuro(1234.5)).toBe("1.235 €");
    expect(compactEuro(Number.NaN)).toBe("–");
  });

  it("formats kilogram quantities with three decimals and preserves fractional pieces", () => {
    expect(quantity(0.696, "kg")).toBe("0,696 kg");
    expect(quantity(0.5, "kg")).toBe("0,500 kg");
    expect(quantity(2.9, "pc")).toBe("2,9 pc");
    expect(quantity(2, "pc")).toBe("2 pc");
    expect(quantity(Number.NaN, "kg")).toBe("–");
  });

  it("formats percentages whose input is already expressed in percent", () => {
    expect(percentage(12.5)).toBe("12,5 %");
    expect(percentage(Number.NaN)).toBe("–");
  });

  it("formats coupon values in their supplied currency or defaults to euros", () => {
    expect(euro(12.5, "USD")).toBe("12,50 $");
    expect(euro(12.5, "invalid")).toBe("12,50 €");
  });

  it("maps retailer codes to display names", () => {
    expect(retailerLabel("lidl")).toBe("Lidl");
    expect(retailerLabel("rewe")).toBe("REWE");
    expect(retailerLabel("dm")).toBe("dm");
    expect(retailerLabel("rossmann")).toBe("Rossmann");
    expect(retailerLabel("other")).toBe("other");
    expect(retailerLabel(undefined)).toBe("–");
  });

  it("joins street and city parts only when present", () => {
    expect(
      addressText({ street: "Bahnhofstr.", street_no: "1", zip: "80335", city: "München" }),
    ).toBe("Bahnhofstr. 1, 80335 München");
    expect(addressText({ city: "München" })).toBe("München");
    expect(addressText({ zip: "80335" })).toBe("80335");
    expect(addressText(undefined)).toBe("");
  });
});
