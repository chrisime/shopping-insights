# receipt-loading-state Specification

## Purpose

Show shoppers whether receipt lookup is loading, completed without results, or failed.

## Requirements

### Requirement: Receipt lookup failure is distinct from an empty result

The receipt list SHALL show loading while a lookup is in progress, an empty state when a lookup succeeds with no receipts, and a clear error state when a lookup fails. A failed lookup SHALL NOT be presented as a successful empty result. A new lookup SHALL clear the previous error state.

#### Scenario: A successful lookup finds no receipts

- **GIVEN** a receipt lookup completes successfully with no matching receipts
- **WHEN** the shopper views the receipt list
- **THEN** the empty-results message is shown
- **AND** no error message is shown

#### Scenario: A receipt lookup fails

- **GIVEN** a receipt lookup fails
- **WHEN** the shopper views the receipt list
- **THEN** a clear error message is shown
- **AND** the empty-results message is not shown

#### Scenario: A new lookup starts after a failure

- **GIVEN** the previous receipt lookup failed
- **WHEN** the shopper opens the receipt list again
- **THEN** the loading state is shown
- **AND** the previous error is cleared
