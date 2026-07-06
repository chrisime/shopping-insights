# Vue Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Streamlit dashboard with a Vue dashboard that consumes a section-based API payload and keeps the receipt-processing pipeline unchanged.

**Architecture:** Keep the Python side responsible for dashboard state computation and payload shaping, expose a Vue-specific JSON endpoint, and build the Vue app as a thin presentation layer that renders `sections` by `kind`. The Vue UI stays single-page, desktop-first, balanced, and primarily read-only.

**Tech Stack:** Python 3.10+, FastAPI, Vue 3, Vite, TypeScript, Vitest, Vue Test Utils, Chart.js

## Global Constraints

- Single-page, desktop-first, balanced analytics view.
- Primarily read-only; filters update content, but no drilldowns or modal flows in the first version.
- CSV export remains out of scope for now.
- OpenAPI hardening / docs polish remains out of scope for now.
- The backend payload must stay section-based (`kind`, `title`, `items`) and must not contain Streamlit-specific formatting.
- The backend payload must be reusable outside Vue.
- The page must remain balanced and not become a dense cockpit UI.

---

### Task 1: Backend Vue Payload Endpoint

**Files:**
- Modify: `frontend/schema.py`
- Create: `api/services/dashboard_service.py`
- Create: `api/routes/dashboard.py`
- Modify: `api/main.py`
- Create: `tests/test_api_ui_dashboard.py`

**Interfaces:**
- Consumes: `build_dashboard_state(provider, retailer, start_date, end_date, time_granularity, spending_view, top_view, top_limit) -> DashboardState` from `frontend/dashboard_state.py`, `build_dashboard_page_model(state: DashboardState) -> DashboardPageModel` from `frontend/ui_model.py`
- Produces: `VueDashboardPayload.from_page_model(page: DashboardPageModel) -> VueDashboardPayload` and `GET /ui/dashboard(retailer, start_date, end_date, time_granularity, spending_view, top_view, top_limit) -> dict[str, Any]`

- [ ] **Step 1: Write the failing test**

```python
def test_ui_dashboard_endpoint_returns_section_payload(monkeypatch):
    from fastapi.testclient import TestClient
    from datetime import date

    from api.main import app
    from api.routes import dashboard as dashboard_route
    from frontend.dashboard_state import DashboardDerivedMetrics, DashboardState
    from frontend.ui_model import DashboardPageModel, DashboardSection
    from metrics import BasicKPIs, RetailerBonusKPIs, TimeSeriesRow, TopItemRow, WeekdayRow

    state = DashboardState(
        retailer="lidl",
        start_date="2024-01-01",
        end_date="2024-01-31",
        time_granularity="Monatlich",
        spending_view="Absolut",
        top_view="Menge",
        top_limit=10,
        available_kpis=BasicKPIs(100.0, 4, 25.0, 10.0, 2.0, "2024-01-01", "2024-01-31"),
        kpis=BasicKPIs(100.0, 4, 25.0, 10.0, 2.0, "2024-01-01", "2024-01-31"),
        bonus_kpis=RetailerBonusKPIs(1.0, 2.0, 3.0, 4.0, 5.0),
        derived=DashboardDerivedMetrics(122.0, 10.0, 12.0, 12.0, 22.0, 22.0, 4.0, 5.0),
        time_series=[TimeSeriesRow(period="2024-01", total_spent=10.0, receipt_count=1)],
        weekday=[WeekdayRow(weekday=0, weekday_name="Montag", trip_count=1, avg_spent=10.0, total_spent=10.0)],
        top_items=[TopItemRow(name="Apfel", total_quantity=2.0, total_spent=4.0, purchase_count=1, unit="pc")],
        min_date=date(2024, 1, 1),
        max_date=date(2024, 1, 31),
    )

    page = DashboardPageModel(
        title="Shopping Analyzer Dashboard",
        sections=[DashboardSection(kind="metrics", title="Kennzahlen", items=[{"label": "A", "value": "1"}])],
    )

    monkeypatch.setattr(dashboard_route, "dashboard_service", ...)

    response = TestClient(app).get(
        "/ui/dashboard",
        params={
            "retailer": "lidl",
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "time_granularity": "Monatlich",
            "spending_view": "Absolut",
            "top_view": "Menge",
            "top_limit": 10,
        },
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Shopping Analyzer Dashboard"
    assert response.json()["sections"][0]["kind"] == "metrics"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_api_ui_dashboard.py -q`

