## Why

The analyzer currently supports Lidl and REWE. dm is a major German supermarket/drogerie where the user shops, and dm exposes the full purchase history (Markt-eBons plus online orders) through a clean, authenticated JSON API. Adding dm as a third retailer gives the dashboard the same KPI coverage the user already gets for Lidl/REWE, using the same import path, normalization schema, and storage.

## What Changes

- Add `dm` as a supported retailer across runtime resolution, config, CLI, and dashboard.
- Add a new `client/dm_client.py` that talks to the dm purchase-history backend:
  - `GET https://purchasehistory-prod.services.dmtech.com/v1/purchasehistory?size=20&untilDateTimePlaced=<iso>` (paginated list, `hasMoreElements` + last item's `dateTimePlaced`).
  - `GET https://ebon-prod.services.dmtech.com/api/customer/ebons/<id>` (eBon detail: date, time, store address, register, discount, payback points, `bonItems` with DAN).
  - `GET https://ebon-prod.services.dmtech.com/api/customer/ebons/<id>/download` (PDF original receipt).
  - Item names/prices are parsed from the downloaded PDFs (`parsing/dm_pdf_items_extractor.py`), because the API's `bonItems` only carry DAN identifiers.
  - `purchaseType` distinguishes `MARKET` (eBon) from online orders (order-history).
- Add an OAuth 2.0 auth-method for dm using the PKCE authorization-code flow against `https://signin.dm.de/dm-de/oauth-anonymous` (client `nextaccount`, scopes `openid email roles customerId`), because dm access tokens expire in ~2.5 minutes and cannot be used as static credentials.
  - Reuse the shared auth-method resolution (`--browser` / `--cookies-file`) pattern; dm adds its own session-cookie + silent-auth flow.
- Add a `workflows/dm_workflow.py` driving initial/update imports through the shared `import_local_sources()` path.
- Normalize dm eBons into the shared receipt schema (`shared/receipt_schema.py`), mapping store address, register, discount, and item data. The dm API only returns DAN item IDs, so item names/prices are parsed from the downloaded eBon PDFs; DAN → product-name enrichment via the dm products gateway is a fallback when a PDF cannot be parsed.
- Extend `shared/retailer_runtime.py`, `config/dm_config.py`, `fetch_tickets.py`, and retailer metadata so `--retailer dm` works end to end.

## Capabilities

### New Capabilities
- `dm-purchase-history`: Fetch, paginate, and download dm purchase history (list + eBon detail + PDF) using the dm OAuth/PKCE flow and session cookies.
- `dm-import`: Import normalized dm eBons into SQLite through the shared import path, including skipped-receipt reporting and dedup/hash handling.

### Modified Capabilities
- No existing spec-level behaviour changes.

## Impact

- `client/` — new `dm_client.py`; shared auth helpers touched for the PKCE/silent-auth flow.
- `workflows/` — new `dm_workflow.py`; `local_import.py` reused unchanged.
- `shared/` — `retailer_runtime.py`, `receipt_schema.py` (dm extra fields), `retailer_runtime.get_retailer_runtime()` returns dm runtime.
- `config/` — new `dm_config.py` with endpoints, client id, cookie file, JSON output file.
- `auth/` — new dm auth module (OAuth token acquisition, refresh/silent-auth, session-cookie handling).
- `fetch_tickets.py` — `--retailer dm` wiring for `initial`, `update`, `check`, `export`.
- `requirements.txt` — no new third-party libs (plain `requests` + stdlib crypto for PKCE).
- Dashboard: dm receipts flow through existing KPIs/receipts/items API once normalized; no frontend changes expected.