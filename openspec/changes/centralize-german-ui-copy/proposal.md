## Why

User-facing text is currently scattered across Vue components and composables, while some API error responses expose human-readable details. A German copy catalog and stable backend error codes will make wording consistent and let the frontend choose error messages by code rather than infer meaning from HTTP status.

## What Changes

- Centralize frontend-facing German text, including labels, buttons, headings, statuses, tooltips, accessibility text, document title, and error messages, in `web/src/locales/de.json`.
- Add a small typed frontend lookup for the catalog without introducing an i18n dependency.
- Preserve language-neutral API values and use stable numeric application error codes from `4001–4099` for 4xx failures and `5001–5099` for 5xx failures. Migrate existing retailer-specific import codes into these ranges without compatibility aliases.
- Map API error codes to German UI messages in the frontend. HTTP status remains available for transport and diagnostics but SHALL NOT alone determine the user-facing error message or state.
- Set the document language to German and provide generic German fallback text for unknown API codes and network failures.
- Keep P3 component extraction out of scope; begin that as a separate change after this one is complete.

## Capabilities

### New Capabilities

- `german-ui-copy`: Centralize all user-facing frontend text in a German JSON catalog while keeping API/domain values language-neutral.
- `api-error-codes`: Return stable numeric codes for frontend-consumed API errors and let the frontend map those codes to user-facing messages independently of HTTP status.

### Modified Capabilities

- None.

## Impact

Frontend Vue components, composables, API adapters, types, tests, `web/index.html`, and the API routes/services whose errors are displayed in the dashboard. No third-party dependencies or changes to successful API payloads are intended.