Expected: FAIL with `404 Not Found` or missing dashboard route imports.

- [ ] **Step 3: Write the minimal implementation**

```python
# frontend/schema.py
@classmethod
def from_page_model(cls, page: DashboardPageModel) -> "VueDashboardPayload":
    return cls.from_dict(page.to_dict())

# api/services/dashboard_service.py
from frontend.dashboard_state import build_dashboard_state
from frontend.ui_model import build_dashboard_page_model
from frontend.schema import VueDashboardPayload

class DashboardService:
    def __init__(self, store):
        self._store = store

    def get_vue_dashboard_payload(**filters) -> VueDashboardPayload:
    state = build_dashboard_state(self._store, **filters)
    page = build_dashboard_page_model(state)
    return VueDashboardPayload.from_page_model(page)

# api/routes/dashboard.py
from fastapi import APIRouter
from api.services.dashboard_service import DashboardService

router = APIRouter(prefix="/ui", tags=["ui"])
dashboard_service = DashboardService(...)

@router.get("/dashboard")
def read_dashboard(
    retailer: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    time_granularity: str = "Täglich",
    spending_view: str = "Absolut",
    top_view: str = "Menge",
    top_limit: int = 20,
):
    return dashboard_service.get_vue_dashboard_payload(
        retailer=retailer,
        start_date=start_date,
        end_date=end_date,
        time_granularity=time_granularity,
        spending_view=spending_view,
        top_view=top_view,
        top_limit=top_limit,
    ).to_dict()
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_api_ui_dashboard.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
 git add frontend/schema.py api/services/dashboard_service.py api/routes/dashboard.py api/main.py tests/test_api_ui_dashboard.py
git commit -m "feat: add vue dashboard payload endpoint"
```

---

### Task 2: Vue App Scaffold and API Client

**Files:**
- Create: `web/package.json`
- Create: `web/index.html`
- Create: `web/vite.config.ts`
- Create: `web/tsconfig.json`
- Create: `web/src/main.ts`
- Create: `web/src/types/dashboard.ts`
- Create: `web/src/api/dashboard.ts`
- Create: `web/src/api/dashboard.spec.ts`

**Interfaces:**
- Consumes: the JSON contract from `GET /ui/dashboard`
- Produces: `fetchDashboard(filters): Promise<DashboardPayload>` and TypeScript types for the Vue UI

- [ ] **Step 1: Write the failing test**

```ts
import { describe, expect, it, vi } from "vitest";
import { fetchDashboard } from "./dashboard";

describe("fetchDashboard", () => {
  it("requests /ui/dashboard with filters", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ title: "Shopping Analyzer Dashboard", sections: [] }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await fetchDashboard({
      retailer: "lidl",
      start_date: "2024-01-01",
      end_date: "2024-01-31",
      time_granularity: "Monatlich",
      spending_view: "Absolut",
      top_view: "Menge",
      top_limit: 10,
    });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock.mock.calls[0][0]).toContain("/ui/dashboard");
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd web && pnpm test -- --run src/api/dashboard.spec.ts`

Expected: FAIL because the `web/` app and `fetchDashboard` do not exist yet.

- [ ] **Step 3: Write the minimal implementation**

