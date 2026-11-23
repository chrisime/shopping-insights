import { t } from "../copy";
import type { KpiCard } from "../kpiCards";

export const REWE_KPI_CARDS: KpiCard[] = [
  { title: t("kpi.reweDiscounts"), fields: ["rewe_discount_amount", "rewe_discount_pct"] },
  { title: t("kpi.reweBonusCollected"), fields: ["rewe_bonus_collected", "rewe_bonus_balance"] },
  { title: t("kpi.reweBonusRedeemed"), fields: ["rewe_bonus_redeemed", "rewe_bonus_open"] },
];
