## 1. Configuration and Runtime Wiring

- [x] 1.1 Add `config/rossmann_config.py` with Rossmann account.ws endpoints (login, receipt/auth), anybill base URL/client id (`4d8b1eb1-a1c6-45da-a271-5ab1167d6018`), cookie file, receipts JSON file, default output dir, timeout/retry settings.
- [x] 1.2 Register `rossmann` in `shared/retailer_runtime.py` (`_RUNTIME_DEFINITIONS`) with name, country getter, and receipts JSON file, following the Lidl/REWE/dm pattern.

## 2. Rossmann Authentication (account API token mint)

- [x] 2.1 Add `auth/rossmann_auth.py` that derives `accountId`/`accountHash` from the Rossmann session (browser or cookie file via the shared `--browser`/`--cookies-file` resolution, optionally via the SSO hop `www.rossmann.de/.rest/sso/app`), per ADR-0006.
- [x] 2.2 Add `POST accounts/login` support with anonymous-account fallback for cases where the session needs a login, and `GET accounts/{accountId}/receipt/auth` to mint the anybill token (`AnybillTokenResultDto`).
- [x] 2.3 Add an anybill token refresher calling `POST authentication/refresh` (or re-mint via receipt/auth) and a 401 handler that retries once.
- [x] 2.4 Add a Rossmann session/credential check (traffic-light diagnostics) usable by `fetch_tickets.py check --retailer rossmann`, following `auth/cookie_diagnostics.py` patterns.

## 3. Rossmann Client (anybill App API v4)

- [x] 3.1 Add `client/rossmann_client.py` with `fetch_receipts()` calling `GET /v4/receipt` with `take` and `continuationToken` pagination (`hasMoreElements`-style continuation), per D2.
- [x] 3.2 Add `fetch_receipt_detail(id)` calling `GET /v4/receipt/{id}`.
- [x] 3.3 Add `download_receipt_pdf(id)` calling `GET /v4/receipt/{id}/pdf` and saving the PDF.
- [x] 3.4 Add retry/backoff on 429/5xx with plain `requests` + `time.sleep` (mirroring the Lidl client), and a 401 handler that refreshes the anybill token and retries once.

## 4. Normalization

- [x] 4.1 Add any Rossmann extras to `shared/receipt_schema.py` (`_RETAILER_EXTRA_DEFAULTS`) if needed, without widening shared fields.
- [x] 4.2 Add a Rossmann parser mapping anybill receipt detail/PDF to the shared receipt schema (`purchase_date`, `address`/`store`, `total_price`, `currency`, `items`).
- [x] 4.3 Add Rossmann PDF item extraction (reusing the dm PDF parse pattern when possible) to recover item names/prices/quantities, else skip with reason.

## 5. Rossmann Workflow

- [x] 5.1 Add `workflows/rossmann_workflow.py` with `run_rossmann_initial` and `run_rossmann_update` driving list fetch → receipt detail/PDF download → shared `import_local_sources()` path (per ADR-0003).
- [x] 5.2 Wire skipped-receipt reporting and dedup/hash handling through the shared import machinery.

## 6. CLI and Menu Wiring

- [x] 6.1 Wire `--retailer rossmann` into `fetch_tickets.py` for `initial`, `update`, `check`, and `export` commands, following the Lidl/REWE/dm dispatch pattern.
- [x] 6.2 Add a `cli/rossmann_menu.py` interactive submenu and register it in `cli/menu.py`.
- [x] 6.3 Update `fetch_tickets.py` docstring/help text to list Rossmann and document the required cookie domains for `check`.

## 7. Tests

- [x] 7.1 Add unit tests for `config/rossmann_config.py` and the retailer-runtime registration.
- [x] 7.2 Add unit tests for the Rossmann token mint flow (session → accountId/accountHash → anybill token, error on invalid session, refresh on 401).
- [x] 7.3 Add unit tests for `client/rossmann_client.py` (list, pagination, detail, PDF download, retry/backoff, 401 refresh/retry).
- [x] 7.4 Add unit tests for the Rossmann parser/normalization (happy path, PDF item extraction, skipped/unparseable entry, duplicate handling).
- [x] 7.5 Add workflow tests for `run_rossmann_initial`/`run_rossmann_update` through the shared import path.
- [x] 7.6 Run `./.venv/bin/python -m pytest -q` and confirm all existing and new tests pass.
- [x] 7.7 Run `pnpm test -- --run` and `pnpm build` in `web/` if the frontend changed (user-facing labels, menu).

## 8. Spec Validation

- [x] 8.1 Run `openspec validate add-rossmann-retailer --type change --strict` and fix any spec/scenario issues before archiving.