<script setup lang="ts">
import { computed } from "vue";

import { euro } from "../utils/format";
import { t } from "../utils/copy";
import type { WeekdayRow } from "../types/dashboard";

const props = defineProps<{
  items: WeekdayRow[];
}>();

const METRICS = [
  {
    key: "trips",
    title: t("weekday.purchasesTitle"),
    value: (item: WeekdayRow) => item.trip_count,
    label: (item: WeekdayRow) => t("weekday.purchases", { count: item.trip_count }),
  },
  {
    key: "avg",
    title: t("weekday.averagePerPurchase"),
    value: (item: WeekdayRow) => item.avg_spent,
    label: (item: WeekdayRow) => euro(item.avg_spent),
  },
];

const columns = computed(() =>
  METRICS.map((metric) => ({
    ...metric,
    max: props.items.reduce((max, item) => Math.max(max, metric.value(item)), 0),
  })),
);

function barWidth(value: number, max: number): string {
  return max <= 0 ? "0%" : `${Math.max(0, (value / max) * 100)}%`;
}
</script>

<template>
  <div class="grid gap-4 xl:grid-cols-2">
    <section v-for="column in columns" :key="column.key" class="grid gap-3">
      <h3 class="px-1 text-sm font-semibold text-slate-900">{{ column.title }}</h3>
      <div class="grid gap-2">
        <div
          v-for="item in items"
          :key="`${column.key}-${item.weekday_name}`"
          class="grid gap-2 rounded-2xl border border-slate-200 bg-slate-50/80 px-4 py-3 text-sm text-slate-700 shadow-sm"
        >
          <div class="flex items-center justify-between gap-3">
            <span class="font-medium text-slate-900">{{ item.weekday_name }}</span>
            <span class="text-slate-600">{{ column.label(item) }}</span>
          </div>
          <div class="h-2 overflow-hidden rounded-full bg-slate-200">
            <div
              class="h-full rounded-full bg-indigo-500"
              :style="{ width: barWidth(column.value(item), column.max) }"
            />
          </div>
        </div>
      </div>
    </section>
  </div>
</template>
