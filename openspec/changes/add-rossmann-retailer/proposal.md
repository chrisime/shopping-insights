## Why

Rossmann is a major German drugstore where the user shops. Since May 2025 Rossmann offers digital receipts in its app, implemented by the white-label provider **anybill**. The web interface has no receipt menu point, but the app's API surface is reachable and partially documented. Adding Rossmann as a fourth retailer gives the dashboard the same KPI coverage as Lidl/REWE/dm, reusing the shared import path, normalization schema, and storage.

## What Changes

- Add `rossmann` as a supported retailer across runtime resolution, config, CLI, dashboard, and interactive menu.
- Add a new `client/rossmann_client.py` that talks to the two-stage Rossmann/anybill backend:
  1. Mint an anybill token via the Rossmann account API:
     - `POST https://rsmappapi.rossmann.net/account.ws/v2/accounts/login` with `LoginRequestDto` (anonymous account + email/password) → `accountId`, `accountHash`.
     - `GET https://rsmappapi.rossmann.net/account.ws/v2/accounts/{accountId}/receipt/auth` with header `Account-Hash: <accountHash>` → `{ accessToken, refreshToken, expiresIn }` (anybill token).
  2. Fetch receipts from the anybill App API v4:
     - `GET https://app.anybill.de/api/v4/receipt` (Bearer token; paginated via `continuationToken`, filterable by `fromDate`/`toDate`).
     - `GET https://app.anybill.de/api/v4/receipt/{id}` (detail).
     - `GET https://app.anybill.de/api/v4/receipt/{id}/pdf` (original receipt PDF).
     - `POST https://app.anybill.de/api/v4/receipt/export` (ZIP export of all/selected receipts).
     - `POST https://app.anybill.de/api/v4/authentication/refresh` (refresh token).
- Add an auth-method for Rossmann reusing the shared `--browser` / `--cookies-file` resolution: derive the Rossmann session from the browser/cookie export, use the SSO hop (`www.rossmann.de/.rest/sso/app`) or the account.ws login to obtain `accountId`/`accountHash`, then mint the anybill token.
- Add a `workflows/rossmann_workflow.py` driving initial/update imports through the shared `import_local_sources()` path.
- Normalize anybill receipts into the shared receipt schema; parse item names/prices from the eBon PDFs (like dm), because the anybill JSON is expected to carry limited item detail.
- Extend `shared/retailer_runtime.py`, `config/rossmann_config.py`, `fetch_tickets.py`, `cli/menu.py`, and retailer metadata so `--retailer rossmann` works end to end.

## Capabilities

### New Capabilities
- `rossmann-purchase-history`: Fetch, paginate, and download Rossmann digital receipts (anybill list, detail, PDF, export) using the Rossmann account token mint plus anybill Bearer token.
- `rossmann-import`: Import normalized Rossmann receipts into SQLite through the shared import path, including skipped-receipt reporting and dedup/hash handling.

### Modified Capabilities
- No existing spec-level behaviour changes.

## Impact

- `client/` — new `rossmann_client.py`.
- `config/` — new `rossmann_config.py` (Rossmann account.ws base, anybill base/clientId, cookie file, JSON output file).
- `auth/` — new Rossmann auth module (session → accountHash/accountId → anybill token; reuse shared auth-method resolution).
- `parsing/` — Rossmann PDF item extraction (reuse dm PDF parser pattern), plus anybill JSON parser.
- `workflows/` — new `rossmann_workflow.py`; `local_import.py` reused unchanged.
- `shared/` — `retailer_runtime.py` registration; `receipt_schema.py` extras if needed.
- `fetch_tickets.py` + `cli/menu.py` — `--retailer rossmann` wiring.
- `requirements.txt` — no new third-party libs (plain `requests` + stdlib; pdfplumber already present).
- Dashboard: Rossmann receipts flow through existing KPIs/receipts/items API once normalized; no frontend changes expected.