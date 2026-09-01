## ADDED Requirements

### Requirement: Retrieve Rossmann purchase history
Feature: rossmann-purchase-history

Rule: The system MUST retrieve a user's Rossmann digital receipts through the two-stage Rossmann/anybill flow (Rossmann account token mint, then anybill App API v4) using an authenticated Rossmann session.

#### Scenario: Fetch the first page of receipts
- **GIVEN** the user is authenticated with Rossmann
- **WHEN** the system requests the receipt list from the anybill API
- **THEN** the system receives the first page of receipts with their metadata
- **AND** the response indicates whether more pages exist

#### Scenario: Fetch subsequent pages of receipts
- **GIVEN** the first page of receipts has been retrieved
- **AND** the response indicates more pages are available
- **WHEN** the system requests the next page using the continuation token
- **THEN** the system receives the next page of receipts

#### Scenario: Stop paginating when no more pages exist
- **GIVEN** a receipt list response indicates no more pages are available
- **WHEN** the system checks for further pages
- **THEN** the system stops requesting additional pages

### Requirement: Retrieve a single Rossmann receipt and its PDF
Feature: rossmann-purchase-history

Rule: The system MUST retrieve the detail of a single receipt and download its original PDF when available.

#### Scenario: Fetch the detail of a receipt
- **GIVEN** a receipt is present in the receipt list
- **WHEN** the system requests the detail for that receipt
- **THEN** the system receives the receipt's detail data

#### Scenario: Download the receipt PDF
- **GIVEN** a receipt supports PDF download
- **WHEN** the system requests the receipt PDF
- **THEN** the system receives a PDF document representing the original receipt

### Requirement: Authenticate with Rossmann using the account token mint
Feature: rossmann-purchase-history

Rule: The system MUST obtain an anybill access token from the authenticated Rossmann session by logging into the Rossmann account API and calling the receipt-auth token endpoint.

#### Scenario: Mint an anybill token from a Rossmann session
- **GIVEN** the user has an active Rossmann session
- **WHEN** the system logs in to the Rossmann account API and requests receipt-auth tokens
- **THEN** the system receives an anybill access token
- **AND** the token is used to authorize anybill receipt requests

#### Scenario: Refresh an expired anybill token
- **GIVEN** an anybill access token has expired
- **WHEN** the system requests a new token with the refresh token
- **THEN** the system receives a fresh access token
- **AND** the failed request is retried once with the new token

#### Scenario: Handle an invalid Rossmann session
- **GIVEN** the user's Rossmann session is not valid for token acquisition
- **WHEN** the system attempts to obtain an anybill token
- **THEN** the system reports the Rossmann session as invalid
- **AND** the system does not attempt to fetch receipts