## Context

The analyzer currently imports Lidl and REWE receipts and serves KPIs to a Vue dashboard. dm exposes the full purchase history (Markt-eBons + online orders) via authenticated JSON APIs. Reverse-engineering of the dm web frontend (`account.dm.de/purchases`) found:

- List: `purchasehistory-prod.services.dmtech.com/v1/purchasehistory` with `size` and `untilDateTimePlaced` cursor pagination.
- Detail: `ebon-prod.services.dmtech.com/api/customer/ebons/<id>` (store, register, discount, payback points, `bonItems` DAN).
- Download: `.../api/customer/ebons/<id>/download` (PDF).
- Auth: OAuth 2.0 authorization-code + PKCE against `signin.dm.de/dm-de/oauth-anonymous`, client `nextaccount`, scopes `openid email roles customerId`. Access tokens expire in ~2.5 minutes.

The project favours plain `requests`, no third-party retry/DI/ABC layers, a shared single import path (`workflows/local_import.py`), and a shared receipt schema. ADR-0003 explicitly commits to onboarding future retailers via the same single shared import path.

```text
System context: dm purchase-history import

+------------+     OAuth PKCE + bearer tokens      +---------------------------+
|   Browser  | -----------------------------------> | signin.dm.de (OAuth/SSO)  |
| (dm session|                                      +---------------------------+
|   active)  |
+------------+
     | cookies-file export (signin.dm.de + services.dmtech.com)
     v
+---------------------------------------------------------+
|                     Analyzer (CLI)                       |
|                                                          |
|  +----------------+   bearer   +-----------------------+ |
|  | auth/dm_auth   | -------->  | dm_client.py          | |
|  | (PKCE flow)    |            |                       | |
|  +----------------+            | /v1/purchasehistory   | |
|        |                       | /api/customer/ebons/* | |
|        |                       +-----------------------+ |
|        |                                   |             |
|  +-----v-------------------+               | HTTPS      |
|  | workflows/dm_workflow   |               v            |
|  | -> local_import()       |   +------------------------+
|  +-------------------------+   | dmtech.com APIs        |
|        |                      | (purchasehistory,      |
|        v                       |  ebon)                 |
|  +-------------------+         +------------------------+
|  | SQLite (SQLAlchemy|         +------------------------+
|  |  Core + Alembic)  |         | products.dm.de (DAN -> |
|  +-------------------+         |  name enrichment)      |
|                               +------------------------+
+---------------------------------------------------------+
        |
        v
  Vue dashboard (existing KPIs/receipts/items APIs, unchanged)
```

Boundaries: the CLI fetches via dmtech.com APIs using a bearer token minted by the OAuth flow; normalized receipts persist through the existing import path into SQLite; the dashboard reads them through existing APIs with no frontend changes.

## Goals / Non-Goals

**Goals:**
- Add dm as a supported retailer (`--retailer dm`) for initial and update imports.
- Acquire dm access tokens from the user's dm session (browser or cookie file) using OAuth PKCE.
- Fetch the paginated purchase history, eBon details, and PDF receipts.
- Normalize dm eBons into the shared receipt schema and persist them through the existing import path so dashboard KPIs/items APIs work unchanged.
- Reuse shared auth-method resolution (`--browser` / `--cookies-file`) patterns.

**Non-Goals:**
- Online order (order-history) line items are out of scope initially; only their existence/amounts are captured for KPI totals.
- No product-name enrichment beyond the dm products gateway; DAN-only items may ship without names if enrichment is unavailable.
- No dashboard/frontend changes (dm receipts flow through existing APIs).
- No refresh-token persistence or daemonized background refresh.

## Decisions

### D1: OAuth 2.0 authorization-code + PKCE for token acquisition
dm access tokens live ~2.5 minutes and static tokens are useless. The browser's dm session on `signin.dm.de` lets the app perform the code flow with PKCE (`code_challenge`/`code_verifier`) and receive fresh tokens without re-login.

- **Why:** Matches the reverse-engineered flow; no credentials stored; session validity is the auth boundary.
- **Alternatives considered:** (a) static bearer tokens — rejected, expire in minutes; (b) login via username/password — rejected, out of scope and less secure; (c) refresh-token grant — not available for public client without secret.

### D2: Session-cookie reuse for the silent-auth hop
The code flow requires the user's `signin.dm.de`/`services.dmtech.com` session cookies. Reuse the existing `--browser` (drive a real browser) and `--cookies-file` (JSON export) mechanisms from the shared auth-method resolution instead of inventing a new auth switch.

- **Why:** AGENTS.md requires shared auth-method resolution between retailers.
- **Alternatives considered:** separate dm-only auth flag — rejected, diverges from the established pattern.

