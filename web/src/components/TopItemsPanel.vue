<script setup lang="ts">
defineProps<{
  items: Array<Record<string, unknown>>;
}>();

function text(value: unknown) {
  return value == null ? "-" : String(value);
}

function quantity(value: unknown, unit: unknown) {
  const numeric = typeof value === "number" ? value : Number(value ?? 0);
  if (!Number.isFinite(numeric) || unit == null) {
    return "-";
  }

  return `${unit === "kg" ? numeric.toFixed(3) : Math.trunc(numeric)} ${text(unit)}`;
}
</script>

<template>
  <div class="grid gap-3">
    <div class="grid gap-2 px-4 text-xs font-medium uppercase tracking-[0.22em] text-slate-500 sm:grid-cols-[minmax(0,1.5fr)_auto_auto_auto]">
      <span>Artikel</span>
      <span class="sm:text-right">Gesamtmenge</span>
      <span class="sm:text-right">Ausgaben</span>
      <span class="sm:text-right">Einkäufe</span>
    </div>
    <ol class="grid gap-3">
      <li
        v-for="item in items"
        :key="text(item.name)"
        class="grid gap-2 rounded-2xl border border-slate-200 bg-slate-50/80 px-4 py-3 text-sm text-slate-700 shadow-sm sm:grid-cols-[minmax(0,1.5fr)_auto_auto_auto] sm:items-center"
      >
        <span class="font-medium text-slate-900">{{ text(item.name) }}</span>
        <span class="sm:text-right">{{ quantity(item.total_quantity, item.unit) }}</span>
        <span class="sm:text-right">{{ text(item.total_spent) }}</span>
        <span class="sm:text-right">{{ text(item.purchase_count) }}</span>
      </li>
    </ol>
  </div>
</template>
