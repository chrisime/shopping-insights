# Oruga + Tailwind UI Design

**Date:** 2026-07-05  
**Status:** Draft  
**Scope:** Migrate the Vue dashboard UI to Oruga components with TailwindCSS styling

---

## 1. Goal

Rebuild the existing Vue dashboard UI so it uses `oruga-ui` for interactive controls and `tailwindcss` for layout, spacing, typography, and visual hierarchy.

The dashboard data contract does not change. Only the presentation layer changes.

---

## 2. Product Decision

Use the **balanced analytic** direction.

### What that means

- Oruga handles form controls, messages, loading states, and other interactive UI primitives.
- Tailwind handles page layout, grid structure, spacing, surfaces, and typography.
- The dashboard keeps its current single-page, read-only, filter-driven behavior.
- The result should feel cleaner and more polished, but not visually loud or overly branded.

### Visual intent

- airy, structured dashboard layout
- clear hierarchy between filters, KPIs, charts, and tables
- muted surfaces with stronger emphasis on values and labels
- desktop-first, but still responsive

---

## 3. Scope

### In scope

- add Oruga and Tailwind to the Vue app
- register Oruga globally in the Vue entrypoint
- replace custom filter inputs with Oruga controls
- restyle the dashboard shell with Tailwind utilities
- restyle KPI, chart, weekday, top-items, skeleton, and error states
- keep the dashboard payload and fetch flow unchanged

### Out of scope

- backend API changes
- dashboard payload shape changes
- CSV export
- chart library replacement
- new interactions such as drilldowns or modal flows

---

## 4. Architecture

### App bootstrap

`web/src/main.ts` becomes the place where the Vue app registers the Oruga plugin and loads the global Tailwind stylesheet.

### Page shell

`DashboardPage.vue` keeps the stateful orchestration:

- fetch data through `useDashboard()`
- show loading, empty, and error states
- render payload sections by `kind`

### Presentational layer

The section components stay focused on rendering data:

- `DashboardFilterBar.vue` uses Oruga inputs/selects/date inputs
- `DashboardSection.vue` becomes a Tailwind-styled section frame
- `KpiRow.vue` uses Tailwind cards for compact metrics
- `TrendChartPanel.vue`, `WeekdayPanel.vue`, and `TopItemsPanel.vue` keep their data logic but use Tailwind surface styling
- `DashboardSkeleton.vue` becomes the loading placeholder

---

## 5. Data Flow

1. Vue calls `GET /ui/dashboard` through the existing client.
2. `useDashboard()` stores payload, loading, and error state.
3. `DashboardPage.vue` renders the top shell and section list.
4. Oruga components handle user input for filters.
5. Tailwind utilities handle the overall dashboard composition.

The backend payload remains the same section-based structure with a payload `title` and per-section `kind`, `title`, and `items`.

---

## 6. UI Rules

### Filters

- use Oruga controls for retailer, date range, granularity, spending view, top-view, and limit
- keep filters in a compact top bar
- preserve the read-only nature of the dashboard

### Layout

- use Tailwind grid/flex utilities instead of handwritten page CSS
- keep the KPI row visually prominent
- keep the main chart as the primary block
- place weekday and top-items panels side by side on wide screens

### States

- show an Oruga message or alert for errors
- show a skeleton or loading placeholder while the first payload loads
- show a compact empty state when a section has no items

---

## 7. Testing

Update the Vue tests to verify:

- the dashboard still renders section titles and item labels
- the filter bar still triggers refetches
- the page still renders when payload sections are empty
- the Oruga/Tailwind refactor does not break the dashboard shell

The tests should continue to focus on behavior, not implementation details.

---

## 8. Non-Goals

- redesigning the dashboard information architecture
- changing the analytics payload
- adding new dashboard interactions
- replacing the chart data model
- mobile-first optimization

---

## 9. Implementation Order

1. add Tailwind and Oruga to the Vue app
2. register the Oruga plugin and load Tailwind base styles
3. restyle the dashboard shell
4. restyle the filter bar
5. restyle the dashboard sections and panels
6. adjust the Vue tests to cover the new rendering

---

## 10. Acceptance Criteria

- the dashboard uses Oruga controls for user inputs
- the dashboard uses Tailwind for page layout and visual hierarchy
- the existing filter-driven refresh behavior still works
- the dashboard remains single-page, read-only, and balanced
- the backend payload contract remains unchanged
