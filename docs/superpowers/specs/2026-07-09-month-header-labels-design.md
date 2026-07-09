# Design: Month Header Labels for Daily Chart

## Goal
When `timeGranularity === "Täglich"`, display month names ("Januar 2024", "Februar 2024", ...) as labels positioned above the day bars in a single Chart.js chart, with thin vertical separator lines between months.

## Architecture

### New file: `web/src/chart-plugins/monthHeaderPlugin.ts`
A Chart.js plugin registered locally in TrendBarChart's script setup (via `ChartJS.register(monthHeaderPlugin)` alongside the other registrations).

```
interface MonthLabel {
  label: string;   // "Januar 2024"
  start: number;   // data index of first day in this month
  end: number;     // data index of last day in this month
}
```

**Plugin hooks:**
- `id: "monthHeader"`
- `afterDraw(chart)`:
  1. If no `monthLabels` on chart options, skip.
  2. Compute chart area top offset — month names sit above x-axis tick labels but within the chart canvas.
  3. For each `MonthLabel`:
     - `chart.scales.x.getPixelForValue(ml.start)` → `leftPx`
     - `chart.scales.x.getPixelForValue(ml.end)` → `rightPx`
     - Draw `ctx.fillText(ml.label, (leftPx + rightPx) / 2, yPos)` centered, bold, slate-600 color.
     - Draw thin vertical line at `leftPx` from `yPos - 4` to `yPos + 4` (stroke, 1px, slate-300).

### TrendChartPanel.vue — changes
`buildDayGroups()` stays unchanged (single flat group).  
Add computed `monthLabels` that extracts month boundaries from `props.items`:
- Iterate items sorted by period (`YYYY-MM-DD` order is already guaranteed).
- When month changes (period.slice(5,7) differs), emit `{ label: $fullMonthName, start, end }`.
- Pass `monthLabels` to TrendBarChart via new prop.

### TrendBarChart.vue — changes
- New prop `monthLabels: MonthLabel[]` (only non-empty for daily granularity).
- Import and register `monthHeaderPlugin`.
- Pass `monthLabels` through chart options so the plugin can read it.
- When `monthLabels` is non-empty, x-axis labels are just day numbers (slice period 8-10).

### monthName mapping
Use full German month names: "Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember". Always append year, e.g. "Januar 2024", "Februar 2024".

### Style
- Month label font: bold 13px sans-serif, `#475569` (slate-600).
- Separator lines: 1px solid `#cbd5e1` (slate-300), drawn only at the start of each month (not before the first month).

## Files affected
- `web/src/chart-plugins/monthHeaderPlugin.ts` — NEW
- `web/src/components/TrendChartPanel.vue` — add `monthLabels` computed, pass to TrendBarChart
- `web/src/components/TrendBarChart.vue` — new prop, register plugin, day-only labels

## Edge Cases
- **Single month**: no separator lines drawn.
- **Empty items**: plugin skips.
- **One day per month**: start === end, midpoint works.
- **Year boundary**: Dec → Jan handled correctly (period slice YYYY-MM changes).
