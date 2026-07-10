<script setup lang="ts">
import { computed, ref, onMounted, watch } from "vue";
import * as d3 from "d3";

import { amount, text } from "../utils/format";
import type { MonthLabel } from "../chart-plugins/monthHeaderPlugin";

const monthNames = [
  "Januar", "Februar", "März", "April", "Mai", "Juni",
  "Juli", "August", "September", "Oktober", "November", "Dezember",
];

let tooltipHideTimer: ReturnType<typeof setTimeout> | null = null;

function computePeriod(period: string, granularity: string): { startDate: string; endDate: string; label: string } {
  if (granularity === "Täglich") {
    const [y, m, d] = period.split("-").map(Number);
    return {
      startDate: period,
      endDate: period,
      label: `${d}. ${monthNames[m - 1]} ${y}`,
    };
  }
  if (granularity === "Monatlich") {
    const [y, m] = period.split("-").map(Number);
    const lastDay = new Date(y, m, 0).getDate();
    return {
      startDate: `${period}-01`,
      endDate: `${period}-${String(lastDay).padStart(2, "0")}`,
      label: `${monthNames[m - 1]} ${y}`,
    };
  }
  return {
    startDate: `${period}-01-01`,
    endDate: `${period}-12-31`,
    label: period,
  };
}

const emit = defineEmits<{
  (e: "select-period", payload: { startDate: string; endDate: string; label: string }): void;
}>();

const props = defineProps<{
  items: Array<Record<string, unknown>>;
  granularity: string;
  monthLabels?: MonthLabel[];
}>();

const CHART_HEIGHT = 500;
const MARGIN = { top: 30, right: 16, bottom: 32, left: 0 };
const Y_AXIS_WIDTH = 64;

const yAxisRef = ref<HTMLDivElement>();
const chartRef = ref<HTMLDivElement>();

const isScrollable = computed(() => props.granularity !== "Jährlich");

function stepSizeForGranularity(granularity: string): number {
  if (granularity === "Täglich") return 10;
  if (granularity === "Monatlich") return 50;
  return 500;
}

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

const totalWidth = computed(() => props.items.length * 56 + MARGIN.right);

