<script setup lang="ts">
import { computed } from "vue";

import TrendBarChart from "./TrendBarChart.vue";
import { euro } from "../utils/format";
import { buildMonthLabels } from "../utils/period";
import type { PeriodSelection } from "../types/chart";
import type { TimeSeriesRow } from "../types/dashboard";

const props = defineProps<{
  items: TimeSeriesRow[];
  timeGranularity?: string;
}>();

const emit = defineEmits<{
  (e: "select-period", payload: PeriodSelection): void;
}>();

const GROUP_LABELS: Record<string, string> = {
  Täglich: "Tage",
  Monatlich: "Monate",
  Jährlich: "Jahre",
};

const granularity = computed(() => props.timeGranularity || "Monatlich");
const groupLabel = computed(() => GROUP_LABELS[granularity.value] ?? "Jahre");
const monthLabels = computed(() =>
  granularity.value === "Täglich" ? buildMonthLabels(props.items) : [],
);

const summaryCards = computed(() => {
  if (props.items.length === 0) return [];

  const values = props.items.map((item) => item.total_spent);
  const total = values.reduce((sum, value) => sum + value, 0);

  return [
    { label: "Ø Ausgaben pro Zeitraum", value: total / values.length },
    { label: "Maximum", value: Math.max(...values) },
    { label: "Minimum", value: Math.min(...values) },
  ];
});
</script>

<template>
  <div class="grid gap-4">
    <div v-if="summaryCards.length" class="grid gap-3 sm:grid-cols-3">
      <article
        v-for="card in summaryCards"
        :key="card.label"
        class="rounded-2xl border border-slate-200 bg-slate-50/80 px-4 py-3 shadow-sm"
      >
        <p class="text-xs font-medium uppercase tracking-[0.22em] text-slate-500">
          {{ card.label }}
        </p>
        <strong class="mt-1 block text-xl font-semibold text-slate-900">{{
          euro(card.value)
        }}</strong>
      </article>
    </div>

    <div class="grid gap-2">
      <h3 v-if="items.length > 0" class="text-sm font-semibold text-slate-800">{{ groupLabel }}</h3>
      <TrendBarChart
        v-if="items.length > 0"
        :items="items"
        :granularity="granularity"
        :month-labels="monthLabels"
        @select-period="emit('select-period', $event)"
      />
    </div>
  </div>
</template>
