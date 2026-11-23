## Purpose

Give frontend-visible API errors stable machine-readable identities so the dashboard can choose German messages by error code rather than infer error meaning from HTTP status.

## ADDED Requirements

### Requirement: Frontend-visible API errors have stable error codes

Frontend-visible API errors SHALL include a stable numeric `error_code`. Codes SHALL use `4001–4099` for 4xx failures and `5001–5099` for 5xx failures. HTTP status remains available, but the frontend SHALL NOT use it alone to select user-facing text or error state. Assigned code meanings SHALL remain stable.

#### Scenario: An API error is returned with a stable code

- **GIVEN** an API operation fails for a known application reason
- **WHEN** the error is returned to the dashboard
- **THEN** the response includes a stable numeric error code from the range matching the HTTP error class
- **AND** the HTTP status remains available independently

#### Scenario: A client error code is returned with different 4xx statuses

- **GIVEN** the frontend receives the same error code with different 4xx HTTP statuses
- **WHEN** it presents the error
- **THEN** it selects the same localized message by error code
- **AND** it does not infer the error meaning from HTTP status alone

#### Scenario: Legacy import codes are migrated

- **GIVEN** an import error previously used a retailer-specific code outside the defined ranges
- **WHEN** the API returns that error after this change
- **THEN** it uses its assigned stable code from the 4xx or 5xx range
- **AND** the frontend does not accept or require the legacy code as an alias

### Requirement: The frontend maps error codes to German catalog messages

The frontend SHALL map known API error codes to German messages from the German catalog. An unknown or missing code SHALL produce a generic German API-error message, and a failure with no API response SHALL produce a generic German network-error message.

#### Scenario: A known API error code is received

- **GIVEN** the frontend receives an API error code present in the German catalog
- **WHEN** the error is displayed
- **THEN** the German message associated with that code is shown

#### Scenario: An unknown API error code is received

- **GIVEN** the frontend receives an unknown or missing API error code
- **WHEN** the error is displayed
- **THEN** a generic German API-error message is shown

#### Scenario: The API cannot be reached

- **GIVEN** a request fails without receiving an API response
- **WHEN** the error is displayed
- **THEN** a generic German network-error message is shown
