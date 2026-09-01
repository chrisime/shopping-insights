# dm-purchase-history Specification

## Purpose
Retrieve a user's dm purchase history (Markt-eBons and online orders) through the dm customer API, authenticate via OAuth 2.0 PKCE against the user's dm session, and download eBon details and original PDF receipts.

## Requirements

### Requirement: Retrieve dm purchase history

Rule: The system MUST retrieve a user's dm purchase history (Markt-eBons and online orders) using the dm customer API with OAuth 2.0 PKCE authentication.

#### Scenario: Fetch the first page of purchase history

- **GIVEN** the user is authenticated with dm
- **WHEN** the system requests the purchase history list
- **THEN** the system receives the first page of purchases with their metadata (id, purchase type, placed date, currency, total amount)
- **AND** the response indicates whether more pages exist

#### Scenario: Fetch subsequent pages of purchase history

- **GIVEN** the first page of purchase history has been retrieved
- **AND** the response indicates more pages are available
- **WHEN** the system requests the next page anchored at the most recent purchase date of the current page
- **THEN** the system receives the next page of older purchases

#### Scenario: Stop paginating when no more pages exist

- **GIVEN** a purchase history response indicates no more pages are available
- **WHEN** the system checks for further pages
- **THEN** the system stops requesting additional pages

### Requirement: Retrieve dm eBon details

Rule: The system MUST retrieve the full detail of a single dm eBon, including store, register, discount, payback points, and purchased item identifiers.

#### Scenario: Fetch the detail of an eBon

- **GIVEN** a purchase history contains a market purchase with an eBon identifier
- **WHEN** the system requests the detail for that eBon
- **THEN** the system receives the eBon's date, time, total amount, currency, store address, register number, discount, and payback points
- **AND** the system receives the list of purchased item identifiers

#### Scenario: Distinguish a market purchase from an online order

- **GIVEN** a purchase history entry
- **WHEN** the system inspects its purchase type
- **THEN** the system treats market purchases as eBons and online orders as order-history entries

### Requirement: Download dm eBon PDF receipts

Rule: The system MUST download the original eBon PDF when the eBon marks a downloadable receipt.

#### Scenario: Download the eBon PDF

- **GIVEN** an eBon detail marks the receipt as downloadable
- **WHEN** the system requests the eBon PDF download
- **THEN** the system receives a PDF document representing the original receipt

### Requirement: Authenticate with dm using OAuth 2.0 PKCE

Rule: The system MUST acquire fresh dm access tokens through the OAuth 2.0 authorization-code flow with PKCE, using the user's dm session.

#### Scenario: Acquire a fresh access token from the user's dm session

- **GIVEN** the user has an active dm session in the browser
- **WHEN** the system performs the OAuth authorization-code flow with PKCE
- **THEN** the system receives a fresh access token
- **AND** the token is used to authorize dm purchase-history requests

#### Scenario: Handle an invalid dm session

- **GIVEN** the user's dm session is not valid for token acquisition
- **WHEN** the system attempts to acquire an access token
- **THEN** the system reports the dm session as invalid
- **AND** the system does not attempt to fetch purchase history