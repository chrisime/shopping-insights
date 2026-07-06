<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  items: Array<Record<string, unknown>>;
  spendingView?: string;
  timeGranularity?: string;
}>();

function text(value: unknown) {
  return value == null ? "-" : String(value);
}

function amount(value: unknown) {
  return typeof value === "number" ? value : Number(value ?? 0);
}

function monthName(value: string) {
  const names = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"];
  const index = Number(value) - 1;
  return names[index] ?? value;
}

const maxSpent = computed(() => props.items.reduce((max, item) => Math.max(max, amount(item.total_spent)), 0));
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

function barWidth(value: unknown) {
  const max = maxSpent.value;
  if (max <= 0) {
    return "0%";
  }

  return `${Math.max(0, (amount(value) / max) * 100)}%`;
}

function euro(value: unknown) {
  const numeric = amount(value);
  return Number.isFinite(numeric) ? `€${numeric.toFixed(2)}` : "-";
}

type TimeNode = {
  label: string;
  key: string;
  level: "year" | "month" | "day";
  totalSpent: number;
  receiptCount: number;
  children: TimeNode[];
};

function buildMonthlyTree(items: Array<Record<string, unknown>>) {
  const map = new Map<string, TimeNode>();
  for (const item of items) {
    const period = text(item.period);
    const year = period.slice(0, 4);
    const month = period.slice(0, 7);
    const yearNode = ensureNode(map, year, year, "year");
    const monthNode = ensureChild(yearNode, month, monthName(period.slice(5, 7)), "month");
    addTotals(yearNode, item);
    addTotals(monthNode, item);
  }
  return [...map.values()];
}

function buildDailyTree(items: Array<Record<string, unknown>>) {
  const map = new Map<string, TimeNode>();
  for (const item of items) {
    const period = text(item.period);
    const year = period.slice(0, 4);
    const month = period.slice(0, 7);
    const day = period;
    const yearNode = ensureNode(map, year, year, "year");
    const monthNode = ensureChild(yearNode, month, monthName(month.slice(5, 7)), "month");
    const dayNode = ensureChild(monthNode, day, day.slice(8, 10), "day");
    addTotals(yearNode, item);
    addTotals(monthNode, item);
    addTotals(dayNode, item);
  }
  return [...map.values()];
}

function ensureNode(map: Map<string, TimeNode>, key: string, label: string, level: TimeNode["level"]) {
  const existing = map.get(key);
  if (existing) {
    return existing;
  }

  const created: TimeNode = { key, label, level, totalSpent: 0, receiptCount: 0, children: [] };
  map.set(key, created);
  return created;
}

function ensureChild(parent: TimeNode, key: string, label: string, level: TimeNode["level"]) {
  const existing = parent.children.find((child) => child.key === key);
  if (existing) {
    return existing;
  }

  const created: TimeNode = { key, label, level, totalSpent: 0, receiptCount: 0, children: [] };
  parent.children.push(created);
  return created;
}

function addTotals(node: TimeNode, item: Record<string, unknown>) {
  node.totalSpent += amount(item.total_spent);
  node.receiptCount += amount(item.receipt_count);
}

const treeItems = computed(() => {
  if (props.timeGranularity === "Monatlich") {
    return buildMonthlyTree(props.items);
  }
  if (props.timeGranularity === "Täglich") {
    return buildDailyTree(props.items);
  }
  return [] as TimeNode[];
});

const isGrouped = computed(() => props.timeGranularity === "Monatlich" || props.timeGranularity === "Täglich");
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

    <div v-if="isGrouped" class="grid gap-3">
      <details v-for="year in treeItems" :key="year.key" class="group/year rounded-xl border border-slate-200 bg-white shadow-sm">
        <summary class="flex cursor-pointer list-none items-center justify-between gap-3 px-3 py-2.5">
          <span class="flex items-center gap-2 text-sm font-semibold text-slate-900">
            <svg class="h-3 w-3 shrink-0 text-slate-400 transition-transform group-open/year:rotate-90" viewBox="0 0 12 12" fill="none" aria-hidden="true">
              <path d="M4 2L8 6L4 10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
            {{ year.label }}
          </span>
          <span class="text-xs font-medium uppercase tracking-[0.22em] text-slate-500">{{ euro(year.totalSpent) }}</span>
        </summary>
        <div class="grid gap-2 border-t border-slate-200 p-2.5 pl-5">
          <details v-for="month in year.children" :key="month.key" class="group/month rounded-lg border border-slate-200 bg-slate-50/80 px-3 py-2">
            <summary class="flex cursor-pointer list-none items-center justify-between gap-3">
              <span class="flex items-center gap-2 text-sm font-medium text-slate-900">
                <svg class="h-3 w-3 shrink-0 text-slate-400 transition-transform group-open/month:rotate-90" viewBox="0 0 12 12" fill="none" aria-hidden="true">
                  <path d="M4 2L8 6L4 10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
                {{ month.label }}
              </span>
              <span class="text-xs font-medium uppercase tracking-[0.22em] text-slate-500">{{ euro(month.totalSpent) }}</span>
            </summary>

            <div v-if="month.children.length" class="mt-2 grid gap-2 border-t border-slate-100 pt-2">
              <div
                v-for="day in month.children"
                :key="day.key"
                class="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3 rounded-md px-2 py-1 text-sm text-slate-700"
              >
                <span class="font-medium text-slate-800">{{ day.label }}</span>
                <span class="font-semibold text-slate-900">{{ euro(day.totalSpent) }}</span>
              </div>
            </div>
          </details>
        </div>
      </details>
    </div>

    <div v-else class="grid gap-3">
      <div class="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3 px-4 text-xs font-medium uppercase tracking-[0.22em] text-slate-500">
        <span>Zeitraum</span>
        <span>Betrag</span>
      </div>
      <div
        v-for="item in items"
        :key="text(item.period)"
        class="grid gap-3 rounded-2xl border border-slate-200 bg-slate-50/80 px-4 py-3 text-sm text-slate-700 shadow-sm"
      >
        <div class="flex items-center justify-between gap-3">
          <span class="font-medium text-slate-900">{{ text(item.period) }}</span>
          <span class="text-sm font-semibold text-slate-900">{{ euro(item.total_spent) }}</span>
        </div>
        <div class="h-2 overflow-hidden rounded-full bg-slate-200">
          <div class="h-full rounded-full bg-indigo-500" :style="{ width: barWidth(item.total_spent) }" />
        </div>
        <div class="flex items-center justify-between text-xs text-slate-500">
          <span>{{ text(item.receipt_count) }} Belege</span>
          <span>{{ maxSpent > 0 ? `${Math.round((amount(item.total_spent) / maxSpent) * 100)}%` : "0%" }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
