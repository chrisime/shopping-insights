---
name: acceptance-test-authoring
description: Use when creating or modifying acceptance tests, configuring cucumber-js or behave runners, writing or refactoring step definitions, linting executable Gherkin specs, choosing an acceptance stack, or implementing OpenSpec tasks that involve acceptance tests.
---

# Acceptance Test Authoring

The acceptance suite executes specs that live under `openspec/` against the running application. Specs are Markdown files named `spec.md` that hold prose plus behaviour scenarios inside fenced code blocks - classic Gherkin for every schema in this project (`intent-driven`/`behaviour-driven`/`jira-driven`). The runner extracts the fenced block into real `.feature` (Gherkin) files on every run.

Everything in this file is stack-agnostic. Tool-specific filenames, dependencies, commands, and examples live in the stack packs. The fence keyword and file extension differ per stack; note it below where it does.

## Choosing The Stack

The project's acceptance stack is declared as `stack:` in `openspec/config.yaml`:

```yaml
schema: jira-driven
stack: java             # javascript | python | java
```

Resolve it in this order:

1. Use `stack:` in `openspec/config.yaml`.
2. If absent and `acceptance-tests/` already exists, infer it from contents: `cucumber.cjs` means `javascript`, `behave.ini` means `python`, `pom.xml` means `java`; offer to record it.
3. Otherwise ask. Never guess silently, and never scaffold a runner without a recorded value. The `jira-driven` schema authors Gherkin just like `intent-driven` - the stack is whichever Gherkin runner fits the project (`javascript` or `python`).

Adding `stack:` is a specs-zone edit under `openspec/`, so commit or stash code-zone work first. See `bdd-zone-check`.

## Reference Files

| Stack | Pack | Runner | Fence | Extracted file |
| --- | --- | --- | --- | --- |
| `javascript` | [references/javascript/SETUP.md](references/javascript/SETUP.md) | cucumber-js | ` ```gherkin ` | `.feature` |
| `python` | [references/python/SETUP.md](references/python/SETUP.md) | behave 1.2.7+ | ` ```gherkin ` | `.feature` |

Note: the `java`/JBehave stack pack is intentionally not shipped here; this project removed it when `jira-driven` moved to Gherkin.

Each pack has a **Files to copy** table naming every destination filename and why it is load-bearing. Copy those files verbatim; they are the canonical runner.

[references/gherkin-lintrc.json](references/gherkin-lintrc.json) is copied to `acceptance-tests/.gherkin-lintrc` by the `javascript` and `python` stacks.

## Spec Format And Extraction

The rest of this section, **Runner Invariants**, **Effective-Spec Composition**, and **Port Parity** describe the Gherkin contract shared by the `javascript` and `python` stacks.

A spec is `openspec/specs/<capability>/spec.md` (source of truth) or `openspec/changes/<id>/specs/<capability>/spec.md` (delta). Markdown prose may appear anywhere; only ` ```gherkin ` fences are executable.

- Fences open with ` ```gherkin ` at column 0 and close with at least as many backticks at column 0.
- A file may hold multiple gherkin fences; concatenated in file order they must form exactly one `Feature:` document.
- Tags stay in the same fence as, and directly above, the `Feature:` line.
- `# @openspec:` delta markers are ordinary Gherkin comments inside a fence, immediately above their `Rule:`.

Extraction writes each `spec.md` to `acceptance-tests/.extracted/<same-relative-path>/spec.feature`. Line fidelity is the core invariant: lines inside Gherkin fences are copied verbatim at their original positions; every other line becomes an empty line. The extracted file has the identical line count, so line N of the `.feature` is line N of the `.md`. Never collapse blank lines.

`.extracted/` is gitignored, wiped and rebuilt on every run, and never edited by hand. The wipe is an invariant, not an optimization.

Extraction edge cases are deliberate and must match across stacks:

