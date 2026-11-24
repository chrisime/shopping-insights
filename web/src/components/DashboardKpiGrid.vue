<script setup lang="ts">
import { computed } from "vue";

import { euro, percentage } from "../utils/format";
import { KPI_FIELD_LABELS, visibleKpiGroups } from "../utils/kpiCards";
import type { MetricsRow } from "../types/dashboard";

const props = defineProps<{
  data: MetricsRow;
}>();

const GRID_CLASSES: Record<number, string> = {
  2: "lg:grid-cols-2",
  3: "lg:grid-cols-3",
  4: "lg:grid-cols-2 xl:grid-cols-4",
};

function formatValue(key: string, value: number): string {
  if (key.endsWith("_pct")) {
    return percentage(value);
  }
  if (key === "receipt_count") {
    return String(value);
  }
  return euro(value);
}

const visibleGroups = computed(() => visibleKpiGroups(props.data));
</script>

<template>
  <div class="grid gap-4">
    <div
      v-for="group in visibleGroups"
      :key="group[0].title"
      class="grid gap-3"
      :class="GRID_CLASSES[group.length] ?? ''"
    >
      <article
        v-for="card in group"
        :key="card.title"
        :data-testid="`kpi-card-${card.fields[0]}`"
        class="grid gap-3 rounded-2xl border border-slate-200 bg-slate-50/80 p-4 shadow-sm ring-1 ring-slate-100/70"
      >
        <div class="border-b border-slate-200/70 pb-2">
          <h3 class="text-sm font-semibold tracking-tight text-slate-900">{{ card.title }}</h3>
        </div>

        <div class="grid gap-3 sm:grid-cols-2">
          <div
            v-for="(field, index) in card.fields"
            :key="field"
            data-testid="kpi-field"
            class="grid gap-1"
            :class="index % 2 === 1 ? 'justify-items-end text-right' : ''"
          >
            <span class="text-xs font-medium uppercase tracking-[0.22em] text-slate-500">{{
              KPI_FIELD_LABELS[field] ?? field
            }}</span>
            <strong class="text-2xl font-semibold tracking-tight text-slate-900">{{
              formatValue(field, data[field])
            }}</strong>
          </div>
        </div>
      </article>
    </div>
  </div>
</template>
