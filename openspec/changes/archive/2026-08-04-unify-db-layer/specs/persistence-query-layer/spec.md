## ADDED Requirements

### Requirement: Receipts are persistable through the persistence layer

Rule: Imports MUST maintain receipts through a single unified data layer; new receipts are created, changed receipts are updated, and unchanged receipts are not written again.

#### Scenario: A new receipt is created

- **GIVEN** a receipt is not yet present in the database
- **WHEN** the receipt is stored through the persistence layer
- **THEN** the receipt is created
- **AND** the result counters report a creation

#### Scenario: An unchanged receipt is not written again

- **GIVEN** a receipt has already been stored and has not changed since
- **WHEN** the receipt is stored again
- **THEN** the stored data remains unchanged

#### Scenario: A changed receipt is updated

- **GIVEN** a receipt has already been stored and has changed since
- **WHEN** the receipt is stored again
- **THEN** the receipt data is updated
- **AND** the result counters report an update

### Requirement: Receipts are retrievable through the persistence layer

Rule: Read operations MUST return receipts in the canonical dictionary format, including items, payment methods, and retailer-specific fields.

#### Scenario: Receipts of a retailer are listed

- **GIVEN** stored receipts exist for a retailer
- **WHEN** the receipts of that retailer are fetched
- **THEN** all receipts of the retailer are returned including items, payment methods, and retailer-specific fields

#### Scenario: Receipts are found by item name with filters

- **GIVEN** receipts exist that contain an item with a certain name
- **WHEN** receipts are queried by item name with optional retailer and date filters
- **THEN** only the matching receipts are returned
- **AND** the matched item is flagged as a hit

#### Scenario: Receipts are found by date range

- **GIVEN** receipts exist across different date ranges and retailers
- **WHEN** receipts are queried by date range, optionally with a retailer filter
- **THEN** only the matching receipts are returned ordered by date descending

### Requirement: Analytical KPI queries are available

Rule: KPI queries MUST support optional retailer and date filters and return aggregated metrics.

#### Scenario: Basic KPIs are returned with filters

- **GIVEN** stored receipts exist
- **WHEN** basic KPIs are queried with optional retailer and date filters
- **THEN** total spending, receipt count, average receipt, discounts, and date bounds are returned

#### Scenario: Spending is aggregated by period

- **GIVEN** receipts exist across multiple periods and retailers
- **WHEN** spending is aggregated by day, month, or year
- **THEN** total spending, receipt count, and involved retailers are returned per period

#### Scenario: Top items are returned with search and pagination

- **GIVEN** receipts with items exist
- **WHEN** top items are queried by quantity or spending with optional search, pagination, and filters
- **THEN** name, total quantity, total spending, purchase count, and unit are returned per item
- **AND** deposit items are excluded

#### Scenario: Spending is analysed by weekday

- **GIVEN** receipts with a purchase date exist
- **WHEN** spending is aggregated by weekday
- **THEN** trip count, average spending, and total spending are returned per weekday

### Requirement: All persistence operations use one unified query technology

Rule: Write and read/analysis paths MUST use the same consistent query technology; there is no parallel query style.

#### Scenario: Write and read paths use the same technology

- **GIVEN** the persistence layer is initialized
- **WHEN** receipts are stored and KPI queries are executed
- **THEN** both operations use the same query technology
- **AND** the former PyPika and raw SQL calls are removed from the persistence layer