| Case | Behavior |
| --- | --- |
| Unclosed fence | Error with `file:line` of the opener |
| Zero gherkin fences in a `spec.md` | Error; a spec must contain gherkin |
| Indented ` ```gherkin ` opener | Hard error; silently ignoring it would drop scenarios |
| ` ```gherkin extra-text ` | Not a gherkin opener; treated as an ordinary fence |
| Non-gherkin fences | Tracked and blanked |
| Gherkin docstrings delimited by ` ``` ` | Safe because docstrings are indented |
| Files other than `spec.md` | Ignored |
| Legacy `.feature` files under `openspec/` | Never run; extraction prints a warning |

## Runner Invariants

1. `acceptance-tests/` is an independent test project at the repo root. Its hooks boot the application before the suite and shut it down after, so the suite must run with a single command.
2. The default run executes the effective spec: every source-of-truth spec with every active change delta applied.
3. Superseded source-of-truth rules marked `MODIFIED` or `REMOVED` by active deltas must not reach the runner and must not be reported as skipped.
4. A green effective suite is the gate for sync/archive, and sync/archive must never change suite results.
5. Specs under `openspec/changes/archive/` must never execute.
6. Provide a source-of-truth-only regression run that executes `openspec/specs/` as-is.
7. Every test run generates an HTML report under `acceptance-tests/reports/`.
8. Verify composition whenever the runner config, extractor, or `openspec/` tree changes.

## Effective-Spec Composition

The procedure below is normative. Stack packs ship implementations; the implementations are not the definition.

1. Extract every `spec.md` under `openspec/specs/` and active `openspec/changes/*/specs/`; archive is excluded.
2. Collect active delta feature files.
3. Scan delta files for `# @openspec: <OP>` comments bound to the next `Rule:` line.
4. Exclude superseded source-of-truth scenarios from the run without editing specs.
5. Add every delta file whole.
6. Print a composition report to stderr for every left-out scenario.

Sanctioned exclusion bindings:

| Binding | Use when |
| --- | --- |
| Line-targeted discovery | The runner filters before loading, as cucumber-js does with `spec.feature:12:19`. |
| Pruning the extracted tree | Line selection would runtime-skip, as behave does. Blank generated `.extracted/` lines rather than editing specs. |

Composition report format is identical across stacks:

```text
[effective-spec] user-signup / Rule: A signup SHALL require an email address and a password
[effective-spec]   superseded by change: signup-email-verification
[effective-spec]   left out: Signing up with valid details (../openspec/specs/user-signup/spec.md:12)
[effective-spec] 1 source-of-truth scenario(s) excluded; delta versions run from openspec/changes/
```

## Port Parity

The extraction edge-cases table and the composition-report format are the contract between stacks. A change to one implementation must be mirrored in the other and re-verified. The strongest check is a cross-stack dry run on the same `openspec/` tree: the same scenario count and names.

## Linting Specs

Spec linting is shared across stacks: gherkin-lint over the extracted output with the pinned `.gherkin-lintrc`.

- Extract first, then lint; pass `.extracted` as a directory argument.
- gherkin-lint has no default rules; it requires `.gherkin-lintrc`.
- Reported line numbers are valid in source `spec.md` files.

Before an `acceptance-tests/` project exists, run the extractor from this skill:

```sh
node .agents/skills/acceptance-test-authoring/references/javascript/extract-gherkin.cjs openspec acceptance-tests/.extracted \
  && npx gherkin-lint --config .agents/skills/acceptance-test-authoring/references/gherkin-lintrc.json acceptance-tests/.extracted
```

The Python extractor is a drop-in substitute:

```sh
python .agents/skills/acceptance-test-authoring/references/python/extract_gherkin.py openspec acceptance-tests/.extracted
```

## Page Object Model

Step definitions must read as intent; all UI knowledge lives in page objects.

- Page objects live under `acceptance-tests/`, one per screen or flow.
- Page objects encapsulate routes, form field names, selectors, and ids.
- Parse responses with the stack's HTML parser, never with regexes over raw HTML.
- Page objects expose intent-level methods such as `open()`, `submit_signup(...)`, `error_message()`, and `confirmation_link()`.
- Step definitions contain no selectors, regexes, or URLs; only page-object calls and assertions.
- The World stays a thin HTTP client and state holder.

## Workflow Cadence

Implement one pending step definition at a time: run the suite so the step fails for the right reason, implement until it passes, then commit. The effective suite's red scenarios at propose time are the change's work list. Finish only when every scenario passes with zero pending or undefined steps and the HTML report is generated.
