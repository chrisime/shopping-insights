<script setup lang="ts">
import { computed, ref } from "vue";
import { Bar } from "vue-chartjs";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import ChartDataLabels from "chartjs-plugin-datalabels";

import { amount, text } from "../utils/format";
import { monthHeaderPlugin } from "../chart-plugins/monthHeaderPlugin";
import type { MonthLabel } from "../chart-plugins/monthHeaderPlugin";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ChartDataLabels,
  monthHeaderPlugin,
  {
    id: "yAxisSync",
    afterLayout(chart: ChartJS) {
      const syncFn = (chart.options as Record<string, unknown>).__syncYAxis as ((chart: ChartJS) => void) | undefined;
      syncFn?.(chart);
    },
  },
);

const props = defineProps<{
  items: Array<Record<string, unknown>>;
  granularity: string;
  monthLabels?: MonthLabel[];
}>();

function stepSizeForGranularity(granularity: string): number {
  if (granularity === "Täglich") return 10;
  if (granularity === "Monatlich") return 50;
  return 500;
}

const chartData = computed(() => ({
  labels: props.items.map((item) => {
    const raw = text(item.period);
    return props.monthLabels && props.monthLabels.length > 0 ? raw.slice(8, 10) : raw;
  }),
  datasets: [
    {
      label: "Ausgaben",
      data: props.items.map((item) => amount(item.total_spent)),
      backgroundColor: "#6366f1",
      borderRadius: 4,
    },
  ],
}));

const yAxisTicks = computed(() => {
  const stepSize = stepSizeForGranularity(props.granularity);
  const maxValue = Math.max(...props.items.map((item) => amount(item.total_spent)), 0);
  const roundedMax = Math.ceil(maxValue / stepSize) * stepSize;
  const ticks: number[] = [];
  for (let i = 0; i <= roundedMax; i += stepSize) {
    ticks.push(i);
  }
  return ticks;
});

const tickPositions = ref<Array<{ value: number; y: number }>>([]);

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  monthLabels: props.monthLabels,
  __syncYAxis: (chart: ChartJS) => {
    const yScale = chart.scales.y;
    if (!yScale) return;
    tickPositions.value = [...yAxisTicks.value].map((value) => ({
      value,
      y: yScale.getPixelForValue(value),
    }));
  },
  layout: {
    padding: { top: 30 },
  },
  plugins: {
    legend: { display: false },
    datalabels: {
      color: "#fff",
      anchor: "center" as const,
      align: "center" as const,
      font: { weight: "bold" as const, size: 12 },
      formatter: (_value: number, ctx: { dataIndex: number }) => {
        const receiptCount = amount(props.items[ctx.dataIndex]?.receipt_count);
        return receiptCount > 0 ? String(receiptCount) : "";
      },
    },
    tooltip: {
      callbacks: {
        label: (ctx: { parsed: { y: number }; dataIndex: number }) => {
          const receiptCount = amount(props.items[ctx.dataIndex]?.receipt_count);
          return [`€${ctx.parsed.y.toFixed(2)}`, `${receiptCount} Belege`];
        },
      },
    },
  },
  scales: {
    x: {
      grid: { display: false },
      ticks: { maxRotation: 45 },
    },
    y: {
      beginAtZero: true,
      grid: { color: "#e2e8f0" },
      ticks: {
        display: false,
        stepSize: yAxisTicks.value.length > 1 ? yAxisTicks.value[1] - yAxisTicks.value[0] : 10,
      },
    },
  },
}));

const isScrollable = computed(() => props.granularity !== "Jährlich");
</script>

<template>
  <div v-if="isScrollable" class="overflow-x-auto">
    <div class="flex">
      <div class="sticky left-0 z-10 flex-shrink-0 bg-white relative" style="width: 64px; height: 500px;">
        <span
          v-for="pos in tickPositions"
          :key="pos.value"
          class="absolute text-xs leading-none text-slate-500 text-right pr-2"
          :style="{ top: `${pos.y - 7}px`, right: '4px' }"
        >€{{ pos.value }}</span>
      </div>
      <div class="flex-shrink-0" :style="{ minWidth: `${items.length * 48}px` }">
        <div style="height: 500px;">
          <Bar :data="chartData" :options="chartOptions" />
        </div>
      </div>
    </div>
  </div>
  <div v-else class="flex">
    <div class="flex-shrink-0 bg-white relative" style="width: 64px; height: 500px;">
      <span
        v-for="pos in tickPositions"
        :key="pos.value"
        class="absolute text-xs leading-none text-slate-500 text-right pr-2"
        :style="{ top: `${pos.y - 7}px`, right: '4px' }"
      >€{{ pos.value }}</span>
    </div>
    <div class="flex-1">
      <div style="height: 500px;">
        <Bar :data="chartData" :options="chartOptions" />
      </div>
    </div>
  </div>
</template>
