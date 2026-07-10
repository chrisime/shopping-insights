# Design: Two-Chart Y-Axis (Sticky + Scrollable)

## Goal
Eliminate all y-axis alignment issues by using two synchronized Chart.js instances: one sticky chart showing only y-axis labels, one scrollable chart showing bars + x-axis.

## Layout
```
Flex row:
  ┌─────────────────────────────────┐
  │ Y-Axis Chart (sticky left-0)    │  Haupt Chart (overflow-x-auto)
  │ 64px wide, 500px tall           │  min-width: N*48px, 500px tall
  │ scales.y.ticks: true (€ labels) │  scales.y.ticks: false
  │ scales.x: display false         │  scales.x: normal
  │ datalabels: false               │  datalabels: true
  │ tooltip: false                  │  tooltip: true
  │ grid: false                     │  grid: true
  │ padding.bottom: 32              │  padding: top 30 only
  └─────────────────────────────────┘
```

## Key Decisions
- **Same `chartData`** for both charts → identical y-scale
- **Same `scales.y` config** (beginAtZero, stepSize) → identical pixel mapping
- **Bottom padding on y-axis chart** (32px) approximates x-axis label height so chartArea.bottom aligns
- **No plugins on y-axis chart** (no datalabels, no monthHeader execution via option check)
- **monthHeader plugin** checks `chart.options.monthLabels` before drawing → skips y-axis chart automatically

## Files Affected
- `web/src/components/TrendBarChart.vue` — replace HTML y-axis with second Bar component; add yAxisOptions computed; remove yAxisSync plugin, tickPositions, afterLayout logic

## Edge Cases
- **Empty items**: both charts show empty (handled by Chart.js)
- **Single month**: no month headers (plugin skips) — works
- **Yearly (non-scrollable)**: no sticky needed, just flex layout without overflow-x-auto
