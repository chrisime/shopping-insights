## Why

Dashboard filter changes can trigger redundant refreshes when a search also resets pagination, while receipt-loading failures are currently presented as an empty result. Tightening these behaviors makes the dashboard's request lifecycle predictable and gives users an accurate result state.

## What Changes

- Coordinate dependent dashboard filter changes so each effective filter state produces one refresh, while preserving the search debounce and discarding stale responses.
- Distinguish a successful receipt lookup with no results from a failed lookup in the receipt list.
- Keep automatic retries, API changes, and new dependencies out of scope.

## Capabilities

### New Capabilities

- `dashboard-request-coordination`: Refresh the dashboard once for each effective filter state and prevent stale responses from replacing newer results.
- `receipt-loading-state`: Present loading, successful-empty, and failed receipt lookup states distinctly.

### Modified Capabilities

- None. Existing date-filter persistence and retailer-change behavior remain unchanged.

## Impact

Vue composables `useDashboard` and `useReceiptBrowser`, receipt-list presentation in `ReceiptListModal.vue` / `ReceiptViewer.vue`, and frontend tests. No backend, API, or dependency changes.
