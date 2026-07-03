# Vue Dashboard Design

**Date:** 2026-07-03  
**Status:** Draft  
**Scope:** Vue-based dashboard replacement for the current Streamlit UI

---

## 1. Goal

Build a Vue dashboard that can replace the current Streamlit frontend without changing the underlying receipt-processing pipeline.

The dashboard must consume a backend payload that is already shaped for UI rendering and can be reused by future frontend clients.

---

## 2. Product Decision

The dashboard starts as a **single-page, desktop-first, balanced analytics view**.

### Layout

- Top filter bar
- KPI row with 4 to 5 cards
- One primary trend chart
- Two side-by-side panels below it:
  - weekday analysis
  - top items
- Optional compact detail/table area below

### Interaction level

- Primarily read-only
- Filters update the dashboard content
- No drilldowns or modal flows in the first version

### Device priority

- Desktop first
- Mobile usable, but not the primary target

---

## 3. Component Structure

### Page Layer

#### `DashboardPage.vue`

Responsibilities:

- loads dashboard data
- owns loading/error state
- binds filter state to the backend request
- passes data to the presentational components

#### `DashboardSection.vue`

Shared wrapper for all non-filter sections.

Responsibilities:

- render title
- render empty state
- normalize spacing and borders

### Filter Layer

#### `DashboardFilterBar.vue`

Responsibilities:

- retailer selector
- date range selectors
- granularity selector
- top-items sort selector
- top-items limit selector

### Content Layer

#### `KpiRow.vue`

Renders the KPI cards.

#### `TrendChartPanel.vue`

Renders the time-series chart.

#### `WeekdayPanel.vue`

Renders weekday distribution and averages.

#### `TopItemsPanel.vue`

Renders the top items table or chart-like ranking.

#### `DashboardSkeleton.vue`

Optional loading placeholder for the first fetch.

---

## 4. Data Flow

1. Vue calls `GET /ui/dashboard`.
2. Query parameters are forwarded as dashboard filters.
3. Backend builds `DashboardState`.
4. `DashboardPageModel` is created from that state.
5. `VueDashboardPayload` is returned as JSON.
6. Vue renders sections by `kind`.

### Query Parameters

- `retailer`
- `start_date`
- `end_date`
- `time_granularity`
- `spending_view`
- `top_view`
- `top_limit`

---

## 5. Backend Payload Contract

The response is a section-based payload.

```json
{
  "title": "Shopping Analyzer Dashboard",
  "sections": [
    {
      "kind": "metrics",
      "title": "Kennzahlen",
      "items": [
        {"label": "Ausgaben gesamt", "value": "€123.45"}
      ]
    },
    {
      "kind": "chart",
      "title": "Ausgaben über Zeit",
      "items": [
        {"period": "2024-01", "total_spent": 123.45, "receipt_count": 12}
      ]
    },
    {
      "kind": "table",
      "title": "Top-Artikel",
      "items": [
        {
          "name": "Apfel",
          "total_quantity": 4,
          "total_spent": 8.0,
          "purchase_count": 2,
          "unit": "pc"
        }
      ]
    }
  ]
}
```

### Rules

- `kind` decides which Vue component renders the section
- `title` is the human-readable label
- `items` stays generic but structured
- no Streamlit-specific formatting appears in the payload

---

## 6. Vue Payload Schema

The project keeps a dedicated frontend schema layer for the future Vue client.

### `frontend/schema.py`

- `VueDashboardSection`
- `VueDashboardPayload`

These are convenience models for serialization and contract clarity.

### `frontend/ui_model.py`

This remains the neutral internal model and now provides:

- `to_dict()` / `from_dict()`
- `to_json()` / `from_json()`

---

## 7. Error Handling

- If the backend has no receipts, the page shows an empty state instead of a broken layout.
- If the backend request fails, the page shows a compact error state and retains the current filter values.
- If a section has no items, the section renders an empty-state message.

---

## 8. Non-Goals

- CSV export
- OpenAPI hardening / docs polish
- drilldown flows
- modal-heavy interaction
- mobile-first layout optimization

---

## 9. Implementation Order

1. Add the Vue endpoint that serves the payload
2. Wire Vue to fetch the payload
3. Build the page shell and filters
4. Add KPI cards and the main chart
5. Add weekday and top-items panels
6. Polish empty/error/loading states

---

## 10. Acceptance Criteria

- Vue dashboard renders the same information as the current Streamlit dashboard
- Filters update the dashboard data
- Backend payload is reusable outside Vue
- The page remains single-page, balanced, and desktop-first
