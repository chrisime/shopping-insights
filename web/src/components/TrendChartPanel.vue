<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  items: Array<Record<string, unknown>>;
}>();

function text(value: unknown) {
  return value == null ? "-" : String(value);
}

function amount(value: unknown) {
  return typeof value === "number" ? value : Number(value ?? 0);
}

const maxSpent = computed(() => Math.max(...props.items.map((item) => amount(item.total_spent)), 0));

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
  <ul class="grid gap-3">
    <li
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
    </li>
  </ul>
</template>
