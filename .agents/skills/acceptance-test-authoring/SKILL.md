---
name: acceptance-test-authoring
description: How to set up and write acceptance tests for this project — specs are Markdown (spec.md) with fenced Gherkin, extracted to .feature files at test time; runner configuration for either supported stack (JavaScript/cucumber-js or Python/behave) covering extraction, effective-spec composition of source-of-truth and active delta specs, archive exclusion, and the HTML report; spec linting over the extracted output; Page Object Model conventions for step definitions. Use when creating or modifying anything under acceptance-tests/, configuring the cucumber-js or behave runner, writing or refactoring step definitions, linting specs, choosing or reading the project's acceptance stack, or implementing tasks from an OpenSpec change that involve acceptance tests.
---

# Acceptance Test Authoring

The acceptance suite executes the Gherkin specs that live under `openspec/` against the running application. Specs are **Markdown files** (`spec.md`) holding prose plus classic Gherkin inside fenced code blocks; the runner **extracts** the Gherkin into real `.feature` files on every run. Three sets of rules govern the suite: **spec format and extraction** (how Gherkin gets out of the Markdown), **runner invariants** (what the suite runs and how), and **code organization** (Page Object Model).

Everything in this file is stack-agnostic. The tool-specific half — filenames, dependencies, commands — lives in the stack packs.

## Choosing the stack

The project's acceptance stack is declared as `stack:` in `openspec/config.yaml`:

```yaml
schema: behavior-driven
stack: javascript      # javascript | python
```

Resolve it in this order:

1. `stack:` in `openspec/config.yaml`.
2. If absent and `acceptance-tests/` already exists, infer it from the contents (`cucumber.cjs` → javascript, `behave.ini` → python) and offer to record it.
3. Otherwise **ask**. Never guess silently, and never scaffold a runner without a recorded value.

`openspec/config.yaml` is in the **specs zone**, so adding `stack:` is a specs-zone edit that must be committed on its own, before any `acceptance-tests/` scaffolding begins. See the `bdd-zone-check` skill.

## Reference files — pick your stack

| Stack | Pack | Runner |
|---|---|---|
| `javascript` | [references/javascript/SETUP.md](references/javascript/SETUP.md) | cucumber-js |
| `python` | [references/python/SETUP.md](references/python/SETUP.md) | behave 1.2.7+ |

Each pack has a **Files to copy** table naming every destination filename and why it is load-bearing, plus that stack's dependencies, commands, verification steps and Page Object Model example. Copy the files verbatim — they are the canonical runner.

[references/gherkin-lintrc.json](references/gherkin-lintrc.json) sits at the `references/` root and is copied to `acceptance-tests/.gherkin-lintrc` by **both** stacks: spec linting is shared, so both accept and reject exactly the same specs.

## Spec format and extraction

A spec is `openspec/specs/<capability>/spec.md` (source of truth) or `openspec/changes/<id>/specs/<capability>/spec.md` (delta). Markdown prose — headings, rationale, links — may appear anywhere; **only ` ```gherkin ` fences are executable**:

- Fences open with ` ```gherkin ` at **column 0** (3+ backticks, info string exactly `gherkin`) and close with at least as many backticks at column 0.
- A file may hold **multiple gherkin fences**; concatenated in file order they must form exactly **one `Feature:` document**. Gherkin ignores blank lines, so prose gaps between fences are harmless.
- Tags stay **in the same fence as** (directly above) the `Feature:` line.
- `# @openspec:` delta markers are ordinary gherkin comments **inside a fence**, immediately above their `Rule:`.

Extraction writes each `spec.md` to `acceptance-tests/.extracted/<same-relative-path>/spec.feature`. **Line fidelity is the core invariant**: lines inside gherkin fences are copied verbatim at their original positions; every other line (prose, fence markers, non-gherkin fence bodies) becomes an empty line, so the extracted file has the IDENTICAL line count and line N of the `.feature` is line N of the `.md`. gherkin-lint messages, runner failure locations and effective-spec composition all point at valid `spec.md` lines with zero translation. **Never "improve" the extractor to collapse blank lines.**

Path mapping: runner output and the HTML report show extracted paths — read `.extracted/X/spec.feature:N` as `openspec/X/spec.md:N` (same line number, always).

`.extracted/` is **gitignored, wiped and rebuilt on every run, and never edited by hand**. The wipe is an invariant, not an optimization — a stale extraction would keep deleted or renamed capabilities executing.

Extraction edge cases (all deliberate — silent drops are the failure mode to fear). **Both stacks classify every row identically**, with the same message and the same `file:line`:

