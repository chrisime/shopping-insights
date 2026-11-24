// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vite-plus/test";

import DashboardKpiGrid from "../DashboardKpiGrid.vue";

function kpiData(overrides: Record<string, number> = {}) {
  return {
    spendings: 1234.0,
    spendings_without_discount: 1417.0,
    receipt_count: 4,
    avg_receipt_amount: 25.0,
    saved_deposit: 2.25,
    total_savings: 19.0,
    total_savings_pct: 19.0,
    ...overrides,
  };
}

describe("DashboardKpiGrid", () => {
  it("renders all default card groups when data is present", () => {
    const wrapper = mount(DashboardKpiGrid, {
      props: { data: kpiData() },
    });
    expect(wrapper.text()).toContain("Ausgaben");
    expect(wrapper.text()).toContain("Kassenbons");
    expect(wrapper.text()).toContain("Pfandrückgabe");
    expect(wrapper.text()).toContain("Gesamter Preisvorteil");
    expect(wrapper.text()).toContain("1.234,00 €");
    expect(wrapper.text()).toContain("4");
  });

  it("formats currency values", () => {
    const wrapper = mount(DashboardKpiGrid, {
      props: { data: kpiData({ spendings: 1000.5 }) },
    });
    expect(wrapper.text()).toContain("1.000,50 €");
  });

  it("formats percentage values", () => {
    const wrapper = mount(DashboardKpiGrid, {
      props: { data: kpiData({ total_savings_pct: 12.5 }) },
    });
    expect(wrapper.text()).toContain("12,5 %");
  });

  it("shows one card per retailer with totals above the details", () => {
    const wrapper = mount(DashboardKpiGrid, {
      props: {
        data: {
          rewe_discount_amount: 371.77,
          rewe_discount_pct: 8,
          rewe_bonus_collected: 191.84,
          rewe_bonus_redeemed: 189.53,
          rewe_bonus_redeemed_pct: 4.1,
          rewe_bonus_open: 2.31,
          rewe_total_savings: 561.3,
          rewe_total_savings_pct: 12.1,
          lidlplus_discount_amount: 545.1,
          lidlplus_discount_pct: 7.1,
          sticker_discount_amount: 48.78,
          sticker_discount_pct: 0.6,
          lidl_discount_amount: 136.41,
          lidl_discount_pct: 1.8,
          lidl_total_savings: 730.29,
          lidl_total_savings_pct: 9.5,
          rossmann_discount_amount: 72.29,
          rossmann_discount_pct: 33.5,
          rossmann_basket_coupon_amount: 23.98,
          rossmann_product_coupon_amount: 48.31,
          rossmann_product_coupon_pct: 22.4,
          dm_total_savings: 43.12,
          dm_total_savings_pct: 16.46,
        },
      },
    });

    const cards = wrapper.findAll("article");
    expect(cards.map((card) => card.get("h3").text())).toEqual(["REWE", "Lidl", "Rossmann", "dm"]);
    expect(
      cards.map((card) =>
        card
          .get("header")
          .findAll("dd")
          .map((value) => value.text()),
      ),
    ).toEqual([
      ["561,30 €", "12,1 %"],
      ["730,29 €", "9,5 %"],
      ["72,29 €", "33,5 %"],
      ["43,12 €", "16,5 %"],
    ]);
    expect(cards[0].findAll("h4").map((heading) => heading.text())).toEqual([
      "Rewe Rabatte",
      "Rewe Bonus",
    ]);
    expect(cards[0].text()).toContain("Gesammelt");
    expect(cards[0].text()).toContain("Eingelöst");
    expect(cards[0].text()).toContain("Offen");
    expect(cards[0].text()).toContain("4,1 %");
    expect(cards[1].findAll("h4").map((heading) => heading.text())).toEqual([
      "Lidl Plus",
      "Sticker Rabatte",
      "Preisvorteil",
    ]);
    expect(cards[2].findAll("h4").map((heading) => heading.text())).toEqual([
      "Rossmann 10% Coupon",
      "Rossmann Produktcoupons",
    ]);
    expect(cards[3].findAll("h4")).toHaveLength(0);
  });

  it("shows only the selected retailer when only its metrics are present", () => {
    const wrapper = mount(DashboardKpiGrid, {
      props: { data: { dm_total_savings: 43.12, dm_total_savings_pct: 16.46 } },
    });
    expect(wrapper.findAll("article")).toHaveLength(1);
    expect(wrapper.get("h3").text()).toBe("dm");
  });
});
