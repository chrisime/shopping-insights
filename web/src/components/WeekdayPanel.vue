<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  items: Array<Record<string, unknown>>;
}>();

function text(value: unknown) {
  return value == null ? "-" : String(value);
}

function currency(value: unknown) {
  const numeric = typeof value === "number" ? value : Number(value ?? 0);
  return Number.isFinite(numeric) ? `€${numeric.toFixed(2)}` : "-";
}

function amount(value: unknown) {
  return typeof value === "number" ? value : Number(value ?? 0);
}

const maxTrips = computed(() => props.items.reduce((max, item) => Math.max(max, amount(item.trip_count)), 0));
const maxAverage = computed(() => props.items.reduce((max, item) => Math.max(max, amount(item.avg_spent)), 0));

function barWidth(value: unknown, max: number) {
  if (max <= 0) {
    return "0%";
  }

  return `${Math.max(0, (amount(value) / max) * 100)}%`;
}
</script>

<template>
  <div class="grid gap-4 xl:grid-cols-2">
    <section class="grid gap-3">
      <h3 class="px-1 text-sm font-semibold text-slate-900">Anzahl Einkäufe</h3>
      <div class="grid gap-2">
        <div
          v-for="item in items"
          :key="`trips-${text(item.weekday_name ?? item.weekday)}`"
          class="grid gap-2 rounded-2xl border border-slate-200 bg-slate-50/80 px-4 py-3 text-sm text-slate-700 shadow-sm"
        >
          <div class="flex items-center justify-between gap-3">
            <span class="font-medium text-slate-900">{{ text(item.weekday_name ?? item.weekday) }}</span>
            <span class="text-slate-600">{{ text(item.trip_count) }} Einkäufe</span>
          </div>
          <div class="h-2 overflow-hidden rounded-full bg-slate-200">
            <div class="h-full rounded-full bg-indigo-500" :style="{ width: barWidth(item.trip_count, maxTrips) }" />
          </div>
        </div>
      </div>
    </section>

    <section class="grid gap-3">
      <h3 class="px-1 text-sm font-semibold text-slate-900">Ø Ausgaben pro Einkauf</h3>
      <div class="grid gap-2">
        <div
          v-for="item in items"
          :key="`avg-${text(item.weekday_name ?? item.weekday)}`"
          class="grid gap-2 rounded-2xl border border-slate-200 bg-slate-50/80 px-4 py-3 text-sm text-slate-700 shadow-sm"
        >
          <div class="flex items-center justify-between gap-3">
            <span class="font-medium text-slate-900">{{ text(item.weekday_name ?? item.weekday) }}</span>
            <span class="text-slate-600">{{ currency(item.avg_spent) }}</span>
          </div>
          <div class="h-2 overflow-hidden rounded-full bg-slate-200">
            <div class="h-full rounded-full bg-indigo-500" :style="{ width: barWidth(item.avg_spent, maxAverage) }" />
          </div>
        </div>
      </div>
    </section>
  </div>
</template>