```ts
// web/src/types/dashboard.ts
export type DashboardSectionKind = "metrics" | "chart" | "table";

export interface DashboardSection {
  kind: DashboardSectionKind;
  title: string;
  items: Array<Record<string, unknown>>;
}

export interface DashboardPayload {
  title: string;
  sections: DashboardSection[];
}

// web/src/api/dashboard.ts
import type { DashboardPayload } from "../types/dashboard";

export async function fetchDashboard(filters: Record<string, string | number | undefined>): Promise<DashboardPayload> {
  const baseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== "") params.set(key, String(value));
  });
  const response = await fetch(`${baseUrl}/ui/dashboard?${params.toString()}`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return (await response.json()) as DashboardPayload;
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd web && pnpm test -- --run src/api/dashboard.spec.ts`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add web/package.json web/index.html web/vite.config.ts web/tsconfig.json web/src/main.ts web/src/types/dashboard.ts web/src/api/dashboard.ts web/src/api/dashboard.spec.ts
git commit -m "feat: scaffold vue dashboard client"
```

---

### Task 3: Vue Dashboard Page and Panels

**Files:**
- Create: `web/src/App.vue`
- Create: `web/src/composables/useDashboard.ts`
- Create: `web/src/components/DashboardPage.vue`
- Create: `web/src/components/DashboardFilterBar.vue`
- Create: `web/src/components/DashboardSection.vue`
- Create: `web/src/components/KpiRow.vue`
- Create: `web/src/components/TrendChartPanel.vue`
- Create: `web/src/components/WeekdayPanel.vue`
- Create: `web/src/components/TopItemsPanel.vue`
- Create: `web/src/components/DashboardSkeleton.vue`
- Create: `web/src/components/__tests__/DashboardPage.spec.ts`

**Interfaces:**
- Consumes: `DashboardPayload` from `web/src/types/dashboard.ts`
- Produces: the visible dashboard page and section renderers

- [ ] **Step 1: Write the failing test**

```ts
import { mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";
import DashboardPage from "../DashboardPage.vue";

it("renders dashboard sections from the API payload", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
    ok: true,
    json: async () => ({
      title: "Shopping Analyzer Dashboard",
      sections: [
        { kind: "metrics", title: "Kennzahlen", items: [{ label: "Ausgaben gesamt", value: "€10.00" }] },
      ],
    }),
  }));

  const wrapper = mount(DashboardPage);
  await wrapper.vm.$nextTick();

  expect(wrapper.text()).toContain("Kennzahlen");
  expect(wrapper.text()).toContain("Ausgaben gesamt");
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd web && pnpm test -- --run src/components/__tests__/DashboardPage.spec.ts`

Expected: FAIL because the Vue page/components do not exist yet.

- [ ] **Step 3: Write the minimal implementation**

```vue
<!-- web/src/components/DashboardPage.vue -->
<script setup lang="ts">
import { onMounted, ref } from "vue";
import { fetchDashboard } from "../api/dashboard";
import type { DashboardPayload } from "../types/dashboard";

const payload = ref<DashboardPayload | null>(null);

onMounted(async () => {
  payload.value = await fetchDashboard({});
});
</script>

<template>
  <div v-if="payload">
    <h1>{{ payload.title }}</h1>
    <section v-for="section in payload.sections" :key="section.title">
      <h2>{{ section.title }}</h2>
    </section>
  </div>
</template>
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd web && pnpm test -- --run src/components/__tests__/DashboardPage.spec.ts`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add web/src/App.vue web/src/composables/useDashboard.ts web/src/components/*.vue web/src/components/__tests__/DashboardPage.spec.ts
git commit -m "feat: add vue dashboard page and panels"
```

---

### Task 4: Documentation and Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/architecture/frontend-transition.md`
- Create: `web/README.md`

**Interfaces:**
- Consumes: the final Vue frontend structure and the `/ui/dashboard` API contract
- Produces: updated onboarding docs and run instructions

- [ ] **Step 1: Write the failing test**

```bash
grep -n "VITE_API_BASE_URL\|web/\|ui/dashboard" README.md docs/architecture/frontend-transition.md web/README.md
```

Expected: the run instructions and endpoint references should be present after the documentation changes.

- [ ] **Step 2: Run the test to verify it fails**

Run: `grep -n "VITE_API_BASE_URL\|web/\|ui/dashboard" README.md docs/architecture/frontend-transition.md web/README.md`

Expected: initially missing or incomplete references before the docs update.

- [ ] **Step 3: Write the minimal implementation**

```md
## Vue Dashboard

Run the Vue frontend:

```bash
cd web
 pnpm install
 pnpm dev
```

Set `VITE_API_BASE_URL` to point at the FastAPI backend.
```

- [ ] **Step 4: Run the verification commands**

Run:

```bash
.venv/bin/python -m pytest
 cd web && pnpm test
 cd web && pnpm build
```

Expected: backend tests pass, frontend unit tests pass, production build succeeds.

- [ ] **Step 5: Commit**

```bash
git add README.md docs/architecture/frontend-transition.md web/README.md
git commit -m "docs: add vue dashboard onboarding"
```
