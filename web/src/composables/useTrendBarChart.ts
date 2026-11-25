import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import * as d3 from "d3";

import { compactEuro, euro, retailerLabel } from "../utils/format";
import { CHART_HEIGHT, Y_AXIS_WIDTH, chartWidth, xTickLabel, yAxisTicks } from "../utils/chart";
import { computePeriod } from "../utils/period";
import { t } from "../utils/copy";
import type { MonthLabel, PeriodSelection } from "../types/chart";
import type { TimeSeriesRow } from "../types/dashboard";

export interface TrendBarChartProps {
  items: TimeSeriesRow[];
  granularity: string;
  monthLabels?: MonthLabel[];
}

type Svg = d3.Selection<SVGSVGElement, unknown, null, undefined>;
type Group = d3.Selection<SVGGElement, unknown, null, undefined>;
type Bars = d3.Selection<SVGRectElement, TimeSeriesRow, SVGSVGElement, unknown>;
type BandScale = d3.ScaleBand<string>;
type ValueScale = d3.ScaleLinear<number, number>;

const MARGIN = { top: 30, bottom: 32 };
const PLOT_BOTTOM = CHART_HEIGHT - MARGIN.bottom;
const YEAR_HEADER_HEIGHT = 18;
const YEAR_LABEL_INSET = 4;
const YEAR_LABEL_SPACE = 36;
const TOOLTIP_WIDTH = 180;
const TOOLTIP_HIDE_DELAY = 200;

const TOOLTIP_ROWS = [
  { className: "tooltip-period", y: 16, fontSize: "14px", fontWeight: "bold", fill: "#1e293b" },
  { className: "tooltip-total", y: 42, fontSize: "13px", fontWeight: "normal", fill: "#334155" },
  { className: "tooltip-count", y: 60, fontSize: "13px", fontWeight: "normal", fill: "#334155" },
  { className: "tooltip-avg", y: 78, fontSize: "13px", fontWeight: "normal", fill: "#334155" },
  {
    className: "tooltip-retailers",
    y: 98,
    fontSize: "12px",
    fontWeight: "normal",
    fill: "#64748b",
  },
];

const BAR_LABELS = [
  {
    className: "datalabel",
    fontSize: "12px",
    fill: "white",
    offset: (barHeight: number) => barHeight / 2 + 4,
    text: (row: TimeSeriesRow) => (row.receipt_count > 0 ? String(row.receipt_count) : ""),
  },
  {
    className: "euroLabel",
    fontSize: "10px",
    fill: "#475569",
    offset: () => -4,
    text: (row: TimeSeriesRow) => euro(row.total_spent),
  },
];

const appendSvg = (container: HTMLDivElement, testId: string, width: number): Svg =>
  d3
    .select(container)
    .append("svg")
    .attr("data-testid", testId)
    .attr("width", width)
    .attr("height", CHART_HEIGHT)
    .style("display", "block");

