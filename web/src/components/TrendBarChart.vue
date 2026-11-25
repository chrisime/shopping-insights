<script setup lang="ts">
import { useTrendBarChart, type TrendBarChartProps } from "../composables/useTrendBarChart";
import type { PeriodSelection } from "../types/chart";
import { CHART_HEIGHT, Y_AXIS_WIDTH } from "../utils/chart";

const props = defineProps<TrendBarChartProps>();
const emit = defineEmits<{
  (eventName: "select-period", payload: PeriodSelection): void;
}>();

const { yAxisRef, chartRef, scrollRef, isScrollable, positionYearLabels } = useTrendBarChart(
  props,
  (period) => emit("select-period", period),
);
</script>

<template>
  <div class="overflow-hidden">
    <div class="relative" :style="{ height: `${CHART_HEIGHT}px` }">
      <div
        ref="yAxisRef"
        class="absolute left-0 top-0 z-10 bg-white"
        :style="{ width: `${Y_AXIS_WIDTH}px`, height: `${CHART_HEIGHT}px` }"
      ></div>
      <div
        ref="scrollRef"
        data-testid="trend-chart-scroll"
        class="overflow-y-hidden"
        :class="isScrollable ? 'overflow-x-auto' : ''"
        :style="{ height: `${CHART_HEIGHT}px`, marginLeft: `${Y_AXIS_WIDTH}px` }"
        @scroll.passive="positionYearLabels"
      >
        <div ref="chartRef" class="inline-block" :style="{ height: `${CHART_HEIGHT}px` }"></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.bar {
  cursor: pointer;
  transition: fill 0.15s ease;
}
.bar:hover {
  fill: #4f46e5;
}
</style>
