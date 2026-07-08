<script setup lang="ts">
const props = defineProps<{
  items: Array<Record<string, unknown>>;
  page: number;
  pageSize: number;
  totalCount: number;
}>();

const emit = defineEmits<{
  (e: "update:page", value: number): void;
}>();

import { computed } from "vue";

const totalPages = computed(() => Math.max(1, Math.ceil(props.totalCount / props.pageSize)));

function prev() {
  if (props.page > 1) emit("update:page", props.page - 1);
}

function next() {
  if (props.page < totalPages) emit("update:page", props.page + 1);
}

function text(value: unknown) {
  return value == null ? "-" : String(value);
}

function currency(value: unknown) {
  const numeric = typeof value === "number" ? value : Number(value ?? 0);
  return Number.isFinite(numeric) ? `€${numeric.toFixed(2)}` : "-";
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
  <div class="overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-sm">
    <table class="min-w-full divide-y divide-slate-200">
      <thead class="bg-slate-50">
        <tr>
          <th scope="col" class="px-4 py-3 text-left text-xs font-medium uppercase tracking-[0.22em] text-slate-500">Artikel</th>
          <th scope="col" class="px-4 py-3 text-right text-xs font-medium uppercase tracking-[0.22em] text-slate-500">Gesamtmenge</th>
          <th scope="col" class="px-4 py-3 text-right text-xs font-medium uppercase tracking-[0.22em] text-slate-500">Ausgaben</th>
          <th scope="col" class="px-4 py-3 text-right text-xs font-medium uppercase tracking-[0.22em] text-slate-500">Einkäufe</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-slate-100 bg-white">
        <tr v-for="item in items" :key="text(item.name)">
          <td class="px-4 py-3 text-sm font-medium text-slate-900">{{ text(item.name) }}</td>
          <td class="px-4 py-3 text-right text-sm text-slate-700">{{ quantity(item.total_quantity, item.unit) }}</td>
          <td class="px-4 py-3 text-right text-sm text-slate-700">{{ currency(item.total_spent) }}</td>
          <td class="px-4 py-3 text-right text-sm text-slate-700">{{ text(item.purchase_count) }}</td>
        </tr>
      </tbody>
    </table>

    <div v-if="totalCount > 0" class="flex items-center justify-between border-t border-slate-200 px-4 py-3">
      <p class="text-sm text-slate-500">
        {{ (page - 1) * pageSize + 1 }}–{{ Math.min(page * pageSize, totalCount) }} von {{ totalCount }}
      </p>
      <div class="flex gap-2">
        <button
          type="button"
          :disabled="page <= 1"
          class="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
          @click="prev"
        >
          Zurück
        </button>
        <button
          type="button"
          :disabled="page >= totalPages"
          class="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
          @click="next"
        >
          Weiter
        </button>
      </div>
    </div>
  </div>
</template>
