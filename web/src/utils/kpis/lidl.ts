import { t } from "../copy";
import type { KpiCard } from "../kpiCards";

export const LIDL_KPI_CARDS: KpiCard[] = [
  { title: t("kpi.lidlPlus"), fields: ["lidlplus_discount_amount", "lidlplus_discount_pct"] },
  { title: t("kpi.stickerDiscounts"), fields: ["sticker_discount_amount", "sticker_discount_pct"] },
  { title: t("common.priceBenefit"), fields: ["lidl_discount_amount", "lidl_discount_pct"] },
];
