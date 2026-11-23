## 1. Dashboard request coordination

- [x] 1.1 Add failing composable tests for a search from a later page producing exactly one debounced request, a retailer change cancelling a pending search refresh, and out-of-order requests keeping the newest payload and loading state.
- [x] 1.2 Refactor `useDashboard` refresh scheduling so dependent filter changes share one request, the 400 ms search debounce remains, and only the latest request can update state; run the composable tests.

## 2. Receipt lookup states

- [x] 2.1 Add failing composable and component tests proving a failed receipt lookup is distinct from a successful empty result and the error clears on a new lookup.
- [x] 2.2 Expose and render a separate receipt lookup error state through `useReceiptBrowser`, `ReceiptListModal`, and `ReceiptViewer`; run the affected tests.

## 3. Verification

- [x] 3.1 Run `corepack pnpm exec vp test run`, `corepack pnpm exec vp check`, `corepack pnpm exec vp run typecheck`, and `corepack pnpm exec vp build` from `web/`.
- [x] 3.2 Run `openspec validate dashboard-loading-resilience --type change --strict` before archive.
