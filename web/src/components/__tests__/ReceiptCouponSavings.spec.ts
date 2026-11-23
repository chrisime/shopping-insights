// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vite-plus/test";

import ReceiptCouponSavings from "../ReceiptCouponSavings.vue";

describe("ReceiptCouponSavings", () => {
  it("formats coupon savings in the receipt currency and defaults to euros", () => {
    const coupons = [{ name: "Coupon", savings: 12.5 }];

    const usd = mount(ReceiptCouponSavings, {
      props: { coupons, currency: "USD" },
    });
    expect(usd.text()).toContain("12,50 $");

    const fallback = mount(ReceiptCouponSavings, {
      props: { coupons, currency: "bad" },
    });
    expect(fallback.text()).toContain("12,50 €");
  });
});
