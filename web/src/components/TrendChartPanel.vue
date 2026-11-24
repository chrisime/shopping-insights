<script setup lang="ts">
import { computed } from "vue";

import TrendBarChart from "./TrendBarChart.vue";
import { euro } from "../utils/format";
import { buildMonthLabels } from "../utils/period";
import { t } from "../utils/copy";
import type { PeriodSelection } from "../types/chart";
import type { TimeSeriesRow } from "../types/dashboard";

const props = defineProps<{
  items: TimeSeriesRow[];
  timeGranularity?: string;
}>();

const emit = defineEmits<{
  (e: "select-period", payload: PeriodSelection): void;
}>();

const granularity = computed(() => props.timeGranularity || "monthly");
const groupLabel = computed(() => {
  if (granularity.value === "daily") return t("dashboard.granularityDays");
  if (granularity.value === "monthly") return t("dashboard.granularityMonths");
  return t("dashboard.granularityYears");
});
const monthLabels = computed(() =>
  granularity.value === "daily" ? buildMonthLabels(props.items) : [],
);

const summaryCards = computed(() => {
  if (props.items.length === 0) return [];

  const values = props.items.map((item) => item.total_spent);
  const total = values.reduce((sum, value) => sum + value, 0);

  return [
    { label: t("dashboard.averagePerPeriod"), value: total / values.length },
    { label: t("dashboard.maximum"), value: Math.max(...values) },
    { label: t("dashboard.minimum"), value: Math.min(...values) },
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
        data-testid="trend-bar-chart"
        v-if="items.length > 0"
        :items="items"
        :granularity="granularity"
        :month-labels="monthLabels"
        @select-period="emit('select-period', $event)"
      />
    </div>
  </div>
</template>
