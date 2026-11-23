---
name: jbehave-authoring
description: Use when drafting, reviewing, or improving JBehave stories, Narrative/Meta/Scenario blocks, BDD acceptance criteria for the jira-driven schema, ExamplesTable data, GivenStories, Lifecycle blocks, or JBehave embedded in Markdown.
---

# JBehave Authoring

## Overview

Write JBehave stories as executable examples of business behavior. Optimize for domain language, concrete examples, and observable outcomes; keep implementation and UI mechanics inside step implementations (Java `@Given`/`@When`/`@Then` methods).

## Scope

Use this for standalone `.story` files and JBehave embedded in Markdown or other prose (the `jira-driven` schema's `spec.md` files). When JBehave is inside a Markdown wrapper, review or rewrite only the JBehave section unless the user asks for broader document edits. Preserve fences, headings, and surrounding prose (including `<!-- AC: TICKET-ID#N -->` traceability comments). If the input includes Markdown around the JBehave block, return the Markdown wrapper with only the JBehave block changed.

## Workflow

1. Identify the JBehave region: whole `.story` file, fenced `jbehave` block, or inline scenario text.
2. Preserve the surrounding wrapper unless explicitly asked to change it. For Markdown input, return the heading/prose/fence context, not just the fenced block.
3. Clarify the behavior as examples: initial state, event, observable outcome.
4. Choose the smallest structure that expresses the behavior: one `Narrative:` per story, a `Meta:` block naming the `@requirement` and any `@openspec` delta marker, one or more `Scenario:`, and `ExamplesTable:` only when data varies.
5. Keep scenarios concrete and short, usually 3-5 steps.
6. Review syntax and readability before returning: keyword spelling, no colon after step keywords, Meta tag placement, and table formatting.

## Quick Reference

| Construct | Use for | Syntax note |
| --- | --- | --- |
| `Narrative:` | One high-level capability per story/spec.md | Followed by `In order to` / `As a` / `I want` lines; no colon on those three |
| `Meta:` | Tags for the following Scenario(s) | One `@tag value` per line; carries `@requirement <name>` and `@openspec <op>` for this schema |
| `Scenario:` | One concrete example | Requires `:`; no `Feature:` or `Rule:` wrapper in JBehave |
| `GivenStories:` | Compose in outcomes of other stories as setup | Comma-separated story paths |
| `Lifecycle:` | Shared Before/After steps for all scenarios in the story | Rare; prefer explicit Given steps |
| `Given` | Known state or precondition | No `:` (unlike Gherkin's `Given:` look-alikes, JBehave also omits it) |
| `When` | Event or action | No `:` |
| `Then` | Observable outcome | No `:` |
| `And` | Continue the previous step type | No `:` |
| `ExamplesTable:` | Data rows for repeating the same steps with varied data | JBehave's equivalent of Gherkin's `Examples:`; `|`-delimited table directly under the scenario steps |
| `!--` | Comment | JBehave story comment syntax; use sparingly, prefer Markdown prose outside the fence |

## Authoring Rules

- Use the language domain experts use. Avoid translating business behavior into UI clicks, HTTP calls, database rows, queues, mocks, or implementation details.
- `Given` puts the system in a known state. Avoid user interaction in `Given` steps.
- `When` describes one meaningful event.
- `Then` describes an outcome visible to a user or external system. Do not assert hidden database state unless that is the actual external contract.
- Use `And` to improve flow, not to hide new phases of the scenario.
- Never put a colon after `Given`, `When`, `Then`, or `And` - that is Gherkin syntax and breaks JBehave's parser.
- One `Narrative:` per spec.md / story. Do not nest a second `Narrative:` inside the same fence.
- Group every `Scenario:` under a `Meta:` block that names its `@requirement`; this is how the jira-driven schema's extractor knows which scenarios form one requirement, since JBehave has no native `Rule:` keyword.
- Use two-space indentation for step continuation only if the project already does; JBehave itself does not require indentation.
- Use `ExamplesTable:` only when examples share the same behavior and differ by data.
- Keep `GivenStories:` and `Lifecycle:` out of specs authored for this schema unless the design explicitly calls for cross-story composition; they add indirection that is hard to review as a delta.

## Example

Markdown wrapper preserved; only the JBehave block is authored:

````markdown
<!-- AC: PROJ-123#2 -->

```jbehave
Narrative:
In order to keep my account secure
As a registered user
I want my password reset link to expire

Meta:
@requirement Reset links expire after their allowed lifetime
@openspec ADDED

Scenario: Customer resets their password before the link expires
Given Priya has requested a password reset
And the reset link is still valid
When Priya chooses a new password with the reset link
Then she can sign in with the new password

Scenario: Customer uses an expired reset link
Given Priya has requested a password reset
And the reset link has expired
When Priya tries to choose a new password with the reset link
Then she is told the reset link has expired
And her password is unchanged
```
````

## Common Mistakes

| Mistake | Fix |
| --- | --- |
| Complaining about Markdown around a JBehave block | Preserve the wrapper and work only on the JBehave section. |
| Returning only a fenced JBehave block when the input was Markdown | Return the original Markdown wrapper with only the JBehave content changed. |
| `Given:` / `When:` / `Then:` with a trailing colon | Remove the colon; JBehave step keywords never take one. |
| Writing `Feature:` or `Rule:` | JBehave has neither; use `Narrative:` once per story and `@requirement` in `Meta:` for grouping. |
| `Given I click the checkout button` | Move interaction to `When`; describe state in `Given`. |
| `Then an order row exists in the database` | Prefer an observable result, such as an order confirmation. |
| Missing `@requirement` tag on a Scenario | Add a `Meta:` block above the scenario naming its requirement, so delta operations and requirement grouping resolve correctly. |
| Missing `<!-- AC: TICKET-ID#N -->` for Jira-sourced capabilities | Add the traceability comment directly above the `Meta:`/`Scenario:` block that satisfies that Acceptance Criterion. |
