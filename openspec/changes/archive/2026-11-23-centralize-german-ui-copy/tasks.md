## 1. Backend error-code contract

- [x] 1.1 Inventory frontend-consumed API error paths and define unique numeric codes from `4001–4099` for 4xx errors and `5001–5099` for 5xx errors, including migrations for existing out-of-range import codes.
- [x] 1.2 Return range-compliant `error_code` values consistently while preserving HTTP statuses and diagnostic details; add backend contract tests and do not retain legacy-code aliases.

## 2. German frontend copy catalog

- [x] 2.1 Add `web/src/locales/de.json` and a typed lookup with a readable fallback for missing catalog keys.
- [x] 2.2 Move all user-facing frontend copy into the catalog, including control labels, buttons, headings, placeholders, loading/empty/error states, tooltips, accessibility text, and document title; set the document language to German.
- [x] 2.3 Separate display labels from language-neutral filter/API values and verify requests keep their existing values.

## 3. Error-code presentation

- [x] 3.1 Update API clients and frontend error handling to parse error codes from non-success responses and map known codes to catalog messages; do not select user-facing error text or state from HTTP status alone.
- [x] 3.2 Add frontend tests for known codes, the same code across differing HTTP statuses, unknown/missing codes, and network failures.

## 4. Verification

- [x] 4.1 Run backend tests with `./.venv/bin/python -m pytest -q` and frontend tests, `vp check`, typecheck, and build from `web/`.
- [x] 4.2 Run `openspec validate centralize-german-ui-copy --type change --strict` before archive.
