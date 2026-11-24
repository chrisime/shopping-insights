import { t } from "../copy";
import type { DiscountDetail } from "../kpiCards";

export const ROSSMANN_DISCOUNT_DETAILS: DiscountDetail[] = [
  { title: t("kpi.rossmannBasketCoupon"), fields: ["rossmann_basket_coupon_amount"] },
  {
    title: t("kpi.rossmannProductCoupons"),
    fields: ["rossmann_product_coupon_amount", "rossmann_product_coupon_pct"],
  },
  {
    title: t("kpi.rossmannOtherCoupons"),
    fields: ["rossmann_unclassified_coupon_amount"],
    isVisible: (data) => data.rossmann_unclassified_coupon_amount > 0,
  },
];