| Case | Behavior |
|---|---|
| Unclosed fence | Error with `file:line` of the opener |
| Zero gherkin fences in a `spec.md` | Error — a spec must contain gherkin |
| Indented ` ```gherkin ` opener | **Hard error** — silently ignoring it would silently drop scenarios |
| ` ```gherkin extra-text ` | Not a gherkin opener (info string must be exactly `gherkin`) — treated as an ordinary fence, contents blanked |
| Non-gherkin fences (` ```js `, plain ` ``` `, 4+ backticks) | Tracked, contents blanked — a ` ```gherkin ` quoted inside a longer documentation fence cannot false-trigger |
| Gherkin docstrings delimited by ` ``` ` | Safe — docstrings are indented; fence closers require column 0 |
| Files other than `spec.md` | Ignored — discovery globs are anchored to `spec.md` (proposal/design/tasks excluded structurally) |
| Legacy `.feature` files under `openspec/` | Never run — extraction prints a WARNING naming them |

## Runner invariants

1. `acceptance-tests/` is an **independent test project in the configured stack**, at the repo root. Its hooks boot the application before the suite and shut it down after — the suite must be runnable with a **single command**. The repo `.gitignore` covers `acceptance-tests/.extracted/` and `acceptance-tests/reports/`.
2. The default run executes the **effective spec**: every `openspec/specs/**/spec.md` (source of truth) with every **active** change's delta (`openspec/changes/*/specs/**/spec.md`) applied — i.e. exactly what the source of truth will become once those changes are synced/archived — extracted to `.extracted/` and composed there. Composition, per `Rule:` in an active delta:

   | Rule in an active delta   | Source-of-truth version | Delta version  |
   |---------------------------|-------------------------|----------------|
   | (untouched)               | runs                    | —              |
   | `# @openspec: ADDED`      | —                       | runs           |
   | `# @openspec: MODIFIED`   | **not discovered**      | runs           |
   | `# @openspec: REMOVED`    | **not discovered**      | (no scenarios) |
   | `# @openspec: RENAMED`    | runs (name change only) | (no scenarios) |

