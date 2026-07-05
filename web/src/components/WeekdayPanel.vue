<script setup lang="ts">
defineProps<{
  items: Array<Record<string, unknown>>;
}>();

function text(value: unknown) {
  return value == null ? "-" : String(value);
}
</script>

<template>
  <ul class="grid gap-3">
    <li
      v-for="item in items"
      :key="text(item.weekday_name ?? item.weekday)"
      class="grid gap-2 rounded-2xl border border-slate-200 bg-slate-50/80 px-4 py-3 text-sm text-slate-700 shadow-sm sm:grid-cols-[1.2fr_1fr_0.8fr_0.8fr] sm:items-center"
    >
      <span class="font-medium text-slate-900">{{ text(item.weekday_name ?? item.weekday) }}</span>
      <span class="sm:text-right">{{ text(item.trip_count) }} Einkäufe</span>
      <span class="text-slate-500 sm:text-right">Ø {{ text(item.avg_spent) }}</span>
      <span class="sm:text-right">{{ text(item.total_spent) }}</span>
    </li>
  </ul>
</template>
