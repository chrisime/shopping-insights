import { describe, expect, it } from "vite-plus/test";

import { visibleRetailerDiscounts } from "../kpiCards";

describe("visibleRetailerDiscounts", () => {
  it("shows Rossmann coupon fields only when they have positive value", () => {
    const data = {
      rossmann_discount_amount: 8,
      rossmann_discount_pct: 20,
      rossmann_basket_coupon_amount: 2,
      rossmann_product_coupon_amount: 4,
      rossmann_product_coupon_pct: 10,
      rossmann_unclassified_coupon_amount: 0,
    };

    const groups = visibleRetailerDiscounts(data);
    expect(groups.flatMap(({ details }) => details).map(({ title }) => title)).not.toContain(
      "Rossmann andere Coupons",
    );
    expect(
      visibleRetailerDiscounts({ ...data, rossmann_unclassified_coupon_amount: 2 })
        .flatMap(({ details }) => details)
        .map(({ title }) => title),
    ).toContain("Rossmann andere Coupons");
  });
});
