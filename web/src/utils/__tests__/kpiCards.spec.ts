import { describe, expect, it } from "vite-plus/test";

import { visibleKpiGroups } from "../kpiCards";

describe("visibleKpiGroups", () => {
  it("shows Rossmann coupon fields only when they have positive value", () => {
    const data = {
      rossmann_discount_amount: 8,
      rossmann_discount_pct: 20,
      rossmann_basket_coupon_amount: 2,
      rossmann_product_coupon_amount: 4,
      rossmann_product_coupon_pct: 10,
      rossmann_unclassified_coupon_amount: 0,
    };

    const groups = visibleKpiGroups(data);
    expect(groups.flat().map(({ title }) => title)).not.toContain("Rossmann andere Coupons");
    expect(
      visibleKpiGroups({ ...data, rossmann_unclassified_coupon_amount: 2 })
        .flat()
        .map(({ title }) => title),
    ).toContain("Rossmann andere Coupons");
  });
});
