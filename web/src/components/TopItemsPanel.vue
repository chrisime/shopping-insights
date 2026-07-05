<script setup lang="ts">
defineProps<{
  items: Array<Record<string, unknown>>;
}>();

function text(value: unknown) {
  return value == null ? "-" : String(value);
}
</script>

<template>
  <ol class="grid gap-3">
    <li
      v-for="item in items"
      :key="text(item.name)"
      class="grid gap-2 rounded-2xl border border-slate-200 bg-slate-50/80 px-4 py-3 text-sm text-slate-700 shadow-sm sm:grid-cols-[minmax(0,1.5fr)_auto_auto_auto_auto] sm:items-center"
    >
      <span class="font-medium text-slate-900">{{ text(item.name) }}</span>
      <span class="sm:text-right">{{ text(item.total_quantity) }}</span>
      <span class="sm:text-right">{{ text(item.total_spent) }}</span>
      <span class="sm:text-right">{{ text(item.purchase_count) }}</span>
      <span class="text-slate-500 sm:text-right">{{ text(item.unit) }}</span>
    </li>
  </ol>
</template>
