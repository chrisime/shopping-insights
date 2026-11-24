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

  it("renders REWE bonus group when rewe fields present", () => {
    const wrapper = mount(DashboardKpiGrid, {
      props: {
        data: kpiData({
          rewe_discount_amount: 10.0,
          rewe_discount_pct: 10.0,
          rewe_bonus_collected: 1.0,
          rewe_bonus_balance: 4.0,
          rewe_bonus_redeemed: 3.0,
          rewe_bonus_open: 0.0,
        }),
      },
    });
    expect(wrapper.text()).toContain("Rewe Rabatte");
    expect(wrapper.text()).toContain("Rewe Bonus gesammelt");
    expect(wrapper.text()).toContain("Rewe Bonus eingelöst");
  });

  it("skips REWE group when no rewe fields", () => {
    const wrapper = mount(DashboardKpiGrid, {
      props: { data: kpiData() },
    });
    expect(wrapper.text()).not.toContain("Rewe Rabatte");
  });

  it("renders Lidl bonus group when lidl fields present", () => {
    const wrapper = mount(DashboardKpiGrid, {
      props: {
        data: kpiData({
          lidlplus_discount_amount: 2.0,
          lidlplus_discount_pct: 4.0,
          sticker_discount_amount: 3.0,
          sticker_discount_pct: 5.0,
          lidl_discount_amount: 10.0,
          lidl_discount_pct: 10.0,
        }),
      },
    });
    expect(wrapper.text()).toContain("Lidl Plus");
    expect(wrapper.text()).toContain("Sticker Rabatte");
    expect(wrapper.text()).toContain("Preisvorteil");
  });

  it("skips Lidl group when no lidl fields", () => {
    const wrapper = mount(DashboardKpiGrid, {
      props: { data: kpiData() },
    });
    expect(wrapper.text()).not.toContain("Lidl Plus");
  });

  it("renders the Rossmann Preisvorteil card", () => {
    const wrapper = mount(DashboardKpiGrid, {
      props: { data: kpiData({ rossmann_discount_amount: 4.91, rossmann_discount_pct: 48.9 }) },
    });
    expect(wrapper.text()).toContain("Preisvorteil");
    expect(wrapper.text()).toContain("48,9 %");
  });

  it("renders only general cards when the data has no discount fields", () => {
    const wrapper = mount(DashboardKpiGrid, { props: { data: kpiData() } });
    expect(wrapper.text()).toContain("Ausgaben");
    expect(wrapper.text()).toContain("Kassenbons");
    expect(wrapper.text()).not.toContain("Rewe Rabatte");
    expect(wrapper.text()).not.toContain("Rossmann");
  });

  it("renders only discount cards when the data has no general fields", () => {
    const wrapper = mount(DashboardKpiGrid, {
      props: {
        data: {
          rossmann_discount_amount: 8,
          rossmann_discount_pct: 20,
          rossmann_basket_coupon_amount: 2,
          rossmann_product_coupon_amount: 4,
          rossmann_product_coupon_pct: 10,
          rossmann_unclassified_coupon_amount: 0,
        },
      },
    });
    expect(wrapper.text()).not.toContain("Ausgaben");
    expect(wrapper.text()).not.toContain("Kassenbons");
    expect(wrapper.text()).toContain("Rossmann 10% Coupon");
    expect(wrapper.text()).toContain("Preisvorteil");
  });

  it("splits Rossmann coupons and shows other coupons only for a positive amount", async () => {
    const data = kpiData({
      rossmann_discount_amount: 8,
      rossmann_discount_pct: 20,
      rossmann_basket_coupon_amount: 2,
      rossmann_product_coupon_amount: 4,
      rossmann_product_coupon_pct: 10,
      rossmann_unclassified_coupon_amount: 0,
    });
    const wrapper = mount(DashboardKpiGrid, { props: { data } });
    expect(wrapper.text()).toContain("Rossmann 10% Coupon");
    const productCard = wrapper.get("[data-testid=kpi-card-rossmann_product_coupon_amount]");
    expect(productCard.text()).toContain("10,0 %");
    expect(wrapper.text()).not.toContain("Rossmann andere Coupons");

    await wrapper.setProps({ data: { ...data, rossmann_unclassified_coupon_amount: 2 } });
    expect(wrapper.text()).toContain("Rossmann andere Coupons");
    await wrapper.setProps({ data: { ...data, rossmann_unclassified_coupon_amount: -2 } });
    expect(wrapper.text()).not.toContain("Rossmann andere Coupons");
  });

  it("aligns Sparquote/Guthaben/Offen to the right", () => {
    const wrapper = mount(DashboardKpiGrid, {
      props: {
        data: kpiData({
          rewe_discount_amount: 10.0,
          rewe_discount_pct: 10.0,
          rewe_bonus_collected: 1.0,
          rewe_bonus_balance: 4.0,
          rewe_bonus_redeemed: 3.0,
          rewe_bonus_open: 0.0,
        }),
      },
    });
    const rightAligned = wrapper.findAll("[data-testid=kpi-field]");
    expect(
      rightAligned.filter((field) => field.classes("justify-items-end")).length,
    ).toBeGreaterThan(0);
  });
});
