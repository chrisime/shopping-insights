# Design: Bar-Click → Receipt Modal

## Objective
Click a bar in the D3 trend chart → open a modal showing all receipts with full item detail for that period.

## Interfaces

### Backend: `GET /receipts/by-date`

- **Params**: `start_date` (ISO date, required), `end_date` (ISO date, required), `retailer` (optional)
- **Response**: bare array of full receipt dicts (same shape as `GET /receipts/by-item`), no `matched` field on items

```jsonc
// 200 OK
[
  {
    "id": "...",
    "retailer": "lidl",
    "purchase_date": "2024-01-15",
    "store": "Lidl …",
    "address": { "street": "…", "street_no": "…", "zip": "…", "city": "…" },
    "total_price": 42.50,
    "items": [ { "name": "…", "quantity": 2, "unit": "stk", "price": 3.99 }, … ],
    "payment_methods": [ … ],
    // … all other receipt fields
  },
  …
]
```

- Uses the same underlying `ReceiptService` / `SqliteReceiptStore` as existing endpoints, with a date-range filter added to the store query.

### Frontend: `ReceiptListModal.vue`

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `startDate` | `string` | yes | ISO date string for period start |
| `endDate` | `string` | yes | ISO date string for period end |
| `visible` | `boolean` | yes | Controls open/close |
| `retailer` | `string` | no | Optional retailer filter |

**Emits**: `close`

- Layout identical to `ReceiptModal.vue` (same card, navigation, receipt-detail sections)
- **Header**: shows human-readable period label (e.g. `"Januar 2024 — Kassenzettel"`) instead of `"articleName — retailer Kassenzettel"`
- **No article highlighting**: item rows always plain (no amber background, no dot)
- Fetches via `fetchReceiptsByDateRange(startDate, endDate, retailer?)` in `dashboard.ts`

### Chart→Modal Connection

**`TrendBarChart.vue`** — click handler on SVG `<rect>` elements
- Period key derived from bar's data index
- Granularity from `props.granularity`
- Compute date boundaries:
  - `daily` → same day as start/end
  - `monthly` → first/last day of the month
  - `yearly` → first/last day of the year
- Emit `select-period` with `{ startDate: string, endDate: string, label: string }`

**`TrendChartPanel.vue`** — forward `select-period` event upward

**`DashboardPage.vue`** — handle event
- `selectedPeriod` ref stores `{ startDate, endDate, label } | null`
- `ReceiptListModal` rendered at top level, bound to `selectedPeriod`
- On `close` → clear `selectedPeriod`

### Period Label Derivation

In `TrendChartPanel.vue` or `DashboardPage.vue`:

| Granularity | Key | Label |
|-------------|-----|-------|
| daily | `"2024-01-15"` | `"15. Januar 2024"` |
| monthly | `"2024-01"` | `"Januar 2024"` |
| yearly | `"2024"` | `"2024"` |

Locale: `de-DE`. Generated via `Intl.DateTimeFormat`.

## Files to Create / Modify

| File | Action |
|------|--------|
| `api/routes/receipts.py` | Add `GET /receipts/by-date` route |
| `api/services/receipt_service.py` | Add `list_receipts_by_date_range()` method |
| `web/src/api/dashboard.ts` | Add `fetchReceiptsByDateRange()` |
| `web/src/components/ReceiptListModal.vue` | **New** — date-range receipt modal |
| `web/src/components/TrendBarChart.vue` | Add click handler on `<rect>`, emit `select-period` |
| `web/src/components/TrendChartPanel.vue` | Forward `select-period` event |
| `web/src/components/DashboardPage.vue` | Handle event, bind `ReceiptListModal` |

## Open Questions
- None