export const useTrendBarChart = (
  props: TrendBarChartProps,
  onSelectPeriod: (period: PeriodSelection) => void,
) => {
  const yAxisRef = ref<HTMLDivElement>();
  const chartRef = ref<HTMLDivElement>();
  const scrollRef = ref<HTMLDivElement>();

  const isScrollable = computed(() => props.granularity !== "yearly");
  const ticks = computed(() => yAxisTicks(props.items, props.granularity));
  const plotTop = computed(() =>
    props.monthLabels?.length ? MARGIN.top + YEAR_HEADER_HEIGHT : MARGIN.top,
  );
  const width = computed(() => chartWidth(props.items.length));

  const renderYAxis = (svg: Svg, scale: ValueScale, tickValues: number[]) => {
    const axis = d3
      .axisLeft(scale)
      .tickValues(tickValues)
      .tickFormat((value) => compactEuro(Number(value)))
      .tickSize(0);

    const group = svg.append("g").attr("transform", `translate(${Y_AXIS_WIDTH - 8}, 0)`);
    axis(group);
    group
      .selectAll(".tick text")
      .attr("text-anchor", "end")
      .attr("font-family", "sans-serif")
      .attr("font-size", "11px")
      .attr("fill", "#64748b");
    group.select(".domain").remove();
  };

  const renderGrid = (svg: Svg, scale: ValueScale, tickValues: number[]) => {
    const axis = d3
      .axisLeft(scale)
      .tickValues(tickValues)
      .tickSize(-width.value)
      .tickFormat(() => "");

    const group = svg.append("g");
    axis(group);
    group.selectAll(".tick line").attr("stroke", "#e2e8f0");
    group.select(".domain").remove();
  };

  interface YearMarker {
    start: number;
    end: number;
  }

  const positionYearLabels = () => {
    const scrollLeft = scrollRef.value?.scrollLeft ?? 0;
    d3.select(chartRef.value ?? null)
      .selectAll<SVGTextElement, YearMarker>(".year-label")
      .attr("x", ({ start, end }) =>
        Math.min(Math.max(start, scrollLeft) + YEAR_LABEL_INSET, end - YEAR_LABEL_SPACE),
      );
  };

  const renderMonthMarkers = (svg: Svg, xScale: BandScale) => {
    const labels = props.monthLabels ?? [];

    for (let i = 1; i < labels.length; i++) {
      const previousEnd = xScale(String(labels[i - 1].end)) ?? 0;
      const currentStart = xScale(String(labels[i].start)) ?? 0;
      const separatorX = (previousEnd + xScale.bandwidth() + currentStart) / 2;

      svg
        .append("line")
        .attr("x1", separatorX)
        .attr("y1", plotTop.value - 4)
        .attr("x2", separatorX)
        .attr("y2", PLOT_BOTTOM)
        .attr("stroke", "#cbd5e1")
        .attr("stroke-width", 1);
    }

    const barCenter = (index: number) => (xScale(String(index)) ?? 0) + xScale.bandwidth() / 2;
    const addLabel = (className: string, x: number, y: number, label: string) =>
      svg
        .append("text")
        .attr("class", className)
        .attr("x", x)
        .attr("y", y)
        .attr("text-anchor", "middle")
        .attr("font-family", "sans-serif")
        .attr("font-size", "13px")
        .attr("font-weight", "bold")
        .attr("fill", "#475569")
        .text(label);

    const yearOf = (label: MonthLabel) => props.items[label.start].period.slice(0, 4);
    const years = d3.groups(labels, yearOf);
    for (const [index, [year, months]] of years.entries()) {
      const start = xScale(String(months[0].start)) ?? 0;
      const nextYear = years[index + 1];
      const end = nextYear ? (xScale(String(nextYear[1][0].start)) ?? width.value) : width.value;

      addLabel("year-label", start, plotTop.value - 6 - YEAR_HEADER_HEIGHT, year)
        .attr("text-anchor", "start")
        .datum<YearMarker>({ start, end });
    }
    positionYearLabels();

    for (const label of labels) {
      const start = barCenter(label.start);
      const end = barCenter(label.end);
      const month = label.label.replace(/ \d{4}$/, "");
      addLabel(
        "month-label",
        (start + end) / 2,
        plotTop.value - 6,
        label.start === label.end ? month.slice(0, 3) : month,
      );
    }
  };

  const renderBars = (svg: Svg, xScale: BandScale, yScale: ValueScale) => {
    const bars = svg
      .selectAll<SVGRectElement, TimeSeriesRow>("rect.bar")
      .data(props.items)
      .enter()
      .append("rect")
      .attr("class", "bar")
      .attr("data-testid", "trend-chart-bar")
      .attr("x", (_row, index) => xScale(String(index)) ?? 0)
      .attr("y", (row) => yScale(row.total_spent))
      .attr("width", xScale.bandwidth())
      .attr("height", (row) => yScale(0) - yScale(row.total_spent))
      .attr("fill", "#6366f1")
      .attr("rx", 4);

    for (const label of BAR_LABELS) {
      svg
        .selectAll<SVGTextElement, TimeSeriesRow>(`text.${label.className}`)
        .data(props.items)
        .enter()
        .append("text")
        .attr("class", label.className)
        .attr("x", (_row, index) => (xScale(String(index)) ?? 0) + xScale.bandwidth() / 2)
        .attr(
          "y",
          (row) => yScale(row.total_spent) + label.offset(yScale(0) - yScale(row.total_spent)),
        )
        .attr("text-anchor", "middle")
        .attr("font-family", "sans-serif")
        .attr("font-size", label.fontSize)
        .attr("font-weight", "bold")
        .attr("fill", label.fill)
        .attr("pointer-events", "none")
        .text((row) => label.text(row));
    }

    return bars;
  };

  /** Appended after the bars so the tooltip paints on top of them. */
  const createTooltip = (svg: Svg): Group => {
    const group = svg
      .append("g")
      .attr("class", "tooltip-group")
      .attr("data-testid", "trend-chart-tooltip")
      .style("display", "none")
      .style("pointer-events", "none");

    group
      .append("rect")
      .attr("class", "tooltip-bg")
      .attr("x", -TOOLTIP_WIDTH / 2)
      .attr("y", 0)
      .attr("width", TOOLTIP_WIDTH)
      .attr("height", 0)
      .attr("rx", 8)
      .attr("ry", 8)
      .attr("fill", "white")
      .attr("stroke", "#e2e8f0")
      .attr("stroke-width", 1)
      .attr("filter", "drop-shadow(0 2px 4px rgba(0,0,0,0.12))");

    group
      .append("line")
      .attr("class", "tooltip-sep")
      .attr("x1", -TOOLTIP_WIDTH / 2 + 8)
      .attr("x2", TOOLTIP_WIDTH / 2 - 8)
      .attr("y1", 22)
      .attr("y2", 22)
      .attr("stroke", "#e2e8f0")
      .attr("stroke-width", 1);

    for (const row of TOOLTIP_ROWS) {
      group
        .append("text")
        .attr("class", row.className)
        .attr("text-anchor", "middle")
        .attr("x", 0)
        .attr("y", row.y)
        .attr("font-family", "sans-serif")
        .attr("font-size", row.fontSize)
        .attr("font-weight", row.fontWeight)
        .attr("fill", row.fill);
    }

    return group;
  };

  let hideTimer: ReturnType<typeof setTimeout> | null = null;

  const cancelTooltipHide = () => {
    if (hideTimer === null) return;
    clearTimeout(hideTimer);
    hideTimer = null;
  };

  const showTooltip = (tooltip: Group, row: TimeSeriesRow, barX: number, barTop: number) => {
    cancelTooltipHide();

    const count = row.receipt_count;
    const average = count > 0 ? row.total_spent / count : 0;
    const retailers = row.retailers ?? [];

    tooltip.attr("transform", `translate(${barX}, ${barTop})`);
    tooltip.select(".tooltip-period").text(computePeriod(row.period, props.granularity).label);
    tooltip.select(".tooltip-total").text(t("chart.total", { amount: euro(row.total_spent) }));
    tooltip.select(".tooltip-count").text(t("chart.receipts", { count }));
    tooltip.select(".tooltip-avg").text(t("chart.averagePerReceipt", { amount: euro(average) }));
    tooltip.select(".tooltip-retailers").text(retailers.map(retailerLabel).join(", "));
    tooltip.select(".tooltip-bg").attr("height", retailers.length > 0 ? 110 : 90);
    tooltip.style("display", "block");
  };

  const attachBarHandlers = (bars: Bars, tooltip: Group) => {
    bars
      .on("click", (_event, row) => {
        onSelectPeriod(computePeriod(row.period, props.granularity));
      })
      .on("mouseenter", function (_event, row) {
        const barX = Number(this.getAttribute("x")) + Number(this.getAttribute("width")) / 2;
        showTooltip(tooltip, row, barX, Number(this.getAttribute("y")));
      })
      .on("mouseleave", () => {
        cancelTooltipHide();
        hideTimer = setTimeout(() => {
          hideTimer = null;
          tooltip.style("display", "none");
        }, TOOLTIP_HIDE_DELAY);
      });
  };

  const renderXAxis = (svg: Svg, xScale: BandScale) => {
    const hasMonthLabels = (props.monthLabels?.length ?? 0) > 0;
    const axis = d3
      .axisBottom(xScale)
      .tickFormat((_value, index) =>
        xTickLabel(props.items[index].period, props.granularity, hasMonthLabels),
      );

    const group = svg.append("g").attr("transform", `translate(0, ${PLOT_BOTTOM})`);
    axis(group);
    group
      .selectAll(".tick text")
      .attr("font-family", "sans-serif")
      .attr("font-size", "10px")
      .attr("fill", "#94a3b8");
    group.selectAll(".tick line").attr("display", "none");
    group.select(".domain").attr("stroke", "#cbd5e1");
  };

  const drawChart = () => {
    if (!yAxisRef.value || !chartRef.value) return;

    cancelTooltipHide();
    d3.select(yAxisRef.value).selectAll("svg").remove();
    d3.select(chartRef.value).selectAll("svg").remove();
    if (props.items.length === 0) return;

    const tickValues = ticks.value;
    const yScale = d3
      .scaleLinear()
      .domain([0, tickValues.at(-1) || 10])
      .range([PLOT_BOTTOM, plotTop.value]);
    const xScale = d3
      .scaleBand<string>()
      .domain(d3.range(props.items.length).map(String))
      .range([0, width.value])
      .padding(0.2);

    const yAxisSvg = appendSvg(yAxisRef.value, "trend-chart-y-axis-svg", Y_AXIS_WIDTH);
    const mainSvg = appendSvg(chartRef.value, "trend-chart-svg", width.value);

    renderYAxis(yAxisSvg, yScale, tickValues);
    renderGrid(mainSvg, yScale, tickValues);
    renderMonthMarkers(mainSvg, xScale);
    const bars = renderBars(mainSvg, xScale, yScale);
    attachBarHandlers(bars, createTooltip(mainSvg));
    renderXAxis(mainSvg, xScale);
  };

  onMounted(drawChart);

  onUnmounted(cancelTooltipHide);

  watch([() => props.items, () => props.monthLabels, () => props.granularity], drawChart);

  return { yAxisRef, chartRef, scrollRef, isScrollable, positionYearLabels };
};
