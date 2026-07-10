# Bar-Click → Receipt Modal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Click a bar in the D3 trend chart to open a modal showing all receipts with full item detail for that period.

**Architecture:** Backend adds `GET /receipts/by-date` endpoint (store → service → route, following the existing `by-item` pattern). Frontend adds a `ReceiptListModal.vue` component, a `fetchReceiptsByDateRange()` API client, a click handler on D3 bar `<rect>` elements, and event wiring through `TrendChartPanel` → `DashboardPage`.

**Tech Stack:** Python/FastAPI, SQLite, Vue 3, D3.js, Vitest (jsdom), pytest

## Global Constraints
- Follow TDD: write failing test first, then implement, then verify
- Use project venv for Python: `./.venv/bin/python -m pytest -q tests/test_api_receipts.py`
- Use `corepack pnpm` for frontend commands
- Bare array response for `GET /receipts/by-date` (same as `by-item`)
- Receipt dict shape must match existing canonical format
- German month names hardcoded (no locale API) for period labels
- No new dependencies

---

### Task 1: Backend — Store, Service, and Route

**Files:**
- Modify: `storage/sqlite_receipt_store.py` — add `list_receipts_by_date_range()` staticmethod
- Modify: `api/services/receipt_service.py` — add `list_receipts_by_date_range()` function
- Modify: `api/routes/receipts.py` — add `GET /receipts/by-date` route
- Test: `tests/test_api_receipts.py`

**Interfaces:**
- Consumes: existing `_map_purchase_to_receipt_dict`, `_connect_sqlite`, `PurchaseDomain`, `StoreDomain`
- Produces:
  - `SqliteReceiptStore.list_receipts_by_date_range(start_date: str, end_date: str, retailer: Optional[str] = None) -> list[dict[str, Any]]`
  - `receipt_service.list_receipts_by_date_range(start_date: str, end_date: str, retailer: Optional[str] = None) -> list[dict[str, Any]]`
  - `GET /receipts/by-date?start_date=...&end_date=...&retailer=...` → bare array of receipt dicts

- [ ] **Step 1: Add failing backend tests**

Append to `tests/test_api_receipts.py`:

