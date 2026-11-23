## ADDED Requirements

### Requirement: Vue dashboard modules have cohesive responsibility boundaries

Dashboard Vue components, composables, and utilities SHALL each have a clear, cohesive responsibility. Components SHALL own presentation and page coordination; composables SHALL own genuinely shared state or flows; utilities SHALL contain reusable pure logic. Retailer-specific KPI rules SHALL have retailer-focused ownership, with shared presentation limited to common structure. Refactoring SHALL NOT split modules solely by size or introduce unnecessary abstractions.

#### Scenario: A large component has separable responsibilities

- **GIVEN** a dashboard component coordinates multiple distinct responsibilities
- **WHEN** its structure is reviewed for maintainability
- **THEN** cohesive responsibilities are separated behind clear interfaces where that improves ownership or testability
- **AND** wrapper-only components or abstractions without a concrete benefit are not introduced

#### Scenario: Retailer KPI rules are maintained by retailer

- **GIVEN** dashboard metrics include retailer-specific KPI rules
- **WHEN** those metrics are organized for display
- **THEN** each retailer's rules have a clear retailer-focused owner
- **AND** presentation is shared only where the retailers have genuinely common structure

#### Scenario: Structural refactoring preserves dashboard behavior

- **GIVEN** the dashboard components, composables, or utilities have been reorganized
- **WHEN** shoppers use dashboard, import, receipt, and chart flows with the same data
- **THEN** visible results and interactions remain unchanged
- **AND** API contracts and language-neutral filter or retailer values remain unchanged
