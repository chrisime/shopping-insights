<script setup lang="ts">
import { computed } from "vue";

import { euro, percentage } from "../utils/format";
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
    { title: "Ausgaben", fields: ["spendings", "spendings_without_discount"] },
    { title: "Kassenbons", fields: ["receipt_count", "avg_receipt_amount"] },
  ],
  [
    { title: "Pfandrückgabe", fields: ["saved_deposit"] },
    { title: "Gesamter Preisvorteil", fields: ["total_savings", "total_savings_pct"] },
  ],
];

const REWE_CARDS: KpiCard[] = [
  { title: "Rewe Rabatte", fields: ["rewe_discount_amount", "rewe_discount_pct"] },
  { title: "Rewe Bonus gesammelt", fields: ["rewe_bonus_collected", "rewe_bonus_balance"] },
  { title: "Rewe Bonus eingelöst", fields: ["rewe_bonus_redeemed", "rewe_bonus_open"] },
];

const LIDL_CARDS: KpiCard[] = [
  { title: "Lidl Plus", fields: ["lidlplus_discount_amount", "lidlplus_discount_pct"] },
  { title: "Sticker Rabatte", fields: ["sticker_discount_amount", "sticker_discount_pct"] },
  { title: "Preisvorteil", fields: ["lidl_discount_amount", "lidl_discount_pct"] },
];

const ROSSMANN_CARDS: KpiCard[] = [
  { title: "Rossmann 10% Coupon", fields: ["rossmann_basket_coupon_amount"] },
  {
    title: "Rossmann Produktcoupons",
    fields: ["rossmann_product_coupon_amount", "rossmann_product_coupon_pct"],
  },
  { title: "Rossmann andere Coupons", fields: ["rossmann_unclassified_coupon_amount"] },
  { title: "Preisvorteil", fields: ["rossmann_discount_amount", "rossmann_discount_pct"] },
];

const FIELD_LABELS: Record<string, string> = {
  spendings: "Ausgaben gesamt",
  spendings_without_discount: "Ausgaben ohne Rabatte",
  receipt_count: "Kassenbons gesamt",
  avg_receipt_amount: "Durchschnittl. Bon-Betrag",
  saved_deposit: "Pfandrückgabe",
  total_savings: "Gespart",
  total_savings_pct: "Sparvorteil",
  rewe_discount_amount: "Gespart",
  rewe_discount_pct: "Sparquote",
  rewe_bonus_collected: "Gesammelt",
  rewe_bonus_balance: "Guthaben",
  rewe_bonus_redeemed: "Eingelöst",
  rewe_bonus_open: "Offen",
  lidlplus_discount_amount: "Gespart",
  lidlplus_discount_pct: "Sparquote",
  sticker_discount_amount: "Gespart",
  sticker_discount_pct: "Sparquote",
  lidl_discount_amount: "Gespart",
  lidl_discount_pct: "Sparquote",
  rossmann_basket_coupon_amount: "Gespart",
  rossmann_product_coupon_amount: "Gespart",
  rossmann_product_coupon_pct: "Sparquote",
  rossmann_unclassified_coupon_amount: "Gespart",
  rossmann_discount_amount: "Gespart",
  rossmann_discount_pct: "Sparquote",
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
