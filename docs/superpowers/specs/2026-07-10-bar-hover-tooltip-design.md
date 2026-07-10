# Design: Bar Hover + Tooltip

## Objective
Hover over a D3 trend chart bar → bar darkens + tooltip shows total spent, receipt count, average per receipt, period, and retailer names.

## Bar Hover Effect (CSS)

Pure CSS in `<style scoped>` of `TrendBarChart.vue`:

```css
.bar {
  cursor: pointer;
  transition: fill 0.15s ease;
}
.bar:hover {
  fill: #4f46e5;  /* indigo-600 */
}
```

No JavaScript involvement. Works across D3 redraws.

## Tooltip: Position & Behavior

- A single `<div>` overlay managed by D3 in `drawChart()`.
- `position: absolute` relative to the chart container.
- **Fixed position**: centered above the hovered bar (X = bar midpoint, Y = top of bar minus padding). Does **not** follow the mouse.
- `pointer-events: none` — does not block bar clicks or hover.
- Created once, reused on each hover (no enter/exit per data point).
- **Show**: on `mouseenter` of `<rect.bar>` → populate innerHTML, set `display: block`, position via `transform: translate(Xpx, Ypx)`.
- **Hide**: on `mouseleave` → `display: none`.
- Z-index above chart elements.

## Tooltip: Layout

```
┌─────────────────────┐
│ Januar 2026          │  ← font-weight: 600, font-size: 14px
│ ——————————————————— │  ← hr
│ €1.234,56  Gesamt    │
│ 12 Belege            │
│ €102,88  Ø/Beleg     │
│ Lidl, REWE           │  ← font-size: 12px, color: #64748b
└─────────────────────┘
```

Background: `#fff`, border-radius: `8px`, box-shadow, padding `8px 14px`.

## Retailer Data per Item

Current trend items have 3 fields: `period`, `total_spent`, `receipt_count`. Need to add `retailers: string[]`.

### Changes

| File | Change |
|------|--------|
| `shared/kpi_dtos.py` | `TimeSeriesRow` add field `retailers: list[str]` with default `[]` |
| `storage/kpi_store.py` | Add `GROUP_CONCAT(DISTINCT p.retailer)` in `spending_by_day()`, `spending_by_month()`, `spending_by_year()`; handle `NULL` → `[]` |
| `api/services/dashboard_service.py` | Include `retailers` in serialized dict for `time_series` section items |

The chart section payload changes from:
```json
{"period": "2024-01", "total_spent": 1234.56, "receipt_count": 12}
```
to:
```json
{"period": "2024-01", "total_spent": 1234.56, "receipt_count": 12, "retailers": ["lidl", "rewe"]}
```

## Files to Create / Modify

| File | Action |
|------|--------|
| `shared/kpi_dtos.py` | Add `retailers` field to `TimeSeriesRow` |
| `storage/kpi_store.py` | Add `GROUP_CONCAT(DISTINCT p.retailer)` to 3 SQL queries |
| `api/services/dashboard_service.py` | Include `retailers` in trend item dict |
| `web/src/components/TrendBarChart.vue` | Add CSS hover rule, D3 tooltip div, mouseenter/mouseleave on bars |
| `web/src/components/__tests__/TrendBarChart.spec.ts` | Add tooltip tests (show on hover, hide on leave, content) |

## Open Questions
- None
