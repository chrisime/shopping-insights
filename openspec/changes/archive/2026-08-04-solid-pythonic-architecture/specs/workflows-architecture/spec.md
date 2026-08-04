# Workflows Architecture Spec

## ADDED Requirements

### Requirement: Single shared local-import path

Feature: Local import orchestration
Rule: Both retailer workflows SHALL import receipts from local JSON/HTML sources through one shared code path that sequences load, parse, validate, and persist.

#### Scenario: Retailer workflow imports through the shared path
- **GIVEN** a retailer workflow that needs to import receipts from a local source
- **WHEN** the workflow performs a local import
- **THEN** it sequences load, parse, validate, and persist through the single shared import path
- **AND** the retailer-specific code supplies only its own loader and parser to that path

#### Scenario: Both retailers use the same shared path
- **GIVEN** the Lidl and REWE workflow implementations
- **WHEN** either performs a local import
- **THEN** both delegate to the same shared import helper
- **AND** no retailer implements its own local-import orchestration

### Requirement: No multi-layer pipeline abstraction

Rule: The workflow layer SHALL NOT maintain stacked abstraction layers (e.g. a pipeline strategy layered over a template-method base) when a single shared path and one thin base suffice.

#### Scenario: Pipeline layer removed
- **GIVEN** the previous workflow layer with a separate pipeline abstraction
- **WHEN** the de-abstraction refactor is applied
- **THEN** the pipeline abstraction layer is removed
- **AND** no equivalent new abstraction replaces it

#### Scenario: At most one thin workflow base
- **GIVEN** the workflow layer after the refactor
- **WHEN** the shared workflow structure is inspected
- **THEN** there is at most one thin workflow base
- **AND** retailer workflows are concrete functions or thin subclasses, not additional inheritance tiers

### Requirement: No interface-only abstractions

Feature: Abstraction discipline
Rule: The refactor SHALL NOT introduce ABCs, interfaces, or dependency-injection frameworks solely to add layers.

#### Scenario: No new ABCs introduced
- **GIVEN** the in-scope modules under refactor
- **WHEN** the refactor is complete
- **THEN** no new abstract base classes or interfaces are added
- **AND** existing workflow entry points used by the CLI remain callable with their current signatures
