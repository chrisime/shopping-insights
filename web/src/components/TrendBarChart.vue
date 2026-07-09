<script setup lang="ts">
import { computed } from "vue";
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

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ChartDataLabels,
);

const props = defineProps<{
  items: Array<Record<string, unknown>>;
  granularity: string;
}>();

const chartData = computed(() => ({
  labels: props.items.map((item) => text(item.period)),
  datasets: [
    {
      label: "Ausgaben",
      data: props.items.map((item) => amount(item.total_spent)),
      backgroundColor: "#6366f1",
      borderRadius: 4,
    },
  ],
}));

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
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
        callback: (value: number) => `€${value.toFixed(0)}`,
      },
    },
  },
}));

const isScrollable = computed(() => props.granularity !== "Jährlich");
</script>

<template>
  <div v-if="isScrollable" class="overflow-x-auto">
    <div class="h-64" :style="{ minWidth: `${items.length * 48}px` }">
      <Bar :data="chartData" :options="chartOptions" />
    </div>
  </div>
  <div v-else class="h-64">
    <Bar :data="chartData" :options="chartOptions" />
  </div>
</template>
