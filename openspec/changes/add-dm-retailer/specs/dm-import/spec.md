## ADDED Requirements

### Requirement: Import dm receipts into the receipt store
Feature: dm-import

Normalized dm eBons are persisted through the shared import path so they appear in the same store as Lidl and REWE receipts and flow into the dashboard KPIs.

#### Scenario: Import a dm eBon
- **GIVEN** a dm purchase history has been fetched
- **AND** the eBon details have been normalized into the shared receipt schema
- **WHEN** the system imports the normalized receipt
- **THEN** the receipt is persisted with retailer dm
- **AND** the receipt can be queried through the dashboard APIs

#### Scenario: Import a market eBon versus an online order
- **GIVEN** a dm purchase history contains a market purchase and an online order
- **WHEN** the system imports both entries
- **THEN** both are persisted
- **AND** each keeps its own purchase type so it can be distinguished later

#### Scenario: Skip a receipt that cannot be normalized
- **GIVEN** a dm purchase history entry cannot be normalized into the receipt schema
- **WHEN** the system attempts to import it
- **THEN** the entry is reported as skipped
- **AND** the import continues with the remaining entries

#### Scenario: Avoid duplicate imports of the same receipt
- **GIVEN** a dm receipt has already been imported
- **WHEN** the same receipt is encountered again
- **THEN** the system recognizes it as a duplicate
- **AND** does not persist a second copy

### Requirement: Report skipped dm receipts
Feature: dm-import

Skipped dm receipts are collected in a skipped-receipts report so failures are visible after an import run.

#### Scenario: Report a skipped receipt
- **GIVEN** a dm receipt was skipped during import
- **WHEN** the import run completes
- **THEN** the skipped receipt is recorded in the skipped-receipts report
- **AND** the report explains why the receipt was skipped