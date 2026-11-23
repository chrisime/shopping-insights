import { t } from "../copy";
import type { KpiCard } from "../kpiCards";

export const ROSSMANN_KPI_CARDS: KpiCard[] = [
  { title: t("kpi.rossmannBasketCoupon"), fields: ["rossmann_basket_coupon_amount"] },
  {
    title: t("kpi.rossmannProductCoupons"),
    fields: ["rossmann_product_coupon_amount", "rossmann_product_coupon_pct"],
  },
  { title: t("kpi.rossmannOtherCoupons"), fields: ["rossmann_unclassified_coupon_amount"] },
  {
    title: t("common.priceBenefit"),
    fields: ["rossmann_discount_amount", "rossmann_discount_pct"],
  },
];
