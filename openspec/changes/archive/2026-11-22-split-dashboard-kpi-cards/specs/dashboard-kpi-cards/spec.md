## ADDED Requirements

### Requirement: General and discount metrics are presented separately
Feature: Dashboard KPI cards

Rule: General spending facts and retailer discounts appear in distinct dashboard sections.

The dashboard SHALL present general spending metrics and retailer discounts in two distinct sections titled "Allgemeine Informationen" and "Rabatte".

#### Scenario: General spending metrics have their own section
- **GIVEN** the dashboard has receipt data
- **WHEN** the user opens the Ausgaben view
- **THEN** the dashboard shows a section titled "Allgemeine Informationen"
- **AND** the section shows cards for Ausgaben, Kassenbons, Pfandrückgabe, and Gesamter Preisvorteil

#### Scenario: Retailer discounts have their own section
- **GIVEN** the dashboard has receipt data with discount metrics
- **WHEN** the user opens the Ausgaben view
- **THEN** the dashboard shows a section titled "Rabatte"
- **AND** the section shows the retailer discount cards that have data

#### Scenario: Discount section is omitted when no discount metrics exist
- **GIVEN** the dashboard only has receipt data without discount metrics
- **WHEN** the user opens the Ausgaben view
- **THEN** the dashboard does not show a section titled "Rabatte"
- **AND** the dashboard still shows the section titled "Allgemeine Informationen"

#### Scenario: Discount section stays visible with zero values for a discount-capable retailer
- **GIVEN** the user selected a retailer that reports discount metrics
- **AND** the selected period has receipts but no discounts
- **WHEN** the user opens the Ausgaben view
- **THEN** the dashboard shows a section titled "Rabatte"
- **AND** the discount cards show 0 € and 0,0 %

### Requirement: Retailer discount cards keep their retailer grouping
Feature: Dashboard KPI cards

Rule: Discount cards are grouped by retailer inside the discount section.

Discount cards SHALL remain grouped per retailer inside the "Rabatte" section.

#### Scenario: Multiple retailers keep separate discount groups
- **GIVEN** the dashboard has receipts from more than one discount-capable retailer
- **WHEN** the user opens the Ausgaben view
- **THEN** the "Rabatte" section shows one group per retailer with data
- **AND** each group contains only that retailer's discount cards

### Requirement: Rossmann discount summary
Feature: Dashboard KPI cards

Rule: Each discount-capable retailer shows a savings summary card.

Each discount-capable retailer SHALL show a savings summary card; Rossmann SHALL show a "Preisvorteil" card.

#### Scenario: Rossmann shows a Preisvorteil card
- **GIVEN** the dashboard has Rossmann receipts with discount data
- **WHEN** the user opens the Ausgaben view
- **THEN** the Rossmann discount group shows a "Preisvorteil" card
- **AND** the card shows the total Rossmann discount amount and its percentage
