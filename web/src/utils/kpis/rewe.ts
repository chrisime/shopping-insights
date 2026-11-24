import { t } from "../copy";
import type { DiscountDetail } from "../kpiCards";

export const REWE_DISCOUNT_DETAILS: DiscountDetail[] = [
  { title: t("kpi.reweDiscounts"), fields: ["rewe_discount_amount", "rewe_discount_pct"] },
  {
    title: t("kpi.reweBonus"),
    fields: ["rewe_bonus_redeemed", "rewe_bonus_redeemed_pct"],
    supportingFields: ["rewe_bonus_collected", "rewe_bonus_open"],
  },
];
