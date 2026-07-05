<script setup lang="ts">
defineProps<{
  items: Array<Record<string, unknown>>;
}>();

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
  </div>
</template>
