## 1. Frontend State Handling

- [x] 1.1 In `web/src/composables/useDashboard.ts`, remove the date-range reset from the `watch(retailer, ...)` handler (the `startDate.value = ""`, `endDate.value = ""` and `pendingDateRangeReset.value = true` lines), keeping the `page = 1` and `search = ""` resets.
- [x] 1.2 Confirm the payload-seed path in `refresh()` still covers the no-explicit-range case via the existing `(!startDate.value && !endDate.value)` branch.

## 2. Tests

- [x] 2.1 Update `web/src/components/__tests__/DashboardPage.spec.ts` so the retailer-change test asserts the date range is preserved (start/end unchanged in the follow-up request and state) while pagination and search reset.
- [x] 2.2 Add a test asserting that switching retailer with no explicit range still seeds the date filter from the new payload's min/max dates.

## 3. Verification

- [x] 3.1 Run `pnpm test -- --run` in `web/` and confirm all frontend tests pass.
- [x] 3.2 Run `pnpm build` in `web/` and confirm it builds cleanly.
- [x] 3.3 Run `openspec validate keep-date-filter-on-retailer-change --type change --strict` and fix any spec/scenario issues before archiving.