```python
def test_receipts_by_date_returns_receipts_in_range(monkeypatch):
    from fastapi.testclient import TestClient
    from api.main import app
    from api.services import receipt_service

    class FakeStore:
        @staticmethod
        def list_receipts_by_date_range(start_date, end_date, retailer=None):
            return [
                {"id": "r1", "purchase_date": "2024-01-15", "total_price": 10.0, "items": [], "payment_methods": []},
                {"id": "r2", "purchase_date": "2024-01-20", "total_price": 20.0, "items": [], "payment_methods": []},
            ]

    monkeypatch.setattr(receipt_service, "SqliteReceiptStore", FakeStore)

    response = TestClient(app).get("/receipts/by-date", params={"start_date": "2024-01-01", "end_date": "2024-01-31"})

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == "r1"
    assert data[1]["id"] == "r2"


def test_receipts_by_date_empty_range(monkeypatch):
    from fastapi.testclient import TestClient
    from api.main import app
    from api.services import receipt_service

    class FakeStore:
        @staticmethod
        def list_receipts_by_date_range(start_date, end_date, retailer=None):
            return []

    monkeypatch.setattr(receipt_service, "SqliteReceiptStore", FakeStore)

    response = TestClient(app).get("/receipts/by-date", params={"start_date": "2023-01-01", "end_date": "2023-01-31"})

    assert response.status_code == 200
    assert response.json() == []


def test_receipts_by_date_filters_by_retailer(monkeypatch):
    from fastapi.testclient import TestClient
    from api.main import app
    from api.services import receipt_service

    class FakeStore:
        @staticmethod
        def list_receipts_by_date_range(start_date, end_date, retailer=None):
            assert retailer == "lidl"
            return [{"id": "r1", "retailer": "lidl", "purchase_date": "2024-01-15", "total_price": 10.0, "items": [], "payment_methods": []}]

    monkeypatch.setattr(receipt_service, "SqliteReceiptStore", FakeStore)

    response = TestClient(app).get("/receipts/by-date", params={"start_date": "2024-01-01", "end_date": "2024-01-31", "retailer": "lidl"})

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "r1"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `./.venv/bin/python -m pytest -q tests/test_api_receipts.py -k "by_date"`

Expected: FAIL — `SqliteReceiptStore.list_receipts_by_date_range` not defined, `receipt_service.list_receipts_by_date_range` not defined, route not found

- [ ] **Step 3: Add store method `list_receipts_by_date_range()`**

In `storage/sqlite_receipt_store.py`, after `list_receipts_by_item()` (after line 266), add:

```python
    @staticmethod
    def list_receipts_by_date_range(
        start_date: str,
        end_date: str,
        retailer: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        with closing(_connect_sqlite()) as connection:
            params: list[Any] = []
            where_clauses: list[str] = []

            if retailer:
                where_clauses.append("store.retailer_code = ?")
                params.append(retailer.lower())

            where_clauses.append("purchase.purchase_date >= ?")
            params.append(start_date)

            where_clauses.append("purchase.purchase_date <= ?")
            params.append(end_date)

            rows = connection.execute(
                f"""
                SELECT purchase.id FROM purchase
                JOIN store ON store.id = purchase.store_id
                WHERE {' AND '.join(where_clauses)}
                ORDER BY purchase.purchase_date DESC, purchase.id
                """,
                params,
            ).fetchall()

            purchase_domain = PurchaseDomain(connection)
            store_domain = StoreDomain(connection)
            receipts: list[dict[str, Any]] = []
            for row in rows:
                purchase = purchase_domain.find_by_id(str(row["id"]))
                if purchase is None:
                    continue
                actual_retailer = retailer or ""
                if purchase.store_id is not None:
                    store = store_domain.find_by_id(purchase.store_id)
                    if store is not None:
                        actual_retailer = store.retailer_code
                receipt = _map_purchase_to_receipt_dict(purchase, actual_retailer, connection)
                receipts.append(receipt)

            return receipts
```

- [ ] **Step 4: Add service function `list_receipts_by_date_range()`**

In `api/services/receipt_service.py`, after `list_receipts_by_item()` (line 61), add:

```python
def list_receipts_by_date_range(
    start_date: str,
    end_date: str,
    retailer: Optional[str] = None,
) -> list[dict[str, Any]]:
    return SqliteReceiptStore.list_receipts_by_date_range(
        start_date=start_date,
        end_date=end_date,
        retailer=retailer,
    )
```

- [ ] **Step 5: Add route `GET /receipts/by-date`**

In `api/routes/receipts.py`, after the `read_receipts_by_item` function (the `/by-item` route), add:

```python
@router.get("/by-date")
def read_receipts_by_date(
    start_date: str,
    end_date: str,
    retailer: Optional[str] = None,
) -> list[dict]:
    return list_receipts_by_date_range(
        start_date=start_date,
        end_date=end_date,
        retailer=retailer,
    )
```

And add the import at the top of the file:
```python
from api.services.receipt_service import (
    list_receipts,
    list_receipts_by_date_range,
    list_receipts_by_item,
    # ... keep existing
)
```

Alternatively, check the existing import and add `list_receipts_by_date_range` to it.

- [ ] **Step 6: Run tests to verify they pass**

Run: `./.venv/bin/python -m pytest -q tests/test_api_receipts.py -k "by_date"`

Expected: 3 PASS

Also run full suite: `./.venv/bin/python -m pytest -q`

Expected: all existing + 3 new tests pass

---

### Task 2: Frontend — API Client + ReceiptListModal

**Files:**
- Modify: `web/src/api/dashboard.ts` — add `fetchReceiptsByDateRange()`
- Create: `web/src/components/ReceiptListModal.vue` — new modal component
- Create: `web/src/components/__tests__/ReceiptListModal.spec.ts` — component tests

**Interfaces:**
- Consumes: existing `ReceiptModal.vue` pattern, `dashboard.ts` API client pattern
- Produces:
  - `fetchReceiptsByDateRange(startDate: string, endDate: string, retailer?: string) → Promise<Record<string, unknown>[]>`
  - `ReceiptListModal` props: `startDate: string`, `endDate: string`, `visible: boolean`, `retailer?: string`
  - `ReceiptListModal` emits: `close`

- [ ] **Step 1: Add test for `ReceiptListModal`**

Create `web/src/components/__tests__/ReceiptListModal.spec.ts`:

```typescript
// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it, vi, afterEach } from "vitest";

import ReceiptListModal from "../ReceiptListModal.vue";

afterEach(() => {
  vi.unstubAllGlobals();
});

function stubFetch(data: unknown) {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({ ok: true, json: async () => data }),
  );
}

