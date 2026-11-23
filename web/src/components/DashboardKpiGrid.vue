<script setup lang="ts">
import { computed } from "vue";

import { euro, percentage } from "../utils/format";
import { t } from "../utils/copy";
import type { MetricsRow } from "../types/dashboard";

const props = defineProps<{
  data: MetricsRow;
}>();

interface KpiCard {
  title: string;
  fields: string[];
}

const GENERAL_GROUPS: KpiCard[][] = [
  [
    { title: t("common.spending"), fields: ["spendings", "spendings_without_discount"] },
    { title: t("common.receipts"), fields: ["receipt_count", "avg_receipt_amount"] },
  ],
  [
    { title: t("kpi.depositReturnCard"), fields: ["saved_deposit"] },
    { title: t("kpi.generalPriceBenefit"), fields: ["total_savings", "total_savings_pct"] },
  ],
];

const REWE_CARDS: KpiCard[] = [
  { title: t("kpi.reweDiscounts"), fields: ["rewe_discount_amount", "rewe_discount_pct"] },
  { title: t("kpi.reweBonusCollected"), fields: ["rewe_bonus_collected", "rewe_bonus_balance"] },
  { title: t("kpi.reweBonusRedeemed"), fields: ["rewe_bonus_redeemed", "rewe_bonus_open"] },
];

const LIDL_CARDS: KpiCard[] = [
  { title: t("kpi.lidlPlus"), fields: ["lidlplus_discount_amount", "lidlplus_discount_pct"] },
  { title: t("kpi.stickerDiscounts"), fields: ["sticker_discount_amount", "sticker_discount_pct"] },
  { title: t("common.priceBenefit"), fields: ["lidl_discount_amount", "lidl_discount_pct"] },
];

const ROSSMANN_CARDS: KpiCard[] = [
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

const FIELD_LABELS: Record<string, string> = {
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

const GRID_CLASSES: Record<number, string> = {
  2: "lg:grid-cols-2",
  3: "lg:grid-cols-3",
  4: "lg:grid-cols-2 xl:grid-cols-4",
};

function hasAllFields(cards: KpiCard[]): boolean {
  return cards.every((card) => card.fields.every((field) => props.data[field] !== undefined));
}

function formatValue(key: string, value: number): string {
  if (key.endsWith("_pct")) {
    return percentage(value);
  }
  if (key === "receipt_count") {
    return String(value);
  }
  return euro(value);
}

const visibleGroups = computed<KpiCard[][]>(() => {
  const groups: KpiCard[][] = [];

  if (props.data.spendings !== undefined) groups.push(...GENERAL_GROUPS);
  if (hasAllFields(REWE_CARDS)) groups.push(REWE_CARDS);
  if (hasAllFields(LIDL_CARDS)) groups.push(LIDL_CARDS);

  const rossmannCards = ROSSMANN_CARDS.filter(
    ({ fields }) =>
      fields.every((field) => props.data[field] !== undefined) &&
      (fields[0] !== "rossmann_unclassified_coupon_amount" || props.data[fields[0]] > 0),
  );
  if (rossmannCards.length) groups.push(rossmannCards);

  return groups;
});
</script>

<template>
  <div class="grid gap-4">
    <div
      v-for="group in visibleGroups"
      :key="group[0].title"
      class="grid gap-3"
      :class="GRID_CLASSES[group.length] ?? ''"
    >
      <article
        v-for="card in group"
        :key="card.title"
        class="grid gap-3 rounded-2xl border border-slate-200 bg-slate-50/80 p-4 shadow-sm ring-1 ring-slate-100/70"
      >
        <div class="border-b border-slate-200/70 pb-2">
          <h3 class="text-sm font-semibold tracking-tight text-slate-900">{{ card.title }}</h3>
        </div>

        <div class="grid gap-3 sm:grid-cols-2">
          <div
            v-for="(field, index) in card.fields"
            :key="field"
            class="grid gap-1"
            :class="index % 2 === 1 ? 'justify-items-end text-right' : ''"
          >
            <span class="text-xs font-medium uppercase tracking-[0.22em] text-slate-500">{{
              FIELD_LABELS[field] ?? field
            }}</span>
            <strong class="text-2xl font-semibold tracking-tight text-slate-900">{{
              formatValue(field, data[field])
            }}</strong>
          </div>
        </div>
      </article>
    </div>
  </div>
</template>
