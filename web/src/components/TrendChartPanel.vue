<script setup lang="ts">
import { computed } from "vue";
import TrendBarChart from "./TrendBarChart.vue";
import { amount, text, euro } from "../utils/format";
import type { MonthLabel } from "../chart-plugins/monthHeaderPlugin";

const emit = defineEmits<{
  (e: "select-period", payload: { startDate: string; endDate: string; label: string }): void;
}>();

const props = defineProps<{
  items: Array<Record<string, unknown>>;
  spendingView?: string;
  timeGranularity?: string;
}>();

const summary = computed(() => {
  if (props.spendingView !== "Absolut" || props.items.length === 0) {
    return null;
  }
  const values = props.items.map((item) => amount(item.total_spent));
  const total = values.reduce((sum, value) => sum + value, 0);
  return {
    average: total / values.length,
    maximum: Math.max(...values),
    minimum: Math.min(...values),
  };
});

type GroupNode = {
  label: string;
  key: string;
  items: Array<Record<string, unknown>>;
};

function buildYearGroups(): GroupNode[] {
  if (props.items.length === 0) return [];
  return [{ label: "Jahre", key: "years", items: [...props.items] }];
}

function buildMonthGroups(): GroupNode[] {
  return props.items.length > 0
    ? [{ label: "Monate", key: "months", items: [...props.items] }]
    : [];
}

function buildDayGroups(): GroupNode[] {
  return props.items.length > 0
    ? [{ label: "Tage", key: "days", items: [...props.items] }]
    : [];
}

const groups = computed(() => {
  const granularity = props.timeGranularity || "Monatlich";
  if (granularity === "Monatlich") return buildMonthGroups();
  if (granularity === "Täglich") return buildDayGroups();
  return buildYearGroups();
});

const chartGranularity = computed(() => props.timeGranularity || "Monatlich");

const fullMonthNames = [
  "Januar", "Februar", "März", "April", "Mai", "Juni",
  "Juli", "August", "September", "Oktober", "November", "Dezember",
];

const monthLabels = computed<MonthLabel[]>(() => {
  const granularity = props.timeGranularity;
  if (granularity !== "Täglich") return [];
  const items = props.items;
  if (items.length === 0) return [];
  const result: MonthLabel[] = [];
  let start = 0;
  let currentMonth = String(text(items[0].period)).slice(5, 7);
  for (let i = 1; i <= items.length; i++) {
    const month = i < items.length ? String(text(items[i].period)).slice(5, 7) : null;
    if (month !== currentMonth) {
      const year = String(text(items[i - 1].period)).slice(0, 4);
      const monthIndex = Number(currentMonth) - 1;
      result.push({
        label: `${fullMonthNames[monthIndex]} ${year}`,
        start,
        end: i - 1,
      });
      if (month !== null) {
        start = i;
        currentMonth = month;
      }
    }
  }
  return result;
});
</script>

<template>
  <div class="grid gap-4">
    <div v-if="summary" class="grid gap-3 sm:grid-cols-3">
      <article class="rounded-2xl border border-slate-200 bg-slate-50/80 px-4 py-3 shadow-sm">
        <p class="text-xs font-medium uppercase tracking-[0.22em] text-slate-500">Ø Ausgaben pro Zeitraum</p>
        <strong class="mt-1 block text-xl font-semibold text-slate-900">{{ euro(summary.average) }}</strong>
      </article>
      <article class="rounded-2xl border border-slate-200 bg-slate-50/80 px-4 py-3 shadow-sm">
        <p class="text-xs font-medium uppercase tracking-[0.22em] text-slate-500">Maximum</p>
        <strong class="mt-1 block text-xl font-semibold text-slate-900">{{ euro(summary.maximum) }}</strong>
      </article>
      <article class="rounded-2xl border border-slate-200 bg-slate-50/80 px-4 py-3 shadow-sm">
        <p class="text-xs font-medium uppercase tracking-[0.22em] text-slate-500">Minimum</p>
        <strong class="mt-1 block text-xl font-semibold text-slate-900">{{ euro(summary.minimum) }}</strong>
      </article>
    </div>

    <div class="grid gap-6">
      <div v-for="group in groups" :key="group.key" class="grid gap-2">
        <h3 v-if="group.items.length > 0" class="text-sm font-semibold text-slate-800">{{ group.label }}</h3>
        <TrendBarChart
          v-if="group.items.length > 0"
          :items="group.items"
          :granularity="chartGranularity"
          :monthLabels="monthLabels"
          @select-period="emit('select-period', $event)"
        />
      </div>
    </div>
  </div>
</template>
