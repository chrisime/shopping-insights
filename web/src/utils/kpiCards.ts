import { t } from "./copy";
import type { MetricsRow } from "../types/dashboard";

export interface KpiCard {
  title: string;
  fields: string[];
}

export const GENERAL_KPI_GROUPS: KpiCard[][] = [
  [
    { title: t("common.spending"), fields: ["spendings", "spendings_without_discount"] },
    { title: t("common.receipts"), fields: ["receipt_count", "avg_receipt_amount"] },
  ],
  [
    { title: t("kpi.depositReturnCard"), fields: ["saved_deposit"] },
    { title: t("kpi.generalPriceBenefit"), fields: ["total_savings", "total_savings_pct"] },
  ],
];

import { LIDL_KPI_CARDS } from "./kpis/lidl";
import { REWE_KPI_CARDS } from "./kpis/rewe";
import { ROSSMANN_KPI_CARDS } from "./kpis/rossmann";

export { LIDL_KPI_CARDS, REWE_KPI_CARDS, ROSSMANN_KPI_CARDS };

export function visibleKpiGroups(data: MetricsRow): KpiCard[][] {
  const hasAllFields = (cards: KpiCard[]) =>
    cards.every((card) => card.fields.every((field) => data[field] !== undefined));
  const groups: KpiCard[][] = [];

  if (data.spendings !== undefined) groups.push(...GENERAL_KPI_GROUPS);
  if (hasAllFields(REWE_KPI_CARDS)) groups.push(REWE_KPI_CARDS);
  if (hasAllFields(LIDL_KPI_CARDS)) groups.push(LIDL_KPI_CARDS);

  const rossmannCards = ROSSMANN_KPI_CARDS.filter(
    ({ fields }) =>
      fields.every((field) => data[field] !== undefined) &&
      (fields[0] !== "rossmann_unclassified_coupon_amount" || data[fields[0]] > 0),
  );
  if (rossmannCards.length) groups.push(rossmannCards);

  return groups;
}

export const KPI_FIELD_LABELS: Record<string, string> = {
  spendings: t("kpi.totalSpending"),
  spendings_without_discount: t("kpi.spendingWithoutDiscount"),
  receipt_count: t("kpi.receiptsTotal"),
  avg_receipt_amount: t("kpi.averageReceipt"),
  saved_deposit: t("kpi.depositReturn"),
  total_savings: t("kpi.saved"),
  total_savings_pct: t("kpi.savingsBenefit"),
  rewe_discount_amount: t("kpi.saved"),
  rewe_discount_pct: t("kpi.savingsRate"),
  rewe_bonus_collected: t("kpi.collected"),
  rewe_bonus_balance: t("kpi.balance"),
  rewe_bonus_redeemed: t("kpi.redeemed"),
  rewe_bonus_open: t("kpi.open"),
  lidlplus_discount_amount: t("kpi.saved"),
  lidlplus_discount_pct: t("kpi.savingsRate"),
  sticker_discount_amount: t("kpi.saved"),
  sticker_discount_pct: t("kpi.savingsRate"),
  lidl_discount_amount: t("kpi.saved"),
  lidl_discount_pct: t("kpi.savingsRate"),
  rossmann_basket_coupon_amount: t("kpi.saved"),
  rossmann_product_coupon_amount: t("kpi.saved"),
  rossmann_product_coupon_pct: t("kpi.savingsRate"),
  rossmann_unclassified_coupon_amount: t("kpi.saved"),
  rossmann_discount_amount: t("kpi.saved"),
  rossmann_discount_pct: t("kpi.savingsRate"),
};
