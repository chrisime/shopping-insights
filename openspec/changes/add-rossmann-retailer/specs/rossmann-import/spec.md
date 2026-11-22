## ADDED Requirements

### Requirement: Import Rossmann receipts into the receipt store
Feature: rossmann-import

Rule: The system MUST persist normalized Rossmann receipts through the shared import path so they appear in the same store as Lidl, REWE, and dm receipts and flow into the dashboard KPIs.

#### Scenario: Import a Rossmann receipt
- **GIVEN** a Rossmann receipt has been fetched
- **AND** the receipt details have been normalized into the shared receipt schema
- **WHEN** the system imports the normalized receipt
- **THEN** the receipt is persisted with retailer rossmann
- **AND** the receipt can be queried through the dashboard APIs

#### Scenario: Extract items from the receipt detail JSON
- **GIVEN** a Rossmann receipt detail has been fetched
- **WHEN** the system parses the receipt detail JSON for item lines
- **THEN** the receipt is stored with item names, prices, and quantities

#### Scenario: Store the original receipt PDF as archive
- **GIVEN** a Rossmann receipt PDF has been downloaded
- **WHEN** the system stores the receipt
- **THEN** the original PDF is kept alongside the receipt data

#### Scenario: Skip a receipt that cannot be normalized
- **GIVEN** a Rossmann receipt cannot be normalized into the receipt schema
- **WHEN** the system attempts to import it
- **THEN** the entry is reported as skipped
- **AND** the import continues with the remaining entries

#### Scenario: Avoid duplicate imports of the same receipt
- **GIVEN** a Rossmann receipt has already been imported
- **WHEN** the same receipt is encountered again
- **THEN** the system recognizes it as a duplicate
- **AND** does not persist a second copy

### Requirement: Report skipped Rossmann receipts
Feature: rossmann-import

Rule: The system MUST collect skipped Rossmann receipts in a skipped-receipts report so failures are visible after an import run.

#### Scenario: Report a skipped receipt
- **GIVEN** a Rossmann receipt was skipped during import
- **WHEN** the import run completes
- **THEN** the skipped receipt is recorded in the skipped-receipts report
- **AND** the report explains why the receipt was skipped