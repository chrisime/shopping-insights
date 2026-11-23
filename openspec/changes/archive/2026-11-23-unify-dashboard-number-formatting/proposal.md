## Why

The dashboard presents the same amount in different formats and truncates fractional piece quantities in the Top Items view. Consistent formatting makes spending and quantities easier to compare across views.

## What Changes

- Display monetary amounts, quantities, and percentages using German number conventions.
- Preserve fractional piece quantities in the Top Items and receipt views; keep whole pieces free of trailing decimals and kilograms at three decimal places.
- Leave API values, translations, date formatting, and loading behavior unchanged.

## Capabilities

### New Capabilities

- `dashboard-number-formatting`: Consistent presentation of monetary amounts, quantities, and percentages across dashboard views.

### Modified Capabilities

- None. Existing KPI card content and grouping remain unchanged.

## Impact

Vue dashboard components, shared number-formatting utilities, and frontend tests. No new dependencies or backend changes.
