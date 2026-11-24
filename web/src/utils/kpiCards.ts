import { t } from "./copy";
import type { MetricsRow } from "../types/dashboard";

import { LIDL_DISCOUNT_DETAILS } from "./kpis/lidl";
import { REWE_DISCOUNT_DETAILS } from "./kpis/rewe";
import { ROSSMANN_DISCOUNT_DETAILS } from "./kpis/rossmann";

export interface KpiCard {
  title: string;
  fields: string[];
  supportingFields?: string[];
}

export interface DiscountDetail extends KpiCard {
  isVisible?: (data: MetricsRow) => boolean;
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

interface VisibleRetailerDiscount {
  name: string;
  amount: number;
  rate: number;
  details: DiscountDetail[];
}

interface RetailerDiscountConfig {
  readonly name: string;
  readonly amountKey: string;
  readonly rateKey: string;
  readonly details: readonly DiscountDetail[];
}

const RETAILER_DISCOUNTS: readonly RetailerDiscountConfig[] = [
  {
    name: t("retailer.rewe"),
    amountKey: "rewe_total_savings",
    rateKey: "rewe_total_savings_pct",
    details: REWE_DISCOUNT_DETAILS,
  },
  {
    name: t("retailer.lidl"),
    amountKey: "lidl_total_savings",
    rateKey: "lidl_total_savings_pct",
    details: LIDL_DISCOUNT_DETAILS,
  },
  {
    name: t("retailer.rossmann"),
    amountKey: "rossmann_discount_amount",
    rateKey: "rossmann_discount_pct",
    details: ROSSMANN_DISCOUNT_DETAILS,
  },
  {
    name: t("retailer.dm"),
    amountKey: "dm_total_savings",
    rateKey: "dm_total_savings_pct",
    details: [],
  },
];

const filterVisibleDiscountDetails = (
  details: readonly DiscountDetail[],
  data: MetricsRow,
): DiscountDetail[] =>
  details.filter(
    ({ fields, isVisible }) =>
      fields.every((field) => data[field] !== undefined) && (isVisible?.(data) ?? true),
  );

export const visibleRetailerDiscounts = (data: MetricsRow): VisibleRetailerDiscount[] => {
  const discounts: VisibleRetailerDiscount[] = [];

  for (const retailer of RETAILER_DISCOUNTS) {
    const amount = data[retailer.amountKey];
    const rate = data[retailer.rateKey];
    if (amount === undefined || rate === undefined) continue;

    const visibleDetails = filterVisibleDiscountDetails(retailer.details, data);

    discounts.push({ name: retailer.name, amount, rate, details: visibleDetails });
  }

  return discounts;
};

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
  rewe_bonus_redeemed: t("kpi.redeemed"),
  rewe_bonus_redeemed_pct: t("kpi.savingsRate"),
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
};
