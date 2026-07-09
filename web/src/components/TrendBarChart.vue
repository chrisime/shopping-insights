<script setup lang="ts">
import { computed, ref, watch, nextTick } from "vue";
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
);

const props = defineProps<{
  items: Array<Record<string, unknown>>;
  granularity: string;
  monthLabels?: MonthLabel[];
}>();

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
  const maxValue = Math.max(...props.items.map((item) => amount(item.total_spent)), 0);
  const roundedMax = Math.ceil(maxValue / 5) * 5;
  const ticks: number[] = [];
  for (let i = 0; i <= roundedMax; i += 5) {
    ticks.push(i);
  }
  return ticks;
});

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  monthLabels: props.monthLabels,
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
        stepSize: 5,
      },
    },
  },
}));

const isScrollable = computed(() => props.granularity !== "Jährlich");

const tickPositions = ref<Array<{ value: number; y: number }>>([]);
const barRef = ref();

function syncTickPositions() {
  const chart = barRef.value?.chart as { scales?: { y?: { getPixelForValue: (v: number) => number } } } | undefined;
  if (!chart?.scales?.y) return;
  tickPositions.value = [...yAxisTicks.value].map((value) => ({
    value,
    y: chart.scales.y!.getPixelForValue(value),
  }));
}

watch(barRef, (instance) => {
  if (instance?.chart) {
    nextTick(syncTickPositions);
  }
});
</script>

<template>
  <div v-if="isScrollable" class="overflow-x-auto">
    <div class="flex">
      <div class="sticky left-0 z-10 flex-shrink-0 bg-white relative" style="width: 44px; height: 320px;">
        <span
          v-for="pos in tickPositions"
          :key="pos.value"
          class="absolute text-xs leading-none text-slate-500 text-right pr-2"
          :style="{ top: `${pos.y - 7}px`, right: '4px' }"
        >€{{ pos.value }}</span>
      </div>
      <div class="flex-shrink-0" :style="{ minWidth: `${items.length * 48}px` }">
        <div class="h-80">
          <Bar ref="barRef" :data="chartData" :options="chartOptions" />
        </div>
      </div>
    </div>
  </div>
  <div v-else class="flex">
    <div class="flex-shrink-0 bg-white relative" style="width: 44px; height: 320px;">
      <span
        v-for="pos in tickPositions"
        :key="pos.value"
        class="absolute text-xs leading-none text-slate-500 text-right pr-2"
        :style="{ top: `${pos.y - 7}px`, right: '4px' }"
      >€{{ pos.value }}</span>
    </div>
    <div class="flex-1">
      <div class="h-80">
        <Bar ref="barRef" :data="chartData" :options="chartOptions" />
      </div>
    </div>
  </div>
</template>
