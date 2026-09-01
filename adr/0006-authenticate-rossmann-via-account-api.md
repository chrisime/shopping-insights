# ADR-0006: Authenticate Rossmann digital receipts via the Rossmann account API plus anybill bearer token

## Status

Accepted

## Date

2026-09-01

## Context and Problem Statement

Rossmann serves digital receipts through the white-label provider anybill. The web interface has no receipt menu point and sits behind a Fastly Client Challenge, so there is no straightforward web-UI path. The Rossmann app derives short-lived anybill access tokens from the retailer's own account API (`rsmappapi.rossmann.net/account.ws/v2`): `POST accounts/login` yields `accountId`/`accountHash`, and `GET accounts/{accountId}/receipt/auth` mints the anybill token. The project needs a repeatable way to obtain these tokens that follows the shared auth-method resolution (`--browser` / `--cookies-file`) and the no-third-party-auth-libraries constraint.

## Considered Options

- Mint the anybill token through the Rossmann account API, reusing the user's Rossmann session (browser or cookie file) to derive `accountId`/`accountHash`
- `POST accounts/login` with stored email/password credentials
- Only anonymous anybill account use (no Rossmann login)

## Decision Outcome

Chosen option: "Mint the anybill token through the Rossmann account API, reusing the user's Rossmann session", because it obtains short-lived tokens without storing credentials, works with the plain-`requests` constraint, and slots into the existing `--browser` / `--cookies-file` auth-method resolution alongside Lidl, REWE, and dm. Stored email/password would introduce credential storage; anonymous accounts cannot export receipts (`_bill-anonymousnoexport`).

### Consequences

- Good, because Rossmann imports authenticate through the user's existing Rossmann session, with no credential storage.
- Good, because token acquisition reuses the shared auth-method pattern already used by the other retailers.
- Bad, because imports depend on a live Rossmann session; cookie exports must include the Rossmann session cookies, which the `check` flow must validate.
- Bad, because the anybill token lifetime requires refresh/retry on 401 during long imports.