// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

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
    expect(wrapper.text()).toContain("€1.234,00");
    expect(wrapper.text()).toContain("4");
  });

  it("formats currency values", () => {
    const wrapper = mount(DashboardKpiGrid, {
      props: { data: kpiData({ spendings: 1000.5 }) },
    });
    expect(wrapper.text()).toContain("€1.000,50");
  });

  it("formats percentage values", () => {
    const wrapper = mount(DashboardKpiGrid, {
      props: { data: kpiData({ total_savings_pct: 12.5 }) },
    });
    expect(wrapper.text()).toContain("12,5%");
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
    const rightAligned = wrapper.findAll(".justify-items-end");
    expect(rightAligned.length).toBeGreaterThan(0);
  });
});
