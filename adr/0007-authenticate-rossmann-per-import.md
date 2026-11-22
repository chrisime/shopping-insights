# ADR-0007: Authenticate the Rossmann account for each import

## Status

Accepted on 2026-11-22. Supersedes [ADR-0006](./0006-authenticate-rossmann-via-account-api.md).

## Context and Problem Statement

The Rossmann account API issues the identity required to obtain a short-lived anybill access token for in-store receipts. The original design expected to derive this identity from a Rossmann web session. A valid web session and the tested SSO flow failed to provide the app account identity. Dashboard and CLI imports need a way to authenticate without storing the user's password.

## Considered Options

- Ask for Rossmann account credentials for each online import.
- Reuse a Rossmann web session as proposed in ADR-0006. The observed session lacks the required app account identity.
- Store credentials for unattended imports. This adds persistent credential storage.

## Decision Outcome

Use per-import sign-in through the Rossmann account API. The dashboard submits credentials to the import job, and the CLI prompts in the terminal. The backend uses the resulting account identity to obtain the anybill token. A cookie file carrying an existing app account identity remains available as an alternative.

### Consequences

- Dashboard and CLI can use the same Rossmann authentication and import logic without persisting the password.
- Users enter their credentials again for a new online import unless they supply an existing app account identity.
- The account API expects app and platform metadata. Changes to the upstream API may require updating the client configuration. [Live comparison and implementation details](../docs/ROSSMANN_ANYBILL_ERKENNTNISSE.md#konto-api)