describe("ReceiptListModal", () => {
  it("renders receipt details from API response", async () => {
    stubFetch([
      {
        id: "r1",
        retailer: "lidl",
        purchase_date: "2024-01-15",
        store: "Lidl München",
        address: { street: "Bahnhofstr.", street_no: "1", zip: "80335", city: "München" },
        total_price: 42.50,
        items: [{ name: "Apfel", quantity: 3, unit: "stk", price: 1.99 }],
        payment_methods: [{ method: "EC-Karte", amount: 42.50 }],
      },
    ]);

    const wrapper = mount(ReceiptListModal, {
      props: { startDate: "2024-01-01", endDate: "2024-01-31", visible: true },
    });

    // Wait for async watch + fetch + render
    await wrapper.vm.$nextTick();
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain("Januar 2024");
    expect(wrapper.text()).toContain("Lidl München");
    expect(wrapper.text()).toContain("€42.50");
    expect(wrapper.text()).toContain("3");
    expect(wrapper.text()).toContain("Apfel");
    expect(wrapper.text()).toContain("1.99");
  });

  it("shows loading state while fetching", () => {
    // Never resolve the fetch
    vi.stubGlobal("fetch", vi.fn().mockReturnValue(new Promise(() => {})));

    const wrapper = mount(ReceiptListModal, {
      props: { startDate: "2024-01-01", endDate: "2024-01-31", visible: true },
    });

    expect(wrapper.text()).toContain("Lade Kassenzettel");
  });

  it("shows empty state when no receipts found", async () => {
    stubFetch([]);

    const wrapper = mount(ReceiptListModal, {
      props: { startDate: "2024-01-01", endDate: "2024-01-31", visible: true },
    });

    await wrapper.vm.$nextTick();
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain("Keine Kassenzettel gefunden");
  });

  it("emits close when background overlay is clicked", async () => {
    stubFetch([]);

    const wrapper = mount(ReceiptListModal, {
      props: { startDate: "2024-01-01", endDate: "2024-01-31", visible: true },
    });

    await wrapper.vm.$nextTick();
    await wrapper.vm.$nextTick();

    await wrapper.find(".fixed.inset-0").trigger("click");
    expect(wrapper.emitted("close")).toHaveLength(1);
  });

  it("computes monthly label from date range", async () => {
    stubFetch([{
      id: "r1", retailer: "lidl", purchase_date: "2024-01-15",
      total_price: 10.0, items: [], payment_methods: [],
    }]);

    const wrapper = mount(ReceiptListModal, {
      props: { startDate: "2024-01-01", endDate: "2024-01-31", visible: true },
    });

    await wrapper.vm.$nextTick();
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain("Januar 2024");
  });

  it("computes daily label from date range", async () => {
    stubFetch([{
      id: "r1", retailer: "lidl", purchase_date: "2024-01-15",
      total_price: 10.0, items: [], payment_methods: [],
    }]);

    const wrapper = mount(ReceiptListModal, {
      props: { startDate: "2024-01-15", endDate: "2024-01-15", visible: true },
    });

    await wrapper.vm.$nextTick();
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain("15. Januar 2024");
  });

  it("computes yearly label from date range", async () => {
    stubFetch([{
      id: "r1", retailer: "lidl", purchase_date: "2024-06-15",
      total_price: 10.0, items: [], payment_methods: [],
    }]);

    const wrapper = mount(ReceiptListModal, {
      props: { startDate: "2024-01-01", endDate: "2024-12-31", visible: true },
    });

    await wrapper.vm.$nextTick();
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain("2024");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `corepack pnpm test -- --run src/components/__tests__/ReceiptListModal.spec.ts`

Expected: FAIL — `ReceiptListModal.vue` not found

- [ ] **Step 3: Add `fetchReceiptsByDateRange()` to dashboard.ts**

In `web/src/api/dashboard.ts`, after `fetchReceiptsByItem()` (line 34), add:

```typescript
export async function fetchReceiptsByDateRange(
  startDate: string,
  endDate: string,
  retailer?: string,
): Promise<Array<Record<string, unknown>>> {
  const baseUrl = import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL;
  const url = new URL("/receipts/by-date", baseUrl);
  url.searchParams.set("start_date", startDate);
  url.searchParams.set("end_date", endDate);
  if (retailer) url.searchParams.set("retailer", retailer);
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Failed to fetch receipts: ${res.status}`);
  return res.json();
}
```

- [ ] **Step 4: Create `ReceiptListModal.vue`**

Create `web/src/components/ReceiptListModal.vue`:

```vue
<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { fetchReceiptsByDateRange } from "../api/dashboard";

const props = defineProps<{
  startDate: string;
  endDate: string;
  visible: boolean;
  retailer?: string;
}>();

const emit = defineEmits<{
  (e: "close"): void;
}>();

const loading = ref(false);
const receipts = ref<Array<Record<string, unknown>>>([]);
const currentIndex = ref(0);
const requestTicket = ref(0);

const monthNames = [
  "Januar", "Februar", "März", "April", "Mai", "Juni",
  "Juli", "August", "September", "Oktober", "November", "Dezember",
];

const periodLabel = computed(() => {
  const s = props.startDate;
  const e = props.endDate;
  if (s === e) {
    const [y, m, d] = s.split("-").map(Number);
    return `${d}. ${monthNames[m - 1]} ${y}`;
  }
  if (s.endsWith("-01-01") && e.endsWith("-12-31")) {
    return s.slice(0, 4);
  }
  const [y, m] = s.split("-").map(Number);
  return `${monthNames[m - 1]} ${y}`;
});

watch(
  () => props.visible,
  async (show) => {
    if (!show) return;
    loading.value = true;
    receipts.value = [];
    currentIndex.value = 0;
    const ticket = ++requestTicket.value;
    try {
      const result = await fetchReceiptsByDateRange(props.startDate, props.endDate, props.retailer);
      if (ticket === requestTicket.value) receipts.value = result;
    } finally {
      if (ticket === requestTicket.value) loading.value = false;
    }
  },
);

const current = computed(() => receipts.value[currentIndex.value] ?? {});

function prev() {
  if (currentIndex.value > 0) currentIndex.value--;
}

function next() {
  if (currentIndex.value < receipts.value.length - 1) currentIndex.value++;
}

function text(value: unknown) {
  return value == null ? "-" : String(value);
}

function currency(value: unknown) {
  const numeric = typeof value === "number" ? value : Number(value ?? 0);
  return Number.isFinite(numeric) ? `\u20AC${numeric.toFixed(2)}` : "-";
}

function retailerLabel(value: unknown): string {
  if (value === "lidl") return "Lidl";
  if (value === "rewe") return "REWE";
  return text(value);
}

function addressText(addr: unknown): string {
  if (!addr || typeof addr !== "object") return "";
  const a = addr as Record<string, unknown>;
  const parts = [
    a.street && a.street_no ? `${a.street} ${a.street_no}` : a.street || "",
    a.zip && a.city ? `${a.zip} ${a.city}` : a.city || a.zip || "",
  ].filter(Boolean);
  return parts.join(", ");
}
</script>

<template>
  <Teleport to="body">
    <div
      v-if="visible"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      @click.self="emit('close')"
    >
      <div class="flex max-h-[85vh] w-full max-w-2xl flex-col rounded-2xl border border-slate-200 bg-white shadow-2xl">
        <!-- Header -->
        <div class="flex items-center justify-between border-b border-slate-200 px-5 py-4">
          <h2 class="text-lg font-semibold tracking-tight text-slate-900">
            {{ periodLabel }} — Kassenzettel
          </h2>
          <button
            type="button"
            class="rounded-lg p-1.5 text-slate-400 transition hover:bg-slate-100 hover:text-slate-600"
            @click="emit('close')"
          >
            <svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
              <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
            </svg>
          </button>
        </div>

        <!-- Loading -->
        <div v-if="loading" class="flex items-center justify-center py-16 text-sm text-slate-500">
          Lade Kassenzettel...
        </div>

        <!-- No receipts -->
        <div v-else-if="receipts.length === 0" class="flex items-center justify-center py-16 text-sm text-slate-500">
          Keine Kassenzettel gefunden.
        </div>

        <!-- Receipt content -->
        <template v-else>
          <!-- Navigation -->
          <div v-if="receipts.length > 1" class="flex items-center justify-between border-b border-slate-100 px-5 py-2.5">
            <button
              type="button"
              :disabled="currentIndex <= 0"
              class="rounded-lg border border-slate-300 bg-white px-3 py-1 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
              @click="prev"
            >
              Zurück
            </button>
            <span class="text-sm text-slate-500">
              {{ currentIndex + 1 }} von {{ receipts.length }}
            </span>
            <button
              type="button"
              :disabled="currentIndex >= receipts.length - 1"
              class="rounded-lg border border-slate-300 bg-white px-3 py-1 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
              @click="next"
            >
              Weiter
            </button>
          </div>

          <!-- Receipt detail -->
          <div class="overflow-y-auto px-5 py-4">
            <div class="mb-4 grid grid-cols-4 gap-3 text-sm">
              <div>
                <p class="text-xs font-medium uppercase tracking-[0.22em] text-slate-500">Händler</p>
                <p class="mt-0.5 font-bold uppercase text-slate-900">{{ retailerLabel(current.retailer) }}</p>
              </div>
              <div>
                <p class="text-xs font-medium uppercase tracking-[0.22em] text-slate-500">Markt</p>
                <p class="mt-0.5 font-medium text-slate-900">{{ text(current.store) }}</p>
              </div>
              <div>
                <p class="text-xs font-medium uppercase tracking-[0.22em] text-slate-500">Adresse</p>
                <p class="mt-0.5 text-xs text-slate-500">{{ addressText(current.address) }}</p>
              </div>
              <div class="text-right">
                <p class="text-xs font-medium uppercase tracking-[0.22em] text-slate-500">Datum</p>
                <p class="mt-0.5 font-medium text-slate-900">{{ text(current.purchase_date) }}</p>
              </div>
            </div>

            <div class="border-t border-slate-200 pt-3">
              <h3 class="mb-2 text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">Artikel</h3>
              <div class="divide-y divide-slate-100">
                <div
                  v-for="(item, ii) in (current.items as Array<Record<string, unknown>> || [])"
                  :key="ii"
                  class="flex items-center justify-between gap-3 px-3 py-2 text-sm"
                >
                  <span class="text-slate-700">{{ text(item.name) }}</span>
                  <span class="shrink-0 text-slate-600">
                    {{ Number(item.quantity)?.toLocaleString("de-DE") }} {{ text(item.unit) }} × {{ currency(item.price) }}
                  </span>
                </div>
              </div>
            </div>

            <div class="mt-4 border-t border-slate-200 pt-3 text-right">
              <span class="text-xs font-medium uppercase tracking-[0.22em] text-slate-500">Gesamt</span>
              <p class="text-xl font-semibold text-slate-900">{{ currency(current.total_price) }}</p>
            </div>
          </div>
        </template>
      </div>
    </div>
  </Teleport>
</template>
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `corepack pnpm test -- --run src/components/__tests__/ReceiptListModal.spec.ts`

Expected: PASS (6 tests)

- [ ] **Step 6: Run full frontend test suite to check for regressions**

Run: `corepack pnpm test -- --run`

Expected: all existing + 6 new tests pass

---

### Task 3: Frontend — Chart Click Handler + Event Wiring

**Files:**
- Modify: `web/src/components/TrendBarChart.vue` — add `defineEmits`, D3 click handler on `<rect>`
- Modify: `web/src/components/TrendChartPanel.vue` — add `defineEmits`, forward `select-period` from TrendBarChart
- Modify: `web/src/components/DashboardPage.vue` — add `selectedPeriod` ref, `ReceiptListModal`, handle `select-period` event
- Modify: `web/src/components/__tests__/DashboardPanels.spec.ts` — add TrendBarChart click test
- Modify: `web/src/components/__tests__/DashboardPage.spec.ts` — add modal rendering in SSR test

**Interfaces:**
- Consumes: `ReceiptListModal.vue` (Task 2), `fetchReceiptsByDateRange` (Task 2)
- Produces:
  - TrendBarChart emit `select-period` with `{ startDate: string, endDate: string, label: string }`
  - TrendChartPanel emit `select-period` (forwarded)
  - DashboardPage: `selectedPeriod` ref → `ReceiptListModal` binding
- Date boundary computation:
  - daily (`"2024-01-15"`): start = end = period string, label = `"15. Januar 2024"`
  - monthly (`"2024-01"`): start = `"2024-01-01"`, end = last day of month, label = `"Januar 2024"`
  - yearly (`"2024"`): start = `"2024-01-01"`, end = `"2024-12-31"`, label = `"2024"`

- [ ] **Step 1: Add click test for TrendBarChart**

In `web/src/components/__tests__/DashboardPanels.spec.ts`, inside the `describe("dashboard panels")` block, add:

```typescript
it("emits select-period when a bar is clicked", async () => {
  const wrapper = mount(TrendBarChart, {
    props: {
      granularity: "Monatlich",
      items: [{ period: "2024-01", total_spent: 10, receipt_count: 1 }],
    },
  });

  const rect = wrapper.find("rect.bar");
  await rect.trigger("click");

  expect(wrapper.emitted("select-period")).toHaveLength(1);
  expect(wrapper.emitted("select-period")![0]).toEqual([
    { startDate: "2024-01-01", endDate: "2024-01-31", label: "Januar 2024" },
  ]);
});

it("emits select-period with daily boundaries", async () => {
  const wrapper = mount(TrendBarChart, {
    props: {
      granularity: "Täglich",
      items: [{ period: "2024-01-15", total_spent: 10, receipt_count: 1 }],
    },
  });

  const rect = wrapper.find("rect.bar");
  await rect.trigger("click");

  expect(wrapper.emitted("select-period")![0]).toEqual([
    { startDate: "2024-01-15", endDate: "2024-01-15", label: "15. Januar 2024" },
  ]);
});

it("emits select-period with yearly boundaries", async () => {
  const wrapper = mount(TrendBarChart, {
    props: {
      granularity: "Jährlich",
      items: [{ period: "2024", total_spent: 100, receipt_count: 12 }],
    },
  });

  const rect = wrapper.find("rect.bar");
  await rect.trigger("click");

  expect(wrapper.emitted("select-period")![0]).toEqual([
    { startDate: "2024-01-01", endDate: "2024-12-31", label: "2024" },
  ]);
});
```

And add `TrendBarChart` to the imports at the top of the test file:
```typescript
import TrendBarChart from "../TrendBarChart.vue";
```

- [ ] **Step 2: Run test to verify it fails**

Run: `corepack pnpm test -- --run src/components/__tests__/DashboardPanels.spec.ts -t "emits select-period"`

Expected: FAIL — TrendBarChart has no `defineEmits`

- [ ] **Step 3: Add `defineEmits` and click handler to TrendBarChart.vue**

In `<script setup>`, after the `props` definition (line 12), add:

```typescript
const emit = defineEmits<{
  (e: "select-period", payload: { startDate: string; endDate: string; label: string }): void;
}>();
```

Then, inside `drawChart()`, where `<rect>` elements are created (around line 132), replace the existing `mainSvg.selectAll("rect.bar")` chain with one that adds a click handler. The new code (replacing lines 132-144):

```typescript
  mainSvg.selectAll("rect.bar")
    .data(items)
    .enter()
    .append("rect")
    .attr("class", "bar")
    .attr("x", (_d: unknown, i: number) => xScale(String(i))!)
    .attr("y", (d: Record<string, unknown>) => yScale(amount(d.total_spent)))
    .attr("width", xScale.bandwidth()!)
    .attr("height", (d: Record<string, unknown>) => yScale(0) - yScale(amount(d.total_spent)))
    .attr("fill", "#6366f1")
    .attr("rx", 4)
    .on("click", (_event: unknown, d: Record<string, unknown>) => {
      emit("select-period", computePeriod(String(d.period ?? ""), props.granularity));
    })
    .append("title")
    .text((d: Record<string, unknown>) => `€${amount(d.total_spent).toFixed(2)}\n${amount(d.receipt_count)} Belege`);
```

Then, add the `computePeriod` helper function inside `<script setup>` (before `drawChart`):

```typescript
function computePeriod(period: string, granularity: string): { startDate: string; endDate: string; label: string } {
  const monthNames = [
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember",
  ];
  if (granularity === "Täglich") {
    const [y, m, d] = period.split("-").map(Number);
    return {
      startDate: period,
      endDate: period,
      label: `${d}. ${monthNames[m - 1]} ${y}`,
    };
  }
  if (granularity === "Monatlich") {
    const [y, m] = period.split("-").map(Number);
    const lastDay = new Date(y, m, 0).getDate();
    return {
      startDate: `${period}-01`,
      endDate: `${period}-${String(lastDay).padStart(2, "0")}`,
      label: `${monthNames[m - 1]} ${y}`,
    };
  }
  // Jährlich
  return {
    startDate: `${period}-01-01`,
    endDate: `${period}-12-31`,
    label: period,
  };
}
```

- [ ] **Step 4: Run bar click tests to verify they pass**

Run: `corepack pnpm test -- --run src/components/__tests__/DashboardPanels.spec.ts -t "emits select-period"`

Expected: 3 PASS

- [ ] **Step 5: Add `select-period` forwarding to TrendChartPanel**

In `web/src/components/TrendChartPanel.vue`, add `defineEmits` after the `defineProps` (line 11):

```typescript
const emit = defineEmits<{
  (e: "select-period", payload: { startDate: string; endDate: string; label: string }): void;
}>();
```

Then in the template, add `@select-period` listener to the `<TrendBarChart>` element (line 120-125):

```vue
        <TrendBarChart
          v-if="group.items.length > 0"
          :items="group.items"
          :granularity="chartGranularity"
          :monthLabels="monthLabels"
          @select-period="emit('select-period', $event)"
        />
```

- [ ] **Step 6: Add `ReceiptListModal` and event handling to DashboardPage**

In `web/src/components/DashboardPage.vue`:

First, add the import for `ReceiptListModal` (after line 16):
```typescript
import ReceiptListModal from "./ReceiptListModal.vue";
```

Then, add the `selectedPeriod` ref (after line 43 `const selectedArticle`):
```typescript
const selectedPeriod = ref<{ startDate: string; endDate: string; label: string } | null>(null);
```

Add the handler function (after `onCloseReceiptModal` at line 72):
```typescript
function onSelectPeriod(payload: { startDate: string; endDate: string; label: string }) {
  selectedPeriod.value = payload;
}

function onClosePeriodModal() {
  selectedPeriod.value = null;
}
```

Wire the event on `<TrendChartPanel>` (line 172-176):
```vue
              <div class="mb-8">
                <TrendChartPanel
                  :items="section.items"
                  :spending-view="spendingView"
                  :time-granularity="timeGranularity"
                  @select-period="onSelectPeriod"
                />
              </div>
```

Add `ReceiptListModal` after the existing `ReceiptModal` (after line 226):
```vue
  <ReceiptListModal
    :start-date="selectedPeriod?.startDate ?? ''"
    :end-date="selectedPeriod?.endDate ?? ''"
    :retailer="retailer"
    :visible="!!selectedPeriod"
    @close="onClosePeriodModal"
  />
```

- [ ] **Step 7: Verify SSR tests still pass (DashboardPage uses renderToString)**

Run: `corepack pnpm test -- --run src/components/__tests__/DashboardPage.spec.ts`

Expected: all 5 PASS. The SSR test renders DashboardPage to HTML string; the new `ReceiptListModal` starts hidden (visible=false), so it shouldn't appear in SSR output, and no runtime errors should occur.

- [ ] **Step 8: Run full frontend test suite**

Run: `corepack pnpm test -- --run`

Expected: all existing + 9 new tests pass

- [ ] **Step 9: Verify frontend build**

Run: `corepack pnpm build`

Expected: Build succeeds, no TypeScript errors with new emits/imports

---

### Task 4: Final Verification

- [ ] **Step 1: Run full backend test suite**

Run: `./.venv/bin/python -m pytest -q`

Expected: all tests pass (420+)

- [ ] **Step 2: Run full frontend test suite**

Run: `corepack pnpm test -- --run`

Expected: all tests pass (60+)

- [ ] **Step 3: Run frontend build**

Run: `corepack pnpm build`

Expected: build succeeds
