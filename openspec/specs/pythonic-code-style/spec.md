# Pythonic Code Style Specification

## Purpose
Adopt idiomatic Python through built-in generics and modern annotations while ensuring these changes remain cosmetic and preserve runtime behavior.

## Requirements

### Requirement: Built-in generics in annotations

Rule: Public and internal annotations SHALL use PEP 585 built-in generics (`list[...]`, `dict[...]`, `tuple[...]`, `set[...]`) and PEP 604 unions (`X | None`) rather than legacy `typing` generics.

#### Scenario: Optional annotated as union with None
- **GIVEN** a function or attribute whose value may be absent
- **WHEN** its annotation is declared
- **THEN** it uses the `X | None` form
- **AND** the `Optional[...]` form is not used

#### Scenario: Containers use built-in generics
- **GIVEN** an annotation describing a container
- **WHEN** the type is declared
- **THEN** it uses built-in generics such as `list[...]`, `dict[...]`, or `tuple[...]`
- **AND** legacy forms such as `List[...]`, `Dict[...]`, or `typing.List[...]` are not used

#### Scenario: Imported legacy generics removed
- **GIVEN** a module that previously imported `typing` generics only for annotations
- **WHEN** the annotations are modernized
- **THEN** the now-unused `typing` imports are removed
- **AND** `from __future__ import annotations` is used only where required for runtime compatibility

### Requirement: Idiomatic Python patterns

Rule: Code SHALL avoid non-Pythonic patterns that mirror Java or C# idioms, including gratuitous getters/setters, verbose type-only abstractions, and ceremony that standard library features already cover.

#### Scenario: No gratuitous accessor methods
- **GIVEN** a plain data holder with only attribute access
- **WHEN** its API is reviewed
- **THEN** attributes are accessed directly rather than through getter/setter methods
- **AND** no boilerplate accessor is added without behavior

#### Scenario: Standard library idioms preferred
- **GIVEN** a transformation or collection operation
- **WHEN** it is implemented
- **THEN** idiomatic constructs (comprehensions, `dataclasses`, context managers, `pathlib`) are used where they are the natural fit
- **AND** verbose hand-rolled loops or custom boilerplate are avoided unless they add clarity

### Requirement: Annotation modernization preserves behavior

Rule: Annotation modernization SHALL be strictly cosmetic: it changes only type annotations and imports, never runtime behavior or public contracts.

#### Scenario: Modernized code behaves identically
- **GIVEN** modules refactored for built-in generics
- **WHEN** the backend test suite runs
- **THEN** all existing tests pass
- **AND** no runtime behavior or public signature semantics change
