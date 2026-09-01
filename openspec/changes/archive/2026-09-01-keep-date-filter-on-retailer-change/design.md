## Context

The Vue dashboard (`web/`) drives its filters from `useDashboard()` in `web/src/composables/useDashboard.ts`. A dedicated `watch(retailer, ...)` handler fires on retailer change: it currently clears `startDate`/`endDate`, sets `pendingDateRangeReset`, resets `page` to 1 and `search` to empty, then refreshes. On the next payload, `refresh()` seeds the date range from `min_date`/`max_date` when `pendingDateRangeReset` is set. The result: any explicit date window the user chose is lost on every retailer switch.

This is purely a frontend state-handling change; the backend `/ui/dashboard` endpoint already accepts `start_date`/`end_date` independently of `retailer`, so no API change is required.

## Goals / Non-Goals

**Goals:**
- Preserve the user's selected `startDate`/`endDate` when the retailer filter changes.
- Keep the existing behavior of resetting pagination and search on retailer change.
- Keep the existing "seed from payload min/max when no explicit range" behavior.

**Non-Goals:**
- Changing the backend dashboard API.
- Persisting filters across page reloads or sessions.
- Changing how the date inputs are rendered.

## Decisions

### D1: Remove the date-range reset from the retailer-change watcher
In `web/src/composables/useDashboard.ts`, the `watch(retailer, ...)` handler stops clearing `startDate`/`endDate` and stops setting `pendingDateRangeReset = true`. Pagination (`page = 1`) and search reset (`search = ""`) stay.

- **Why:** The user wants the current date window preserved; the reset exists only for the "first load / no explicit range" seed case, which is already handled by the existing `(!startDate.value && !endDate.value)` branch in `refresh()`.
- **Alternatives considered:** (a) keep reset but only when the new retailer has no data — rejected, adds conditional complexity and contradicts the request; (b) preserve via local storage — out of scope (non-goal).

```text
Dynamic: retailer change (before -> after)

User -> DashboardPage (select retailer)
  |                                          |
  |  BEFORE: watcher clears start/end dates  |  AFTER: watcher keeps start/end dates
  v                                          v
useDashboard watch(retailer)          useDashboard watch(retailer)
  |  startDate=""; endDate=""           |  page=1; search=""
  |  pendingDateRangeReset=true         |  (dates untouched)
  |  page=1; search=""                  |
  v                                     v
refresh() -> GET /ui/dashboard        refresh() -> GET /ui/dashboard
  |  min/max seed dates (reset)         |  filter already carries start/end dates
  v                                     v
payload rendered                       payload rendered
```

Boundaries: only the dashboard frontend state layer changes; the backend endpoint and the payload seed branch are reused unchanged.

### D2: Keep the payload-seed path for the no-explicit-range case
`refresh()` already seeds `startDate`/`endDate` from the payload when `pendingDateRangeReset` is set **or** when both are empty. With `pendingDateRangeReset` no longer set on retailer change, the existing `(!startDate.value && !endDate.value)` branch still covers the "no explicit range" case — so no extra seeding logic is needed.

- **Why:** minimal change; reuses the existing seed mechanism.
- **Alternatives considered:** a separate seed-on-retailer-change flag — rejected as redundant.

## Risks / Trade-offs

- [A preserved date range has no data for the new retailer] -> Mitigation: the dashboard already renders empty sections gracefully; the user can clear the date inputs manually. Acceptable for this change.
- [The `resets the date range when the retailer changes` test asserts old behavior] -> Mitigation: update `web/src/components/__tests__/DashboardPage.spec.ts:108` to assert the range is preserved and that pagination/search reset.

## Migration Plan

1. Edit `web/src/composables/useDashboard.ts` — remove the two date-reset lines and `pendingDateRangeReset` assignment from the retailer watcher; leave `page`/`search` resets.
2. Update `web/src/components/__tests__/DashboardPage.spec.ts` — change the existing retailer-change test to expect the preserved range, and assert `search`/`page` reset behavior (add a scenario if needed).
3. Run `pnpm test -- --run` and `pnpm build` in `web/`.

Rollback: revert the two-file diff; no schema or migration concerns.

## Open Questions

- None. The behavior is unambiguous; the only decision point (preserve range, keep page/search reset) is recorded in D1/D2.