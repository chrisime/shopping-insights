## Context

The analyzer currently imports Lidl, REWE, and dm receipts. Rossmann introduced digital receipts in its app in May 2025, implemented by the white-label provider **anybill** (with POS partner Combase). Reverse-engineering of the Rossmann Android app (`de.rossmann.app.android` v5.11.0, decompiled with jadx) found:

- The app embeds `de.anybill.anybill_android_sdk` and talks directly to the anybill App API v4 at `https://app.anybill.de/api/v4/` (base), client id `4d8b1eb1-a1c6-45da-a271-5ab1167d6018`, auth header `Authorization: Bearer <token>`.
- Rossmann mints the anybill token itself via its account API `https://rsmappapi.rossmann.net/account.ws/v2`:
  - `POST accounts/login` (`LoginRequestDto`: anonymousAccountHash, anonymousAccountId, password, email) → `LoginResponseDto` with `accountId`, `accountHash`.
  - `GET accounts/{accountId}/receipt/auth` with header `Account-Hash: <accountHash>` → `AnybillTokenResultDto { accessToken, refreshToken, expiresIn }`.
- The anybill App API v4 is publicly documented (`app.anybill.de/api/swagger/v4/swagger.json`): receipt list/detail/PDF/export, search, favourites, notes, user, `authentication/refresh`.
- `www.rossmann.de` is behind a Fastly Client Challenge (bot protection); `rsmappapi.rossmann.net` is reachable without it.

The project favours plain `requests`, no third-party retry/DI/ABC layers, a shared single import path (`workflows/local_import.py`), and a shared receipt schema. ADR-0003 commits to onboarding future retailers via the shared import path; ADR-0005 (dm OAuth PKCE) is dm-specific but the pattern of minting a short-lived token from the retailer session applies analogously.

```text
System context: Rossmann digital-receipt import

+----------------+   session (browser cookies / cookie file)   +---------------------------+
|  Rossmann web  | ------------------------------------------> | rsmappapi.rossmann.net    |
|  (account.ws)  |   POST accounts/login                       |  (account.ws/v2)          |
+----------------+   GET accounts/{id}/receipt/auth            +---------------------------+
        |                          | anybill accessToken              |
        |                          v                                   |
        |            +--------------------------+                    |
        |            |      Analyzer (CLI)       |                    |
        |            |                          |                    |
        |            |  auth/rossmann_auth       |                    |
        |            |  client/rossmann_client   |                    |
        |            |  workflows/rossmann_workflow -> local_import() |
        |            +--------------------------+                    |
        |                          | HTTPS + Bearer                   |
        |                          v                                  |
        |            +--------------------------+                    |
        +----------> | app.anybill.de/api/v4/   |                    |
                     |  receipt, receipt/{id},  |                    |
                     |  receipt/{id}/pdf,       |                    |
                     |  export, auth/refresh    |                    |
                     +--------------------------+                    |
                                |                                     |
                                v                                     |
                     +--------------------------+                    |
                     | SQLite (SQLAlchemy Core  |                    |
                     |  + Alembic)              |                    |
                     +--------------------------+                    |
                                |                                     |
                                v                                     |
                     Vue dashboard (existing KPIs/receipts/items APIs, unchanged)
```

Boundaries: the CLI mints an anybill token via the Rossmann account API from the user's session, then fetches receipts/PDFs from anybill; normalized receipts persist through the shared import path into SQLite; the dashboard reads them through existing APIs with no frontend changes.

## Goals / Non-Goals

**Goals:**
- Add Rossmann as a supported retailer (`--retailer rossmann`) for initial and update imports.
- Obtain an anybill access token from an authenticated Rossmann session (browser or cookie file) via the Rossmann account API.
- Fetch the paginated receipt list, single receipt details, and original PDFs from the anybill App API v4.
- Normalize Rossmann receipts into the shared receipt schema, extracting item names/prices/quantities from the receipt PDFs.
- Reuse the shared auth-method resolution (`--browser` / `--cookies-file`) and the shared import path.

**Non-Goals:**
- Rossmann online-shop order history (`api-ocm-de-prod.rossmann.net/order-history-api`) is out of scope; only the anybill in-store receipts are imported.
- No dashboard/frontend changes (Rossmann receipts flow through existing APIs).
- No refresh-token persistence or daemonized background refresh.

## Decisions

### D1: Mint the anybill token through the Rossmann account API (session-derived)
The web UI has no receipt menu and sits behind bot protection. Instead, derive `accountId`/`accountHash` from the user's Rossmann session (browser cookies or cookie file via the shared auth-method resolution, optionally via the SSO hop `www.rossmann.de/.rest/sso/app`), then call `GET accounts/{accountId}/receipt/auth` to mint the anybill token.

