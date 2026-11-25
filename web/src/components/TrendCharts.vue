<script setup lang="ts">
import { defineAsyncComponent } from "vue";
import type { PeriodSelection } from "../types/chart";
import type { TimeSeriesRow } from "../types/dashboard";

defineProps<{ items: TimeSeriesRow[]; granularity: string }>();
const emit = defineEmits<{ "select-period": [period: PeriodSelection] }>();
const TrendChartRenderer = defineAsyncComponent(() => import("./TrendChartRenderer.vue"));
</script>

<template>
  <TrendChartRenderer
    v-if="items.length"
    :items="items"
    :granularity="granularity"
    @select-period="emit('select-period', $event)"
  />
</template>
