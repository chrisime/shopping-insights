# Vue Dashboard Review Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore the Streamlit-equivalent bonus KPI sections, visual time-series treatment, and initial date-range seeding in the Vue dashboard.

**Architecture:** Keep the current section-based payload shape and extend it only with the missing bonus sections plus min/max date metadata. Format KPI values server-side so Vue renders the same human-readable euro/percent strings the Streamlit dashboard shows, while the time-series panel remains a lightweight presentational component that derives its bar widths from numeric totals.

**Tech Stack:** Python, FastAPI, Vue 3, TypeScript, Vitest, Vue Test Utils

## Global Constraints

- Keep the changes minimal and aligned with the existing dashboard behavior.
- Preserve the current payload shape as much as possible.
- Add only small top-level metadata fields when needed for the initial date range.
- Do not push to GitHub.

---

### Task 1: Restore bonus sections and formatted KPI values in the payload

**Files:**
- Modify: `frontend/ui_model.py`
- Modify: `frontend/schema.py`
- Modify: `web/src/types/dashboard.ts`
- Modify: `tests/test_api_ui_dashboard.py`

**Interfaces:**
- Consumes: `DashboardState` fields `kpis`, `bonus_kpis`, `derived`, `min_date`, `max_date`
- Produces: `VueDashboardPayload` with formatted metric strings, bonus sections, and initial date metadata

- [ ] **Step 1: Write the failing test**

```python
def test_ui_dashboard_payload_includes_bonus_sections_and_date_range():
    ...
    payload = build_dashboard_page_model(state).to_dict()
    assert payload["sections"][1]["kind"] == "bonus_rewe"
    assert payload["sections"][1]["items"][0]["value"] == "€1.00"
    assert payload["min_date"] == "2024-01-01"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd .worktrees/vue-dashboard && pytest tests/test_api_ui_dashboard.py -q`

Expected: FAIL because bonus sections and payload metadata are not present yet.

- [ ] **Step 3: Write the minimal implementation**

```python
def _format_currency(value: float) -> str:
    return f"€{value:,.2f}"

def _format_percent(value: float) -> str:
    return f"{value:.1f}%"
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd .worktrees/vue-dashboard && pytest tests/test_api_ui_dashboard.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/ui_model.py frontend/schema.py web/src/types/dashboard.ts tests/test_api_ui_dashboard.py
git commit -m "fix: restore dashboard bonus metrics"
```

---

### Task 2: Seed dashboard dates and restore chart-like time series rendering

**Files:**
- Modify: `web/src/composables/useDashboard.ts`
- Modify: `web/src/components/TrendChartPanel.vue`
- Modify: `web/src/components/DashboardPage.vue`
- Modify: `web/src/components/__tests__/DashboardPage.spec.ts`
- Modify: `web/src/components/__tests__/DashboardPanels.spec.ts`

**Interfaces:**
- Consumes: `DashboardPayload.min_date`, `DashboardPayload.max_date`, `DashboardSectionKind`
- Produces: initial date filter values, proportional time-series bars, and Vue tests that cover both behaviors

- [ ] **Step 1: Write the failing test**

```ts
it("seeds the dashboard date filters from the first payload", async () => {
  ...
  await dashboard.refresh();
  expect(dashboard.startDate.value).toBe("2024-01-01");
  expect(dashboard.endDate.value).toBe("2024-01-31");
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd web && npm test -- --run src/components/__tests__/DashboardPage.spec.ts`

Expected: FAIL because the composable does not read `min_date` / `max_date` yet.

- [ ] **Step 3: Write the minimal implementation**

```ts
const skipNextAutoRefresh = ref(false);

watch([retailer, startDate, endDate, timeGranularity, spendingView, topView, topLimit], () => {
  if (skipNextAutoRefresh.value) {
    skipNextAutoRefresh.value = false;
    return;
  }
  void refresh();
});
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd web && npm test -- --run src/components/__tests__/DashboardPage.spec.ts src/components/__tests__/DashboardPanels.spec.ts`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add web/src/composables/useDashboard.ts web/src/components/TrendChartPanel.vue web/src/components/DashboardPage.vue web/src/components/__tests__/DashboardPage.spec.ts web/src/components/__tests__/DashboardPanels.spec.ts
git commit -m "fix: seed dashboard filters and restore chart panel"
```
