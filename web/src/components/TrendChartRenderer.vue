<script setup lang="ts">
import { useTemplateRef, watch } from "vue";
import VChart from "vue-echarts";

import { useTimelineScroll } from "../composables/useTimelineScroll";
import { useTrendECharts } from "../composables/useTrendECharts";
import { useTrendYearLabels } from "../composables/useTrendYearLabels";
import type { PeriodSelection } from "../types/chart";
import type { TimeSeriesRow } from "../types/dashboard";
import { CHART_HEIGHT, TREND_PLOT_TOP } from "../utils/chart";
import "./trendEChartsSetup";

const props = defineProps<{ items: TimeSeriesRow[]; granularity: string }>();
const emit = defineEmits<{ "select-period": [period: PeriodSelection] }>();

const { option, selectBar } = useTrendECharts(props, (period) => emit("select-period", period));
const chart = useTemplateRef<InstanceType<typeof VChart>>("chart");
const { scrollTimeline, resetScroll } = useTimelineScroll(() => props.items.length, chart);
const { yearLayout, updateYearLabels } = useTrendYearLabels(props, chart);

watch(option, resetScroll);
</script>

<template>
  <div v-if="items.length" class="relative" @wheel="scrollTimeline">
    <VChart
      ref="chart"
      :option="option"
      :init-options="{ renderer: 'svg' }"
      :style="{ height: CHART_HEIGHT + 'px' }"
      autoresize
      @click="selectBar"
      @datazoom="resetScroll"
      @updated="updateYearLabels"
    />
    <div
      v-if="yearLayout"
      data-testid="trend-year-overlay"
      class="pointer-events-none absolute top-0 overflow-hidden"
      :style="{
        left: yearLayout.left + 'px',
        width: yearLayout.width + 'px',
        height: TREND_PLOT_TOP + 'px',
      }"
    >
      <span
        v-for="label in yearLayout.labels"
        :key="label.year"
        class="absolute bottom-2.5 font-sans text-[13px] leading-none font-bold text-slate-600"
        :style="{ left: label.left + 'px' }"
        >{{ label.year }}</span
      >
    </div>
  </div>
</template>
