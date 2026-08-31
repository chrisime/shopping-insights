## 1. Configuration and Runtime Wiring

- [ ] 1.1 Add `config/dm_config.py` with dm endpoints (purchasehistory list, eBon detail, eBon download, products gateway), OAuth issuer/client id/scopes, cookie file, receipts JSON file, default output dir, timeout/retry settings.
- [ ] 1.2 Register `dm` in `shared/retailer_runtime.py` (`_RUNTIME_DEFINITIONS`) with name, country getter, and receipts JSON file, following the Lidl/REWE pattern.

## 2. dm Authentication (OAuth PKCE)

- [ ] 2.1 Add `auth/dm_auth.py` implementing the OAuth 2.0 authorization-code flow with PKCE against `signin.dm.de/dm-de/oauth-anonymous` (client `nextaccount`, scopes `openid email roles customerId`), using stdlib `secrets`/`hashlib`/`base64`.
- [ ] 2.2 Add a function to acquire a fresh access token from a browser session or a cookies-file export (`signin.dm.de` and `*.services.dmtech.com` domains), per ADR-0005.
- [ ] 2.3 Add a dm session/credential check (traffic-light diagnostics) usable by `fetch_tickets.py check --retailer dm`, following `auth/cookie_diagnostics.py` patterns.
- [ ] 2.4 Reuse the shared auth-method resolution (`--browser` / `--cookies-file`) from `workflows/import_workflow.py` for dm.

## 3. dm Client

- [ ] 3.1 Add `client/dm_client.py` with `fetch_purchase_history()` calling `GET /v1/purchasehistory` with `size` and cursor pagination (`untilDateTimePlaced` + `hasMoreElements`).
- [ ] 3.2 Add `fetch_ebon_detail(id)` calling `GET /api/customer/ebons/<id>` returning date, time, store address, register, discount, payback points, and DAN item list.
- [ ] 3.3 Add `download_ebon_pdf(id)` calling `GET /api/customer/ebons/<id>/download` and saving the PDF.
- [ ] 3.4 Add retry/backoff on 429/5xx with plain `requests` + `time.sleep` (mirroring the Lidl client), and a 401 handler that re-acquires a token and retries once.

## 4. Normalization

- [ ] 4.1 Add dm extras to `shared/receipt_schema.py` (`_RETAILER_EXTRA_DEFAULTS`, money fields, e.g. payback points) without widening shared fields.
- [ ] 4.2 Add a dm parser mapping eBon detail to the shared receipt schema (`purchase_date`, `address`, `register`, `discount`, `total_price`, `items` with DAN).
- [ ] 4.3 Add DAN → product-name enrichment via the dm products gateway, falling back to empty descriptions when unavailable.

## 5. dm Workflow

- [ ] 5.1 Add `workflows/dm_workflow.py` with `run_dm_initial` and `run_dm_update` driving list fetch → eBon detail/PDF download → shared `import_local_sources()` path (per ADR-0003).
- [ ] 5.2 Wire skipped-receipt reporting and dedup/hash handling through the shared import machinery.

## 6. CLI Wiring

- [ ] 6.1 Wire `--retailer dm` into `fetch_tickets.py` for `initial`, `update`, `check`, and `export` commands, following the Lidl/REWE dispatch pattern.
- [ ] 6.2 Update `fetch_tickets.py` docstring/help text to list dm and document the required cookie domains for `check`.

## 7. Tests

- [ ] 7.1 Add unit tests for `config/dm_config.py` and the retailer-runtime registration.
- [ ] 7.2 Add unit tests for the dm OAuth PKCE flow (token acquisition, error on invalid session).
- [ ] 7.3 Add unit tests for `client/dm_client.py` (list, pagination, detail, PDF download, retry/backoff, 401 retry).
- [ ] 7.4 Add unit tests for the dm receipt parser/normalization (happy path, skipped/unparseable entry, duplicate handling).
- [ ] 7.5 Add workflow tests for `run_dm_initial`/`run_dm_update` through the shared import path.
- [ ] 7.6 Run `./.venv/bin/python -m pytest -q` and confirm all existing and new tests pass.

## 8. Spec Validation

- [ ] 8.1 Run `openspec validate add-dm-retailer --type change --strict` and fix any spec/scenario issues before archiving.