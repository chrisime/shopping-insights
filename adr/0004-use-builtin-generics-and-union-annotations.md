# ADR-0004: Use built-in generics and union annotations

## Status

Accepted

## Date

2026-08-04

## Context and Problem Statement

Annotations across the codebase still use pre-3.10 `typing` generics (`Optional[...]`, `List[...]`, `typing.List`, …). The project runs Python 3.12/3.14, where PEP 585 built-in generics (`list[...]`, `dict[...]`) and PEP 604 unions (`X | None`) are supported and idiomatic. The legacy forms add imports and noise without adding compatibility value.

## Considered Options

- Modernize to PEP 585/604 built-in generics and `X | None`
- Keep legacy `typing` generics
- Use a code-mod tool to rewrite automatically

## Decision Outcome

Chosen option: "Modernize to PEP 585/604 built-in generics and `X | None`", because it is the modern idiomatic form, is runtime-safe on the supported Python versions, and requires no new tooling (a mechanical in-repo pass is covered by the existing test suite). `Callable`, `TypeVar`, and `Any` remain only where genuinely needed; `from __future__ import annotations` stays where already present and is added only when a deferred name is required.

### Consequences

- Good, because annotations are shorter, imports are fewer, and the codebase reads as modern Python.
- Good, because no new dependency or tooling is introduced.
- Bad, because the sweep touches many files at once and must be verified by the full suite and pyright after each commit.