function drawChart() {
  if (!yAxisRef.value || !chartRef.value) return;
  const items = props.items;
  if (items.length === 0) return;
  const monthLabels = props.monthLabels;
  const ticks = yAxisTicks.value;

  d3.select(yAxisRef.value).selectAll("svg").remove();
  d3.select(chartRef.value).selectAll("svg").remove();

  const yScale = d3.scaleLinear()
    .domain([0, ticks.length > 1 ? ticks[ticks.length - 1] : ticks[0] || 10])
    .range([CHART_HEIGHT - MARGIN.bottom, MARGIN.top]);

  const xScale = d3.scaleBand()
    .domain(d3.range(items.length).map(String))
    .range([0, totalWidth.value])
    .padding(0.2);

  const yAxisSvg = d3.select(yAxisRef.value)
    .append("svg")
    .attr("width", Y_AXIS_WIDTH)
    .attr("height", CHART_HEIGHT)
    .style("display", "block");

  yAxisSvg.append("g")
    .attr("transform", `translate(${Y_AXIS_WIDTH - 8}, 0)`)
    .call(d3.axisLeft(yScale)
      .tickValues(ticks)
      .tickFormat((d: number) => `€${d.toFixed(0)}`)
      .tickSize(0),
    )
    .call((g) => {
      g.selectAll(".tick text")
        .attr("text-anchor", "end")
        .attr("font-family", "sans-serif")
        .attr("font-size", "11px")
        .attr("fill", "#64748b");
      g.select(".domain").remove();
    });

  const mainSvg = d3.select(chartRef.value)
    .append("svg")
    .attr("width", totalWidth.value)
    .attr("height", CHART_HEIGHT)
    .style("display", "block");

  mainSvg.append("g")
    .call(d3.axisLeft(yScale)
      .tickValues(ticks)
      .tickSize(-totalWidth.value)
      .tickFormat(""),
    )
    .call((g) => {
      g.selectAll(".tick line")
        .attr("stroke", "#e2e8f0");
      g.select(".domain").remove();
    });

  const tooltipW = 180;
  const tooltipLineH = 20;
  const tooltipPad = 12;

  const tooltipG = mainSvg.append("g")
    .attr("class", "tooltip-group")
    .style("display", "none")
    .style("pointer-events", "none");

  tooltipG.append("rect")
    .attr("class", "tooltip-bg")
    .attr("x", -tooltipW / 2)
    .attr("y", 0)
    .attr("width", tooltipW)
    .attr("height", 0)
    .attr("rx", 8)
    .attr("ry", 8)
    .attr("fill", "white")
    .attr("stroke", "#e2e8f0")
    .attr("stroke-width", 1)
    .attr("filter", "drop-shadow(0 2px 4px rgba(0,0,0,0.12))");

  tooltipG.append("line")
    .attr("class", "tooltip-sep")
    .attr("x1", -tooltipW / 2 + 8)
    .attr("x2", tooltipW / 2 - 8)
    .attr("y1", 0)
    .attr("y2", 0)
    .attr("stroke", "#e2e8f0")
    .attr("stroke-width", 1);

  const textStyle = {
    period: { yOffset: 18, fontSize: "14px", fontWeight: "bold", fill: "#1e293b" },
    total: { yOffset: 44, fontSize: "13px", fontWeight: "normal", fill: "#334155" },
    count: { yOffset: 62, fontSize: "13px", fontWeight: "normal", fill: "#334155" },
    avg: { yOffset: 80, fontSize: "13px", fontWeight: "normal", fill: "#334155" },
    retailers: { yOffset: 100, fontSize: "12px", fontWeight: "normal", fill: "#64748b" },
  };

  Object.entries(textStyle).forEach(([cls, s]) => {
    tooltipG.append("text")
      .attr("class", `tooltip-${cls}`)
      .attr("text-anchor", "middle")
      .attr("x", 0)
      .attr("y", s.yOffset)
      .attr("font-family", "sans-serif")
      .attr("font-size", s.fontSize)
      .attr("font-weight", s.fontWeight)
      .attr("fill", s.fill);
  });

  if (monthLabels && monthLabels.length > 1) {
    for (let i = 1; i < monthLabels.length; i++) {
      const prevEnd = monthLabels[i - 1].end;
      const currStart = monthLabels[i].start;
      const sepX = (xScale(String(prevEnd))! + xScale.bandwidth()! + xScale(String(currStart))!) / 2;
      mainSvg.append("line")
        .attr("x1", sepX)
        .attr("y1", MARGIN.top - 4)
        .attr("x2", sepX)
        .attr("y2", CHART_HEIGHT - MARGIN.bottom)
        .attr("stroke", "#cbd5e1")
        .attr("stroke-width", 1);
    }
  }

  if (monthLabels) {
    monthLabels.forEach((ml) => {
      const midIndex = (ml.start + ml.end) / 2;
      const midX = xScale(String(Math.floor(midIndex)))! + xScale.bandwidth()! / 2;
      mainSvg.append("text")
        .attr("x", midX)
        .attr("y", MARGIN.top - 6)
        .attr("text-anchor", "middle")
        .attr("font-family", "sans-serif")
        .attr("font-size", "13px")
        .attr("font-weight", "bold")
        .attr("fill", "#475569")
        .text(ml.label);
    });
  }

  mainSvg.selectAll("rect.bar")
    .data(items)
    .enter()
    .append("rect")
    .attr("class", "bar")
    .attr("x", (_d: unknown, i: number) => xScale(String(i))!)
    .attr("y", (d: Record<string, unknown>) => yScale(amount(d.total_spent)))
    .attr("width", xScale.bandwidth()!)
    .attr("height", (d: Record<string, unknown>) => yScale(0) - yScale(amount(d.total_spent)))
    .attr("fill", "#6366f1")
    .attr("rx", 4)
    .on("click", (_event: unknown, d: Record<string, unknown>) => {
      emit("select-period", computePeriod(String(d.period ?? ""), props.granularity));
    })
    .on("mouseenter", function (this: SVGRectElement, _event: unknown, d: Record<string, unknown>) {
      if (tooltipHideTimer) clearTimeout(tooltipHideTimer);

      const barX = xScale(String(items.indexOf(d)))!;
      const barTop = yScale(amount(d.total_spent));
      const total = amount(d.total_spent);
      const count = amount(d.receipt_count);
      const avg = count > 0 ? total / count : 0;
      const retailers = (d.retailers as string[] | undefined) ?? [];

      tooltipG.attr("transform", `translate(${barX + xScale.bandwidth()! / 2}, ${barTop})`);

      const periodLabel = computePeriod(String(d.period ?? ""), props.granularity).label;
      tooltipG.select(".tooltip-period").text(periodLabel);
      tooltipG.select(".tooltip-total").text(`€${total.toFixed(2)}  Gesamt`);
      tooltipG.select(".tooltip-count").text(`${count} Belege`);
      tooltipG.select(".tooltip-avg").text(`€${avg.toFixed(2)}  Ø/Beleg`);

      const hasRetailers = retailers.length > 0;
      tooltipG.select(".tooltip-retailers").text(hasRetailers ? retailers.join(", ") : "");

      const bodyH = hasRetailers ? 104 : 84;
      const totalH = bodyH + 6;
      tooltipG.select(".tooltip-bg").attr("height", totalH);

      tooltipG.select(".tooltip-sep").attr("y1", 22).attr("y2", 22);

      tooltipG.select(".tooltip-period").attr("y", 16);
      tooltipG.select(".tooltip-total").attr("y", 42);
      tooltipG.select(".tooltip-count").attr("y", 60);
      tooltipG.select(".tooltip-avg").attr("y", 78);
      if (hasRetailers) {
        tooltipG.select(".tooltip-retailers").attr("y", 98);
      }

      tooltipG.style("display", "block");
    })
    .on("mouseleave", function () {
      tooltipHideTimer = setTimeout(() => {
        tooltipG.style("display", "none");
      }, 200);
    })

  mainSvg.selectAll("text.datalabel")
    .data(items)
    .enter()
    .append("text")
    .attr("class", "datalabel")
    .attr("x", (_d: unknown, i: number) => xScale(String(i))! + xScale.bandwidth()! / 2)
    .attr("y", (d: Record<string, unknown>) => {
      const barH = yScale(0) - yScale(amount(d.total_spent));
      return yScale(amount(d.total_spent)) + barH / 2 + 4;
    })
    .attr("text-anchor", "middle")
    .attr("font-family", "sans-serif")
    .attr("font-size", "12px")
    .attr("font-weight", "bold")
    .attr("fill", "white")
    .attr("pointer-events", "none")
    .text((d: Record<string, unknown>) => {
      const count = amount(d.receipt_count);
      return count > 0 ? String(count) : "";
    });

  mainSvg.selectAll("text.euroLabel")
    .data(items)
    .enter()
    .append("text")
    .attr("class", "euroLabel")
    .attr("x", (_d: unknown, i: number) => xScale(String(i))! + xScale.bandwidth()! / 2)
    .attr("y", (d: Record<string, unknown>) => yScale(amount(d.total_spent)) - 4)
    .attr("text-anchor", "middle")
    .attr("font-family", "sans-serif")
    .attr("font-size", "10px")
    .attr("font-weight", "bold")
    .attr("fill", "#475569")
    .attr("pointer-events", "none")
    .text((d: Record<string, unknown>) => `€${amount(d.total_spent).toFixed(2)}`);

  mainSvg.append("g")
    .attr("transform", `translate(0, ${CHART_HEIGHT - MARGIN.bottom})`)
    .call(d3.axisBottom(xScale)
      .tickFormat((_d: unknown, i: number) => {
        const raw = text(items[i].period);
        return monthLabels && monthLabels.length > 0 ? raw.slice(8, 10) : raw;
      }),
    )
    .call((g) => {
      g.selectAll(".tick text")
        .attr("font-family", "sans-serif")
        .attr("font-size", "10px")
        .attr("fill", "#94a3b8");
      g.selectAll(".tick line").attr("display", "none");
      g.select(".domain").attr("stroke", "#cbd5e1");
    });
}

onMounted(() => drawChart());

watch(
  () => [props.items, props.monthLabels, props.granularity],
  () => drawChart(),
  { deep: true },
);
</script>

<template>
  <div style="overflow: hidden;">
    <div style="height: 500px; position: relative;">
      <div ref="yAxisRef" class="bg-white" style="position: absolute; left: 0; top: 0; width: 64px; height: 500px; z-index: 10;"></div>
      <div :class="isScrollable ? 'overflow-x-auto' : ''" style="height: 500px; margin-left: 64px; overflow-y: hidden;">
        <div ref="chartRef" style="height: 500px; display: inline-block;"></div>
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
