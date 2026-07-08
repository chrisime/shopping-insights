# Article Receipt Modal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Click an article in TopItemsPanel to see full receipts containing that article in a modal, with the article highlighted.

**Architecture:** New backend endpoint joins `purchase_item → purchase → store` by item name, returns full receipt dicts with `matched` flag on items. Frontend modal fetches and displays receipts with prev/next navigation.

**Tech Stack:** Python/FastAPI, SQLite, Vue 3, Tailwind CSS, Oruga UI

## Global Constraints

- No new dependencies
- Backend: 416 pytest suite must pass
- Frontend: 38 vitest suite must pass, `corepack pnpm build` must pass
- Follow existing code style (no comments, no emoji)
- SQL queries use raw strings for LIKE (query builder has no LIKE support)

---

### Task 1: Backend — Add `find_purchase_ids_by_item_name` to PurchaseItemDomain

**Files:**
- Modify: `storage/sqlite_domains.py` (add method to `PurchaseItemDomain`)

**Produces:**
- `PurchaseItemDomain.find_purchase_ids_by_item_name(name: str) -> list[str]`

- [ ] **Step 1: Add the method to PurchaseItemDomain**

After `find_by_purchase_id`, add:

```python
def find_purchase_ids_by_item_name(self, name: str) -> list[str]:
    rows = self.connection.execute(
        "SELECT DISTINCT purchase_id FROM purchase_item WHERE UPPER(name) LIKE UPPER(?)",
        (f"%{name}%",),
    ).fetchall()

    return [str(row["purchase_id"]) for row in rows]
```

- [ ] **Step 2: Run backend tests**

```bash
./.venv/bin/python3 -m pytest -q
```
Expected: 416 passed

- [ ] **Step 3: Commit**

```bash
git add storage/sqlite_domains.py
git commit -m "feat: add find_purchase_ids_by_item_name to PurchaseItemDomain"
```

### Task 2: Backend — Add `list_receipts_by_item` to SqliteReceiptStore

**Files:**
- Modify: `storage/sqlite_receipt_store.py`

**Consumes:** `PurchaseItemDomain.find_purchase_ids_by_item_name`
**Produces:** `SqliteReceiptStore.list_receipts_by_item(name, retailer, start_date, end_date) -> list[dict]`

- [ ] **Step 1: Add `list_receipts_by_item` static method**

Before `persist_receipts` (or after `list_receipts`), add:

```python
@staticmethod
def list_receipts_by_item(
    name: str,
    retailer: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> list[dict[str, Any]]:
    with closing(_connect_sqlite()) as connection:
        purchase_item_domain = PurchaseItemDomain(connection)
        purchase_ids = purchase_item_domain.find_purchase_ids_by_item_name(name)

        if not purchase_ids:
            return []

        placeholders = ",".join("?" for _ in purchase_ids)
        params: list[Any] = purchase_ids[:]
        where_clauses = [f"purchase.id IN ({placeholders})"]

        if retailer:
            where_clauses.append("store.retailer_code = ?")
            params.append(retailer.lower())

        if start_date:
            where_clauses.append("purchase.purchase_date >= ?")
            params.append(start_date)

        if end_date:
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
        matched_name_upper = name.upper()
        receipts: list[dict[str, Any]] = []
        for row in rows:
            purchase = purchase_domain.find_by_id(str(row["id"]))
            if purchase is None:
                continue
            receipt = _map_purchase_to_receipt_dict(purchase, retailer or "", connection)
            for item in receipt["items"]:
                if str(item.get("name", "")).upper() == matched_name_upper:
                    item["matched"] = True
            receipts.append(receipt)

        return receipts
```

Add imports: `from typing import Optional, Any` at top of file (check if already imported).

- [ ] **Step 2: Run backend tests**

```bash
./.venv/bin/python3 -m pytest -q
```
Expected: 416 passed

- [ ] **Step 3: Commit**

```bash
git add storage/sqlite_receipt_store.py
git commit -m "feat: add list_receipts_by_item to SqliteReceiptStore"
```

### Task 3: Backend — New `list_receipts_by_item` service

**Files:**
- Modify: `api/services/receipt_service.py`

**Consumes:** `SqliteReceiptStore.list_receipts_by_item`

- [ ] **Step 1: Add service function**

At the end of `api/services/receipt_service.py`, add:

```python
def list_receipts_by_item(
    name: str,
    retailer: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> list[dict[str, Any]]:
    return SqliteReceiptStore.list_receipts_by_item(
        name=name,
        retailer=retailer,
        start_date=start_date,
        end_date=end_date,
    )
```

- [ ] **Step 2: Run backend tests**

```bash
./.venv/bin/python3 -m pytest -q
```
Expected: 416 passed

- [ ] **Step 3: Commit**

