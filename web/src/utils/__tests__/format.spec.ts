import { describe, expect, it } from "vite-plus/test";

import { addressText, amount, euro, quantity, retailerLabel, text } from "../format";

describe("format helpers", () => {
  it("normalizes numeric input", () => {
    expect(amount("4.5")).toBe(4.5);
    expect(amount(null)).toBe(0);
    expect(amount(3)).toBe(3);
  });

  it("renders missing values as a dash", () => {
    expect(text(null)).toBe("-");
    expect(text(undefined)).toBe("-");
    expect(text("Apfel")).toBe("Apfel");
  });

  it("formats euro amounts with two decimals", () => {
    expect(euro(4)).toBe("€4.00");
    expect(euro("2.5")).toBe("€2.50");
    expect(euro(Number.NaN)).toBe("-");
  });

  it("formats kilogram quantities with three decimals and pieces as integers", () => {
    expect(quantity(0.696, "kg")).toBe("0.696 kg");
    expect(quantity(2.9, "pc")).toBe("2 pc");
    expect(quantity(Number.NaN, "kg")).toBe("-");
  });

  it("maps retailer codes to display names", () => {
    expect(retailerLabel("lidl")).toBe("Lidl");
    expect(retailerLabel("rewe")).toBe("REWE");
    expect(retailerLabel("dm")).toBe("dm");
    expect(retailerLabel("rossmann")).toBe("Rossmann");
    expect(retailerLabel("other")).toBe("other");
    expect(retailerLabel(undefined)).toBe("-");
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
