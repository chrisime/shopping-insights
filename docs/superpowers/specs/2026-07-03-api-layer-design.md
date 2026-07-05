# API Layer Design

**Date:** 2026-07-03  
**Status:** Draft  
**Author:** Generated via brainstorming session

---

## 1. Overview

Introduce a RESTful API layer (FastAPI) to parameterize data access currently served by the Streamlit dashboard. This is a preparatory step for a Streamlit-free frontend.

**Scope:** Full – KPIs, Receipts (with items & payments), Exports, Fetch Triggers

---

## 2. Architecture

### 2.1 Directory Structure

```
api/
├── main.py                 # FastAPI app, router registration, lifespan
├── routes/
│   ├── kpis.py             # /kpis endpoints
│   ├── receipts.py         # /receipts endpoints
│   ├── items.py            # /items endpoints
│   ├── exports.py          # /exports endpoints
│   └── triggers.py         # /triggers endpoints (fetch operations)
├── schemas/
│   ├── kpis.py             # Pydantic models for KPI responses
│   ├── receipts.py         # Receipt, Item, Payment models
│   ├── items.py            # Item list models
│   └── exports.py          # Export request/response models
├── services/
│   ├── kpi_service.py      # Wraps MetricsStore, builds queries from params
│   ├── receipt_service.py  # Storage queries for receipt details
│   └── trigger_service.py  # Calls fetch workflows
└── deps.py                 # DB session, pagination, filter parsing
```

### 2.2 Migration: `api/` → `client/`

| Old Path | New Path |
|----------|----------|
| `api/lidl_client.py` | `client/lidl_client.py` |
| `api/rewe_client.py` | `client/rewe_client.py` |
| `api/__init__.py` | `client/__init__.py` |

All imports in `workflows/`, `auth/`, `config/` updated accordingly.

---

## 3. Endpoints

### 3.1 KPIs (`/kpis`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/kpis/summary` | Grundkennzahlen (total_spent, total_receipts, avg_receipt, total_discount, total_saved_deposit, min_date, max_date) |
| GET | `/kpis/bonus` | Händler-spezifische Bonus-KPIs (REWE: collected, balance, redeemed; Lidl: lidlplus, sticker) |
| GET | `/kpis/trend` | Zeitreihe – Ausgaben über Zeit |
| GET | `/kpis/top-items` | Top-Artikel nach Menge oder Ausgaben |
| GET | `/kpis/weekday` | Wochentag-Analyse (Einkäufe, Ø-Ausgaben) |

### 3.2 Receipts (`/receipts`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/receipts` | Paginierte Liste aller Kassenbons mit Metadaten |
| GET | `/receipts/{id}` | Einzelner Kassenbon mit allen Details |
| GET | `/receipts/{id}/items` | Artikel eines Kassenbons |
| GET | `/receipts/{id}/payments` | Zahlungsinformationen eines Kassenbons |

### 3.3 Items (`/items`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/items` | Durchsuchbare, paginierte Artikelliste (global über alle Bons) |

### 3.4 Exports (`/exports`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/exports/kpis` | KPI-Daten als JSON oder CSV |
| GET | `/exports/receipts` | Kassenbons als JSON oder CSV |

### 3.5 Triggers (`/triggers`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/triggers/fetch/lidl` | Lidl-Fetch anstoßen (optional `days_back`) |
| POST | `/triggers/fetch/rewe` | REWE-Fetch anstoßen (optional `days_back`) |

---

## 4. Query Parameters (Standardisiert)

| Parameter | Type | Values | Default |
|-----------|------|--------|---------|
| `retailer` | string | `lidl` \| `rewe` | (alle) |
| `start_date` | date | ISO 8601 `YYYY-MM-DD` | – |
| `end_date` | date | ISO 8601 `YYYY-MM-DD` | – |
| `granularity` | string | `day` \| `month` \| `year` | `day` |
| `sort` | string | `quantity` \| `spend` | `quantity` |
| `limit` | int | 1–200 | 20 |
| `page` | int | ≥ 1 | 1 |
| `page_size` | int | 1–200 | 50 |
| `search` | string | Freitext (items) | – |
| `format` | string | `json` \| `csv` | `json` |
| `days_back` | int | ≥ 1 (triggers) | 30 |

