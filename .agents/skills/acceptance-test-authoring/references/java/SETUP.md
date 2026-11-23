# Java Stack - JBehave

For `stack: java` in `openspec/config.yaml`, used by the `jira-driven` schema.
Read the skill's `SKILL.md` first: it holds the spec format, invariants, and
effective-spec procedure this pack implements (partially - see Known Gaps
below).

Requires Java 17+, Maven, and `python3` on `PATH` (the extraction step is a
Python script, reused across stacks for consistency; only the runner itself
is Java/JBehave).

## Files To Copy

Copy into `acceptance-tests/` at the repo root. Destination filenames are
load-bearing.

| Source | Destination | Why the name is fixed |
| --- | --- | --- |
| `java/extract_jbehave.py` | `extract_jbehave.py` | invoked by the Maven `exec-maven-plugin` binding in `pom.xml` |
| `java/pom.xml` | `pom.xml` | Maven's fixed project descriptor name |
| `java/src/test/java/openspec/acceptance/AcceptanceStories.java` | `src/test/java/openspec/acceptance/AcceptanceStories.java` | JUnit entry point Maven's `mvn test` discovers by Surefire's default `*Stories`/`*Test` patterns |
| `java/src/test/java/openspec/acceptance/StepDefinitions.java` | `src/test/java/openspec/acceptance/StepDefinitions.java` | wired into `AcceptanceStories` by class reference |

## Required Layout

```text
acceptance-tests/
  pom.xml
  extract_jbehave.py
  src/test/java/openspec/acceptance/
    AcceptanceStories.java
    StepDefinitions.java
  .extracted/  reports/    # generated, gitignored
```

## Commands

```sh
mvn test                 # extracts specs (via the pom.xml plugin binding), then runs the effective spec
mvn -q exec:exec@extract-jbehave-specs   # extraction only, for inspection
```

There is no `--specs`, `--lint`, `--print-locations`, or `--dry-run` flag
here yet - unlike the javascript and python packs, this pack does not ship a
wrapper script. If your project needs those, port `run_acceptance.py`'s CLI
surface from the python pack; the extraction step (`extract_jbehave.py`) is
already line-for-line equivalent to `extract_gherkin.py`, just for the
`jbehave` fence and `.story` output instead of `gherkin`/`.feature`.

## Known Gaps (compared to the javascript/python packs)

This pack is a functional starting point, not a full port of every invariant
in `SKILL.md`:

- **Effective-spec composition and exclusion** (superseded `@requirement`
  groups from active deltas must not reach the runner and must not show as
  skipped) is **not implemented**. `AcceptanceStories` currently runs every
  `.story` file under `.extracted/` unfiltered - source-of-truth and delta
  side by side. Port `python/openspec_effective_spec.py`'s composition logic
  (keyed on `@requirement`/`@openspec` Meta tags instead of `Rule:` comments)
  before relying on this for real ADDED/MODIFIED/REMOVED merges.
- **Composition report to stderr** for left-out scenarios is not implemented.
- **`.gherkin-lintrc`-equivalent linting** for JBehave stories is not
  wired up; JBehave has no widely-used standalone linter analogous to
  `gherkin-lint`. Rely on the `jbehave-authoring` skill's authoring rules and
  manual review instead.

Treat this pack the way the project treats `.opencode`/`.agents` skills in
general: adapt it further as real usage surfaces gaps, the same way
`jira-driven` was forked from `intent-driven` rather than editing it in
place.

## HTML Report

`AcceptanceStories.configuration()` requests `Format.HTML` with
`withRelativeDirectory("reports")`, so JBehave writes to
`acceptance-tests/reports/` - mirroring where the javascript/python packs put
their reports.

## Page Objects / Step Implementation

Keep step implementations in `StepDefinitions.java` (or split into
page-object-style helper classes as the suite grows) thin: call into
application/page-object code, assert on observable outcomes, and keep
business language out of Java method bodies - the same separation the
`jbehave-authoring` skill asks for in the stories themselves.
