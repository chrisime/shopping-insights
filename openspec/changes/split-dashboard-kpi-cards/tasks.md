## 1. Backend metrics split

- [ ] 1.1 In `api/services/dashboard_builders.py`, partition the flat metrics dict into a general key set (`spendings`, `spendings_without_discount`, `receipt_count`, `avg_receipt_amount`, `saved_deposit`, `total_savings`, `total_savings_pct`) and a discount key set (all remaining `rewe_*`, `lidl*`, `sticker_*`, `rossmann_*` fields).
- [ ] 1.2 Emit `DashboardSection(kind="metrics", title="Allgemeine Informationen")` always, and `DashboardSection(kind="metrics", title="Rabatte")` only when the discount key set is non-empty.
- [ ] 1.3 Confirm that a selected discount-capable retailer with zero discounts still yields a non-empty discount set, so the "Rabatte" section renders with `0` values.

## 2. Frontend KPI cards

- [ ] 2.1 In `web/src/components/DashboardKpiGrid.vue`, gate the general card groups on the presence of `spendings` while keeping the existing Rewe/Lidl/Rossmann field-presence gating.
- [ ] 2.2 Add a Rossmann "Preisvorteil" card (`rossmann_discount_amount`, `rossmann_discount_pct`) as the last card of the Rossmann group, mirroring Lidl.

## 3. Tests and verification

- [ ] 3.1 Update backend tests (`tests/test_api_imports.py`, `tests/test_api_ui_dashboard.py`, `tests/test_dashboard_ui_model.py`, `tests/test_frontend_schema.py`) for two metrics sections and the new titles, including the dm-only omission case.
- [ ] 3.2 Update/add frontend tests (`web/src/components/__tests__/DashboardKpiGrid.spec.ts`, `DashboardPage.spec.ts`, `DashboardPageExport.spec.ts`) for the split, the omitted empty "Rabatte" section, and the Rossmann "Preisvorteil" card.
- [ ] 3.3 Run `./.venv/bin/python -m pytest -q` and, in `web/`, `corepack pnpm test -- --run`; ensure both suites pass.
- [ ] 3.4 Run `openspec validate split-dashboard-kpi-cards --type change --strict` and fix any validation errors.
