<script setup lang="ts">
const props = defineProps<{
  data: Record<string, number>;
}>();

interface KpiCardDef {
  title: string;
  fields: string[];
}

interface KpiCardGroup {
  cards: KpiCardDef[];
}

const cardGroups: KpiCardGroup[] = [
  {
    cards: [
      { title: "Ausgaben", fields: ["spendings", "spendings_without_discount"] },
      { title: "Kassenbons", fields: ["receipt_count", "avg_receipt_amount"] },
    ],
  },
  {
    cards: [
      { title: "Pfandrückgabe", fields: ["saved_deposit"] },
      { title: "Gesamter Preisvorteil", fields: ["total_savings", "total_savings_pct"] },
    ],
  },
];

const reweGroup: KpiCardGroup = {
  cards: [
    { title: "Rewe Rabatte", fields: ["rewe_discount_amount", "rewe_discount_pct"] },
    { title: "Rewe Bonus gesammelt", fields: ["rewe_bonus_collected", "rewe_bonus_balance"] },
    { title: "Rewe Bonus eingelöst", fields: ["rewe_bonus_redeemed", "rewe_bonus_open"] },
  ],
};

const lidlGroup: KpiCardGroup = {
  cards: [
    { title: "Lidl Plus", fields: ["lidlplus_discount_amount", "lidlplus_discount_pct"] },
    { title: "Sticker Rabatte", fields: ["sticker_discount_amount", "sticker_discount_pct"] },
    { title: "Preisvorteil", fields: ["lidl_discount_amount", "lidl_discount_pct"] },
  ],
};

function hasAllFields(group: KpiCardGroup): boolean {
  return group.cards.every((card) => card.fields.every((f) => props.data[f] !== undefined));
}

function formatValue(key: string, value: number): string {
  if (key.endsWith("_pct")) {
    return `${value.toLocaleString("de-DE", { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%`;
  }
  if (key === "receipt_count") {
    return String(value);
  }
  return `€${value.toLocaleString("de-DE", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function fieldLabel(key: string): string {
  const labels: Record<string, string> = {
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
  };
  return labels[key] ?? key;
}

function visibleGroups(): KpiCardGroup[] {
  const groups = [...cardGroups];
  if (hasAllFields(reweGroup)) groups.push(reweGroup);
  if (hasAllFields(lidlGroup)) groups.push(lidlGroup);
  return groups;
}
</script>

<template>
  <div class="grid gap-4">
    <div
      v-for="(group, gi) in visibleGroups()"
      :key="gi"
      class="grid gap-3"
      :class="group.cards.length === 3 ? 'lg:grid-cols-3' : group.cards.length === 2 ? 'lg:grid-cols-2' : ''"
    >
      <article
        v-for="(card, ci) in group.cards"
        :key="ci"
        class="grid gap-3 rounded-2xl border border-slate-200 bg-slate-50/80 p-4 shadow-sm ring-1 ring-slate-100/70"
      >
        <div class="border-b border-slate-200/70 pb-2">
          <h3 class="text-sm font-semibold tracking-tight text-slate-900">{{ card.title }}</h3>
        </div>

        <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <div
            v-for="(field, fi) in card.fields"
            :key="field"
            class="grid gap-1"
            :class="fi === 1 ? 'justify-items-end text-right' : ''"
          >
            <span class="text-xs font-medium uppercase tracking-[0.22em] text-slate-500">{{ fieldLabel(field) }}</span>
            <strong class="text-2xl font-semibold tracking-tight text-slate-900">{{ formatValue(field, data[field]) }}</strong>
          </div>
        </div>
      </article>
    </div>
  </div>
</template>
