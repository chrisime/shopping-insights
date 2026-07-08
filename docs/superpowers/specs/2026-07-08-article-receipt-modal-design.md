# Article → Receipt Modal Feature

## Problem
In der Top-Artikel-Liste soll ein Klick auf einen Artikel die zugehörigen Kassenzettel anzeigen, mit dem Artikel hervorgehoben.

## User Flow
1. User klickt auf eine Artikel-Zeile in TopItemsPanel
2. Modal öffnet sich, lädt alle Belege mit diesem Artikel
3. Belege werden nacheinander angezeigt (Navigation via Vor/Zurück)
4. Der gesuchte Artikel ist in jedem Beleg gelb hinterlegt
5. Modal kann per Schließen-Button oder Klick außerhalb geschlossen werden

## Backend

### Neuer Endpoint: `GET /receipts/by-item`

**Route:** `api/routes/receipts.py`

**Parameter:**
- `name: str` (required) — Artikelname (LIKE-Suche, case-insensitive)
- `retailer: Optional[str]`
- `start_date: Optional[str]`
- `end_date: Optional[str]`

**Response:** Array vollständiger Receipt-Dicts (gleiches Format wie `GET /receipts/{id}`), jedes Item um `matched: bool` erweitert.

**Implementation:**
- `PurchaseItemDomain` bekommt Methode `find_purchase_ids_by_item_name(name, connection)` — SQL Join `purchase_item → purchase`, filtert auf `UPPER(name) LIKE UPPER(?)`
- `SqliteReceiptStore` bekommt Methode `list_receipts_by_item(name, retailer, start_date, end_date)` — nutzt `find_purchase_ids_by_item_name`, lädt volle Receipts via `_map_purchase_to_receipt_dict`, markiert Items mit `matched`
- `receipts.py` bekommt neuen Endpoint `read_receipts_by_item`

## Frontend

### Neue API-Funktion: `fetchReceiptsByItem`
- Datei: `web/src/api/dashboard.ts`
- Aufruf: `GET /receipts/by-item?name=X&retailer=Y`

### Neue Komponente: `ReceiptModal.vue`
- Props: `articleName: string`, `retailer?: string`, `visible: boolean`
- Emits: `close`
- States: `loading`, `receipts[]`, `currentIndex`
- UI:
  - Modal-Overlay (halbtransparent, klick zum Schließen)
  - Kopf: "Apfel — Kassenzettel" + Schließen-X
  - Navigation: "3 von 5" + Zurück/Weiter-Buttons
  - Beleg-Details: Store, Datum, Gesamtbetrag
  - Items-Liste mit dem gesuchten Artikel in `bg-amber-50 border-l-4 border-amber-400`

### TopItemsPanel.vue
- `<tr>` bekommt `class="cursor-pointer"` und `@click="emit('select-article', item.name)"`
- Neues Event: `select-article(name: string)`

### DashboardPage.vue
- State `selectedArticle: string | null` + Computed `receiptModalVisible`
- `ReceiptModal` einbinden, an `select-article`-Event binden

## Files
- `api/routes/receipts.py` — neuer Endpoint
- `storage/sqlite_domains.py` — `find_purchase_ids_by_item_name` in `PurchaseItemDomain`
- `storage/sqlite_receipt_store.py` — `list_receipts_by_item`
- `web/src/api/dashboard.ts` — `fetchReceiptsByItem`
- `web/src/components/ReceiptModal.vue` — neue Komponente
- `web/src/components/TopItemsPanel.vue` — `cursor-pointer` + Event
- `web/src/components/DashboardPage.vue` — Modal-Integration
