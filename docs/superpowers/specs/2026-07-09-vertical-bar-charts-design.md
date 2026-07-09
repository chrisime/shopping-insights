# Vertical Bar Charts for Spending-over-Time

## Goal

Replace the existing horizontal-bar / collapsible-tree spending visualization with
vertical bar charts that show receipt-count labels on each bar, rendered in a
coordinate-system look with x/y axes.

## Dependencies

Add to `web/package.json`:

- `chart.js` (v4)
- `vue-chartjs` (Vue 3 wrapper)
- `chartjs-plugin-datalabels` (for receipt-count labels on bars)

## Component Architecture

### `TrendBarChart.vue` (new)

A thin Chart.js `Bar` wrapper.

**Props:**
- `items: Array<{period: string, total_spent: number, receipt_count: number}>`
- `granularity: "Täglich" | "Monatlich" | "Jährlich"`

**Rendering:**
- Uses `vue-chartjs` `<Bar>` component
- X-axis labels: formatted period names (e.g. "Jan 2024", "2024")
- Y-axis: spending in EUR, `beginAtZero`, grid lines
- `chartjs-plugin-datalabels` places `receipt_count` centered inside each bar
- `responsive: true`, `maintainAspectRatio: false`
- Wrapped in `<div class="overflow-x-auto">` so monthly/daily charts can scroll
  horizontally when there are many bars

### `TrendChartPanel.vue` (rewritten)

Keeps the summary cards (average / max / min spending). Replaces the old
horizontal-bar / tree template with `TrendBarChart`.

**Layout by granularity:**

| Granularity | Layout |
|---|---|
| `Jährlich` | Single `TrendBarChart` with one bar per year |
| `Monatlich` | One `TrendBarChart` per year (year header + 12 month bars), scrollable |
| `Täglich`   | One `TrendBarChart` per year-month (year/month header + daily bars), scrollable |

**Grouping logic** stays in `TrendChartPanel.vue` (already has `buildMonthlyTree`,
`buildDailyTree`). Each leaf group is passed as `items` to a `TrendBarChart`.

## Data Flow

No backend changes needed. The `time_series` section of the dashboard payload
already provides `{period, total_spent, receipt_count}` items at the requested
granularity (daily / monthly / yearly).

The existing filter controls (retailer, date range, granularity) continue to
work unchanged.

## Styling

Chart.js defaults with minor overrides:
- Bar color: indigo-500 (matching current `bg-indigo-500`)
- Grid lines: light grey
- Font family: inherit from Tailwind
- Datalabels: white text inside bar, dark background

## Future Considerations

- Cumulative spending view (already in filter UI, currently unused in charts)
- Chart.js theming via `chartjs-plugin-tailwindcss` if needed later
