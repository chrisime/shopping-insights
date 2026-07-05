<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  items: Array<Record<string, unknown>>;
  spendingView?: string;
}>();

function text(value: unknown) {
  return value == null ? "-" : String(value);
}

function amount(value: unknown) {
  return typeof value === "number" ? value : Number(value ?? 0);
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
  return `${Math.max(4, (amount(value) / max) * 100)}%`;
}

function euro(value: unknown) {
  const numeric = amount(value);
  return Number.isFinite(numeric) ? `€${numeric.toFixed(2)}` : "-";
}
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

    <div class="grid gap-3">
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