```bash
git add api/services/receipt_service.py
git commit -m "feat: add list_receipts_by_item service function"
```

### Task 4: Backend — New `/receipts/by-item` route

**Files:**
- Modify: `api/routes/receipts.py`

**Consumes:** `receipt_service.list_receipts_by_item`

- [ ] **Step 1: Add the endpoint**

In `api/routes/receipts.py`, update the import line and add the new endpoint:

Import:
```python
from api.services.receipt_service import get_receipt, get_receipt_items, get_receipt_payments, list_receipts, list_receipts_by_item
```

After `read_receipt_payments` (before the last line), add:

```python
@router.get("/by-item")
def read_receipts_by_item(
    name: str,
    retailer: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> list[dict]:
    return list_receipts_by_item(
        name=name,
        retailer=retailer,
        start_date=start_date,
        end_date=end_date,
    )
```

- [ ] **Step 2: Run backend tests**

```bash
./.venv/bin/python3 -m pytest -q
```
Expected: 416 passed

- [ ] **Step 3: Commit**

```bash
git add api/routes/receipts.py
git commit -m "feat: add GET /receipts/by-item endpoint"
```

### Task 5: Frontend — API function + ReceiptModal component

**Files:**
- Modify: `web/src/api/dashboard.ts`
- Create: `web/src/components/ReceiptModal.vue`

**Consumes:** Backend `/receipts/by-item` endpoint
**Produces:** `fetchReceiptsByItem` function, `ReceiptModal` component

- [ ] **Step 1: Add `fetchReceiptsByItem` to `web/src/api/dashboard.ts`**

Add after existing `fetchDashboard` or `exportReceiptsJson`:

```typescript
export async function fetchReceiptsByItem(
  name: string,
  retailer?: string,
): Promise<Array<Record<string, unknown>>> {
  const params = new URLSearchParams({ name });
  if (retailer) params.set("retailer", retailer);
  const res = await fetch(`/api/receipts/by-item?${params}`);
  if (!res.ok) throw new Error(`Failed to fetch receipts: ${res.status}`);
  return res.json();
}
```

- [ ] **Step 2: Create `web/src/components/ReceiptModal.vue`**

```vue
<script setup lang="ts">
import { ref, watch } from "vue";
import { fetchReceiptsByItem } from "../api/dashboard";

const props = defineProps<{
  articleName: string;
  retailer?: string;
  visible: boolean;
}>();

const emit = defineEmits<{
  (e: "close"): void;
}>();

const loading = ref(false);
const receipts = ref<Array<Record<string, unknown>>>([]);
const currentIndex = ref(0);

watch(
  () => props.visible,
  async (show) => {
    if (!show) return;
    loading.value = true;
    receipts.value = [];
    currentIndex.value = 0;
    try {
      receipts.value = await fetchReceiptsByItem(props.articleName, props.retailer);
    } finally {
      loading.value = false;
    }
  },
);

const current = ref<Record<string, unknown>>({});
watch(
  [receipts, currentIndex],
  () => {
    current.value = receipts.value[currentIndex.value] ?? {};
  },
  { immediate: true },
);

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

function isMatched(item: Record<string, unknown>): boolean {
  return item.matched === true;
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
            {{ articleName }} — Kassenzettel
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
            <div class="mb-4 grid grid-cols-3 gap-3 text-sm">
              <div>
                <span class="text-xs font-medium uppercase tracking-[0.22em] text-slate-500">Datum</span>
                <p class="mt-0.5 font-medium text-slate-900">{{ text(current.purchase_date) }}</p>
              </div>
              <div>
                <span class="text-xs font-medium uppercase tracking-[0.22em] text-slate-500">Markt</span>
                <p class="mt-0.5 font-medium text-slate-900">{{ text(current.store) }}</p>
              </div>
              <div>
                <span class="text-xs font-medium uppercase tracking-[0.22em] text-slate-500">Gesamt</span>
                <p class="mt-0.5 font-medium text-slate-900">{{ currency(current.total_price) }}</p>
              </div>
            </div>

            <div class="border-t border-slate-200 pt-3">
              <h3 class="mb-2 text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">Artikel</h3>
              <div class="divide-y divide-slate-100">
                <div
                  v-for="(item, ii) in (current.items as Array<Record<string, unknown>> || [])"
                  :key="ii"
                  class="flex items-center justify-between gap-3 px-3 py-2 text-sm"
                  :class="isMatched(item) ? '-mx-3 rounded-xl bg-amber-50 px-3 ring-1 ring-amber-300' : ''"
                >
                  <div class="flex items-center gap-2">
                    <span v-if="isMatched(item)" class="h-2 w-2 rounded-full bg-amber-400" />
                    <span :class="isMatched(item) ? 'font-semibold text-amber-900' : 'text-slate-700'">
                      {{ text(item.name) }}
                    </span>
                  </div>
                  <span class="shrink-0 text-slate-600">
                    {{ Number(item.quantity)?.toLocaleString("de-DE") }} {{ text(item.unit) }} × {{ currency(item.price) }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </template>
      </div>
    </div>
  </Teleport>
</template>
```

