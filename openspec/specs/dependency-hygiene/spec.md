# Dependency Hygiene Specification

## Purpose
Keep the project's declared dependencies (backend `pyproject.toml` + `uv.lock`, frontend `web/package.json` + `web/pnpm-lock.yaml`) minimal, current, and in sync with what the code actually imports, so installs are lean and the test suite and production build stay green.

## Requirements

### Requirement: Declared backend dependencies match actual imports

Rule: Every package in `pyproject.toml` SHALL be used by the project source, entry points, or tests; packages that are never used SHALL be removed.

#### Scenario: Unused backend package removed from requirements

- **GIVEN** a package declared in `pyproject.toml` that is not imported by any source module or test
- **WHEN** the dependency list is updated
- **THEN** the package is removed from `pyproject.toml`
- **AND** no source module or test imports that package

#### Scenario: Used backend package kept

- **GIVEN** a package in `pyproject.toml` that is imported by at least one source module or test
- **WHEN** the dependency list is reviewed
- **THEN** the package remains declared in `pyproject.toml`

#### Scenario: Clean install resolves

- **GIVEN** a fresh virtual environment and the updated `pyproject.toml`
- **WHEN** `uv sync --locked` runs
- **THEN** all declared packages resolve and install without errors

### Requirement: Declared frontend dependencies match actual imports

Rule: Every package in `web/package.json` dependencies and devDependencies SHALL be imported by the frontend source or its tests; packages that are never imported SHALL be removed.

#### Scenario: Unused frontend package removed

- **GIVEN** a package declared in `web/package.json` that is not imported by any frontend source module or test
- **WHEN** the dependency list is updated
- **THEN** the package is removed from `web/package.json`
- **AND** no frontend source module or test imports that package

#### Scenario: Frontend lockfile stays consistent

- **GIVEN** an updated `web/package.json`
- **WHEN** `pnpm install` is run
- **THEN** `web/pnpm-lock.yaml` is regenerated consistently with the manifest
- **AND** `pnpm install` reports no missing or extraneous packages

### Requirement: Dependency updates keep verification green

Rule: Updating or removing dependencies SHALL not break the backend test suite, the frontend test suite, or the frontend production build.

#### Scenario: Backend tests pass after dependency changes

- **GIVEN** updated and pruned backend dependencies
- **WHEN** the backend test suite runs
- **THEN** all backend tests pass

#### Scenario: Frontend tests and build pass after dependency changes

- **GIVEN** updated and pruned frontend dependencies
- **WHEN** the frontend test suite runs and the production build runs
- **THEN** all frontend tests pass
- **AND** the production build completes successfully

### Requirement: Removed frontend chart artifacts leave no dangling imports

Rule: When the legacy vue-chartjs stack is removed, no frontend module SHALL retain a broken import of the removed plugin or its packages.

#### Scenario: Removed chart plugin file has no live references

- **GIVEN** the legacy `chart.js`-based `monthHeaderPlugin` is removed
- **WHEN** the frontend source is scanned for references to it
- **THEN** only its own removed test file references it
- **AND** the still-needed `MonthLabel` interface is available from the location components import
- **AND** the frontend build and tests pass