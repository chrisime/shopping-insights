## 1. Shared number formatting

- [x] 1.1 Add failing formatter tests for German euros, compact axis ticks, supplied and fallback coupon currencies, fractional and whole pieces, three-decimal kilograms, percentages already expressed in percent, and non-finite values.
- [x] 1.2 Implement the pure formatters in `web/src/utils/format.ts` and run the formatter tests.

## 2. Dashboard integration

- [x] 2.1 Add regression tests for matching spending and receipt totals, D3 tooltip amounts, KPI percentages, and matching receipt and Top Items quantity precision.
- [x] 2.2 Use the shared formatters in the KPI grid, trend chart, receipt viewer, coupon savings, and existing formatter consumers; run the affected frontend tests.

## 3. Verification

- [x] 3.1 Run `corepack pnpm exec vp test run`, `corepack pnpm exec vp check`, `corepack pnpm exec vp run typecheck`, and `corepack pnpm exec vp build` from `web/`.
- [x] 3.2 Run `openspec validate unify-dashboard-number-formatting --type change --strict` before archive.
