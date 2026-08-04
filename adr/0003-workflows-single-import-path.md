# ADR-0003: Single shared local-import path with one thin workflow base

## Status

Accepted

## Date

2026-08-04

## Context and Problem Statement

The workflow layer (`workflows/`) stacks two abstractions for two retailers: `ImportWorkflow` (template-method base: download → import → summary) and `ImportPipeline` (ABC: load → parse → validate → persist), each with Lidl and REWE subclasses. Two retailers do not justify this two-tier inheritance; the pipeline ABC adds a second abstraction level while contributing only a loader hook and a handful of configurable values. The project also wants a general commitment against interface-only abstraction layers and dependency-injection frameworks.

## Considered Options

- Collapse `ImportPipeline` into one shared function and keep only the `ImportWorkflow` base
- Keep both ABCs as-is
- Merge `ImportPipeline` into `ImportWorkflow`
- Flatten everything to standalone functions (no base at all)

## Decision Outcome

Chosen option: "Collapse `ImportPipeline` into one shared function and keep only the `ImportWorkflow` base", because the download-then-import lifecycle is the one real shared behavior (a base is justified), while the pipeline orchestration is expressible as a plain function with a `loader` callable and a config record — removing the second inheritance tier without adding any new abstraction. No new ABCs or DI frameworks are introduced; SOLID is applied via plain functions and parameter injection.

### Consequences

- Good, because the workflow layer reduces from two abstraction tiers to one thin base plus a shared `import_local_sources()` path.
- Good, because a future third retailer follows the same single shared path instead of new subclasses.
- Bad, because retailer-specific pipeline hooks move from subclass overrides to callable/config parameters, so readers must pass them explicitly at call sites.
- Follow-up: if the base later becomes trivially thin, flattening it to functions can be a separate refactor.