### D3: New `client/dm_client.py` + `config/dm_config.py`, no new libraries
Endpoints, client id, scopes, cookie file, and JSON output file live in `config/dm_config.py`; all HTTP in `client/dm_client.py` using plain `requests` (session reuse). Retry/backoff on 429/5xx mirrors Lidl behaviour with plain `requests` + `time.sleep`.

- **Why:** Project constraints forbid third-party retry/HTTP wrappers; keeps symmetry with Lidl/REWE clients.
- **Alternatives considered:** introducing an OAuth library (`authlib`) — rejected by project constraint "no third-party retry libraries"; PKCE is simple stdlib work (`hashlib`, `base64`, `secrets`).

### D4: Normalize into the shared receipt schema with a dm retailer marker
Map eBon fields to `shared/receipt_schema.py`: `purchase_date`/time → `purchase_date`, store `address` → `address`, `cashRegisterId` → `register`, `discount` → `discount`, `totalAmount` → `total_price`, `bonItems` DAN → `items` with DAN as item id. Add retailer-specific dm defaults in `_RETAILER_EXTRA_DEFAULTS` (e.g. `total_payback_points`) rather than widening shared fields.

The dm API only returns DAN identifiers without names or prices. To surface itemized receipts, the workflow downloads the original eBon PDF and parses it with `parsing/dm_pdf_items_extractor.py` (single-item and multi-quantity line formats). Those parsed items (`pdfItems`) take precedence over the DAN-only `bonItems`; DANs are merged into the PDF items by position when both are present. DAN → product-name enrichment via the products gateway is only a fallback when no PDF was parsed.

- **Why:** Dashboard KPIs and the items view consume the normalized schema; a new retailer must not change the shared contract, and itemized data requires parsing the PDF because the API payload is DAN-only.
- **Alternatives considered:** a dm-specific DTO sidecar — rejected, would fork the shared normalization and break KPIs; DAN-only items without names — rejected for the items dashboard, since the PDFs contain the real names/prices.

### D5: Drive import through the existing shared path (`import_local_sources`)
`workflows/dm_workflow.py` fetches/parses dm data and delegates to the shared `import_local_sources()` loader → parse → validate → persist pipeline, per ADR-0003. Dedup/hash handling and skipped-receipt reporting come from the shared machinery.

- **Why:** ADR-0003 mandates one shared import path for future retailers; avoids a new abstraction layer.
- **Alternatives considered:** a second pipeline tier — rejected by ADR-0003.

## Risks / Trade-offs

- [dm frontend API changes without notice] -> Mitigation: endpoints/config centralized in `config/dm_config.py`; document the reverse-engineering source; treat API drift as a config/tests fix.
- [Session-cookie export missing the `signin.dm.de`/`services.dmtech.com` cookies] -> Mitigation: `check --retailer dm` validates session reachability and produces a traffic-light diagnostic like Lidl/REWE; document the required cookie domains in the CLI help.
- [2.5-minute token lifetime makes long paginated imports fragile] -> Mitigation: acquire one token per run; if a 401 occurs mid-run, re-run the silent code flow and retry once; keep imports under the token lifetime.
- [DAN item IDs without names degrade the items view] -> Mitigation: itemized names/prices are parsed from the original eBon PDF (`parsing/dm_pdf_items_extractor.py`); when a PDF is unavailable, fall back to the dm products gateway enrichment, otherwise store the DAN with an empty description and let a later enrichment step fill names.
- [DM only exposes eBons for accounts that opted in / for Market purchases] -> Mitigation: treat missing eBon detail as a skipped receipt with a clear reason in the report.

## Migration Plan

1. Add `config/dm_config.py`, `client/dm_client.py`, `auth/dm_auth.py`, `workflows/dm_workflow.py`.
2. Wire `--retailer dm` into `fetch_tickets.py` (initial/update/check/export).
3. Register dm in `shared/retailer_runtime.py` (code `dm`, name `DM`, receipts JSON file) and add dm extras to `shared/receipt_schema.py`.
4. Add Alembic migration if new persisted fields (e.g. payback points) are needed.
5. Verify via `check`, then `initial`, then `update`; confirm dashboard KPIs include dm receipts.

Rollback: removing dm is purely additive — drop `_RUNTIME_DEFINITIONS["dm"]` and remove dm config/client/workflow modules; no schema migration required if no columns were added.

## Open Questions

- Should online orders (order-history) be imported as receipts too, or only Market eBons? **Resolved:** only Market eBons are persisted; online orders are recognized, counted and reported separately, matching the non-goal.
- Do we need persisted payback-points totals, or is that derivable from stored receipts? (Affects whether a schema migration is needed.)
- Is DAN → product-name enrichment mandatory for the items dashboard, or acceptable as a later enhancement? (Currently a later enhancement.)
- None of the in-force ADRs (0001–0004) appear to need supersession for this change; dm onboarding follows ADR-0003's stated intent.