3. Superseded rules (MODIFIED/REMOVED by an active delta) must **not reach the runner** and must **not be reported as skipped**. **Never edit or tag the spec files to skip them** — the source of truth stays pristine until sync — and never let them show up as skipped counts, which pollute the zero-pending completion signal: a superseded rule is replaced, not unfinished. The mechanism differs per stack (see [Effective-spec composition](#effective-spec-composition), step 4); the observable contract does not. Every exclusion is announced via the composition report on stderr — an excluded scenario must never be silently absent from results or the HTML report.
4. **A green effective suite is the gate for sync/archive — and sync/archive must never change suite results.** At propose time the suite goes red on exactly the delta's new/changed scenarios (that red set is the implementation work list); at completion it is fully green; syncing and archiving then only collapse the composition back to the source of truth. Never sync or archive on red.
5. **Specs under `openspec/changes/archive/` must NEVER execute.** Archived changes are historical deltas already merged into `openspec/specs/`; running them re-executes stale duplicates. This is non-negotiable. The extractor already skips the archive (nothing under `changes/archive/` reaches `.extracted/`), and the composition filters it again — defense in depth.
6. Alongside the default run, provide a **source-of-truth-only regression run** that executes `openspec/specs/` as-is, freshly extracted by the same entry point.
7. Every test run generates an **HTML report** under `acceptance-tests/reports/`.
8. **Verify the composition** whenever the runner config, the extractor, or the `openspec/` tree changes: do a dry run and confirm `.extracted/` was rebuilt, no loaded scenario originates from `openspec/changes/archive/`, no scenario appears twice, and no scenario of a superseded source-of-truth rule is loaded. The per-stack commands are in the pack's SETUP.md.

## Effective-spec composition

The **procedure below is normative**. Each stack pack ships an implementation of it; neither implementation is the definition.

1. **Extract** — every `spec.md` under `openspec/specs/` and `openspec/changes/*/specs/` (archive excluded) becomes `.extracted/<same-path>/spec.feature` with identical line numbers.
2. **Collect active deltas** — every `.extracted/changes/*/specs/**/*.feature`, with a defensive `changes/archive/` filter.
3. **Extract superseded rules** — scan each delta for `# @openspec: <OP>` marker comments bound to the next `Rule:` line (use the regexes from the schema's `format:` block); record `(capability, rule name)` for MODIFIED and REMOVED. The capability is the path segment after the delta's last `specs/`. ADDED and RENAMED supersede nothing. **Fail** if two active changes supersede the same rule; **warn** if a superseded rule doesn't exist in the source of truth (delta drift).
4. **Exclude the superseded scenarios from the run.** The goal is invariant 3: they must not reach the runner, and must not be reported as skipped. Two sanctioned bindings, chosen by what the runner actually supports:
   - **Line-targeted discovery**, where the runner genuinely filters before loading — cucumber-js `spec.feature:12:19` loads only the scenarios starting at those lines. Nothing is written back to `.extracted/`.
   - **Pruning the extracted tree**, where line selection would merely runtime-skip — behave reports every unselected scenario as skipped, and no flag suppresses that count, so the superseded `Rule:` blocks are blanked out of `.extracted/` and whole files are passed instead.

   Pruning is not a spec edit: `.extracted/` is a generated artifact, gitignored and rebuilt every run, so the source of truth stays pristine — which is what invariant 3 protects. Blank the lines rather than deleting them, so line fidelity survives. Omit a file entirely if no scenario survives; include untouched files whole.
5. **Add every delta file whole.**
6. **Print the composition report** to stderr — each superseded rule, the change that superseded it, and every left-out scenario with its **source `spec.md`** `file:line` (identical line numbers, by line fidelity), plus a summary count, so an excluded scenario is never silently absent from results or reports. **This format is identical across stacks:**

   ```
   [effective-spec] user-signup / Rule: A signup SHALL require an email address and a password
   [effective-spec]   superseded by change: signup-email-verification
   [effective-spec]   left out: Signing up with valid details (../openspec/specs/user-signup/spec.md:12)
   [effective-spec]   left out: Rejecting a signup with no email (../openspec/specs/user-signup/spec.md:37)
   [effective-spec] 2 source-of-truth scenario(s) excluded; delta versions run from openspec/changes/
   ```

### Port parity

The extraction edge-cases table and the composition-report format are **the contract between the stacks**. A change to one implementation must be mirrored in the other and re-verified — otherwise the two silently drift and the same specs start meaning different things.

The strongest check is a cross-stack dry run on the same `openspec/` tree: **the same scenario count and the same scenario names**. Run it first after touching either extractor or either composition module. The per-stack dry-run commands are in the packs.

## Linting specs

Spec linting is **shared across stacks**: gherkin-lint over the extracted output, with the one pinned `.gherkin-lintrc`. That is deliberate — a stack-native linter would accept a different set of specs, and specs are the thing both stacks are supposed to agree on.

- Extract first, then lint; pass `.extracted` as a **directory argument** — a quoted `'**'` glob silently matches nothing through the dot-directory.
- gherkin-lint has **no default rules**; it requires `.gherkin-lintrc`. The pinned off-rules are load-bearing: whitespace rules (`no-multiple-empty-lines`, `new-line-at-eof`, `indentation`) would flood on the extraction's blank-line padding, and the dupe-name rules fire on legitimate SOT/delta pairs (same Feature name; MODIFIED deltas copy scenario names). Without them, "fix all lint issues" is unsatisfiable.
- Reported line numbers are valid in the source `spec.md` files.
- Known limitation: gherkin-lint's AST rules do not descend into `Rule:` children, so e.g. `no-unnamed-scenarios` misses scenarios nested under a Rule. Line-based rules (trailing spaces, tags) and feature-level rules work fine.

Linting a spec **before** an `acceptance-tests/` project exists (e.g. from a specs-authoring session) — run the extractor straight from the skill references, then lint. With the JS extractor (no venv needed):

```sh
node .agents/skills/acceptance-test-authoring/references/javascript/extract-gherkin.cjs openspec acceptance-tests/.extracted \
  && npx gherkin-lint --config .agents/skills/acceptance-test-authoring/references/gherkin-lintrc.json acceptance-tests/.extracted
```

The Python extractor is a drop-in substitute (`python .agents/skills/acceptance-test-authoring/references/python/extract_gherkin.py openspec acceptance-tests/.extracted`) — both are dependency-free and produce byte-identical output. The output dir is gitignored; writing it via Bash does not violate the spec/code zone split, which guards file edits only.

## Page Object Model

Step definitions must read as intent; all knowledge of the UI lives in page objects.

- Page objects live under `acceptance-tests/`, **one per screen or flow** (e.g. a signup page, a login page, a dashboard page).
- A page object encapsulates **all UI identifiers**: routes/URLs, form field names, CSS selectors and element ids. Parse responses with the stack's HTML parser — **never with regexes over raw HTML**.
- Page objects expose **intent-level methods**, e.g. `open()`, `submit_signup(...)`, `error_message()`, `confirmation_link()`. They receive the World (or its HTTP client) and use it for requests.
- Step definitions contain **no selectors, no regexes, no URLs** — only page-object calls and assertions.
- The World stays a thin HTTP client (request/response state, redirect helper). It holds page-object instances; it does not parse pages itself.
- When the UI changes an identifier, exactly one page object should need editing.

The per-stack idioms and a worked example are in each pack's SETUP.md.

## Workflow cadence

Implement one pending step definition at a time: run the suite so the step **fails for the right reason** (red), implement until it **passes** (green), then **commit**. The effective suite's red scenarios at propose time are exactly the change's work list. Finish only when every scenario passes with zero pending/undefined steps and the HTML report is generated — then, and only then, sync and archive.
