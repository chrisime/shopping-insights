# ADR-0005: Authenticate dm via OAuth 2.0 PKCE with session-cookie reuse

## Status

Accepted

## Date

2026-08-31

## Context and Problem Statement

dm exposes purchase history through authenticated JSON APIs (purchasehistory, eBon detail/download). Access tokens minted by `signin.dm.de` expire after ~2.5 minutes, so static bearer tokens are useless as credentials. The project needs a repeatable way to obtain fresh tokens for dm imports that follows the existing shared auth-method resolution (`--browser` / `--cookies-file`) and the constraint of no third-party OAuth/auth libraries.

## Considered Options

- OAuth 2.0 authorization-code flow with PKCE, reusing the user's dm session cookies (`signin.dm.de`/`services.dmtech.com`)
- Static bearer tokens captured from the browser
- Username/password login against the dm token endpoint
- Third-party OAuth library (e.g. authlib) wrapping the flow

## Decision Outcome

Chosen option: "OAuth 2.0 authorization-code flow with PKCE, reusing the user's dm session cookies", because it yields fresh short-lived tokens without storing credentials, works with the project's plain-`requests` constraint (PKCE is simple stdlib work: `secrets`, `hashlib`, `base64`), and slots into the existing `--browser` / `--cookies-file` auth-method resolution. Static tokens expire in minutes; username/password login stores credentials and is out of scope; a third-party OAuth library violates the no-third-party-auth-libraries constraint.

### Consequences

- Good, because dm imports authenticate through the user's existing dm session, with no credential storage.
- Good, because token acquisition reuses the shared auth-method pattern already used by Lidl and REWE.
- Bad, because imports depend on a live dm session; cookie exports must include the `signin.dm.de` and `*.services.dmtech.com` domains, which the `check` flow must validate.
- Bad, because the ~2.5-minute token lifetime means a run that exceeds it must re-acquire a token and retry on 401.