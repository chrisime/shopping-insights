## Context

The dashboard currently formats numbers in `web/src/utils/format.ts`, Vue templates, and D3 rendering callbacks. Some paths use `Intl.NumberFormat`; others concatenate a currency symbol or use `toFixed`. The Top Items formatter truncates every non-kilogram quantity.

## Goals / Non-Goals

**Goals:** Use shared, testable number formatting and retain fractional piece quantities in both views.

**Non-Goals:** No translation framework, locale switcher, date changes, API changes, or component restructure.

## Decisions

- Reuse the pure helpers in `web/src/utils/format.ts` with native `Intl.NumberFormat` and an explicit `de-DE` default. Vue and D3 remain consumers; no reactive formatter or dependency is needed.
- Format euro amounts with two decimals, except for deliberately compact chart-axis ticks. Preserve the existing coupon currency selection and fallback to EUR, using the shared formatter rather than a separate component formatter.
- Format kilograms with exactly three decimals. For pieces, keep the supplied fractional precision without padding whole numbers. Preserve unit labels and avoid inventing a unit if a receipt does not supply one.
- Convert percent-valued KPI inputs to ratios at the formatter boundary when using `Intl` percent style. Leave the source values unchanged. Keep a dash fallback for non-finite inputs.

## Risks / Trade-offs

- `Intl` emits non-breaking spaces in German currency and percentage strings. Assert exact output in unit tests and account for whitespace normalization in DOM assertions.
- Chart labels grow for larger amounts. Retain compact whole-euro axis ticks; keep full precision on values and tooltips.

## Migration Plan

No data migration or API rollout. Roll back by reverting the frontend formatting change.

## Open Questions

None.
