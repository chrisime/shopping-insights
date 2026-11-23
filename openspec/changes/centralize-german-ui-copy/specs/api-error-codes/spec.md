## Purpose

Give frontend-visible API errors stable machine-readable identities so the dashboard can choose German messages by error code rather than infer error meaning from HTTP status.

## ADDED Requirements

### Requirement: Frontend-visible API errors have stable error codes

API errors consumed by the frontend SHALL include a stable numeric `error_code` while preserving the appropriate HTTP status for transport and diagnostics. The frontend SHALL NOT use HTTP status alone to select a user-facing error message or error state. Existing numeric error codes SHALL remain stable.

#### Scenario: An API error is returned with a stable code

- **GIVEN** an API operation fails for a known application reason
- **WHEN** the error is returned to the dashboard
- **THEN** the response includes the stable numeric error code for that reason
- **AND** the HTTP status remains available independently

#### Scenario: The same error code is returned with different HTTP statuses

- **GIVEN** the frontend receives the same error code with different HTTP statuses
- **WHEN** it presents the error
- **THEN** it selects the same localized message by error code
- **AND** it does not infer the error meaning from HTTP status alone

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