- **Why:** matches how the app authenticates; no stored credentials; reuses the shared `--browser`/`--cookies-file` pattern.
- **Alternatives considered:** (a) `POST accounts/login` with email/password — rejected, stores credentials and is less secure; (b) anonymous account only — rejected, anonymous anybill users likely cannot export receipts (`_bill-anonymousnoexport`).

### D2: Talk directly to the anybill App API v4
Use `https://app.anybill.de/api/v4/` for receipt list/detail/PDF/export with the anybill Bearer token. Pagination via `continuationToken`; refresh via `POST authentication/refresh` on 401.

- **Why:** this is exactly what the embedded SDK does; publicly documented; avoids replaying the SDK's internal Retrofit layer.
- **Alternatives considered:** embedding the anybill Android SDK — rejected, not usable server-side; proxying through Rossmann — no such endpoint exists.

### D3: New `client/rossmann_client.py` + `config/rossmann_config.py`, no new libraries
Rossmann account.ws endpoints, anybill base/clientId, cookie file, and JSON output file live in `config/rossmann_config.py`; all HTTP in `client/rossmann_client.py` using plain `requests`. Retry/backoff on 429/5xx mirrors Lidl; 401 triggers an anybill refresh and one retry.

- **Why:** project constraints forbid third-party retry/HTTP wrappers; keeps symmetry with Lidl/REWE/dm clients.
- **Alternatives considered:** an OAuth library — rejected by the no-third-party-auth-libraries constraint.

### D4: Normalize into the shared receipt schema, parse item lines from the PDF
Map anybill receipt fields to `shared/receipt_schema.py` (date, store/address, total, currency). Item names/prices/quantities are parsed from the receipt PDF using the same pattern as the dm PDF extractor (`parsing/dm_pdf_items_extractor.py`), since the anybill list/detail JSON carries limited item detail.

- **Why:** dashboard KPIs and the items view consume the normalized schema; PDF parsing was already proven for dm.
- **Alternatives considered:** anybill JSON-only items — rejected, would degrade the items dashboard.

### D5: Drive import through the existing shared path (`import_local_sources`)
`workflows/rossmann_workflow.py` fetches/parses Rossmann data and delegates to the shared `import_local_sources()` pipeline, per ADR-0003. Dedup/hash handling and skipped-receipt reporting come from the shared machinery.

- **Why:** ADR-0003 mandates one shared import path for future retailers.
- **Alternatives considered:** a second pipeline tier — rejected by ADR-0003.

## Risks / Trade-offs

- [Rossmann/anybill frontend API changes without notice] -> Mitigation: endpoints/config centralized in `config/rossmann_config.py`; document the reverse-engineering source; treat drift as a config/tests fix.
- [Cookie export missing the Rossmann session cookies or SSO requires the web session behind Fastly] -> Mitigation: `check --retailer rossmann` validates session reachability and produces a traffic-light diagnostic; document the required cookie domains in the CLI help.
- [anybill token lifetime/refresh] -> Mitigation: mint per run; on 401 call `authentication/refresh` and retry once; keep imports under the token lifetime.
- [Receipt PDFs without parseable item lines] -> Mitigation: store the receipt with empty items and report a skip reason, like dm; later enrichment can re-parse.
- [Anonymous anybill users cannot export receipts] -> Mitigation: the workflow imports from the list/detail endpoints; export ZIP is only an optional convenience.

## Migration Plan

1. Add `config/rossmann_config.py`, `client/rossmann_client.py`, `auth/rossmann_auth.py`, `workflows/rossmann_workflow.py`.
2. Wire `--retailer rossmann` into `fetch_tickets.py` (initial/update/check/export) and `cli/menu.py`.
3. Register Rossmann in `shared/retailer_runtime.py` and add any needed extras to `shared/receipt_schema.py`.
4. Add Alembic migration only if new persisted fields are needed (likely none).
5. Verify via `check`, then `initial`, then `update`; confirm dashboard KPIs include Rossmann receipts.

Rollback: removing Rossmann is purely additive — drop `_RUNTIME_DEFINITIONS["rossmann"]` and remove the config/client/auth/workflow modules; no schema migration required if no columns were added.

## Open Questions

- Exact Rossmann session cookies needed for `account.ws` (which cookie names/domains the session uses) — to be confirmed during implementation with a real session.
- Whether the SSO hop `www.rossmann.de/.rest/sso/app` is required, or the account.ws API accepts the browser cookies directly — to be validated in a spike.
- Exact structure of the anybill `ReceiptDto` (store/address/currency fields) — to be confirmed against a real receipt response during implementation.
- No in-force ADRs (0001–0005) appear to need supersession; Rossmann onboarding follows ADR-0003's stated intent.