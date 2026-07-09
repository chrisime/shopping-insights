<script setup lang="ts">
import { computed } from "vue";
import TrendBarChart from "./TrendBarChart.vue";

const props = defineProps<{
  items: Array<Record<string, unknown>>;
  spendingView?: string;
  timeGranularity?: string;
}>();

function amount(value: unknown): number {
  return typeof value === "number" ? value : Number(value ?? 0);
}

function text(value: unknown): string {
  return value == null ? "-" : String(value);
}

function euro(value: unknown): string {
  const numeric = amount(value);
  return Number.isFinite(numeric) ? `€${numeric.toFixed(2)}` : "-";
}

function monthName(value: string): string {
  const names = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"];
  const index = Number(value) - 1;
  return names[index] ?? value;
}

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
  const map = new Map<string, GroupNode>();
  for (const item of props.items) {
    const period = text(item.period);
    const year = period.slice(0, 4);
    if (!map.has(year)) {
      map.set(year, { label: year, key: year, items: [] });
    }
    map.get(year)!.items.push(item);
  }
  return [...map.values()];
}

function buildMonthGroups(): GroupNode[] {
  const map = new Map<string, GroupNode>();
  for (const item of props.items) {
    const period = text(item.period);
    const year = period.slice(0, 4);
    const month = period.slice(5, 7);
    if (!map.has(year)) {
      map.set(year, { label: year, key: year, items: [] });
    }
    map.get(year)!.items.push({ ...item, period: `${monthName(month)} ${year}` });
  }
  return [...map.values()];
}

function buildDayGroups(): GroupNode[] {
  const yearMap = new Map<string, { key: string; monthNodes: Map<string, GroupNode> }>();
  for (const item of props.items) {
    const period = text(item.period);
    const year = period.slice(0, 4);
    const month = period.slice(5, 7);
    const day = period.slice(8, 10);
    if (!yearMap.has(year)) {
      yearMap.set(year, { key: year, monthNodes: new Map() });
    }
    const monthKey = `${year}-${month}`;
    if (!yearMap.get(year)!.monthNodes.has(monthKey)) {
      yearMap.get(year)!.monthNodes.set(monthKey, { label: `${monthName(month)} ${year}`, key: monthKey, items: [] });
    }
    yearMap.get(year)!.monthNodes.get(monthKey)!.items.push({ ...item, period: day });
  }
  const result: GroupNode[] = [];
  for (const [yearKey, yearEntry] of yearMap) {
    result.push({ label: yearKey, key: yearKey, items: [] });
    for (const monthNode of yearEntry.monthNodes.values()) {
      result.push(monthNode);
    }
  }
  return result;
}

const groups = computed(() => {
  const granularity = props.timeGranularity || "Monatlich";
  if (granularity === "Monatlich") return buildMonthGroups();
  if (granularity === "Täglich") return buildDayGroups();
  return buildYearGroups();
});

const chartGranularity = computed(() => props.timeGranularity || "Monatlich");
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
        />
      </div>
    </div>
  </div>
</template>
