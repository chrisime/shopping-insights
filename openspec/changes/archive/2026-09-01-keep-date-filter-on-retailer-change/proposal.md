## Why

When the user switches the retailer in the Vue dashboard, the date filter is reset to the new retailer's full available range (`min_date`/`max_date`). If the user is comparing the same time window across retailers, every switch erases their chosen period and forces them to re-pick it. The dashboard should preserve the current date filter on retailer change and only adapt when the selection becomes empty.

## What Changes

- Remove the date-range reset from the retailer-change handler in `web/src/composables/useDashboard.ts` (`startDate`/`endDate` stay as they are).
- Keep the reset of pagination (`page`) and search (`search`) on retailer change — only the date filter is preserved.
- When the user switches retailer with an already-set date range, keep that range for the new retailer.
- When the user switches retailer with no explicit date range, continue to seed the filter from the new payload's `min_date`/`max_date` as today.
- Update the existing frontend test `DashboardPage.spec.ts:108` that currently asserts the date range is reset on retailer change.

## Capabilities

### New Capabilities
- `dashboard-date-filter-persistence`: Preserve the user's date filter when switching retailers in the dashboard; reset only pagination and search.

### Modified Capabilities
- No existing spec-level behaviour changes.

## Impact

- `web/src/composables/useDashboard.ts` — retailer-change watcher no longer clears `startDate`/`endDate` or sets `pendingDateRangeReset`; pagination/search reset retained.
- `web/src/components/__tests__/DashboardPage.spec.ts` — update the `resets the date range when the retailer changes` test to assert the range is preserved instead.
- No backend/API changes; the dashboard endpoint already filters by `start_date`/`end_date` independent of retailer.