- [ ] **Step 3: Run frontend tests**

```bash
corepack pnpm test -- --run
```
Expected: 38 passed

- [ ] **Step 4: Run frontend build**

```bash
corepack pnpm build
```
Expected: build succeeds

- [ ] **Step 5: Commit**

```bash
git add web/src/api/dashboard.ts web/src/components/ReceiptModal.vue
git commit -m "feat: add fetchReceiptsByItem API and ReceiptModal component"
```

### Task 6: Frontend — Wire up TopItemsPanel and DashboardPage

**Files:**
- Modify: `web/src/components/TopItemsPanel.vue`
- Modify: `web/src/components/DashboardPage.vue`

- [ ] **Step 1: Add select-article event to TopItemsPanel**

In the `<tr>` element, add `cursor-pointer` class and click handler:

```vue
<tr
  v-for="item in items"
  :key="text(item.name)"
  class="cursor-pointer transition hover:bg-slate-50"
  @click="emit('select-article', text(item.name))"
>
```

Add to `defineEmits`:
```typescript
const emit = defineEmits<{
  (e: "update:page", value: number): void;
  (e: "update:topLimit", value: number): void;
  (e: "select-article", name: string): void;
}>();

function handleRowClick(name: string) {
  emit("select-article", name);
}
```

- [ ] **Step 2: Integrate ReceiptModal in DashboardPage.vue**

Add import:
```vue
import ReceiptModal from "./ReceiptModal.vue";
```

Add ref:
```typescript
const selectedArticle = ref<string | null>(null);
```

Add handler:
```typescript
function onSelectArticle(name: string) {
  selectedArticle.value = name;
}

function onCloseReceiptModal() {
  selectedArticle.value = null;
}
```

Add before closing `</template>`:
```vue
<ReceiptModal
  :article-name="selectedArticle ?? ''"
  :retailer="retailer"
  :visible="!!selectedArticle"
  @close="onCloseReceiptModal"
/>
```

We need to pass `retailer` to the modal. The `retailer` ref is already available from `useDashboard()`.

Wire up the event on `TopItemsPanel`:
```vue
<TopItemsPanel
  :items="section.items"
  :page="page"
  :page-size="(section.items[0] as any)?.page_size ?? 20"
  :total-count="(section.items[0] as any)?.total_count ?? 0"
  :top-limit="topLimit"
  @update:page="page = $event"
  @update:top-limit="topLimit = $event"
  @select-article="onSelectArticle"
/>
```

- [ ] **Step 3: Run frontend tests**

```bash
corepack pnpm test -- --run
```
Expected: 38 passed

- [ ] **Step 4: Run frontend build**

```bash
corepack pnpm build
```
Expected: build succeeds

- [ ] **Step 5: Commit**

```bash
git add web/src/components/TopItemsPanel.vue web/src/components/DashboardPage.vue
git commit -m "feat: wire article click → receipt modal in dashboard"
```

### Task 7: Backend — Add test for new endpoint

**Files:**
- Modify: `tests/test_api_receipts.py`

- [ ] **Step 1: Add test for `/receipts/by-item`**

At the end of the file, add:

```python
def test_receipts_by_item_returns_matching_receipts(monkeypatch):
    from fastapi.testclient import TestClient

    from api.main import app
    from api.services import receipt_service

    class FakeStore:
        @staticmethod
        def list_receipts_by_item(name, retailer=None, start_date=None, end_date=None):
            return [
                {
                    "id": "r1",
                    "retailer": "lidl",
                    "purchase_date": "2024-01-15",
                    "store": "Lidl München",
                    "items": [
                        {"name": "Apfel", "quantity": 1, "unit": "kg", "price": 2.99, "matched": True},
                        {"name": "Brot", "quantity": 1, "unit": "pc", "price": 1.49, "matched": False},
                    ],
                    "payment_methods": [],
                }
            ]

    monkeypatch.setattr(receipt_service, "SqliteReceiptStore", FakeStore)

    response = TestClient(app).get("/receipts/by-item", params={"name": "Apfel"})

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "r1"
    assert data[0]["items"][0]["matched"] is True
```

- [ ] **Step 2: Run final full test suite**

```bash
./.venv/bin/python3 -m pytest -q
corepack pnpm test -- --run
corepack pnpm build
```

- [ ] **Step 3: Commit all remaining changes**

```bash
git add tests/test_api_receipts.py
git commit -m "test: add integration test for /receipts/by-item"
```
