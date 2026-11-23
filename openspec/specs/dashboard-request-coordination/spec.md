# dashboard-request-coordination Specification

## Purpose

Keep dashboard results synchronized with effective filters without issuing redundant refreshes or accepting stale responses.

## Requirements

### Requirement: Effective filter changes produce one current dashboard refresh

The dashboard SHALL issue one refresh for each effective filter state. Search input SHALL remain debounced by 400 milliseconds; dependent page resets and retailer changes SHALL be included in the resulting refresh rather than triggering duplicate refreshes. Only the most recently requested dashboard response SHALL update the displayed payload or loading state.

#### Scenario: Searching from a later page refreshes the first page once

- **GIVEN** the dashboard is showing a later page of results
- **WHEN** the shopper enters a search term of at least three characters
- **THEN** the page resets to the first page
- **AND** exactly one dashboard request is made after the search debounce

#### Scenario: Changing retailer cancels a pending search refresh

- **GIVEN** a search refresh is pending
- **WHEN** the shopper changes retailer and the search is cleared
- **THEN** exactly one request is made for the new retailer with the cleared search

#### Scenario: A stale dashboard response arrives after a newer response

- **GIVEN** two dashboard requests are in flight for different filter states
- **WHEN** the newer request completes before the older request
- **THEN** the dashboard continues to show the newer response
- **AND** the older response does not change the displayed payload or loading state
