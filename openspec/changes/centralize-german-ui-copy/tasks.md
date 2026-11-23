## 1. Backend error-code contract

- [ ] 1.1 Inventory frontend-consumed API error paths and define stable numeric codes for those that currently return only HTTP status or human-readable detail; preserve all existing code meanings.
- [ ] 1.2 Return the numeric `error_code` consistently for those API failures while preserving HTTP statuses and diagnostic details; add backend contract tests for error responses.

## 2. German frontend copy catalog

- [ ] 2.1 Add `web/src/locales/de.json` and a typed lookup with a readable fallback for missing catalog keys.
- [ ] 2.2 Move all user-facing frontend copy into the catalog, including control labels, buttons, headings, placeholders, loading/empty/error states, tooltips, accessibility text, and document title; set the document language to German.
- [ ] 2.3 Separate display labels from language-neutral filter/API values and verify requests keep their existing values.

## 3. Error-code presentation

- [ ] 3.1 Update API clients and frontend error handling to parse error codes from non-success responses and map known codes to catalog messages; do not select user-facing error text or state from HTTP status alone.
- [ ] 3.2 Add frontend tests for known codes, the same code across differing HTTP statuses, unknown/missing codes, and network failures.

## 4. Verification

- [ ] 4.1 Run backend tests with `./.venv/bin/python -m pytest -q` and frontend tests, `vp check`, typecheck, and build from `web/`.
- [ ] 4.2 Run `openspec validate centralize-german-ui-copy --type change --strict` before archive.