---

## 5. Response Format

### 5.1 List Responses (Paginated)

```json
{
  "data": [...],
  "meta": {
    "total": 123,
    "page_total": 3,
    "page": 1,
    "page_size": 50
  }
}
```

- `total`: Gesamtanzahl Datensätze
- `page_total`: Anzahl Seiten (`ceil(total / page_size)`)
- Keine `filters` im Response (Parameter stehen in URL)

### 5.2 Single Resources

```json
{
  "data": { ... }
}
```

### 5.3 Errors

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "start_date must be before end_date",
    "details": { "field": "start_date" }
  }
}
```

HTTP Status: 400 (Validation), 404 (Not Found), 500 (Internal)

---

## 6. Pydantic Schemas (Auszug)

### 6.1 KPIs

```python
# schemas/kpis.py
class KpiSummary(BaseModel):
    total_spent: float
    total_receipts: int
    avg_receipt: float
    total_discount: float
    total_saved_deposit: float
    min_date: Optional[str]
    max_date: Optional[str]

class KpiBonus(BaseModel):
    rewe_bonus_collected: float
    rewe_bonus_balance: float
    rewe_bonus_redeemed: float
    lidlplus_discount: float
    sticker_discount: float

class TimeSeriesRow(BaseModel):
    period: str
    total_spent: float
    receipt_count: int

class TopItemRow(BaseModel):
    name: str
    total_quantity: float
    total_spent: float
    purchase_count: int
    unit: str

class WeekdayRow(BaseModel):
    weekday: int
    weekday_name: str
    trip_count: int
    avg_spent: float
    total_spent: float
```

### 6.2 Receipts

```python
# schemas/receipts.py
class ReceiptItem(BaseModel):
    name: str
    quantity: float
    unit: str
    price: float
    total: float
    is_discount: bool
    discount_amount: Optional[float]

class ReceiptPayment(BaseModel):
    method: str
    amount: float

class ReceiptDetail(BaseModel):
    id: int
    retailer_code: str
    store_name: str
    store_address: Optional[str]
    purchase_date: str
    total_price: float
    discount: float
    saved_deposit: float
    items: List[ReceiptItem]
    payments: List[ReceiptPayment]
```

---

## 7. Services

### 7.1 KpiService
- Wrappt `MetricsStore`
- Baut `WHERE`-Klauseln aus Query-Parametern
- Mappt Dataclasses → Pydantic Models

### 7.2 ReceiptService
- Nutzt `storage/` Repositories (`PurchaseRepository`, `PurchaseItemRepository`, etc.)
- Führt JOINs für Details durch (Items, Payments, Store)

### 7.3 TriggerService
- Ruft `workflows.lidl_workflow.run_fetch()` / `rewe_workflow.run_fetch()` auf
- Gibt Job-ID / Status zurück (async optional)

---

## 8. Configuration

- Keine Auth (lokale Nutzung)
- CORS: `allow_origins=["*"]` für Entwicklung
- DB-Pfad via `config.storage_config.SQLITE_RECEIPTS_DB_FILE`
- Port: 8000 (konfigurierbar via `API_PORT` env var)

---

## 9. Testing

- Unit-Tests für Services (mock DB)
- Integration-Tests für Routes (TestClient + echte SQLite in-memory)
- Mindestabdeckung: Happy-Path je Endpoint, Validierungsfehler, leere Ergebnisse

---

## 10. Open Questions / Future

- [ ] CSV-Export bleibt vorerst aus
- [ ] OpenAPI-Docs (`/docs`) bleiben vorerst aus
- [ ] Async DB-Layer (aiosqlite) für echte Concurrency
- [ ] Auth (API-Key) falls Deployment geplant
- [ ] WebSocket für Fetch-Progress-Updates
