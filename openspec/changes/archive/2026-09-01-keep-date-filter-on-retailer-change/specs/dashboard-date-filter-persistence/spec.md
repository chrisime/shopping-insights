## ADDED Requirements

### Requirement: Preserve the date filter when switching retailers
Feature: dashboard-date-filter-persistence

Rule: The system MUST preserve the user-selected date filter when the retailer is changed in the dashboard, resetting only pagination and search.

#### Scenario: Keep an explicit date range on retailer change
- **GIVEN** the dashboard shows a date range selected by the user
- **AND** the user switches the retailer filter
- **WHEN** the dashboard refreshes for the new retailer
- **THEN** the selected start and end dates remain unchanged
- **AND** the dashboard requests data for the new retailer within the preserved date range

#### Scenario: Reset pagination and search on retailer change
- **GIVEN** the user has searched for an item and navigated to a later page
- **AND** the user switches the retailer filter
- **WHEN** the dashboard refreshes for the new retailer
- **THEN** the search term is cleared
- **AND** the page is reset to the first page

#### Scenario: Seed the date range when no explicit range is set
- **GIVEN** the user switches the retailer filter while no date range is selected
- **WHEN** the dashboard receives the new retailer's payload
- **THEN** the date filter is seeded from the payload's available minimum and maximum dates